"""ICP qualification and product-fit matching.

Answers two questions the outreach ranking does not: is this company in the
ideal customer profile at all, and which product should be led with.

The ICP is derived from the data rather than assumed. Across the 176 rows only
the domestic trade segment shows the combination that makes conversational AI
sell - urgent demand, high job values, an owner who physically cannot answer the
phone, and enough volume for a missed call to cost real money. The industrial,
distribution and energy-major segments have essentially no urgent work, almost
no mobile numbers and negligible consumer review volume, so they are excluded
from the ICP even though some are large businesses.
"""
from __future__ import annotations

import re

from .outreach import (
    COMMERCIAL,
    DOMESTIC,
    MOBILE,
    phone_kind,
    segment_of,
)

# ------------------------------------------------------- demand signatures ---

URGENT = re.compile(
    r"emergency|24/?7|breakdown|leak|repair|call-?out|fault|unsafe|"
    r"no heating|burst|blockage", re.I)
INSTALL = re.compile(
    r"install|replacement|replace|fitting|new boiler|renewable|solar|"
    r"heat pump|\bEV\b|conversion|upgrade", re.I)
RECURRING = re.compile(
    r"servic|maintenance|certificat|\bcerts?\b|safety check|contract|"
    r"service plan|inspection|annual", re.I)

# Rough UK job values, used only to explain the size of the prize in a pitch.
# These are order-of-magnitude working figures, not researched market data.
JOB_VALUE = {
    "install": "£2,000-4,000",
    "urgent": "£90-250",
    "recurring": "£60-120",
}


# --------------------------------------------------------------- products ----

AI_RECEPTIONIST = "AI Receptionist (24/7 call answering)"
SPEED_TO_LEAD = "Speed-to-Lead (instant quote follow-up)"
BOOKING_REMINDERS = "Online Booking + annual renewal reminders"
ENQUIRY_TRIAGE = "Enquiry triage + out-of-hours cover"


def job_noun(row: dict[str, str]) -> str:
    """What this company's big-ticket job is actually called.

    Generic 'boiler jobs' copy read out to an oil-tank fitter or a solar
    installer lands as a script, which is exactly what kills a cold call.
    """
    blob = f"{row.get('Industry', '')} {row.get('Services', '')}".lower()
    if "tank" in blob:
        return "tank replacements"
    if "solar" in blob or "renewable" in blob or "heat pump" in blob:
        return "renewables installs"
    if re.search(r"\bev\b|charger", blob):
        return "EV charger installs"
    if "structural" in blob or "design" in blob:
        return "design jobs"
    if "electric" in blob and "boiler" not in blob:
        return "electrical installs"
    if "boiler" in blob or "heating" in blob or "gas" in blob:
        return "boiler jobs"
    return "installs"


def demand_profile(row: dict[str, str]) -> dict[str, bool]:
    blob = f"{row.get('Industry', '')} {row.get('Services', '')}"
    return {
        "urgent": bool(URGENT.search(blob)),
        "install": bool(INSTALL.search(blob)),
        "recurring": bool(RECURRING.search(blob)),
    }


def in_icp(row: dict[str, str]) -> tuple[bool, str]:
    """Is this company worth calling at all? Returns (verdict, reason)."""
    segment = segment_of(row)
    if segment not in (DOMESTIC, COMMERCIAL):
        return False, f"{segment}: no urgent demand, procurement-led buying"

    reviews = str(row.get("Google Reviews (verified)", "") or "").strip()
    volume = int(reviews) if reviews.isdigit() else 0
    profile = demand_profile(row)

    # Volume is the proxy for "a missed call actually costs them something".
    # Below roughly 20 reviews there is not enough inbound for the pitch to
    # land, whatever the trade.
    if volume < 20 and not profile["urgent"]:
        return False, f"only {volume} reviews and no urgent work: too little inbound"

    return True, f"{segment}, {volume} reviews"


def product_fit(row: dict[str, str]) -> tuple[str, str, str]:
    """Return (primary product, why, secondary product).

    One primary, chosen by the sharpest pain. A second is named only as an
    upsell for later, never as part of the opening.
    """
    profile = demand_profile(row)
    kind = phone_kind(row.get("Phone Number", ""))
    reviews = str(row.get("Google Reviews (verified)", "") or "").strip()
    volume = int(reviews) if reviews.isdigit() else 0

    # Urgent work on a mobile is the strongest case there is: the customer with
    # no heating rings the next name on Google within about a minute.
    if profile["urgent"] and kind == MOBILE:
        return (
            AI_RECEPTIONIST,
            f"Emergency work on a personal mobile with {volume} reviews of "
            f"inbound. Every call missed while they are on a job goes to the "
            f"next engineer on Google, and an emergency callout is "
            f"{JOB_VALUE['urgent']}.",
            SPEED_TO_LEAD if profile["install"] else BOOKING_REMINDERS,
        )

    if profile["urgent"]:
        return (
            AI_RECEPTIONIST,
            f"Emergency work routed through an office line. Out of hours and "
            f"at lunchtime those calls go unanswered, and {volume} reviews "
            f"says the volume is real.",
            BOOKING_REMINDERS,
        )

    # Install-led businesses lose money at the quote stage, not the call stage.
    if profile["install"] and volume >= 80:
        return (
            SPEED_TO_LEAD,
            f"Install-led with {volume} reviews. {job_noun(row).capitalize()} "
            f"run {JOB_VALUE['install']} and the customer is collecting three "
            f"quotes; whoever replies first usually wins. Quotes going out "
            f"days late is where the money leaks.",
            AI_RECEPTIONIST,
        )

    if profile["recurring"]:
        return (
            BOOKING_REMINDERS,
            f"Servicing and certificate work is annual and predictable, but "
            f"only if someone chases it. {volume} past customers is a renewal "
            f"list nobody is working.",
            AI_RECEPTIONIST,
        )

    if profile["install"]:
        return (
            SPEED_TO_LEAD,
            f"{job_noun(row).capitalize()} at {JOB_VALUE['install']} a job. "
            f"Slow quote follow-up is the single biggest leak in this trade.",
            AI_RECEPTIONIST,
        )

    return (
        ENQUIRY_TRIAGE,
        f"{volume} reviews of steady demand with no obvious triage on "
        f"incoming enquiries.",
        BOOKING_REMINDERS,
    )


def opener(row: dict[str, str], product: str) -> str:
    """A first line to actually say, tuned to the product being led with."""
    name = row.get("Company Name", "there")
    reviews = str(row.get("Google Reviews (verified)", "") or "").strip()
    volume = int(reviews) if reviews.isdigit() else 0

    on_mobile = phone_kind(row.get("Phone Number", "")) == MOBILE
    if product == AI_RECEPTIONIST:
        if on_mobile:
            return (f"Hi, is that {name}? Quick one - when you're on a job and "
                    f"the phone goes, what happens to that call? I ask because "
                    f"you've got {volume} reviews, so you're clearly busy, and "
                    f"that usually means calls are going to voicemail.")
        return (f"Hi, is that {name}? Quick one - what happens to calls that "
                f"come in after hours or when the office is on the other line? "
                f"With {volume} reviews you'll be taking a fair volume, and "
                f"that's usually where they slip.")
    if product == SPEED_TO_LEAD:
        return (f"Hi, is that {name}? When someone asks you to quote for "
                f"{job_noun(row)}, how long does it usually take to get back to "
                f"them? Most engineers I speak to say a day or two, and by then "
                f"the customer's taken someone else's.")
    if product == BOOKING_REMINDERS:
        return (f"Hi, is that {name}? Do you chase your service and safety "
                f"certificate renewals, or wait for customers to ring you? "
                f"You've got {volume} past customers there - that's a list "
                f"most engineers never work.")
    return (f"Hi, is that {name}? How do enquiries reach you at the moment - "
            f"phone, website, or both? Trying to understand where they land "
            f"when you're mid-job.")


QUALIFIED_COLUMNS = [
    "Rank",
    "Company",
    "Score",
    "What They Do",
    "Phone",
    "How To Contact",
    "Best Time",
    "Website",
    "SELL THEM",
    "Why It Fits",
    "Opening Line",
    "Upsell Later",
    "Location",
    "Reviews",
    "Rating",
]
