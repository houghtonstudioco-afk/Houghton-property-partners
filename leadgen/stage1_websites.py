"""Stage 1 - discover each company's official website.

The governing rule is the user's: a wrong domain poisons every later stage, so
a blank is always preferable to a guess. Nothing is written to the Website
column unless it clears the verification gate in ``verify_candidate``, which
requires corroboration from the row's own verified data (phone number, town)
rather than trusting search rank.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

from . import config
from .fetcher import Fetcher, base_url, normalise_url, registrable_host
from .store import FailureLog, set_if_blank
from .textutil import (
    compact,
    location_city,
    name_similarity,
    name_tokens,
    phone_matches,
    slugify,
    town_matches,
)

log = logging.getLogger("leadgen")


@dataclass
class Candidate:
    url: str
    source: str
    rank: int = 99


# ------------------------------------------------------------- providers -----

class SearchProvider:
    name = "none"
    available = False
    # How many candidates are worth verifying. Search engines rank, so the tail
    # is noise; the domain guesser does not rank, so its whole list must be
    # tried or correct guesses get silently dropped.
    max_candidates = 8

    def search(self, query: str, fetcher: Fetcher) -> tuple[list[Candidate], str | None]:
        raise NotImplementedError


class BraveProvider(SearchProvider):
    name = "brave"

    def __init__(self, key: str):
        self.key = key
        self.available = bool(key)

    def search(self, query, fetcher):
        payload, err = fetcher.get_json(
            "https://api.search.brave.com/res/v1/web/search"
            f"?q={quote_plus(query)}&count=10&country=GB",
            headers={"X-Subscription-Token": self.key, "Accept": "application/json"},
            cache_namespace="search:brave",
            cache_key=query,
        )
        if err:
            return [], err
        results = ((payload or {}).get("web") or {}).get("results") or []
        return [
            Candidate(url=r["url"], source=self.name, rank=i)
            for i, r in enumerate(results) if r.get("url")
        ], None


class SerperProvider(SearchProvider):
    name = "serper"

    def __init__(self, key: str):
        self.key = key
        self.available = bool(key)

    def search(self, query, fetcher):
        # Serper's search endpoint is POST-only, so it bypasses get_json's
        # caching helper and manages its own cache entry.
        cached = fetcher.cache.get_json("search:serper", query)
        if cached is None:
            if fetcher.offline:
                return [], "offline_cache_miss"
            try:
                resp = fetcher.session.post(
                    "https://google.serper.dev/search",
                    json={"q": query, "gl": "gb", "num": 10},
                    headers={"X-API-KEY": self.key, "Content-Type": "application/json"},
                    timeout=(config.CONNECT_TIMEOUT, config.READ_TIMEOUT),
                )
                if resp.status_code == 401:
                    return [], "http_401_unauthorised (check SERPER_API_KEY)"
                if resp.status_code >= 400:
                    return [], f"http_{resp.status_code}"
                cached = resp.json()
                fetcher.cache.put_json("search:serper", query, cached)
                fetcher.request_count += 1
            except Exception as exc:  # noqa: BLE001
                return [], f"{type(exc).__name__}: {exc}"
        results = (cached or {}).get("organic") or []
        return [
            Candidate(url=r["link"], source=self.name, rank=i)
            for i, r in enumerate(results) if r.get("link")
        ], None


class GoogleCSEProvider(SearchProvider):
    name = "google_cse"

    def __init__(self, key: str, cx: str):
        self.key, self.cx = key, cx
        self.available = bool(key and cx)

    def search(self, query, fetcher):
        payload, err = fetcher.get_json(
            "https://www.googleapis.com/customsearch/v1"
            f"?key={self.key}&cx={self.cx}&num=10&gl=uk&q={quote_plus(query)}",
            cache_namespace="search:google_cse",
            cache_key=query,
        )
        if err:
            return [], err
        items = (payload or {}).get("items") or []
        return [
            Candidate(url=r["link"], source=self.name, rank=i)
            for i, r in enumerate(items) if r.get("link")
        ], None


class DuckDuckGoProvider(SearchProvider):
    """Free fallback. Scrapes the HTML endpoint.

    Best-effort only: DDG rate-limits aggressively and its markup changes
    without notice. An API-key provider is strongly preferred for a full run.
    """
    name = "duckduckgo"
    available = True

    _LINK = re.compile(r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"', re.I)
    _ANY = re.compile(r'href="(/l/\?uddg=[^"]+)"', re.I)

    def search(self, query, fetcher):
        cached = fetcher.cache.get_json("search:ddg", query)
        if cached is None:
            if fetcher.offline:
                return [], "offline_cache_miss"
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}&kl=uk-en"
            resp = fetcher.get(url, check_robots=False)
            if resp.error:
                return [], resp.error
            if resp.status in (202, 403, 429):
                return [], f"ddg_blocked_http_{resp.status}"
            cached = {"html": resp.body}
            fetcher.cache.put_json("search:ddg", query, cached)

        html = (cached or {}).get("html", "")
        urls: list[str] = []
        for raw in self._LINK.findall(html) + self._ANY.findall(html):
            urls.append(self._unwrap(raw))
        seen, out = set(), []
        for i, u in enumerate(urls):
            if not u or not u.startswith("http"):
                continue
            host = registrable_host(u)
            if host in seen:
                continue
            seen.add(host)
            out.append(Candidate(url=u, source=self.name, rank=i))
        return out, None

    @staticmethod
    def _unwrap(href: str) -> str:
        """DDG wraps results as /l/?uddg=<encoded target>."""
        if href.startswith("//"):
            href = "https:" + href
        parsed = urlparse(href)
        if parsed.path.startswith("/l/"):
            target = parse_qs(parsed.query).get("uddg")
            if target:
                return unquote(target[0])
        return href


class DomainGuessProvider(SearchProvider):
    """Constructs plausible domains from the company name.

    Cheap, needs no API, and because every candidate still has to pass the
    verification gate, a wrong guess costs one request and is discarded.
    """
    name = "domain_guess"
    available = True
    max_candidates = 18

    def search(self, query, fetcher):  # query is the raw company name here
        stems = self._stems(query)
        # TLD-major ordering: every stem gets a .co.uk try before any stem gets
        # a .ltd.uk try, since a UK trade business is overwhelmingly on .co.uk
        # or .com. Stem-major ordering wastes the budget on obscure TLDs for
        # the first stem.
        out: list[Candidate] = []
        for tld_rank, tld in enumerate(config.GUESS_TLDS):
            for stem_rank, stem in enumerate(stems):
                out.append(Candidate(
                    url=f"https://{stem}{tld}",
                    source=self.name,
                    rank=tld_rank * len(stems) + stem_rank,
                ))
        return out[:self.max_candidates], None

    @staticmethod
    def _stems(name: str) -> list[str]:
        tokens = name_tokens(name)
        if not tokens:
            return []
        stems: list[str] = []

        def add(value: str) -> None:
            if value and value not in stems and len(value) >= 4:
                stems.append(value)

        add(compact(name))                       # thegaspro
        add("".join(tokens))                     # gaspro
        add("-".join(tokens))                    # gas-pro
        distinctive = name_tokens(name, drop_trade_words=True)
        if distinctive != tokens:
            add("".join(distinctive))
            add("-".join(distinctive))
        if len(tokens) > 2:
            add("".join(tokens[:2]))
        return stems[:4]


def build_providers() -> list[SearchProvider]:
    """Assemble providers in preference order based on which keys are present."""
    providers: list[SearchProvider] = []
    if key := config.brave_key():
        providers.append(BraveProvider(key))
    if key := config.serper_key():
        providers.append(SerperProvider(key))
    if pair := config.google_cse():
        providers.append(GoogleCSEProvider(*pair))
    if not providers:
        log.warning(
            "No search API key found (BRAVE_SEARCH_API_KEY / SERPER_API_KEY / "
            "GOOGLE_CSE_KEY+GOOGLE_CSE_CX). Falling back to DuckDuckGo HTML "
            "plus domain guessing - expect a lower hit rate."
        )
        providers.append(DuckDuckGoProvider())
    providers.append(DomainGuessProvider())
    return providers


# ------------------------------------------------------ verification gate ----

_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
_OG_SITE = re.compile(r'<meta[^>]+property=["\']og:site_name["\'][^>]+content=["\']([^"\']+)', re.I)
_TAG_STRIP = re.compile(r"<[^>]+>")
_PARKED = re.compile(
    r"(domain (is )?for sale|buy this domain|this domain is parked|"
    r"website coming soon|under construction|default web page|"
    r"apache2? (ubuntu|debian) default page|welcome to nginx|"
    r"future home of something|index of /|account suspended|"
    r"this site can.t be reached|sedoparking|godaddy.*parked)",
    re.I,
)


def looks_parked(html: str) -> bool:
    text = _TAG_STRIP.sub(" ", html or "")
    if _PARKED.search(text):
        return True
    # A page with essentially no content is a placeholder in practice.
    return len(text.split()) < 25


@dataclass
class Verdict:
    accepted: bool
    score: int
    evidence: list[str]
    confidence: str
    url: str = ""
    reason: str = ""


def verify_candidate(candidate: Candidate, row: dict[str, str],
                     fetcher: Fetcher) -> Verdict:
    """Decide whether a candidate URL really belongs to this company.

    Scoring rubric (accept at >= DISCOVERY_ACCEPT_THRESHOLD, default 5):
        +5  the row's verified phone number appears in the page source
        +3  strong company-name match in <title>/og:site_name
        +2  moderate company-name match
        +2  the Location town appears on the page
        +2  domain slug closely resembles the company name
        +1  domain slug loosely resembles the company name
        -3  page looks parked/placeholder
        -2  free site-builder host

    A phone match alone clears the bar because it is near-conclusive. Without
    it, a name match must be corroborated by town or domain resemblance.
    """
    url = normalise_url(candidate.url)
    host = registrable_host(url)
    company = row.get("Company Name", "")
    location = row.get("Location", "")
    phone = row.get("Phone Number", "")

    if not host or "." not in host:
        return Verdict(False, 0, [], "none", url, "malformed_url")
    if host in config.DIRECTORY_BLOCKLIST or any(
        host.endswith("." + b) for b in config.DIRECTORY_BLOCKLIST
    ):
        return Verdict(False, 0, [], "none", url, f"directory_host:{host}")

    resp = fetcher.get(base_url(url))

    # A dead domain is the single strongest signal in this dataset, so it must
    # not be discarded as "no website found". But the distinction matters: a
    # search engine returning a name-matching domain is evidence the company
    # HAS a site and it is broken, whereas a blind domain guess failing means
    # only that the guess was wrong. So unreachable candidates are trusted only
    # when a search engine produced them AND the domain matches the name.
    unreachable = bool(resp.error) or resp.status is None or resp.status >= 400
    if unreachable:
        from_search = candidate.source not in ("domain_guess", "")
        host_stem = registrable_host(url).split(".")[0].replace("-", " ")
        strong_domain = (
            name_similarity(company, host_stem) >= 0.80
            or compact(company).startswith(compact(host_stem))
        )
        detail = resp.error or f"http_{resp.status}"
        if from_search and strong_domain:
            return Verdict(
                True, config.DISCOVERY_ACCEPT_THRESHOLD,
                ["domain-match", f"unreachable({detail.split(':')[0]})"],
                "medium", url,
            )
        return Verdict(False, 0, [], "none", url, detail)

    html = resp.body or ""
    final = resp.final_url or url
    final_host = registrable_host(final)

    # A redirect off to a directory or social page means there is no own site.
    if final_host in config.DIRECTORY_BLOCKLIST or any(
        final_host.endswith("." + b) for b in config.DIRECTORY_BLOCKLIST
    ):
        return Verdict(False, 0, [], "none", final, f"redirects_to_directory:{final_host}")

    score = 0
    evidence: list[str] = []

    if phone and phone_matches(phone, html):
        score += 5
        evidence.append("phone-match")

    title = ""
    if m := _TITLE.search(html):
        title = _TAG_STRIP.sub(" ", m.group(1))
    if m := _OG_SITE.search(html):
        title = f"{title} {m.group(1)}"
    sim = max(
        name_similarity(company, title),
        name_similarity(company, final_host.rsplit(".", 2)[0].replace("-", " ")),
    )
    if sim >= 0.80:
        score += 3
        evidence.append(f"name-strong({sim:.2f})")
    elif sim >= 0.60:
        score += 2
        evidence.append(f"name-moderate({sim:.2f})")

    text = _TAG_STRIP.sub(" ", html)
    matched_town, basis = town_matches(location, text)
    if matched_town:
        score += 2
        evidence.append(f"town-{basis}")

    dom_sim = name_similarity(company, final_host.split(".")[0].replace("-", " "))
    slug_hit = compact(company).startswith(compact(final_host.split(".")[0])) \
        or compact(final_host.split(".")[0]).startswith(compact(company))
    if dom_sim >= 0.80 or slug_hit:
        score += 2
        evidence.append("domain-match")
    elif dom_sim >= 0.55:
        score += 1
        evidence.append("domain-partial")

    if looks_parked(html):
        score -= 3
        evidence.append("parked-page")
    if any(final_host.endswith(s.lstrip(".")) or final_host.endswith(s)
           for s in config.WEAK_HOSTING_SUFFIXES):
        score -= 2
        evidence.append("site-builder-host")

    has_phone = "phone-match" in evidence
    has_name = sim >= 0.60
    corroborated = matched_town or dom_sim >= 0.55 or slug_hit

    accepted = score >= config.DISCOVERY_ACCEPT_THRESHOLD and (
        has_phone or (has_name and corroborated)
    )
    confidence = "none"
    if accepted:
        confidence = "high" if has_phone and (has_name or matched_town) else "medium"

    reason = "" if accepted else f"insufficient_evidence(score={score})"
    return Verdict(accepted, score, evidence, confidence, final, reason)


# ------------------------------------------------------------------ stage ----

def discover_website(row: dict[str, str], providers: list[SearchProvider],
                     fetcher: Fetcher, failures: FailureLog,
                     row_num: int) -> Verdict:
    company = row.get("Company Name", "")
    location = row.get("Location", "")
    city = location_city(location) or location

    queries = [
        f"{company} {location}",
        f"{company} {city} official website",
    ]
    if tokens := name_tokens(company, drop_trade_words=True):
        queries.append(f"{' '.join(tokens)} {city} {row.get('Industry', '')}".strip())

    seen_hosts: set[str] = set()
    best = Verdict(False, -99, [], "none")
    # Deduped: the same provider failing on three query variants is one problem,
    # not three, and tripling it just buries the real failures in the log.
    provider_errors: set[str] = set()

    for provider in providers:
        if not provider.available:
            continue
        # The guesser takes the bare company name, search engines take queries.
        prov_queries = [company] if provider.name == "domain_guess" else queries

        for query in prov_queries:
            candidates, err = provider.search(query, fetcher)
            if err:
                provider_errors.add(f"{provider.name}:{err}")
                continue
            for cand in candidates[:provider.max_candidates]:
                host = registrable_host(cand.url)
                if not host or host in seen_hosts:
                    continue
                seen_hosts.add(host)
                verdict = verify_candidate(cand, row, fetcher)
                verdict.url = verdict.url or cand.url
                if verdict.score > best.score:
                    best = verdict
                if verdict.accepted:
                    verdict.evidence.append(f"via:{provider.name}")
                    return verdict
        if best.accepted:
            break

    for err in sorted(provider_errors):
        failures.record("stage1", row_num, company, "search_provider_error", err)
    if not best.accepted:
        failures.record(
            "stage1", row_num, company, "website_not_found",
            f"best={best.url or 'n/a'} {best.reason or 'no candidates'} "
            f"evidence={'+'.join(best.evidence) or 'none'}",
        )
    return best


def run(rows: list[dict[str, str]], fetcher: Fetcher, failures: FailureLog,
        checkpoint, limit: int | None = None) -> dict[str, int]:
    providers = build_providers()
    active = [p.name for p in providers if p.available]
    log.info("stage 1 providers: %s", ", ".join(active))

    stats = {"already_had": 0, "found": 0, "not_found": 0, "processed": 0}
    todo = [(i, r) for i, r in enumerate(rows, start=2)
            if not str(r.get("Website", "") or "").strip()]
    stats["already_had"] = len(rows) - len(todo)
    if limit:
        todo = todo[:limit]

    for n, (row_num, row) in enumerate(todo, start=1):
        company = row.get("Company Name", "")
        log.info("[stage1 %d/%d] %s", n, len(todo), company)
        try:
            verdict = discover_website(row, providers, fetcher, failures, row_num)
        except Exception as exc:  # noqa: BLE001 - one bad row must not kill the run
            failures.record("stage1", row_num, company, "unhandled_exception",
                            f"{type(exc).__name__}: {exc}")
            continue
        stats["processed"] += 1

        if verdict.accepted:
            set_if_blank(row, "Website", verdict.url)
            row["Website Confidence"] = verdict.confidence
            row["Website Evidence"] = "+".join(verdict.evidence)
            row["Website Source"] = next(
                (e.split(":", 1)[1] for e in verdict.evidence if e.startswith("via:")),
                "",
            )
            stats["found"] += 1
        else:
            row["Website Confidence"] = "none"
            row["Website Evidence"] = "+".join(verdict.evidence) or "no-evidence"
            stats["not_found"] += 1

        if n % 10 == 0:
            checkpoint()

    checkpoint()
    return stats
