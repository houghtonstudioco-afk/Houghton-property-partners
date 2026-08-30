#!/usr/bin/env python3
"""Build the formatted call sheet workbook from QUALIFIED_LEADS.csv.

Produces Call_Sheet.xlsx: one row per qualified lead, styled for working
through on the phone rather than for analysis.
"""
from __future__ import annotations

import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from leadgen import pricing
from leadgen.outreach import phone_kind, segment_of

REPO = Path(__file__).resolve().parent

# Websites confirmed by hand on 2 Aug 2026. Everything else is unverified,
# because the automated crawl has never had network access.
VERIFIED_SITES = {
    "HydroGreen Heating and Gas Engineering": (
        "hydrogreenheatinga.wixsite.com", "Free Wix subdomain - no own domain"),
    "Pipe Guys (Bham) Ltd": (
        "pipeguys.co.uk", "Own domain, real site"),
    "Blaymires Plumbing & Heating": (
        "blaymires-plumbing-heating-1.ueniweb.com", "UENI subdomain - no own domain"),
    "Secure Gas 247": (
        "securegas247.co.uk", "Own domain, real site"),
    "The Gas Pro": (
        "", "thegaspro.co.uk does not resolve - check listing"),
}

# Firms confirmed to advertise round-the-clock cover while running on one
# mobile. The strongest opening line available, and verified rather than
# inferred - but only found by hand-checking, so this list is not exhaustive.
ADVERTISES_247 = {
    "HydroGreen Heating and Gas Engineering",
    "Pipe Guys (Bham) Ltd",
    "Blaymires Plumbing & Heating",
    "Secure Gas 247",
}

# Product -> short label for the sheet.
PRODUCT_SHORT = {
    "AI Receptionist (24/7 call answering)": "AI Receptionist",
    "Speed-to-Lead (instant quote follow-up)": "Speed-to-Lead",
    "Online Booking + annual renewal reminders": "Booking + Reminders",
    "Enquiry triage + out-of-hours cover": "Enquiry Triage",
}

# Website status per company: 'none', 'weak', 'ok', 'unknown'.
SITE_STATUS = {
    "HydroGreen Heating and Gas Engineering": "weak",
    "Pipe Guys (Bham) Ltd": "ok",
    "Blaymires Plumbing & Heating": "weak",
    "Secure Gas 247": "ok",
    "The Gas Pro": "none",
}

PRODUCT_FILL = {
    "AI Receptionist": "FFE8D9",      # warm
    "Speed-to-Lead": "DEEAF6",        # blue
    "Booking + Reminders": "E2EFDA",  # green
    "Enquiry Triage": "F2F2F2",       # grey
}

FONT = "Arial"
INK = "1F2937"
MUTED = "6B7280"
HEADER_BG = "1F3864"
ACCENT = "C00000"

THIN = Side(style="thin", color="D9D9D9")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

COLUMNS = [
    ("#", 5),
    ("Company", 32),
    ("Size Tier", 22),
    ("Verdict", 40),
    ("Phone", 15),
    ("Call At", 18),
    ("Website", 30),
    ("SELL THEM", 19),
    ("Setup", 15),
    ("Monthly", 15),
    ("Website Build", 14),
    ("Year 1 (low)", 13),
    ("Year 1 (high)", 13),
    ("Sales Cycle", 24),
    ("Why / What To Say", 54),
    ("Location", 20),
    ("Reviews", 9),
    ("Called?", 11),
    ("Outcome", 24),
]


def build() -> Path:
    rows = list(csv.DictReader(
        (REPO / "QUALIFIED_LEADS.csv").open(encoding="utf-8-sig")))

    wb = Workbook()
    ws = wb.active
    ws.title = "Call Sheet"

    # ---- title block ----
    ws["A1"] = "Gas & Heating Trades - Qualified Call Sheet"
    ws["A1"].font = Font(name=FONT, size=16, bold=True, color=HEADER_BG)
    ws["A2"] = (f"{len(rows)} qualified leads, best to weakest.  "
                f"Call mobiles 07:30-08:30 or after 17:00.  "
                f"Peak heating season starts October - sell the coming rush.")
    ws["A2"].font = Font(name=FONT, size=10, color=MUTED)
    ws["A3"] = ("SCREEN ALL NUMBERS AGAINST TPS AND CTPS BEFORE CALLING - "
                "sole traders are TPS, limited companies are CTPS, both must be checked (PECR 2003).")
    ws["A3"].font = Font(name=FONT, size=10, bold=True, color=ACCENT)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(COLUMNS))
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(COLUMNS))
    ws.merge_cells(start_row=3, start_column=1, end_row=3, end_column=len(COLUMNS))
    ws.row_dimensions[1].height = 24
    ws.row_dimensions[2].height = 16
    ws.row_dimensions[3].height = 16

    HEADER_ROW = 5

    # ---- header ----
    for idx, (label, width) in enumerate(COLUMNS, start=1):
        cell = ws.cell(row=HEADER_ROW, column=idx, value=label)
        cell.font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=HEADER_BG)
        cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        cell.border = BORDER
        ws.column_dimensions[get_column_letter(idx)].width = width
    ws.row_dimensions[HEADER_ROW].height = 26

    # ---- data ----
    for offset, row in enumerate(rows):
        r = HEADER_ROW + 1 + offset
        company = row["Company"]
        product = PRODUCT_SHORT.get(row["SELL THEM"], row["SELL THEM"])

        site, site_note = VERIFIED_SITES.get(company, (None, None))
        if site is None:
            website = "not checked"
            verified = False
        elif site:
            website = site
            verified = True
        else:
            website = "NO SITE FOUND"
            verified = True

        # The 24/7 contradiction is the sharpest opener there is, so it
        # replaces the generic script wherever it has been confirmed.
        if company in ADVERTISES_247:
            say = ('ADVERTISES 24/7 on one mobile. Say: "Your website says '
                   '24/7 - who picks it up at 2am when you\'re asleep?"')
        else:
            say = row["Opening Line"]

        reviews = int(row["Reviews"]) if row["Reviews"].strip().isdigit() else None
        quote = pricing.quote_for(
            company, phone_kind(row["Phone"]), reviews,
            segment_of({"Industry": row.get("What They Do", ""),
                        "Services": row.get("What They Do", "")}),
            SITE_STATUS.get(company, "unknown"))

        values = [
            offset + 1,
            company,
            quote.tier,
            quote.verdict,
            row["Phone"],
            row["Best Time"],
            website,
            product,
            quote.setup_range,
            quote.monthly_range,
            quote.website_build if quote.website_build else "-",
            quote.year_one_low,
            quote.year_one_high,
            quote.sales_cycle,
            say,
            row["Location"],
            reviews if reviews is not None else "",
            "",
            "",
        ]

        banded = "FFFFFF" if offset % 2 == 0 else "F7F9FC"
        for idx, value in enumerate(values, start=1):
            cell = ws.cell(row=r, column=idx, value=value)
            cell.font = Font(name=FONT, size=10, color=INK)
            cell.alignment = Alignment(vertical="top", wrap_text=(idx in (2, 4, 15)))
            cell.border = BORDER
            cell.fill = PatternFill("solid", fgColor=banded)

        # Emphasis that helps while dialling.
        ws.cell(row=r, column=1).alignment = Alignment(horizontal="center", vertical="top")
        ws.cell(row=r, column=2).font = Font(name=FONT, size=10, bold=True, color=INK)
        ws.cell(row=r, column=3).font = Font(name=FONT, size=11, bold=True, color=INK)

        product_cell = ws.cell(row=r, column=8)
        product_cell.font = Font(name=FONT, size=10, bold=True, color=INK)
        product_cell.fill = PatternFill("solid", fgColor=PRODUCT_FILL.get(product, banded))

        site_cell = ws.cell(row=r, column=5)
        if website == "NO SITE FOUND":
            site_cell.font = Font(name=FONT, size=10, bold=True, color=ACCENT)
        elif verified and "subdomain" in (site_note or ""):
            # Free site-builder subdomain: a website sale sits next to the
            # receptionist sale.
            site_cell.font = Font(name=FONT, size=10, bold=True, color="B45309")
        elif not verified:
            site_cell.font = Font(name=FONT, size=10, italic=True, color=MUTED)
        if site_note:
            site_cell.comment = None
            ws.cell(row=r, column=5).value = (
                f"{website}  ({site_note})" if website != "NO SITE FOUND" else site_note)

        if company in ADVERTISES_247:
            ws.cell(row=r, column=15).font = Font(name=FONT, size=10, bold=True, color=ACCENT)

        ws.cell(row=r, column=17).alignment = Alignment(
            horizontal="center", vertical="top")
        for col in (11, 12, 13):
            c = ws.cell(row=r, column=col)
            if isinstance(c.value, int):
                c.number_format = "\u00a3#,##0"
            c.alignment = Alignment(horizontal="right", vertical="top")
            c.font = Font(name=FONT, size=10, bold=(col in (12, 13)), color=INK)
        for col in (12, 13):
            ws.cell(row=r, column=col).fill = PatternFill("solid", fgColor="FFF2CC")
        for col in (9, 10):
            ws.cell(row=r, column=col).font = Font(
                name=FONT, size=10, bold=True, color=INK)
            ws.cell(row=r, column=col).alignment = Alignment(
                horizontal="right", vertical="top")
        # Tier drives everything, so colour it.
        tier_fill = {"Mid-market trade": "C6E0B4", "Industrial / commercial": "FFE699",
                     "Sole trader": "F2F2F2", "Corporate / energy major": "F8CBAD"}
        ws.cell(row=r, column=3).fill = PatternFill(
            "solid", fgColor=tier_fill.get(quote.tier, banded))
        ws.cell(row=r, column=3).font = Font(name=FONT, size=10, bold=True, color=INK)
        if quote.tier == "Mid-market trade":
            ws.cell(row=r, column=4).font = Font(
                name=FONT, size=10, bold=True, color="2E7D32")
        elif quote.tier == "Corporate / energy major":
            ws.cell(row=r, column=4).font = Font(name=FONT, size=10, color=ACCENT)
        ws.row_dimensions[r].height = 46

    last = HEADER_ROW + len(rows)

    # Tick-box column, so the sheet is usable as a worklist.
    dv = DataValidation(type="list", formula1='"Yes,No answer,Call back,Not interested"',
                        allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"R{HEADER_ROW + 1}:R{last}")

    ws.freeze_panes = f"A{HEADER_ROW + 1}"
    ws.auto_filter.ref = f"A{HEADER_ROW}:S{last}"
    ws.sheet_view.showGridLines = False

    # ---- summary sheet ----
    s = wb.create_sheet("Summary")
    s.sheet_view.showGridLines = False
    s["A1"] = "What To Sell - Breakdown"
    s["A1"].font = Font(name=FONT, size=14, bold=True, color=HEADER_BG)

    s["A3"] = "Size Tier"
    s["B3"] = "Leads"
    for c in ("A3", "B3"):
        s[c].font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
        s[c].fill = PatternFill("solid", fgColor=HEADER_BG)
        s[c].border = BORDER

    products = ["Mid-market trade", "Industrial / commercial", "Sole trader",
                "Corporate / energy major"]
    for i, product in enumerate(products):
        r = 4 + i
        s.cell(row=r, column=1, value=product).font = Font(name=FONT, size=10, color=INK)
        s.cell(row=r, column=1).fill = PatternFill("solid", fgColor={
            "Mid-market trade": "C6E0B4", "Industrial / commercial": "FFE699",
            "Sole trader": "F2F2F2", "Corporate / energy major": "F8CBAD",
        }.get(product, "FFFFFF"))
        s.cell(row=r, column=2,
               value=f"=COUNTIF('Call Sheet'!$C${HEADER_ROW + 1}:$C${last},A{r})")
        for col in (1, 2):
            s.cell(row=r, column=col).border = BORDER
            s.cell(row=r, column=col).font = Font(name=FONT, size=10, color=INK)

    total_row = 4 + len(products)
    s.cell(row=total_row, column=1, value="Total").font = Font(name=FONT, size=10, bold=True)
    s.cell(row=total_row, column=2, value=f"=SUM(B4:B{total_row - 1})").font = Font(
        name=FONT, size=10, bold=True)
    for col in (1, 2):
        s.cell(row=total_row, column=col).border = BORDER

    s["A11"] = "Progress"
    s["A11"].font = Font(name=FONT, size=14, bold=True, color=HEADER_BG)
    progress = [
        ("Called", f"=COUNTIF('Call Sheet'!$R${HEADER_ROW + 1}:$R${last},\"Yes\")"),
        ("No answer", f"=COUNTIF('Call Sheet'!$R${HEADER_ROW + 1}:$R${last},\"No answer\")"),
        ("Call back", f"=COUNTIF('Call Sheet'!$R${HEADER_ROW + 1}:$R${last},\"Call back\")"),
        ("Not interested", f"=COUNTIF('Call Sheet'!$R${HEADER_ROW + 1}:$R${last},\"Not interested\")"),
        ("Still to call", f"=COUNTBLANK('Call Sheet'!$R${HEADER_ROW + 1}:$R${last})"),
    ]
    for i, (label, formula) in enumerate(progress):
        r = 12 + i
        s.cell(row=r, column=1, value=label).font = Font(name=FONT, size=10, color=INK)
        s.cell(row=r, column=2, value=formula).font = Font(name=FONT, size=10, color=INK)
        for col in (1, 2):
            s.cell(row=r, column=col).border = BORDER

    # ---- pipeline value ----
    # Setup and Monthly are quoted as ranges, so only the Year 1 low/high
    # columns are summable.
    s["D3"] = "Pipeline - Year 1 Value"
    s["D3"].font = Font(name=FONT, size=14, bold=True, color=HEADER_BG)

    s.cell(row=5, column=4, value="If every lead closed (low end)")
    c = s.cell(row=5, column=5, value=f"=SUM('Call Sheet'!$L${HEADER_ROW + 1}:$L${last})")
    c.number_format = "\u00a3#,##0"
    s.cell(row=6, column=4, value="If every lead closed (high end)")
    c2 = s.cell(row=6, column=5, value=f"=SUM('Call Sheet'!$M${HEADER_ROW + 1}:$M${last})")
    c2.number_format = "\u00a3#,##0"
    for r in (5, 6):
        s.cell(row=r, column=4).font = Font(name=FONT, size=10, color=INK)
        s.cell(row=r, column=5).font = Font(name=FONT, size=10, bold=True, color=INK)
        for col in (4, 5):
            s.cell(row=r, column=col).border = BORDER

    s["D8"] = ("A ceiling, not a forecast - it assumes all 66 say yes. "
               "Realistic outcomes below.")
    s["D8"].font = Font(name=FONT, size=9, italic=True, color=ACCENT)
    s.merge_cells(start_row=8, start_column=4, end_row=8, end_column=8)

    s["D10"] = "Realistic outcomes (low-end pricing)"
    s["D10"].font = Font(name=FONT, size=12, bold=True, color=HEADER_BG)
    for i, label in enumerate(("Close rate", "Deals", "Year 1")):
        c = s.cell(row=11, column=4 + i, value=label)
        c.font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=HEADER_BG)
        c.border = BORDER
    for i, rate in enumerate((0.05, 0.10, 0.20)):
        r = 12 + i
        s.cell(row=r, column=4, value=rate).number_format = "0%"
        s.cell(row=r, column=5, value=f"=ROUND($B$8*D{r},0)")
        cc = s.cell(row=r, column=6, value=f"=ROUND($E$5*D{r},0)")
        cc.number_format = "\u00a3#,##0"
        for col in (4, 5, 6):
            s.cell(row=r, column=col).border = BORDER
            s.cell(row=r, column=col).font = Font(
                name=FONT, size=10, bold=(rate == 0.10), color=INK)

    s["D16"] = ("Mid-market is the tier to work: it can pay agency rates and the "
                "owner still decides. Corporates pay more but take months.")
    s["D16"].font = Font(name=FONT, size=9, italic=True, color=MUTED)
    s.merge_cells(start_row=16, start_column=4, end_row=16, end_column=8)

    s["A19"] = "Notes"
    s["A19"].font = Font(name=FONT, size=14, bold=True, color=HEADER_BG)
    notes = [
        "Prices are anchored to UK market rates researched 2 Aug 2026: AI receptionists "
        "for trades sell at \u00a345-99/mo self-serve, human answering at \u00a3100-400/mo, "
        "basic trade websites \u00a3349-499 and multi-page \u00a3800-2,000. Setup fees are what "
        "done-for-you buys you above the \u00a345 self-serve tier.",
        "Tiers by Google reviews as a proxy for call volume and ability to pay: "
        "High volume 200+, Established 60-199, Growing under 60.",
        "A website is only quoted where the site is missing or on a free subdomain. "
        "Never pitch a rebuild to someone whose site is fine - it ends the call.",
        "Bundle discount: 20% off the website build when sold with a service. The "
        "discount comes off setup, never off the monthly.",
        "Websites: only 5 companies were checked by hand (2 Aug 2026). Every other row "
        "reads 'not checked' - the automated crawl has never had network access.",
        "Amber website text = free site-builder subdomain, so a website sale sits "
        "alongside the receptionist sale.",
        "Red 'What To Say' = confirmed to advertise 24/7 while running on one mobile. "
        "Best opener in the list.",
        "110 of the original 176 rows were rejected: industrial, fuel distribution and "
        "oil & gas majors have no urgent demand and buy through procurement.",
        "Legal: PECR 2003 prohibits unsolicited marketing calls to TPS/CTPS-registered "
        "numbers without prior consent. Sole traders fall under TPS. Screen both registers.",
        "Job values used in the pitch (£2-4k installs, £90-250 callouts) are "
        "order-of-magnitude estimates, not audited market data.",
    ]
    for i, note in enumerate(notes):
        r = 20 + i
        s.cell(row=r, column=1, value=f"- {note}").font = Font(
            name=FONT, size=10, color=INK)
        s.cell(row=r, column=1).alignment = Alignment(wrap_text=True, vertical="top")
        s.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
        s.row_dimensions[r].height = 30

    s.column_dimensions["A"].width = 32
    s.column_dimensions["B"].width = 12
    for col in "CDEF":
        s.column_dimensions[col].width = 18

    out = REPO / "Call_Sheet.xlsx"
    wb.save(out)
    return out


if __name__ == "__main__":
    print(build())
