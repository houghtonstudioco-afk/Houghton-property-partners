"""Per-company pricing, on the AI automation agency model.

An earlier version of this module priced against self-serve AI receptionist
SaaS (£45-99/mo) and was wrong by roughly an order of magnitude. That is a
different business: a productised widget the customer configures themselves.
The agency model sells a built, integrated, maintained system, and the market
rates researched on 2 Aug 2026 are:

  Setup / project fee            $2,000-12,000 typical, $2,500-50,000 range
  Small business retainer        $1,000-3,500/mo  (2-3 workflows)
  Mid-market retainer            $4,000-10,000/mo (multi-workflow + reporting)
  Solo consultants / small shops $1,000-5,000/mo
  Growth system, 3-6 workflows   $4,000-12,000 build
  Agencies target clients at     $500K-$20M revenue

That last figure is the one that governs everything here. A sole trader gas
engineer on a personal mobile turns over well below £500K and cannot pay
£1,000/mo whatever the ROI argument says. Pricing at agency rates therefore
forces a different customer, not just a different number - which is why the
tier is derived from size signals rather than applied uniformly.

Scope is stated per tier on purpose. The clearest red flag buyers are warned
about is a large fixed quote with no written deliverables.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# Size signals -------------------------------------------------------------

INCORPORATED = re.compile(
    r"\b(ltd|limited|plc|llp|group|holdings|international|\(uk\))\b", re.I)

SOLE_TRADER = "Sole trader"
MID_MARKET = "Mid-market trade"
INDUSTRIAL_CO = "Industrial / commercial"
MAJOR = "Corporate / energy major"


def size_tier(company: str, phone_kind_value: str, reviews: int | None,
              segment: str) -> str:
    """Classify by ability to pay, not by how good a prospect they are."""
    reviews = reviews or 0
    incorporated = bool(INCORPORATED.search(company))
    office = phone_kind_value != "mobile"
    branch_of_group = " - " in company

    if segment == "energy major" or branch_of_group:
        return MAJOR
    if segment in ("b2b industrial", "fuel distribution"):
        return INDUSTRIAL_CO

    # Trade firms. An office line plus real review volume means vans and staff.
    if office and (reviews >= 60 or incorporated):
        return MID_MARKET
    # A mobile does not prove a one-man band: plenty of owners of multi-van
    # firms still carry the business phone. An incorporated firm with real
    # volume, or sheer job volume on its own, is a company not a sole trader.
    if incorporated and reviews >= 150:
        return MID_MARKET
    if reviews >= 250:
        return MID_MARKET
    return SOLE_TRADER


# Pricing ------------------------------------------------------------------
# (setup_low, setup_high, monthly_low, monthly_high)

TIER_PRICING: dict[str, tuple[int, int, int, int]] = {
    SOLE_TRADER:   (500, 1500, 199, 399),
    MID_MARKET:    (3000, 6000, 750, 1500),
    INDUSTRIAL_CO: (6000, 12000, 1500, 2500),
    MAJOR:         (12000, 25000, 2500, 5000),
}

TIER_SCOPE: dict[str, list[str]] = {
    SOLE_TRADER: [
        "AI call answering with job details captured and texted through",
        "Missed-call text-back",
        "Monthly summary",
    ],
    MID_MARKET: [
        "AI call answering, 24/7, with job triage and urgency routing",
        "Instant quote follow-up sequence (SMS + email)",
        "Online booking wired to the existing diary",
        "Annual service and gas-certificate renewal chasing",
        "Google review request automation",
        "Monthly reporting dashboard: calls caught, jobs booked, revenue attributed",
    ],
    INDUSTRIAL_CO: [
        "Enquiry intake and triage across phone, email and web form",
        "Quote and tender turnaround workflow with chase sequences",
        "CRM integration and pipeline hygiene automation",
        "Document and compliance-certificate handling",
        "Scheduled reporting to management",
        "Monitoring, model updates and API maintenance",
    ],
    MAJOR: [
        "Multi-site enquiry and dispatch automation",
        "Integration with existing ERP / field service platform",
        "Compliance-conscious intake and audit trail",
        "Custom agent development against internal systems",
        "SLA-backed monitoring, drift detection and change management",
        "Quarterly business review and expansion roadmap",
    ],
}

# Weeks from first contact to signature, for expectation setting.
TIER_SALES_CYCLE: dict[str, str] = {
    SOLE_TRADER: "same call to 1 week",
    MID_MARKET: "2-4 weeks, 1-2 decision makers",
    INDUSTRIAL_CO: "4-10 weeks, MD plus ops",
    MAJOR: "3-9 months, procurement-gated",
}

# Whether to lead with this tier when the goal is deals closed this month.
TIER_VERDICT: dict[str, str] = {
    SOLE_TRADER: "Low ticket - only worth it as a productised offer at volume",
    MID_MARKET: "BEST FIT - can pay agency rates, owner still decides",
    INDUSTRIAL_CO: "High ticket, slower - build this pipeline in parallel",
    MAJOR: "Do not cold call - long procurement cycle, wrong motion",
}


@dataclass
class Quote:
    tier: str
    setup_low: int
    setup_high: int
    monthly_low: int
    monthly_high: int
    scope: list[str] = field(default_factory=list)
    sales_cycle: str = ""
    verdict: str = ""
    website_build: int = 0
    website_reason: str = ""

    @property
    def setup_range(self) -> str:
        return f"£{self.setup_low:,}-{self.setup_high:,}"

    @property
    def monthly_range(self) -> str:
        return f"£{self.monthly_low:,}-{self.monthly_high:,}/mo"

    @property
    def year_one_low(self) -> int:
        return self.setup_low + self.monthly_low * 12 + self.website_build

    @property
    def year_one_high(self) -> int:
        return self.setup_high + self.monthly_high * 12 + self.website_build


# A website is folded into the build rather than sold separately at this level;
# it is a line item, not a product.
WEBSITE_LINE: dict[str, int] = {
    SOLE_TRADER: 750,
    MID_MARKET: 2000,
    INDUSTRIAL_CO: 3500,
    MAJOR: 6000,
}


def quote_for(company: str, phone_kind_value: str, reviews: int | None,
              segment: str, website_status: str) -> Quote:
    tier = size_tier(company, phone_kind_value, reviews, segment)
    setup_low, setup_high, monthly_low, monthly_high = TIER_PRICING[tier]

    if website_status == "none":
        web, reason = WEBSITE_LINE[tier], "No website - build included"
    elif website_status == "weak":
        web, reason = WEBSITE_LINE[tier], "Free subdomain - rebuild included"
    elif website_status == "ok":
        web, reason = 0, "Site is fine - do not pitch a rebuild"
    else:
        web, reason = 0, "Check site before quoting"

    return Quote(
        tier=tier,
        setup_low=setup_low,
        setup_high=setup_high,
        monthly_low=monthly_low,
        monthly_high=monthly_high,
        scope=TIER_SCOPE[tier],
        sales_cycle=TIER_SALES_CYCLE[tier],
        verdict=TIER_VERDICT[tier],
        website_build=web,
        website_reason=reason,
    )
