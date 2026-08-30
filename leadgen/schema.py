"""CSV column contract.

The 24 original columns keep their exact names and order so any existing sheet
formulas or CRM import mappings continue to line up. Everything the pipeline
learns that has nowhere to go in the original schema is appended after them.
"""
from __future__ import annotations

# Exact header order of the source file. Verified against the input at load
# time; a mismatch aborts rather than silently writing to the wrong column.
ORIGINAL_COLUMNS = [
    "Company Name",
    "Website",
    "Industry",
    "Services",
    "Location",
    "Number of Employees",
    "Annual Revenue",
    "Managing Director / Owner",
    "Email Address",
    "Phone Number",
    "LinkedIn Company Page",
    "Company LinkedIn URL",
    "Decision Maker LinkedIn",
    "Companies House Number",
    "Uses CRM (unverified)",
    "Online Booking (unverified)",
    "Live Chat (unverified)",
    "Website Outdated Score (unverified)",
    "Google Reviews (verified)",
    "Google Rating (verified)",
    "Automation Opportunity",
    "Suggested AI Automation Package",
    "Opening Line",
    "Lead Score /100",
]

# Appended columns, grouped by the stage that populates them.
STAGE1_COLUMNS = [
    "Website Source",              # which provider produced the URL
    "Website Confidence",          # high | medium | none
    "Website Evidence",            # why we believed it (phone match, town, ...)
]

STAGE2_COLUMNS = [
    "Final URL",                   # after redirects
    "HTTP Status",                 # 200, 404, timeout, dns_error, ssl_expired...
    "Site Health",                 # ok | insecure | broken | unreachable | none
    "SSL Status",                  # valid | expired | hostname_mismatch | ...
    "Live Chat Vendor",
    "Online Booking Vendor",
    "CRM Vendor",
    "Contact Method",              # form | mailto | phone | none
    "Outdated Signals",            # which rules fired, semicolon separated
    "All Emails Found",            # every usable address on the site, best first
    "Site Checked At",
]

STAGE3_COLUMNS = [
    "Companies House Name Matched",
    "Companies House Status",       # active | dissolved | liquidation | ...
    "Companies House Match Basis",  # town | postcode-area
    "Companies House Address",
]

STAGE4_COLUMNS = [
    "Lead Score (Original)",       # preserved before the rescore overwrites
    "Lead Score Breakdown",
    "Lead Score Confidence",       # high | medium | low
    "Web Dev Opportunity",         # what a web developer could sell them
    "Web Dev Priority",            # 1 (hottest) .. 6, blank = not a prospect
]

APPENDED_COLUMNS = (
    STAGE1_COLUMNS + STAGE2_COLUMNS + STAGE3_COLUMNS + STAGE4_COLUMNS
    + ["Enrichment Notes"]
)

OUTPUT_COLUMNS = ORIGINAL_COLUMNS + APPENDED_COLUMNS

# Original columns the pipeline is allowed to fill when blank.
FILLABLE_ORIGINAL = {
    "Website",
    "Companies House Number",
    "Uses CRM (unverified)",
    "Online Booking (unverified)",
    "Live Chat (unverified)",
    "Website Outdated Score (unverified)",
}

# The single column the user explicitly authorised overwriting (stage 4).
OVERWRITE_ALLOWED = {"Lead Score /100"}
