#!/usr/bin/env python3
"""Build the France outreach pack: everything workable by email or phone.

Ten days abroad rules out walk-ins, which was the strongest channel for
dealerships and dentistry. So this ranks purely on what can be done remotely:
a published email, a phone number, or ideally both.

Two tabs, because they are different jobs:

  New Outreach  - never contacted. Email first, call 2-3 days later.
  Follow-Up     - already emailed and did not reply. These are the highest-value
                  calls available, since most replies to cold email come from the
                  follow-up rather than the first touch.

Every email and phone number here was read from a real source. Rows with
neither are dropped rather than shipped as filler.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

REPO = Path(__file__).resolve().parent

FONT = "Arial"
INK = "1F2937"
MUTED = "6B7280"
HEADER_BG = "1F3864"
ACCENT = "C00000"
GOOD = "2E7D32"

THIN = Side(style="thin", color="D9D9D9")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

BAND_MID = "£3-6k + £750-1.5k/mo"
BAND_UPPER = "£6-12k + £1.5-2.5k/mo"


@dataclass
class L:
    company: str
    sector: str
    email: str
    phone: str
    sell: str
    hook: str
    band: str
    score: int
    note: str = ""
    tags: list[str] = field(default_factory=list)


# --------------------------------------------------------------- new leads ---
# Scored on: can they pay, how sharp is the need, how reachable remotely.
NEW: list[L] = [
    L("The Campbell Clinic", "Private dentistry", "info@campbell-clinic.co.uk",
      "0115 982 3913", "AI Receptionist + treatment-plan follow-up",
      "Three implant pricing tiers and Invisalign across six surgeries - what "
      "happens to enquiries when you're closed?", BAND_MID, 95,
      tags=["email+phone", "high case value"]),

    L("North Bristol Private Hospital", "Private hospital", "info@nbph.co.uk",
      "0117 911 4000", "Out-of-hours self-pay enquiry line + consultation booking",
      "A self-pay enquiry at 8pm Saturday - what happens to it before Monday?",
      BAND_UPPER, 94, tags=["email+phone", "five-figure cases"]),

    L("58 Queen Square", "Cosmetic surgery", "info@58queensquare.com",
      "0117 910 2400", "Speed-to-Lead + consultation booking",
      "How quickly does someone hear back after enquiring about a procedure?",
      BAND_MID, 92, tags=["email+phone"]),

    L("Quinn Clinics", "Aesthetics", "info@quinnclinics.co.uk",
      "0117 924 4592", "AI Receptionist + automated rebooking",
      "CQC-registered since 2006 - who picks up when you're mid-treatment?",
      BAND_MID, 88, tags=["email+phone", "established"]),

    L("Azthetics Clinic", "Aesthetics", "info@aztheticsclinic.co.uk",
      "0117 973 3666", "Enquiry routing across your three clinics",
      "Bristol, Taunton and Weston - how do enquiries reach the right one?",
      BAND_MID, 87, tags=["email+phone", "multi-site"]),

    L("Milsted Langdon LLP", "Accountancy", "advice@milstedlangdon.co.uk",
      "0117 945 2500", "Automated records chasing before January",
      "Five offices - how much of December and January goes on chasing records?",
      BAND_UPPER, 86, tags=["email+phone", "5 offices", "seasonal"]),

    L("Pamela Neave", "Recruitment", "enquiries@pamela-neave.co.uk",
      "0117 921 1831", "CV screener + candidate follow-up",
      "How many CVs land for a role before you find one worth calling?",
      BAND_MID, 85, tags=["email+phone", "LinkedIn-native"]),

    L("Fernlea Vets", "Veterinary", "robin@fernleavets.co.uk",
      "0117 967 7067", "Recall reminders + phone overflow",
      "How often do clients give up because the phone was engaged?",
      BAND_MID, 84, note="Named contact - ask for Robin.",
      tags=["email+phone", "named contact", "independent"]),

    L("The Private Clinic", "Cosmetic clinic group", "enquiries@theprivateclinic.co.uk",
      "0333 920 9135", "Multi-site enquiry triage and routing",
      "With clinics across several cities, how are enquiries routed and chased?",
      BAND_UPPER, 83, note="Larger group - more than one decision maker.",
      tags=["email+phone", "ad spend"]),

    L("Paul Wilson Aesthetics", "Aesthetics", "info@paulwilsonaesthetics.co.uk",
      "0117 332 1585", "Enquiry line that books while you're in clinic",
      "While you're in clinic, who's answering the enquiries?", BAND_MID, 82,
      tags=["email+phone", "owner is bottleneck"]),

    L("Motts Insurance Brokers", "Insurance broking", "info@mottsinsurance.com",
      "", "Renewal and servicing automation",
      "How many hours a week go on policy requests and renewal admin?",
      BAND_MID, 78, note="No phone found - email only.", tags=["email only"]),

    L("Avenue Veterinary Centre", "Veterinary", "enquiries@avenue-vets.com",
      "0117 956 9038", "Recall reminders + booking overflow",
      "Independent for 100 years - how often is the phone engaged?", BAND_MID, 77,
      tags=["email+phone", "independent"]),

    L("Charlton Baker", "Accountancy", "info@charltonbaker.co.uk",
      "", "Records chasing across nine offices",
      "Across nine offices, how much of January goes on chasing records?",
      BAND_MID, 76, note="No phone found - email only.", tags=["email only"]),

    L("Watkins Solicitors", "Conveyancing", "info@watkinssolicitors.co.uk",
      "", "Automated case-progress updates",
      "How much of the day goes on clients ringing to ask where their matter is?",
      BAND_MID, 74, note="No phone found - email only.", tags=["email only"]),

    L("AMD Solicitors", "Conveyancing", "info@amdsolicitors.com",
      "", "Case-progress updates + document chasing across offices",
      "Across your offices, how much time goes on progress calls and ID chasing?",
      BAND_MID, 73, note="No phone found - email only.", tags=["email only"]),

    L("Future Engineering Recruitment", "Recruitment", "info@futureengineer.co.uk",
      "0203 411 4199", "CV screener + candidate follow-up",
      "How many CVs does a consultant read before finding one worth a call?",
      BAND_MID, 80, tags=["email+phone"]),

    L("Somerset Bridge Group", "Insurance broking", "Enquiries@sbgl.co.uk",
      "", "Renewal and servicing automation",
      "How many hours a week does your team lose to renewal admin?",
      BAND_UPPER, 75, note="No phone found - email only.", tags=["email only"]),

    # -- phone-only: no published email, but callable from anywhere ----------
    L("Alexander Mae", "Recruitment", "", "0117 905 5035",
      "CV screener + candidate follow-up",
      "How many CVs does a consultant read before one is worth a call?",
      BAND_MID, 72, note="Phone only - no published email.", tags=["phone only"]),

    L("Mola Dental", "Private dentistry", "", "0114 317 7002",
      "AI Receptionist + treatment-plan follow-up",
      "When an implant enquiry comes in overnight, where does it go?",
      BAND_MID, 71, note="Phone only.", tags=["phone only"]),

    L("Harley Private Dental", "Private dentistry", "", "0114 551 4000",
      "AI Receptionist + treatment-plan follow-up",
      "When an implant enquiry comes in overnight, where does it go?",
      BAND_MID, 70, note="Phone only.", tags=["phone only"]),

    L("High Street Dental Care", "Private dentistry", "", "0114 248 4400",
      "AI Receptionist + treatment-plan follow-up",
      "You're an implant practice - what happens to out-of-hours enquiries?",
      BAND_MID, 69, note="Phone only.", tags=["phone only"]),

    L("Green Square Dental & Implant Centre", "Private dentistry", "",
      "01709 917 666", "AI Receptionist + treatment-plan follow-up",
      "What happens to implant enquiries that arrive after you close?",
      BAND_MID, 68, note="Phone only.", tags=["phone only"]),

    L("Shine Dental Care", "Private dentistry", "", "01623 629391",
      "AI Receptionist + treatment-plan follow-up",
      "What happens to implant enquiries that arrive after you close?",
      BAND_MID, 67, note="Phone only.", tags=["phone only"]),

    L("The Dental Care Clinic", "Private dentistry", "", "0191 286 9156",
      "AI Receptionist + treatment-plan follow-up",
      "What happens to implant and ortho enquiries out of hours?",
      BAND_MID, 66, note="Phone only.", tags=["phone only"]),

    L("Newcastle Dental Care", "Private dentistry", "", "0191 232 4284",
      "AI Receptionist + treatment-plan follow-up",
      "What happens to private enquiries that arrive after you close?",
      BAND_MID, 65, note="Phone only.", tags=["phone only"]),

    L("Hayes Parsons Insurance Brokers", "Insurance broking", "", "0117 929 9381",
      "Renewal and servicing automation",
      "How many hours a week go on renewal and policy admin?", BAND_UPPER, 74,
      note="Phone only - chartered broker, commercial and marine.",
      tags=["phone only"]),

    L("Brunel Group", "Insurance broking", "", "0117 325 2224",
      "Renewal and servicing automation",
      "How many hours a week go on renewal and policy admin?", BAND_MID, 72,
      note="Phone only - independent since 2005.", tags=["phone only"]),

    L("Castlemead Insurance Brokers", "Insurance broking", "", "0117 945 3900",
      "Renewal and servicing automation",
      "How many hours a week go on renewal and policy admin?", BAND_MID, 70,
      note="Phone only.", tags=["phone only"]),

    L("Mark Richard Insurance Brokers", "Insurance broking", "", "0117 947 9510",
      "Renewal and servicing automation",
      "How many hours a week go on renewal and policy admin?", BAND_MID, 69,
      note="Phone only - Bristol and Bath.", tags=["phone only"]),

    L("Animal Health Centre", "Veterinary", "", "0117 924 7832",
      "Recall reminders + booking overflow",
      "How often do clients give up because the phone was engaged?",
      BAND_MID, 64, note="Phone only.", tags=["phone only"]),

    L("Crown Clinic", "Cosmetic surgery", "", "03452 100 300",
      "Speed-to-Lead + consultation booking",
      "How long does an enquirer wait before someone gets back to them?",
      BAND_MID, 63, note="Phone only - London and Manchester.",
      tags=["phone only"]),

    L("Harley Street Healthcare", "Cosmetic surgery", "", "0207 030 3364",
      "Multi-site enquiry routing",
      "Three clinics - how are enquiries routed and chased?", BAND_MID, 62,
      note="Phone only.", tags=["phone only"]),

    # ------------------------------------- batch 4: Scotland, Midlands, North --
    L("Morgan Reach", "Accountancy", "info@morganreach.com",
      "0161 521 6222", "Records chasing + client onboarding across offices",
      "Three offices - how much of December and January goes on chasing "
      "clients for records?", BAND_UPPER, 90,
      note="MD is Kamran Shaikh - ask for him by name. Also 0121 236 0777 "
           "for Birmingham.",
      tags=["email+phone", "3 offices", "named decision maker", "seasonal"]),

    L("Glasgow Smile Clinic", "Private dentistry", "info@glasgowsmileclinic.com",
      "0141 204 4080", "AI Receptionist + treatment-plan follow-up",
      "When an implant enquiry comes in overnight, where does it go?",
      BAND_MID, 89, tags=["email+phone", "high case value"]),

    L("Dental Implant Centre Glasgow", "Private dentistry",
      "hello@dentalimplantcentreglasgow.com", "0141 673 8888",
      "AI Receptionist + treatment-plan follow-up",
      "A dedicated implant centre - what happens to enquiries after you close?",
      BAND_MID, 88, tags=["email+phone", "implant-only", "high case value"]),

    L("ATD General", "Insurance broking", "enquiries@atdgen.co.uk",
      "0161 236 3636", "Renewal and servicing automation",
      "How many hours a week go on policy requests and renewal admin?",
      BAND_MID, 81, tags=["email+phone"]),

    L("MCM Insurance", "Insurance broking", "", "0161 786 3150",
      "Renewal and servicing automation",
      "Trading since 1977 across Manchester and Birmingham - how much of the "
      "week goes on renewal admin?", BAND_MID, 76,
      note="Phone only. MD is Allan Broomhead - ask for him.",
      tags=["phone only", "named decision maker", "multi-site"]),

    L("Lucy Walker Recruitment", "Recruitment", "", "0113 367 2880",
      "CV screener + candidate follow-up",
      "How many CVs does a consultant read before one is worth a call?",
      BAND_MID, 75, note="Phone only. Leeds and Manchester.",
      tags=["phone only", "multi-site"]),

    L("Potential Recruitment", "Recruitment", "", "0161 241 9660",
      "CV screener + candidate follow-up",
      "How many CVs does a consultant read before one is worth a call?",
      BAND_MID, 73, note="Phone only. Independent generalist agency.",
      tags=["phone only", "independent"]),

    L("Glasgow Dental Cosmetic & Implant Centre", "Private dentistry", "",
      "0141 636 5588", "AI Receptionist + treatment-plan follow-up",
      "What happens to implant enquiries that arrive after you close?",
      BAND_MID, 70, note="Phone only.", tags=["phone only"]),

    L("Advanced Dentistry Scotland", "Private dentistry", "", "0141 339 7579",
      "AI Receptionist + multi-site enquiry routing",
      "Glasgow and Inverness - how do enquiries reach the right clinic?",
      BAND_MID, 69, note="Phone only.", tags=["phone only", "multi-site"]),
]

# ------------------------------------------------------ follow-up callbacks ---
# Already emailed. Most cold-email replies come from follow-up, so these are
# the highest-value calls in the pack.
FOLLOWUP: list[L] = [
    L("CJ Hole", "Estate agency", "bishopston@cjhole.co.uk", "0145 462 6300",
      "AI Receptionist for enquiries and tenant maintenance",
      "I emailed last week - calling to put a voice to it.", BAND_MID, 60),
    L("Ocean Estate Agents", "Estate agency", "customercare@oceanhome.co.uk",
      "0117 946 6666", "AI Receptionist for enquiries and viewings",
      "I emailed last week - calling to put a voice to it.", BAND_MID, 59),
    L("Bundy and Bond", "Estate agency", "info@bundyandbond.co.uk",
      "01454 540 200", "AI Receptionist + applicant qualification",
      "I emailed last week - calling to put a voice to it.", BAND_MID, 58),
    L("Bonds of Thornbury", "Estate agency", "enquiries@bondsofthornbury.co.uk",
      "01454 858 007", "AI Receptionist + applicant qualification",
      "I emailed last week - calling to put a voice to it.", BAND_MID, 57),
    L("Brunt & Fussell", "Estate agency", "info@bruntandfussell.co.uk",
      "0117 956 6004", "AI Receptionist + applicant qualification",
      "I emailed last week - calling to put a voice to it.", BAND_MID, 56),
    L("Edison Ford Property", "Estate agency", "enquiries@edisonfordproperty.co.uk",
      "01454 316 718", "AI Receptionist + tenant maintenance triage",
      "I emailed last week - calling to put a voice to it.", BAND_MID, 55),
    L("Cobb Farr", "Estate agency", "bath@cobbfarr.com", "01225 333 332",
      "AI Receptionist + applicant qualification",
      "I emailed last week - calling to put a voice to it.", BAND_MID, 54),
    L("Wentworth Estate Agents", "Estate agency", "bath@wentworthea.com",
      "01225 904 904", "AI Receptionist + applicant qualification",
      "I emailed last week - calling to put a voice to it.", BAND_MID, 53,
      note="Verify this is the right Wentworth - several trade as it."),
    L("Hobbs Property Agents", "Estate agency", "michaelhobbs219@gmail.com",
      "07477 618 008", "AI Receptionist + applicant qualification",
      "I emailed last week - Michael? Calling to put a voice to it.",
      BAND_MID, 52, note="Mobile - owner answers directly."),
    L("React Property Management", "Estate agency", "info@reactproperty.co.uk",
      "07493 342 410", "Tenant maintenance triage + out-of-hours cover",
      "I emailed last week - calling to put a voice to it.", BAND_MID, 51,
      note="Mobile - owner answers directly."),
    L("Crisp Cowley", "Estate agency", "", "01225 789 333",
      "AI Receptionist + applicant qualification",
      "No email published, so this is a first touch by phone.", BAND_MID, 50,
      note="Never emailed - no address published. Phone is the only route."),
    L("Pipe Guys (Bham) Ltd", "Gas & heating", "info@pipeguys.co.uk",
      "07869 837 241", "AI Receptionist for the 24/7 line",
      "Your site says 24/7 - who picks up at 2am? I emailed last week.",
      BAND_MID, 61, note="Mobile - owner answers. Advertises 24/7 on one phone."),
]

COLUMNS = [
    ("#", 5), ("Score", 7), ("Company", 32), ("Sector", 20),
    ("Email", 34), ("Phone", 16), ("WHAT TO SELL", 40),
    ("Opening line", 62), ("Price band", 22), ("Note", 34),
    ("Done?", 10), ("Outcome", 24),
]


def write_sheet(ws, rows: list[L], title: str, subtitle: str) -> None:
    ws.sheet_view.showGridLines = False
    ws["A1"] = title
    ws["A1"].font = Font(name=FONT, size=15, bold=True, color=HEADER_BG)
    ws["A2"] = subtitle
    ws["A2"].font = Font(name=FONT, size=10, color=MUTED)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(COLUMNS))
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(COLUMNS))

    HDR = 4
    for i, (label, width) in enumerate(COLUMNS, start=1):
        c = ws.cell(row=HDR, column=i, value=label)
        c.font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=HEADER_BG)
        c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        c.border = BORDER
        ws.column_dimensions[get_column_letter(i)].width = width
    ws.row_dimensions[HDR].height = 26

    rows = sorted(rows, key=lambda r: -r.score)
    for n, r in enumerate(rows, start=1):
        row = HDR + n
        both = bool(r.email and r.phone)
        values = [n, r.score, r.company, r.sector, r.email or "—",
                  r.phone or "—", r.sell, r.hook, r.band, r.note, "", ""]
        banded = "FFFFFF" if n % 2 else "F7F9FC"
        for i, v in enumerate(values, start=1):
            c = ws.cell(row=row, column=i, value=v)
            c.font = Font(name=FONT, size=10, color=INK)
            c.alignment = Alignment(vertical="top", wrap_text=(i in (3, 7, 8, 10)))
            c.border = BORDER
            c.fill = PatternFill("solid", fgColor=banded)
        ws.cell(row=row, column=1).alignment = Alignment(horizontal="center", vertical="top")
        ws.cell(row=row, column=3).font = Font(name=FONT, size=10, bold=True, color=INK)
        ws.cell(row=row, column=6).font = Font(name=FONT, size=11, bold=True, color=INK)
        ws.cell(row=row, column=7).font = Font(name=FONT, size=10, bold=True, color=INK)
        sc = ws.cell(row=row, column=2)
        sc.alignment = Alignment(horizontal="center", vertical="top")
        sc.font = Font(name=FONT, size=10, bold=True,
                       color=GOOD if r.score >= 80 else INK)
        # Both channels available is the thing that matters most remotely.
        ws.cell(row=row, column=5).fill = PatternFill(
            "solid", fgColor="E2EFDA" if r.email else "FCE4D6")
        ws.cell(row=row, column=6).fill = PatternFill(
            "solid", fgColor="E2EFDA" if r.phone else "FCE4D6")
        if both:
            ws.cell(row=row, column=3).font = Font(
                name=FONT, size=10, bold=True, color=GOOD)
        ws.row_dimensions[row].height = 54

    last = HDR + len(rows)
    dv = DataValidation(type="list", allow_blank=True,
                        formula1='"Emailed,Called,Both,Replied,Not interested"')
    ws.add_data_validation(dv)
    dv.add(f"K{HDR + 1}:K{last}")
    ws.freeze_panes = f"A{HDR + 1}"
    ws.auto_filter.ref = f"A{HDR}:L{last}"
    return last


def main() -> None:
    wb = Workbook()

    ws1 = wb.active
    ws1.title = "New Outreach"
    n1 = write_sheet(
        ws1, NEW, "New Outreach — never contacted, ranked best first",
        f"{len(NEW)} leads, best first. Green company name = email AND phone. "
        "Email first, then call 2-3 days later. Orange cell = that channel "
        "is missing.")

    ws2 = wb.create_sheet("Follow-Up Calls")
    n2 = write_sheet(
        ws2, FOLLOWUP, "Follow-Up Calls — already emailed, no reply",
        f"{len(FOLLOWUP)} leads. Most cold-email replies come from the "
        "follow-up, not the first touch, so these are the highest-value calls "
        "in the pack.")

    s = wb.create_sheet("Plan")
    s.sheet_view.showGridLines = False
    s["A1"] = "10 days in France — the plan"
    s["A1"].font = Font(name=FONT, size=15, bold=True, color=HEADER_BG)

    plan = [
        ("Channel reality", "Walk-ins are out, so dealerships and walk-in "
         "dentistry drop off. Recruitment, clinics and brokers all work fine "
         "by email and phone."),
        ("Calling from France", "Use a UK VoIP number or WhatsApp rather than "
         "roaming — a French mobile number showing up on caller ID gets far "
         "fewer answers. Time zone is +1, so UK 9am is your 10am."),
        ("Best calling hours", "Clinics and practices: 10:00-11:30 or "
         "14:00-16:00 UK, avoiding first thing when reception is swamped. "
         "Brokers and accountants: Tue-Thu 10:00-11:30 UK."),
        ("Sequence per lead", "Email on day 1. Call on day 3 or 4 referencing "
         "the email. That combination roughly doubles reply rates against "
         "either alone."),
        ("Daily target", "6-8 emails and 5-6 calls. That clears both tabs "
         "inside the trip with room for follow-ups."),
        ("Do the follow-ups first", "The 12 on tab 2 have already had an "
         "email. A call to someone who has seen your name is a materially "
         "warmer conversation than a fresh cold one."),
        ("Dealerships", "Parked until you're back — their edge was walking "
         "into a quiet showroom and you cannot do that from Bordeaux."),
        ("Pricing reminder", "Mid band £3-6k setup + £750-1.5k/mo. Upper band "
         "£6-12k + £1.5-2.5k/mo for multi-site and multi-office."),
    ]
    for i, (k, v) in enumerate(plan):
        r = 3 + i * 2
        s.cell(row=r, column=1, value=k).font = Font(
            name=FONT, size=11, bold=True, color=HEADER_BG)
        c = s.cell(row=r + 1, column=1, value=v)
        c.font = Font(name=FONT, size=10, color=INK)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        s.merge_cells(start_row=r + 1, start_column=1, end_row=r + 1, end_column=7)
        s.row_dimensions[r + 1].height = 32
    s.column_dimensions["A"].width = 30
    for col in "BCDEFG":
        s.column_dimensions[col].width = 16

    out = REPO / "MASTER_LEAD_LIST.xlsx"
    wb.save(out)
    print(f"wrote {out.name}")
    print(f"  New Outreach   : {len(NEW)} leads")
    print(f"  Follow-Up Calls: {len(FOLLOWUP)} leads")
    both = sum(1 for r in NEW + FOLLOWUP if r.email and r.phone)
    eo = sum(1 for r in NEW + FOLLOWUP if r.email and not r.phone)
    po = sum(1 for r in NEW + FOLLOWUP if r.phone and not r.email)
    print(f"  email + phone  : {both}")
    print(f"  email only     : {eo}")
    print(f"  phone only     : {po}")


if __name__ == "__main__":
    main()
