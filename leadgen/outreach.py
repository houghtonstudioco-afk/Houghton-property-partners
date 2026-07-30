"""Outreach ranking and per-company contact strategy.

Built only from columns that are verified in the source file - company name,
industry, services, location, phone number, Google reviews and rating - so this
runs and is trustworthy before any web enrichment has happened.

The central modelling decision: **review count is only comparable within a
business segment.** A domestic gas engineer with 300 Google reviews and a pipe
fabricator with 4 are both healthy businesses; consumers review the first and
never review the second. Ranking them on one scale would bury good industrial
firms and flatter consumer trades. So demand is scored as a percentile *within*
segment, and segment fit for cold outreach is scored separately.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# ------------------------------------------------------------- segments ------

DOMESTIC = "domestic trade"
COMMERCIAL = "commercial trade"
DISTRIBUTION = "fuel distribution"
INDUSTRIAL = "b2b industrial"
ENERGY_MAJOR = "energy major"

# Checked in order; first match wins, so the more specific patterns lead.
#
# Consumer-trade terms are tested BEFORE the industrial ones on purpose. A firm
# whose services read "boiler repair, gas pipe replacement" is a domestic gas
# engineer, but the bare word 'pipe' would otherwise drag it into b2b industrial
# alongside the pipe fabricators.
SEGMENT_RULES: list[tuple[str, re.Pattern[str]]] = [
    (ENERGY_MAJOR, re.compile(
        r"exploration|production|offshore|oilfield|oil & gas (operations|services)|"
        r"energy (services|equipment)|e&p", re.I)),
    (COMMERCIAL, re.compile(
        r"commercial gas|building services|industrial & commercial|"
        r"commercial & domestic|energy assessment|energy consultancy|"
        r"engineering recruitment|engineering consultancy", re.I)),
    (DOMESTIC, re.compile(
        r"boiler|central heating|gas safety|gas safe|landlord|radiator|"
        r"underfloor|domestic|plumbing|gas servicing|gas engineering|"
        r"gas & heating|heating engineering|oil tank|home", re.I)),
    (DISTRIBUTION, re.compile(
        r"distribution|lubricants|petroleum|fuel", re.I)),
    (INDUSTRIAL, re.compile(
        r"precision|fabricat|manufactur|pipeline|pipework|pipe |structural|"
        r"mechanical|industrial|maintenance contracting|water infrastructure|"
        r"drainage|construction|supplies|technology", re.I)),
    (DOMESTIC, re.compile(
        r"gas|heating|plumbing|renewable|electrical", re.I)),
]

# Consumers leave Google reviews; the customers of a pipe fabricator or an
# oilfield services firm do not. So a mobile number plus real review volume is
# direct evidence of a consumer-facing business, and it overrides any keyword
# that says otherwise.
CONSUMER_EVIDENCE_REVIEWS = 50

# How receptive each segment is to a cold approach about web work/automation.
SEGMENT_FIT = {
    DOMESTIC: 25,       # owner decides, fast, phone-driven business
    COMMERCIAL: 20,     # small management layer, still reachable
    DISTRIBUTION: 15,   # depot managers, moderate process
    INDUSTRIAL: 10,     # works managers, slower, rarely buys on first call
    ENERGY_MAJOR: 2,    # procurement-gated, existing agencies, wrong motion
}


def segment_of(row: dict[str, str]) -> str:
    blob = f"{row.get('Industry', '')} {row.get('Services', '')}"
    segment = INDUSTRIAL
    for name, pattern in SEGMENT_RULES:
        if pattern.search(blob):
            segment = name
            break

    # Evidence override: a heavily reviewed business on a mobile number is
    # serving consumers whatever its industry label says.
    if segment in (INDUSTRIAL, DISTRIBUTION):
        reviews = str(row.get("Google Reviews (verified)", "") or "").strip()
        if (reviews.isdigit() and int(reviews) >= CONSUMER_EVIDENCE_REVIEWS
                and phone_kind(row.get("Phone Number", "")) == MOBILE):
            return DOMESTIC
    return segment


# ---------------------------------------------------------------- phones -----

MOBILE = "mobile"
LANDLINE = "landline"
NON_GEO = "non-geographic"


def phone_kind(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("44"):
        digits = "0" + digits[2:]
    if digits.startswith("07"):
        return MOBILE
    if digits.startswith(("08", "03")):
        return NON_GEO
    if digits.startswith("0"):
        return LANDLINE
    return "unknown"


# A mobile number is the single best predictor of reaching the decision maker
# directly: it means the owner carries the business phone.
REACHABILITY = {MOBILE: 25, LANDLINE: 15, NON_GEO: 5, "unknown": 10}


# ----------------------------------------------------------- contact plan ----

@dataclass
class ContactPlan:
    channel: str
    best_time: str
    ask_for: str
    approach: str

    def as_text(self) -> str:
        return (f"{self.channel} | {self.best_time} | ask for: {self.ask_for} "
                f"| {self.approach}")


def contact_plan(row: dict[str, str], segment: str, kind: str,
                 reviews: int | None) -> ContactPlan:
    """Per-company contact strategy, from segment + phone type + demand."""

    # Non-geographic numbers front a switchboard; the phone is the wrong door.
    if kind == NON_GEO:
        return ContactPlan(
            channel="LinkedIn or email, not the phone",
            best_time="Tue-Thu, 09:00-11:00",
            ask_for="owner / operations lead by name",
            approach=("0800/03 number means a switchboard will screen you. Find "
                      "the decision maker on LinkedIn first and reference "
                      "something specific about their operation."),
        )

    if segment == ENERGY_MAJOR:
        return ContactPlan(
            channel="LinkedIn only - do not cold call",
            best_time="Tue-Thu, business hours",
            ask_for="digital / IT manager or communications lead",
            approach=("Procurement gates all supplier spend and they almost "
                      "certainly retain an agency. A cold call reaches a "
                      "receptionist and burns the name. Approach a named "
                      "individual on LinkedIn with a specific observation, or "
                      "deprioritise entirely."),
        )

    if segment == INDUSTRIAL:
        return ContactPlan(
            channel="Phone, then email a one-pager",
            best_time="Tue-Thu, 09:00-10:30",
            ask_for="works manager, general manager or director",
            approach=("Shop-floor businesses rarely buy on a first call. Open on "
                      "trade credibility - quoting turnaround, drawing handling, "
                      "enquiry tracking - not on Google reviews, which this "
                      "sector does not collect. Expect two or three touches."),
        )

    if segment == DISTRIBUTION:
        return ContactPlan(
            channel="Phone the depot",
            best_time="Mon-Thu, 10:00-11:30",
            ask_for="depot manager or general manager",
            approach=("Avoid early morning - drivers and deliveries dominate. "
                      "Angle on order-taking and delivery scheduling: winter "
                      "peaks bury them in phone orders. Skip cold weather snaps, "
                      "they will have no time to talk."),
        )

    if segment == COMMERCIAL:
        if kind == MOBILE:
            return ContactPlan(
                channel="Direct mobile call",
                best_time="07:30-08:30 or 17:00-18:30",
                ask_for="whoever answers - it is the owner",
                approach=("Owner-run commercial outfit. They decide on the spot. "
                          "Lead on missed out-of-hours enquiries from commercial "
                          "clients, where a lost call is a lost contract."),
            )
        return ContactPlan(
            channel="Office phone, follow up by email",
            best_time="Tue-Thu, 09:00-11:00",
            ask_for="contracts manager or operations manager",
            approach=("An admin will screen. Ask for the person who handles "
                      "incoming enquiries by role, not by name you do not have. "
                      "Angle on service contracts and planned maintenance "
                      "scheduling."),
        )

    # DOMESTIC
    volume_note = ""
    if reviews and reviews >= 200:
        volume_note = (f" Lead with their volume: {reviews} Google reviews means "
                       f"heavy inbound, so ask what happens to enquiries that "
                       f"arrive while they are under a boiler.")
    elif reviews and reviews >= 50:
        volume_note = (f" {reviews} reviews shows steady demand - ask how they "
                       f"handle enquiries while on a job.")

    if kind == MOBILE:
        return ContactPlan(
            channel="Direct mobile call (SMS/WhatsApp acceptable)",
            best_time="07:30-08:30 or 17:00-18:30",
            ask_for="whoever answers - it is the owner",
            approach=("Sole trader or owner-operator carrying the business phone. "
                      "They decide instantly and hate admin. Keep it under 60 "
                      "seconds. Do not call 09:00-16:00, they are on jobs and "
                      "will resent it." + volume_note),
        )
    return ContactPlan(
        channel="Office phone, follow up by email",
        best_time="Tue-Thu, 09:00-11:00 or 16:00-17:00",
        ask_for="the owner or whoever books the diary",
        approach=("Landline means an office with someone on the desk - often a "
                  "partner or part-time admin. They are the gatekeeper and also "
                  "the person whose workload you are offering to cut, so make "
                  "them the ally." + volume_note),
    )


# ---------------------------------------------------------------- scoring ----

def _percentile_within(value: int, population: list[int]) -> float:
    """Fraction of the segment this company sits at or above (0..1)."""
    if not population:
        return 0.5
    below = sum(1 for v in population if v < value)
    equal = sum(1 for v in population if v == value)
    return (below + equal / 2) / len(population)


def reputation_points(rating: float | None, reviews: int | None) -> tuple[int, str]:
    if rating is None:
        return 8, "no rating"
    if rating >= 4.8:
        return 20, f"{rating} excellent"
    if rating >= 4.5:
        return 16, f"{rating} strong"
    if rating >= 4.0:
        return 12, f"{rating} good"
    if rating >= 3.0:
        return 8, f"{rating} mixed"
    # A poor rating with real volume means an active reputation problem: a
    # genuine need, but a harder and riskier client to take on.
    return 10 if (reviews or 0) >= 20 else 5, f"{rating} poor"


def rank(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Annotate every row with segment, contact plan and an outreach score.

    Returns the rows sorted best-to-weakest. Mutates the rows in place.
    """
    def parse_int(value: str) -> int | None:
        value = str(value or "").strip()
        return int(value) if value.isdigit() else None

    def parse_float(value: str) -> float | None:
        value = str(value or "").strip()
        try:
            return float(value)
        except ValueError:
            return None

    # Segment first, so demand can be percentile-ranked within it.
    segments: dict[str, list[int]] = {}
    for row in rows:
        seg = segment_of(row)
        row["_segment"] = seg
        reviews = parse_int(row.get("Google Reviews (verified)", ""))
        if reviews is not None:
            segments.setdefault(seg, []).append(reviews)

    for row in rows:
        seg = row["_segment"]
        kind = phone_kind(row.get("Phone Number", ""))
        reviews = parse_int(row.get("Google Reviews (verified)", ""))
        rating = parse_float(row.get("Google Rating (verified)", ""))

        reach = REACHABILITY[kind]
        fit = SEGMENT_FIT[seg]
        if reviews is None:
            demand = 12                     # unknown, mid-band
            demand_note = "no review data"
        else:
            pct = _percentile_within(reviews, segments.get(seg, []))
            demand = round(30 * pct)
            demand_note = f"{reviews} reviews, {pct:.0%} of {seg}"
        rep, rep_note = reputation_points(rating, reviews)

        total = reach + fit + demand + rep
        plan = contact_plan(row, seg, kind, reviews)

        row["Segment"] = seg
        row["Phone Type"] = kind
        row["Outreach Score /100"] = str(total)
        row["Outreach Breakdown"] = (
            f"reach[{kind}]={reach}/25 segment[{seg}]={fit}/25 "
            f"demand={demand}/30 ({demand_note}) reputation={rep}/20 ({rep_note})"
        )
        row["Contact Channel"] = plan.channel
        row["Best Time To Call"] = plan.best_time
        row["Ask For"] = plan.ask_for
        row["Contact Approach"] = plan.approach

    ordered = sorted(rows, key=lambda r: -int(r["Outreach Score /100"]))
    for position, row in enumerate(ordered, start=1):
        row["Outreach Rank"] = str(position)
        row.pop("_segment", None)
    return ordered


# ------------------------------------------------------------ pitch sheet ----

def what_they_do(row: dict[str, str]) -> str:
    """One short phrase: what this business actually does."""
    services = (row.get("Services") or "").strip()
    industry = (row.get("Industry") or "").strip()
    if services:
        # Services is concrete ("Boiler installation, gas servicing"); trim to
        # the first two items so the column stays scannable.
        parts = [p.strip() for p in services.split(",") if p.strip()]
        return ", ".join(parts[:2])
    return industry or "unknown"


def website_cell(row: dict[str, str]) -> str:
    """What to show in the website column, without ever implying we checked."""
    site = (row.get("Website") or "").strip()
    if site:
        health = (row.get("Site Health") or "").strip()
        if health in ("broken", "unreachable"):
            return f"{site}  (DEAD)"
        if health == "insecure":
            return f"{site}  (no valid HTTPS)"
        if health == "placeholder":
            return f"{site}  (placeholder)"
        return site
    opportunity = (row.get("Web Dev Opportunity") or "").strip()
    if opportunity.startswith("no website"):
        return "NONE FOUND - needs a site"
    return "not checked yet"


def pitch_for(row: dict[str, str], segment: str, kind: str,
              reviews: int | None) -> str:
    """The single most sellable gap, phrased as something you can open with.

    Deliberately one specific idea per company rather than a list - a pitch
    that names three products is a pitch with no point of entry.
    """
    site = (row.get("Website") or "").strip()
    health = (row.get("Site Health") or "").strip()
    opportunity = (row.get("Web Dev Opportunity") or "").strip()

    # A confirmed site problem outranks everything: it is concrete, visible to
    # them, and easy to open on.
    if opportunity.startswith("no website"):
        return "Website build - no site at all, invisible outside Google"
    if health in ("broken", "unreachable"):
        return "Urgent rebuild - their site is down right now"
    if health == "placeholder":
        return "Real website - currently just a placeholder page"
    if health == "insecure":
        return "HTTPS fix + rebuild - browsers flag them as 'not secure'"

    outdated = str(row.get("Website Outdated Score (unverified)", "") or "").strip()
    if outdated.isdigit() and int(outdated) >= 8:
        return "Redesign - site looks a decade old, no mobile layout"

    has_chat = bool((row.get("Live Chat Vendor") or "").strip())
    has_booking = bool((row.get("Online Booking Vendor") or "").strip())

    if segment == ENERGY_MAJOR:
        return "Skip - procurement-gated, almost certainly has an agency"

    if segment == INDUSTRIAL:
        return "Quote turnaround - enquiries sit in an inbox between jobs"

    if segment == DISTRIBUTION:
        return "Order taking + delivery scheduling - winter phone peaks"

    if segment == COMMERCIAL:
        if not has_chat:
            return "Out-of-hours cover - a missed call is a lost contract"
        return "Service-contract scheduling and renewals"

    # Domestic trade - the strongest segment, so be specific about why.
    # Keep the wording trade-neutral: this segment also holds structural
    # engineers and tank fitters, who are not "under a boiler".
    if kind == MOBILE and reviews and reviews >= 150:
        return (f"Call answering - {reviews} reviews of inbound landing on one "
                f"mobile while they are out on jobs")
    if kind == MOBILE:
        return "Call answering - owner misses enquiries while out on site"
    if reviews and reviews >= 150 and not has_booking:
        return (f"Online booking + enquiry handling - {reviews} reviews of "
                f"demand, all funnelled through the office phone")
    if not site:
        return "Website + call answering - check what they have first"
    return "Online booking - stop the diary going through the phone"


PITCH_COLUMNS = [
    "Rank",
    "Company",
    "Score",
    "What They Do",
    "Phone",
    "Website",
    "What To Pitch",
]


def pitch_sheet(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Slimmed, scannable view. Assumes rank() has already run."""
    sheet = []
    for row in rows:
        reviews = str(row.get("Google Reviews (verified)", "") or "").strip()
        sheet.append({
            "Rank": row.get("Outreach Rank", ""),
            "Company": row.get("Company Name", ""),
            "Score": row.get("Outreach Score /100", ""),
            "What They Do": what_they_do(row),
            "Phone": row.get("Phone Number", ""),
            "Website": website_cell(row),
            "What To Pitch": pitch_for(
                row,
                row.get("Segment", ""),
                row.get("Phone Type", ""),
                int(reviews) if reviews.isdigit() else None,
            ),
        })
    return sheet


EXPORT_COLUMNS = [
    "Outreach Rank",
    "Outreach Score /100",
    "Company Name",
    "Segment",
    "Phone Number",
    "Phone Type",
    "Contact Channel",
    "Best Time To Call",
    "Ask For",
    "Contact Approach",
    "Location",
    "Industry",
    "Services",
    "Google Reviews (verified)",
    "Google Rating (verified)",
    "Website",
    "Web Dev Opportunity",
    "Lead Score /100",
    "Outreach Breakdown",
    "Opening Line",
]
