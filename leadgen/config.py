"""Tunable configuration for the lead enrichment pipeline.

Everything a human is likely to want to change lives here rather than being
scattered through the stage modules.
"""
from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------- paths ------

REPO_ROOT = Path(__file__).resolve().parent.parent

INPUT_CSV = REPO_ROOT / "gas_oil_engineering_leads.csv"
OUTPUT_CSV = REPO_ROOT / "gas_oil_engineering_leads_enriched.csv"
FAILURE_LOG = REPO_ROOT / "enrichment_failures.log"
RUN_LOG = REPO_ROOT / "enrichment_run.log"
CACHE_DIR = REPO_ROOT / ".enrichment_cache"
CACHE_DB = CACHE_DIR / "cache.sqlite"

# ------------------------------------------------------------- politeness ----

USER_AGENT = os.environ.get(
    "LEADGEN_USER_AGENT",
    # A real, identifiable agent string with a contact route, as requested.
    "HoughtonPropertyPartners-LeadResearch/1.0 "
    "(+mailto:houghtonstudio.co@gmail.com) python-requests",
)

# Seconds between outbound requests. A uniform random delay in this range is
# applied globally, and additionally enforced per-host.
MIN_DELAY_SECONDS = float(os.environ.get("LEADGEN_MIN_DELAY", "1.0"))
MAX_DELAY_SECONDS = float(os.environ.get("LEADGEN_MAX_DELAY", "2.0"))

CONNECT_TIMEOUT = 10.0
READ_TIMEOUT = 20.0

# Retries for transient network failures only (never for 4xx).
MAX_RETRIES = 2
RETRY_BACKOFF_SECONDS = 3.0

RESPECT_ROBOTS = os.environ.get("LEADGEN_RESPECT_ROBOTS", "1") != "0"

# Cap on downloaded bytes per page. Homepages that exceed this are truncated;
# every signal we look for lives in the first chunk of markup in practice.
MAX_BYTES_PER_PAGE = 3_000_000

# How long a cached HTTP response stays fresh.
CACHE_TTL_DAYS = int(os.environ.get("LEADGEN_CACHE_TTL_DAYS", "14"))

# --------------------------------------------------------------- secrets -----


def _env_first(*names: str) -> str | None:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return None


def load_dotenv(path: Path | None = None) -> None:
    """Minimal .env loader so keys never need to live in the repo.

    Existing environment variables always win, so an explicit export in the
    shell overrides the file.
    """
    path = path or (REPO_ROOT / ".env")
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def companies_house_key() -> str | None:
    return _env_first("COMPANIES_HOUSE_API_KEY", "CH_API_KEY")


def brave_key() -> str | None:
    return _env_first("BRAVE_SEARCH_API_KEY", "BRAVE_API_KEY")


def serper_key() -> str | None:
    return _env_first("SERPER_API_KEY")


def google_cse() -> tuple[str, str] | None:
    key = _env_first("GOOGLE_CSE_KEY", "GOOGLE_API_KEY")
    cx = _env_first("GOOGLE_CSE_CX", "GOOGLE_CSE_ID")
    if key and cx:
        return key, cx
    return None


# ------------------------------------------------------- discovery gating ----

# Hosts that are never a company's own website. A match here is discarded
# outright before any scoring happens.
DIRECTORY_BLOCKLIST = {
    "192.com", "aboutus.com", "acquisitions.co.uk", "airtasker.com",
    "aliexpress.com", "amazon.co.uk", "amazon.com", "apple.com", "bark.com",
    "bbb.org", "bing.com", "bizdb.co.uk", "bloomberg.com", "brownbook.net",
    "bt.com", "business-live.co.uk", "businessmagnet.co.uk", "checkatrade.com",
    "childcare.co.uk", "citysearch.com", "companiesintheuk.co.uk",
    "companycheck.co.uk", "company-director-check.co.uk", "companylist.org",
    "cybo.com", "cylex-uk.co.uk", "dnb.com", "duckduckgo.com", "ebay.co.uk",
    "endole.co.uk", "europages.co.uk", "facebook.com", "fb.com",
    "find-and-update.company-information.service.gov.uk", "findthecompany.com",
    "freeindex.co.uk", "gassaferegister.co.uk", "glassdoor.co.uk",
    "goo.gl", "google.co.uk", "google.com", "gov.uk", "hotfrog.co.uk",
    "houzz.co.uk", "ibm.com", "indeed.co.uk", "indeed.com", "instagram.com",
    "kompass.com", "linkedin.com", "local.com", "localsearch24.co.uk",
    "m.facebook.com", "maps.app.goo.gl", "mybuilder.com", "nextdoor.co.uk",
    "opencorporates.com", "pinterest.co.uk", "pinterest.com",
    "plumbers.checkatrade.com", "ratedpeople.com", "reddit.com",
    "reviews.co.uk", "reviews.io", "scoot.co.uk", "t.co", "thebestof.co.uk",
    "thomsonlocal.com", "threads.net", "tiktok.com", "touchlocal.com",
    "trustatrader.com", "trustpilot.com", "tripadvisor.co.uk", "tumblr.com",
    "twitter.com", "vimeo.com", "wa.me", "which.co.uk", "whocallsme.com",
    "wikipedia.org", "x.com", "yell.com", "yelp.co.uk", "yelp.com",
    "youtube.com", "zoominfo.com",
}

# Free site builders / parking hosts. Not blocked (a real trader may genuinely
# use one) but they cap discovery confidence and read as an outdated signal.
WEAK_HOSTING_SUFFIXES = (
    ".wixsite.com", ".weebly.com", ".webnode.com", ".yolasite.com",
    ".business.site", ".godaddysites.com", ".square.site", ".wordpress.com",
    ".blogspot.com", ".btck.co.uk", ".moonfruit.com", ".jimdosite.com",
    ".site123.me", ".mystrikingly.com", ".sitey.me", ".webs.com",
)

# Candidate TLDs tried when guessing a domain from the company name.
GUESS_TLDS = (".co.uk", ".com", ".uk", ".net", ".ltd.uk", ".org.uk")

# Minimum verification score before a discovered URL is written to the CSV.
# See stage1.verify_candidate for the scoring rubric.
DISCOVERY_ACCEPT_THRESHOLD = 5

# ------------------------------------------------- Companies House gating ----

CH_NAME_SIMILARITY_THRESHOLD = 0.72

# Leading letters of a UK outcode -> the town/city as it appears in Location.
# Used so a CH record filed as "Bristol" still matches Location "Bishopsworth,
# Bristol", and vice versa.
POSTCODE_AREA_TO_CITY = {
    "AB": "aberdeen", "B": "birmingham", "BS": "bristol", "BA": "bath",
    "BR": "kent", "CT": "kent", "DA": "kent", "ME": "kent", "TN": "kent",
    "DL": "n yorkshire", "HG": "n yorkshire", "YO": "n yorkshire",
    "EX": "devon", "PL": "devon", "TQ": "devon",
    "G": "glasgow", "PA": "glasgow", "ML": "glasgow",
    "LS": "leeds", "WF": "leeds", "BD": "leeds",
    "M": "manchester", "OL": "manchester", "SK": "manchester",
    "BL": "manchester", "WA": "manchester",
    "NG": "nottingham", "DE": "derby",
    "S": "sheffield", "DN": "doncaster",
    "E": "london", "EC": "london", "N": "london", "NW": "london",
    "SE": "london", "SW": "london", "W": "london", "WC": "london",
    "IG": "london", "UB": "london", "HA": "london", "EN": "london",
    "TW": "london", "KT": "london", "SM": "london", "CR": "london",
    "RM": "london", "WD": "london",
    "EH": "edinburgh", "DD": "dundee", "IV": "inverness", "KY": "fife",
    "L": "liverpool", "CH": "chester", "NE": "newcastle", "SR": "sunderland",
    "TS": "teesside", "HU": "hull", "LN": "lincoln", "PE": "peterborough",
    "NR": "norwich", "IP": "ipswich", "CB": "cambridge", "CO": "colchester",
    "SS": "southend", "CM": "chelmsford", "AL": "st albans", "LU": "luton",
    "MK": "milton keynes", "OX": "oxford", "RG": "reading", "SL": "slough",
    "GU": "guildford", "RH": "crawley", "BN": "brighton", "PO": "portsmouth",
    "SO": "southampton", "SP": "salisbury", "DT": "dorchester",
    "BH": "bournemouth", "TA": "taunton", "TR": "truro", "GL": "gloucester",
    "SN": "swindon", "HR": "hereford", "WR": "worcester", "DY": "dudley",
    "WS": "walsall", "WV": "wolverhampton", "CV": "coventry", "LE": "leicester",
    "ST": "stoke", "TF": "telford", "SY": "shrewsbury", "CW": "crewe",
    "PR": "preston", "FY": "blackpool", "LA": "lancaster", "CA": "carlisle",
    "HD": "huddersfield", "HX": "halifax", "WN": "wigan", "SG": "stevenage",
    "NP": "newport", "CF": "cardiff", "SA": "swansea", "LD": "llandrindod",
    "LL": "llandudno", "BT": "belfast", "KA": "kilmarnock", "FK": "falkirk",
    "PH": "perth", "DG": "dumfries", "TD": "galashiels", "ZE": "shetland",
    "KW": "caithness", "HS": "hebrides",
}

# Company-name noise stripped before similarity comparison.
CH_NAME_NOISE = (
    "limited", "ltd", "plc", "llp", "lp", "cic", "company", "co",
    "holdings", "group", "uk", "the", "and",
)
