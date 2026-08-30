"""Polite, cached HTTP fetching with SSL diagnosis.

Rules enforced here so no stage has to remember them:
  * 1-2s randomised delay between requests, additionally enforced per host
  * robots.txt consulted before every company-site fetch
  * identifiable user agent
  * every outcome cached, including failures
  * TLS problems classified rather than swallowed, because an expired
    certificate is one of the strongest buying signals in this dataset
"""
from __future__ import annotations

import logging
import random
import socket
import ssl
import time
import urllib.robotparser
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse

import requests
from requests.exceptions import (
    ConnectionError as ReqConnectionError,
    ProxyError,
    ReadTimeout,
    SSLError,
    TooManyRedirects,
)

from . import config
from .store import Cache, CachedResponse

log = logging.getLogger("leadgen")

# A proxy that rejects one host rejects them all. Past this many failures in a
# row with nothing succeeding in between, the run is producing no information
# and should stop rather than spend an hour confirming the network is down.
PROXY_ERROR_CIRCUIT_BREAK = 12


class EgressBlocked(RuntimeError):
    """Raised when every request is failing at the proxy layer."""


# ------------------------------------------------------------- URL helpers ---

def normalise_url(url: str) -> str:
    """Canonicalise for cache keys and comparison."""
    url = (url or "").strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url.lstrip("/")
    parts = urlparse(url)
    netloc = parts.netloc.lower().rstrip(".")
    if netloc.endswith(":443") and parts.scheme == "https":
        netloc = netloc[:-4]
    if netloc.endswith(":80") and parts.scheme == "http":
        netloc = netloc[:-3]
    path = parts.path or "/"
    return urlunparse((parts.scheme, netloc, path, "", parts.query, ""))


def registrable_host(url: str) -> str:
    """Host with a leading 'www.' removed. Not a full PSL implementation —
    enough to compare a candidate against a blocklist."""
    host = urlparse(normalise_url(url)).netloc.lower()
    if ":" in host:
        host = host.split(":", 1)[0]
    return host[4:] if host.startswith("www.") else host


def base_url(url: str) -> str:
    parts = urlparse(normalise_url(url))
    return f"{parts.scheme}://{parts.netloc}"


# ------------------------------------------------------ SSL classification ---

def diagnose_ssl(error_text: str) -> str:
    """Map an OpenSSL error string onto a stable label."""
    t = (error_text or "").lower()
    if "certificate has expired" in t or "certificate is not yet valid" in t:
        return "expired"
    if "hostname mismatch" in t or "doesn't match" in t or "no alternative certificate" in t:
        return "hostname_mismatch"
    if "self signed" in t or "self-signed" in t:
        return "self_signed"
    if "unable to get local issuer" in t or "unable to verify the first certificate" in t:
        return "untrusted_chain"
    if "sslv3" in t or "unsupported protocol" in t or "protocol version" in t:
        return "obsolete_protocol"
    if "wrong version number" in t or "record layer failure" in t:
        return "tls_handshake_failed"
    return "ssl_error"


def probe_certificate(host: str, port: int = 443, timeout: float = 8.0) -> dict[str, object]:
    """Read the certificate without validating it.

    requests only tells us that verification failed; to report *how many days*
    expired, we need the cert itself. Verification is disabled deliberately and
    only to read metadata — nothing fetched this way is trusted as content.
    """
    result: dict[str, object] = {"status": "unknown", "not_after": None, "days": None}
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as tls:
                der = tls.getpeercert(binary_form=True)
    except Exception as exc:  # noqa: BLE001 - diagnostic path, never fatal
        result["status"] = f"probe_failed:{type(exc).__name__}"
        return result

    if not der:
        return result
    try:
        from cryptography import x509

        cert = x509.load_der_x509_certificate(der)
        not_after = cert.not_valid_after_utc
        result["not_after"] = not_after.date().isoformat()
        days = (not_after - datetime.now(timezone.utc)).days
        result["days"] = days
        result["status"] = "expired" if days < 0 else "valid"
    except Exception as exc:  # noqa: BLE001
        result["status"] = f"parse_failed:{type(exc).__name__}"
    return result


# ---------------------------------------------------------------- fetcher ----

class Fetcher:
    def __init__(self, cache: Cache, offline: bool = False,
                 respect_robots: bool | None = None):
        self.cache = cache
        self.offline = offline
        self.respect_robots = config.RESPECT_ROBOTS if respect_robots is None else respect_robots
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": config.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.9",
        })
        self._last_request_at = 0.0
        self._host_last_at: dict[str, float] = {}
        self._robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}
        self.request_count = 0
        self.cache_hits = 0
        self.proxy_errors = 0
        self.consecutive_proxy_errors = 0

    # -- politeness --

    def _sleep(self, host: str) -> None:
        delay = random.uniform(config.MIN_DELAY_SECONDS, config.MAX_DELAY_SECONDS)
        now = time.monotonic()
        waits = [delay - (now - self._last_request_at)]
        if host in self._host_last_at:
            waits.append(delay - (now - self._host_last_at[host]))
        wait = max(waits)
        if wait > 0:
            time.sleep(wait)

    def _mark(self, host: str) -> None:
        now = time.monotonic()
        self._last_request_at = now
        self._host_last_at[host] = now

    # -- robots --

    def _robots_for(self, url: str) -> urllib.robotparser.RobotFileParser | None:
        host = urlparse(normalise_url(url)).netloc.lower()
        if host in self._robots:
            return self._robots[host]

        body = self.cache.get_robots(host)
        if body is None and not self.offline:
            robots_url = f"{base_url(url)}/robots.txt"
            try:
                self._sleep(host)
                resp = self.session.get(
                    robots_url,
                    timeout=(config.CONNECT_TIMEOUT, 10.0),
                    allow_redirects=True,
                )
                self._mark(host)
                self.request_count += 1
                # 4xx/5xx on robots.txt means "no restrictions published".
                body = resp.text if resp.status_code == 200 else ""
            except Exception:  # noqa: BLE001 - unreachable robots means allow
                body = ""
            self.cache.put_robots(host, body)
        if body is None:
            body = ""

        parser: urllib.robotparser.RobotFileParser | None = None
        if body.strip():
            parser = urllib.robotparser.RobotFileParser()
            parser.parse(body.splitlines())
        self._robots[host] = parser
        return parser

    def allowed(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        try:
            parser = self._robots_for(url)
        except Exception:  # noqa: BLE001
            return True
        if parser is None:
            return True
        try:
            return parser.can_fetch(config.USER_AGENT, normalise_url(url))
        except Exception:  # noqa: BLE001
            return True

    # -- the fetch itself --

    def get(self, url: str, check_robots: bool = True,
            allow_insecure_retry: bool = True) -> CachedResponse:
        """Fetch a URL, returning a CachedResponse in every case.

        Never raises for network conditions; the failure is reported in
        ``.error`` so the caller can log it and carry on.
        """
        url = normalise_url(url)
        if not url:
            return CachedResponse(url="", error="empty_url")

        cached = self.cache.get_response(url)
        if cached is not None:
            self.cache_hits += 1
            return cached

        if self.offline:
            return CachedResponse(url=url, error="offline_cache_miss")

        if check_robots and not self.allowed(url):
            resp = CachedResponse(url=url, error="robots_disallowed")
            self.cache.put_response(resp)
            return resp

        host = urlparse(url).netloc.lower()
        result = self._attempt(url, host)

        # An unverifiable certificate still leaves a site we want to audit. Try
        # once more without verification purely to collect page signals, and
        # keep the TLS verdict attached so scoring can use it.
        if (result.error and result.ssl_status and allow_insecure_retry
                and url.startswith("https://")):
            probe = probe_certificate(host.split(":")[0])
            if probe["status"] == "expired":
                result.ssl_status = "expired"
            insecure = self._attempt(url, host, verify=False)
            if insecure.status is not None:
                insecure.ssl_status = result.ssl_status
                insecure.error = None
                result = insecure

        self.cache.put_response(result)
        return result

    def _attempt(self, url: str, host: str, verify: bool = True) -> CachedResponse:
        last: CachedResponse | None = None
        for attempt in range(config.MAX_RETRIES + 1):
            self._sleep(host)
            try:
                resp = self.session.get(
                    url,
                    timeout=(config.CONNECT_TIMEOUT, config.READ_TIMEOUT),
                    allow_redirects=True,
                    verify=verify,
                    stream=True,
                )
                body = b""
                for chunk in resp.iter_content(65536):
                    body += chunk
                    if len(body) >= config.MAX_BYTES_PER_PAGE:
                        break
                resp.close()
                encoding = resp.encoding or resp.apparent_encoding or "utf-8"
                text = body.decode(encoding, errors="replace")
                self._mark(host)
                self.request_count += 1
                self.consecutive_proxy_errors = 0
                return CachedResponse(
                    url=url,
                    status=resp.status_code,
                    final_url=str(resp.url),
                    headers={k.lower(): v for k, v in resp.headers.items()},
                    body=text,
                    ssl_status="valid" if (verify and url.startswith("https://")) else None,
                )
            except SSLError as exc:
                # A TLS error proves we reached the host, so egress is fine.
                self._mark(host)
                self.request_count += 1
                self.consecutive_proxy_errors = 0
                return CachedResponse(
                    url=url, error=f"ssl_error: {exc}",
                    ssl_status=diagnose_ssl(str(exc)),
                )
            except ProxyError as exc:
                # A blocking or misconfigured proxy fails identically for every
                # host. Reporting it as dns_error would read as "this company's
                # domain is dead", which is exactly the wrong conclusion, so it
                # gets its own label and is not retried.
                self._mark(host)
                self.request_count += 1
                self.proxy_errors += 1
                self.consecutive_proxy_errors += 1
                if self.consecutive_proxy_errors >= PROXY_ERROR_CIRCUIT_BREAK:
                    raise EgressBlocked(
                        f"{self.consecutive_proxy_errors} consecutive proxy "
                        f"failures with no successful request. Outbound HTTPS "
                        f"appears blocked, so continuing would only mark every "
                        f"remaining company as unverifiable. Last error: {exc}"
                    ) from exc
                return CachedResponse(url=url, error=f"proxy_error: {exc}")
            except ReadTimeout as exc:
                last = CachedResponse(url=url, error=f"timeout: {exc}")
            except TooManyRedirects as exc:
                self._mark(host)
                return CachedResponse(url=url, error=f"redirect_loop: {exc}")
            except ReqConnectionError as exc:
                text = str(exc).lower()
                if "name or service not known" in text or "nodename nor servname" in text \
                        or "temporary failure in name resolution" in text \
                        or "getaddrinfo failed" in text:
                    # DNS resolution ran, so egress is working - this domain is
                    # genuinely dead, which is a real finding.
                    self._mark(host)
                    self.request_count += 1
                    self.consecutive_proxy_errors = 0
                    return CachedResponse(url=url, error=f"dns_error: {exc}")
                last = CachedResponse(url=url, error=f"connection_error: {exc}")
            except Exception as exc:  # noqa: BLE001
                last = CachedResponse(url=url, error=f"{type(exc).__name__}: {exc}")

            self._mark(host)
            self.request_count += 1
            if attempt < config.MAX_RETRIES:
                time.sleep(config.RETRY_BACKOFF_SECONDS * (attempt + 1))

        return last or CachedResponse(url=url, error="unknown_error")

    def get_json(self, url: str, headers: dict[str, str] | None = None,
                 auth: tuple[str, str] | None = None,
                 cache_namespace: str | None = None,
                 cache_key: str | None = None) -> tuple[object | None, str | None]:
        """API GET returning (payload, error). Cached by namespace+key."""
        if cache_namespace and cache_key:
            hit = self.cache.get_json(cache_namespace, cache_key)
            if hit is not None:
                self.cache_hits += 1
                return hit, None

        if self.offline:
            return None, "offline_cache_miss"

        host = urlparse(url).netloc.lower()
        for attempt in range(config.MAX_RETRIES + 1):
            self._sleep(host)
            try:
                resp = self.session.get(
                    url,
                    headers=headers or {},
                    auth=auth,
                    timeout=(config.CONNECT_TIMEOUT, config.READ_TIMEOUT),
                )
                self._mark(host)
                self.request_count += 1
                if resp.status_code == 429:
                    retry_after = float(resp.headers.get("retry-after", 30) or 30)
                    log.warning("rate limited by %s, sleeping %.0fs", host, retry_after)
                    time.sleep(min(retry_after, 120))
                    continue
                if resp.status_code == 401:
                    return None, "http_401_unauthorised (check API key)"
                if resp.status_code >= 400:
                    return None, f"http_{resp.status_code}"
                payload = resp.json()
                if cache_namespace and cache_key:
                    self.cache.put_json(cache_namespace, cache_key, payload)
                return payload, None
            except Exception as exc:  # noqa: BLE001
                self._mark(host)
                self.request_count += 1
                if attempt < config.MAX_RETRIES:
                    time.sleep(config.RETRY_BACKOFF_SECONDS * (attempt + 1))
                else:
                    return None, f"{type(exc).__name__}: {exc}"
        return None, "exhausted_retries"
