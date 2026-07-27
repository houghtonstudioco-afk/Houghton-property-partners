"""Stage 2 - audit each discovered website.

Records HTTP/TLS health, live-chat vendor, online booking, CRM tracking, an
outdated-technology score of 1-10 and how a prospect can actually be contacted.

Detection is deliberately signature-based on the page source rather than
rendered DOM: the widgets we care about all inject an identifiable script tag or
host reference, and requesting one page per site keeps the crawl polite.
"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field

from .fetcher import Fetcher, base_url, normalise_url, registrable_host
from .store import CachedResponse, FailureLog, set_if_blank

log = logging.getLogger("leadgen")

_TAG_STRIP = re.compile(r"<[^>]+>")
_SCRIPT_BLOCK = re.compile(r"<script\b.*?</script>", re.I | re.S)


# ------------------------------------------------------------- signatures ----
# (vendor label, compiled pattern). Ordered so the more specific vendor wins.

def _pat(*alternatives: str) -> re.Pattern[str]:
    return re.compile("|".join(alternatives), re.I)


LIVE_CHAT_SIGNATURES: list[tuple[str, re.Pattern[str]]] = [
    ("Intercom",     _pat(r"widget\.intercom\.io", r"js\.intercomcdn\.com",
                          r"intercomSettings", r"window\.Intercom")),
    ("Drift",        _pat(r"js\.driftt\.com", r"driftt\.com/include",
                          r"drift\.load\(", r"window\.drift")),
    ("Tawk.to",      _pat(r"embed\.tawk\.to", r"tawk\.to/chat", r"Tawk_API")),
    ("Crisp",        _pat(r"client\.crisp\.chat", r"CRISP_WEBSITE_ID",
                          r"\$crisp")),
    ("LiveChat",     _pat(r"cdn\.livechatinc\.com", r"livechatinc\.com/tracking",
                          r"__lc\s*=", r"LiveChatWidget")),
    ("Zendesk Chat", _pat(r"static\.zdassets\.com", r"zopim\.com",
                          r"\$zopim", r"zE\s*\(", r"zendesk\.com/embeddable")),
    ("HubSpot Chat", _pat(r"js\.hs-scripts\.com", r"js\.usemessages\.com",
                          r"hs-conversations", r"HubSpotConversations")),
    # Beyond the requested seven, but common on trade sites and worth knowing.
    ("Olark",        _pat(r"static\.olark\.com", r"olark\.identify")),
    ("Freshchat",    _pat(r"wchat\.freshchat\.com", r"fcWidget")),
    ("Smartsupp",    _pat(r"smartsuppchat\.com", r"_smartsupp")),
    ("Chatra",       _pat(r"call\.chatra\.io", r"ChatraID")),
    ("Tidio",        _pat(r"code\.tidio\.co", r"tidioChatApi")),
    ("WhatsApp",     _pat(r"wa\.me/\d", r"api\.whatsapp\.com/send")),
]

BOOKING_SIGNATURES: list[tuple[str, re.Pattern[str]]] = [
    ("Calendly",    _pat(r"calendly\.com", r"assets\.calendly\.com")),
    ("Acuity",      _pat(r"acuityscheduling\.com", r"squarespacescheduling\.com")),
    ("Cal.com",     _pat(r"\bcal\.com/", r"app\.cal\.com", r"embed\.cal\.com")),
    ("SimplyBook",  _pat(r"simplybook\.(it|me)", r"simplybook\.asia")),
    ("Setmore",     _pat(r"setmore\.com", r"my\.setmore\.com")),
    ("YouCanBookMe", _pat(r"youcanbook\.me")),
    ("Housecall Pro", _pat(r"housecallpro\.com/book", r"book\.housecallpro")),
    ("ServiceM8",   _pat(r"servicem8\.com/(?:booking|form)")),
    ("Commusoft",   _pat(r"commusoft\.co\.uk/(?:booking|portal)")),
]

# A booking/scheduling route linked from the site's own navigation.
BOOKING_ROUTE = re.compile(
    r'href=["\'](?P<href>[^"\']*/(?:book|book-now|book-online|booking|bookings|'
    r'schedule|scheduling|appointment|appointments|make-a-booking|'
    r'book-a-(?:service|visit|survey|call))/?(?:\?[^"\']*)?)["\']',
    re.I,
)

CRM_SIGNATURES: list[tuple[str, re.Pattern[str]]] = [
    ("HubSpot",    _pat(r"js\.hs-scripts\.com", r"js\.hsforms\.net",
                        r"js\.hs-analytics\.net", r"hsforms\.com",
                        r"track\.hubspot\.com", r"_hsq\b")),
    ("Salesforce", _pat(r"\.pardot\.com", r"pi\.pardot\.com", r"piAId",
                        r"\.my\.salesforce\.com", r"salesforceliveagent",
                        r"web-to-lead", r"webto\.salesforce\.com",
                        r"\.force\.com/servlet")),
    ("Pipedrive",  _pat(r"pipedriveassets\.com", r"leadbooster-chat",
                        r"webforms\.pipedrive\.com", r"pipedrive\.com/scripts")),
    ("Zoho",       _pat(r"salesiq\.zoho", r"\$zoho", r"zohopublic\.com",
                        r"crm\.zoho\.com", r"forms\.zohopublic",
                        r"js\.zohocdn\.com")),
]


def _find(signatures: list[tuple[str, re.Pattern[str]]], html: str) -> list[str]:
    return [vendor for vendor, pattern in signatures if pattern.search(html)]


# ------------------------------------------------- outdated-tech scoring -----

_VIEWPORT = re.compile(r'<meta[^>]+name=["\']viewport["\']', re.I)
_JQUERY = re.compile(r"jquery[.-]?(?P<ver>\d+(?:\.\d+)*)?(?:\.min)?\.js", re.I)
_JQUERY_ANY = re.compile(r"jquery", re.I)
_MODERN_STACK = _pat(
    r"react(?:-dom)?[.@/]", r"__NEXT_DATA__", r"_next/static", r"nuxt",
    r"vue(?:\.runtime)?[.@]", r"svelte", r"angular", r"webpack",
    r"type=[\"']module[\"']", r"/build/assets/", r"data-astro", r"htmx",
    r"alpinejs", r"gatsby", r"wp-content/themes/[^\"']*\bblocks?\b",
)
_TABLE = re.compile(r"<table\b[^>]*>", re.I)
_TABLE_PRESENTATION = re.compile(r'<table\b[^>]*role=["\']presentation["\']', re.I)
_NESTED_TABLE = re.compile(r"<table\b[^>]*>(?:(?!</table>).)*?<table\b", re.I | re.S)
_TABLE_LAYOUT_ATTRS = re.compile(
    r'<table\b[^>]*(?:cellpadding|cellspacing|bgcolor|width=["\']?\d{2,})', re.I)
_LEGACY_TAGS = re.compile(r"<(?:font|center|marquee|blink|frameset|frame|big|tt)\b", re.I)
_FLASH = re.compile(
    r"\.swf\b|application/x-shockwave-flash|<embed[^>]+swf|swfobject|"
    r"macromedia\.com/go/getflashplayer|AC_RunActiveContent", re.I)
_COPYRIGHT_YEAR = re.compile(
    r"(?:©|&copy;|&#169;|copyright)[^0-9]{0,40}((?:19|20)\d{2})"
    r"(?:\s*(?:-|–|—|to)\s*((?:19|20)\d{2}))?", re.I)
_ANY_RECENT_YEAR = re.compile(r"\b(20[0-2]\d)\b")


def copyright_year(html: str) -> int | None:
    """Latest copyright year in the page, preferring an explicit © notice."""
    years: list[int] = []
    for match in _COPYRIGHT_YEAR.finditer(html or ""):
        for group in match.groups():
            if group:
                years.append(int(group))
    if years:
        return max(years)
    # Fall back to the last plausible year mentioned near the end of the page,
    # where footers live.
    tail = (html or "")[-4000:]
    tail_years = [int(y) for y in _ANY_RECENT_YEAR.findall(tail)]
    return max(tail_years) if tail_years else None


def score_outdated(html: str, final_url: str, ssl_status: str | None,
                   now_year: int | None = None) -> tuple[int, list[str]]:
    """Score 1-10 where 10 is the most dated. Returns (score, signals)."""
    now_year = now_year or time.gmtime().tm_year
    html = html or ""
    points = 0
    signals: list[str] = []

    if not _VIEWPORT.search(html):
        points += 3
        signals.append("no-responsive-viewport")

    has_modern = bool(_MODERN_STACK.search(html))
    if _JQUERY_ANY.search(html) and not has_modern:
        points += 2
        signals.append("jquery-only-stack")
        versions = [m.group("ver") for m in _JQUERY.finditer(html) if m.group("ver")]
        if versions:
            major = min(int(v.split(".")[0]) for v in versions)
            if major <= 1:
                points += 1
                signals.append(f"jquery-1.x({min(versions)})")

    tables = _TABLE.findall(html)
    layout_tables = [t for t in tables if not _TABLE_PRESENTATION.match(t)]
    if layout_tables and (_NESTED_TABLE.search(html) or _TABLE_LAYOUT_ATTRS.search(html)):
        points += 2
        signals.append(f"table-based-layout({len(layout_tables)})")
    elif len(layout_tables) >= 6:
        points += 1
        signals.append(f"table-heavy({len(layout_tables)})")

    if _LEGACY_TAGS.search(html):
        points += 1
        signals.append("legacy-html-tags")

    if _FLASH.search(html):
        points += 2
        signals.append("flash-remnants")

    year = copyright_year(html)
    if year:
        age = now_year - year
        if age >= 5:
            points += 2
            signals.append(f"copyright-{year}(stale-{age}y)")
        elif age >= 2:
            points += 1
            signals.append(f"copyright-{year}(stale-{age}y)")
    else:
        signals.append("no-copyright-year")

    if not (final_url or "").startswith("https://"):
        points += 2
        signals.append("no-https")
    elif ssl_status and ssl_status != "valid":
        points += 2
        signals.append(f"tls-{ssl_status}")

    return max(1, min(10, points)), signals


# ---------------------------------------------------- contact-method audit ---

_FORM = re.compile(r"<form\b.*?</form>", re.I | re.S)
_SEARCH_FORM = re.compile(r'type=["\']search["\']|name=["\']s["\']|/search|role=["\']search["\']', re.I)
_CONTACT_FIELD = re.compile(
    r'(?:name|id|placeholder|aria-label)=["\'][^"\']*'
    r'(?:e-?mail|message|enquir|inquir|comment|your-?name|fullname|phone|tel|'
    r'subject|postcode|how-can-we-help)[^"\']*["\']|<textarea', re.I)
_MAILTO = re.compile(r'href=["\']mailto:([^"\'?]+)', re.I)
_TEL = re.compile(r'href=["\']tel:([^"\']+)', re.I)
_EMBEDDED_FORM = _pat(
    r"docs\.google\.com/forms", r"jotform\.com", r"typeform\.com",
    r"formstack\.com", r"wufoo\.com", r"gravityforms", r"wpforms",
    r"contact-form-7", r"formspree\.io", r"hsforms\.net", r"zohopublic\.com/.*form",
    r"forms\.office\.com", r"paperform\.co", r"tally\.so",
)


def detect_contact_method(html: str) -> tuple[str, list[str]]:
    """Return (primary_method, all_channels_found).

    Primary follows the user's framing: a real form outranks a bare mailto,
    which outranks phone-only.
    """
    html = html or ""
    channels: list[str] = []

    has_form = bool(_EMBEDDED_FORM.search(html))
    if not has_form:
        for block in _FORM.findall(html):
            if _SEARCH_FORM.search(block) and not _CONTACT_FIELD.search(block):
                continue
            if _CONTACT_FIELD.search(block):
                has_form = True
                break
    if has_form:
        channels.append("form")
    if _MAILTO.search(html):
        channels.append("mailto")
    if _TEL.search(html):
        channels.append("tel")

    for primary in ("form", "mailto", "tel"):
        if primary in channels:
            return ("phone" if primary == "tel" else primary), channels
    return "none", channels


# ------------------------------------------------------------ audit result ----

@dataclass
class Audit:
    url: str = ""
    final_url: str = ""
    http_status: str = ""
    site_health: str = "none"      # ok | insecure | broken | unreachable | none
    ssl_status: str = ""
    chat_vendors: list[str] = field(default_factory=list)
    booking_vendors: list[str] = field(default_factory=list)
    crm_vendors: list[str] = field(default_factory=list)
    contact_method: str = ""
    contact_channels: list[str] = field(default_factory=list)
    outdated_score: int | None = None
    outdated_signals: list[str] = field(default_factory=list)
    error: str = ""
    parked: bool = False


BROKEN_ERRORS = ("dns_error", "connection_error", "timeout", "redirect_loop")


def classify(resp: CachedResponse) -> tuple[str, str]:
    """Map a fetch outcome onto (http_status_label, site_health)."""
    if resp.error:
        code = resp.error.split(":", 1)[0].strip()
        if code == "robots_disallowed":
            return "robots_disallowed", "unknown"
        if code == "offline_cache_miss":
            return "not_checked", "unknown"
        if code == "proxy_error":
            # Says nothing about the site - our egress is broken, not theirs.
            # Must never be scored as 'unreachable' or every row looks dead.
            return "proxy_error", "unknown"
        if code.startswith("ssl") or resp.ssl_status:
            return f"ssl_{resp.ssl_status or 'error'}", "insecure"
        if code in BROKEN_ERRORS:
            return code, "unreachable"
        return code, "unreachable"

    status = resp.status or 0
    if status in (404, 410):
        return str(status), "broken"
    if status >= 500:
        return str(status), "broken"
    if status >= 400:
        return str(status), "broken"

    final = resp.final_url or resp.url
    if not final.startswith("https://"):
        return str(status), "insecure"
    if resp.ssl_status and resp.ssl_status != "valid":
        return f"{status}_ssl_{resp.ssl_status}", "insecure"
    return str(status), "ok"


def audit_site(url: str, fetcher: Fetcher, check_contact_page: bool = True) -> Audit:
    audit = Audit(url=normalise_url(url))
    resp = fetcher.get(audit.url)
    audit.http_status, audit.site_health = classify(resp)
    audit.ssl_status = resp.ssl_status or ""
    audit.final_url = resp.final_url or ""
    if resp.error:
        audit.error = resp.error

    html = resp.body or ""
    if not html:
        return audit

    audit.parked = looks_parked_light(html)
    if audit.parked and audit.site_health == "ok":
        audit.site_health = "placeholder"

    # A contact page usually carries the form and the mailto that the homepage
    # only links to, so it materially improves contact-method accuracy.
    combined = html
    if check_contact_page:
        for path in ("/contact", "/contact-us", "/contact.html", "/contact-us.html"):
            link = re.search(
                rf'href=["\']([^"\']*{re.escape(path)}[^"\']*)["\']', html, re.I)
            if not link:
                continue
            target = link.group(1)
            if target.startswith("http"):
                if registrable_host(target) != registrable_host(audit.final_url or audit.url):
                    continue
            else:
                target = base_url(audit.final_url or audit.url) + "/" + target.lstrip("/")
            contact = fetcher.get(target)
            if contact.body:
                combined = html + "\n" + contact.body
            break

    audit.chat_vendors = _find(LIVE_CHAT_SIGNATURES, combined)
    audit.booking_vendors = _find(BOOKING_SIGNATURES, combined)
    if not audit.booking_vendors and BOOKING_ROUTE.search(combined):
        audit.booking_vendors = ["own booking route"]
    audit.crm_vendors = _find(CRM_SIGNATURES, combined)
    audit.contact_method, audit.contact_channels = detect_contact_method(combined)
    audit.outdated_score, audit.outdated_signals = score_outdated(
        html, audit.final_url or audit.url, resp.ssl_status
    )
    return audit


def looks_parked_light(html: str) -> bool:
    from .stage1_websites import looks_parked
    return looks_parked(html)


# ------------------------------------------------------------------ stage ----

def run(rows: list[dict[str, str]], fetcher: Fetcher, failures: FailureLog,
        checkpoint, limit: int | None = None) -> dict[str, int]:
    todo = [(i, r) for i, r in enumerate(rows, start=2)
            if str(r.get("Website", "") or "").strip()]
    stats = {"no_website": len(rows) - len(todo), "checked": 0, "ok": 0,
             "broken": 0, "insecure": 0, "unreachable": 0, "with_chat": 0,
             "with_booking": 0, "with_crm": 0}
    if limit:
        todo = todo[:limit]

    for n, (row_num, row) in enumerate(todo, start=1):
        company = row.get("Company Name", "")
        website = row["Website"].strip()

        # Skip rows already audited so a resumed run does not redo work.
        if str(row.get("HTTP Status", "") or "").strip():
            continue

        log.info("[stage2 %d/%d] %s -> %s", n, len(todo), company, website)
        try:
            audit = audit_site(website, fetcher)
        except Exception as exc:  # noqa: BLE001
            failures.record("stage2", row_num, company, "unhandled_exception",
                            f"{type(exc).__name__}: {exc}")
            continue

        stats["checked"] += 1
        stats[audit.site_health] = stats.get(audit.site_health, 0) + 1

        row["Final URL"] = audit.final_url or ""
        row["HTTP Status"] = audit.http_status
        row["Site Health"] = audit.site_health
        row["SSL Status"] = audit.ssl_status
        row["Live Chat Vendor"] = ", ".join(audit.chat_vendors)
        row["Online Booking Vendor"] = ", ".join(audit.booking_vendors)
        row["CRM Vendor"] = ", ".join(audit.crm_vendors)
        row["Contact Method"] = audit.contact_method
        row["Outdated Signals"] = "; ".join(audit.outdated_signals)
        row["Site Checked At"] = time.strftime("%Y-%m-%d")

        # Original "(unverified)" columns are blank in the source, so filling
        # them is allowed; the header text is left alone so existing mappings
        # keep working.
        set_if_blank(row, "Live Chat (unverified)",
                     "Yes" if audit.chat_vendors else "No")
        set_if_blank(row, "Online Booking (unverified)",
                     "Yes" if audit.booking_vendors else "No")
        set_if_blank(row, "Uses CRM (unverified)",
                     "Yes" if audit.crm_vendors else "No")
        if audit.outdated_score is not None:
            set_if_blank(row, "Website Outdated Score (unverified)",
                         str(audit.outdated_score))

        if audit.chat_vendors:
            stats["with_chat"] += 1
        if audit.booking_vendors:
            stats["with_booking"] += 1
        if audit.crm_vendors:
            stats["with_crm"] += 1

        if audit.error:
            failures.record("stage2", row_num, company, audit.http_status,
                            f"{website} -> {audit.error}")
        elif audit.site_health in ("broken", "placeholder"):
            failures.record("stage2", row_num, company, f"site_{audit.site_health}",
                            f"{website} -> HTTP {audit.http_status}")

        if n % 10 == 0:
            checkpoint()

    checkpoint()
    return stats
