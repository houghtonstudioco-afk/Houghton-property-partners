"""Per-company pricing for each service.

Anchored to UK market rates researched on 2 August 2026 (see
RESEARCH_FINDINGS.md for sources), not invented:

  AI receptionists aimed at UK trades   £45-99/mo, mostly self-serve
  Human answering services              £100-400/mo
  Basic sole-trader trade website       £349-499 one-off
  Professional multi-page trade site    £800-2,000 one-off
  Website care plans                    £45-250/mo
  Pay-monthly website model             £0-200 upfront + £40-100/mo

Positioning: the £45-50 self-serve tier is the anchor, and a one-person
operation cannot win a price war against it. The defensible position is
done-for-you setup and trade-specific configuration, which is what the setup
fee buys and what these prospects actually need - they will not self-serve
onboard. Monthly still lands under the human-answering services being
displaced.

Tiering is by Google review count, used as a proxy for call volume and
therefore both the value at stake and the ability to pay.
"""
from __future__ import annotations

from dataclasses import dataclass

# Tier thresholds on review count.
TIER_HIGH = 200
TIER_MID = 60

TIER_HIGH_NAME = "High volume"
TIER_MID_NAME = "Established"
TIER_LOW_NAME = "Growing"


def tier_of(reviews: int | None) -> str:
    if reviews is None:
        return TIER_MID_NAME
    if reviews >= TIER_HIGH:
        return TIER_HIGH_NAME
    if reviews >= TIER_MID:
        return TIER_MID_NAME
    return TIER_LOW_NAME


# product -> tier -> (setup, monthly)
PRICES: dict[str, dict[str, tuple[int, int]]] = {
    "AI Receptionist": {
        TIER_HIGH_NAME: (349, 129),
        TIER_MID_NAME: (249, 89),
        TIER_LOW_NAME: (149, 59),
    },
    "Speed-to-Lead": {
        TIER_HIGH_NAME: (349, 79),
        TIER_MID_NAME: (249, 59),
        TIER_LOW_NAME: (149, 45),
    },
    "Booking + Reminders": {
        TIER_HIGH_NAME: (299, 69),
        TIER_MID_NAME: (199, 49),
        TIER_LOW_NAME: (149, 39),
    },
    "Enquiry Triage": {
        TIER_HIGH_NAME: (299, 79),
        TIER_MID_NAME: (199, 59),
        TIER_LOW_NAME: (149, 45),
    },
}

# Website build, quoted only where the site is missing or on a free
# subdomain. Sits inside the researched £349-2,000 band.
WEBSITE_PRICES: dict[str, tuple[int, int]] = {
    TIER_HIGH_NAME: (1495, 49),   # multi-page, service pages, local SEO
    TIER_MID_NAME: (895, 39),
    TIER_LOW_NAME: (499, 29),
}

# Taking both together, the bundle discounts the website setup rather than the
# recurring fee, because recurring revenue is the point.
BUNDLE_SETUP_DISCOUNT = 0.20


@dataclass
class Quote:
    tier: str
    service: str
    service_setup: int
    service_monthly: int
    website_setup: int          # 0 when no website is being sold
    website_monthly: int
    needs_website: bool
    website_reason: str

    @property
    def total_setup(self) -> int:
        if self.needs_website:
            return round(self.service_setup
                         + self.website_setup * (1 - BUNDLE_SETUP_DISCOUNT))
        return self.service_setup

    @property
    def total_monthly(self) -> int:
        return self.service_monthly + (self.website_monthly if self.needs_website else 0)

    @property
    def year_one(self) -> int:
        return self.total_setup + self.total_monthly * 12

    def summary(self) -> str:
        if self.needs_website:
            return (f"£{self.total_setup:,} setup + £{self.total_monthly}/mo "
                    f"(incl. website, 20% bundle discount)")
        return f"£{self.total_setup:,} setup + £{self.total_monthly}/mo"


def quote_for(service: str, reviews: int | None, website_status: str) -> Quote:
    """Price one company.

    ``website_status`` is one of: 'none' (no site found), 'weak' (free
    site-builder subdomain), 'ok' (own domain, real site), 'unknown' (never
    checked). A website is only quoted for 'none' and 'weak' - quoting a
    rebuild to someone with a perfectly good site is how a call ends early.
    """
    tier = tier_of(reviews)
    setup, monthly = PRICES.get(service, PRICES["Enquiry Triage"])[tier]
    web_setup, web_monthly = WEBSITE_PRICES[tier]

    if website_status == "none":
        needs, reason = True, "No website found - full build"
    elif website_status == "weak":
        needs, reason = True, "On a free subdomain - own domain + real site"
    elif website_status == "ok":
        needs, reason = False, "Has a working site - do not pitch a rebuild"
    else:
        needs, reason = False, "Site not checked - confirm before quoting"

    return Quote(
        tier=tier,
        service=service,
        service_setup=setup,
        service_monthly=monthly,
        website_setup=web_setup,
        website_monthly=web_monthly,
        needs_website=needs,
        website_reason=reason,
    )
