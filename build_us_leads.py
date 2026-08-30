"""Build US_LEADS.xlsx - US market research and lead list for Houghton Automations.

Every email address in this file was read from a published source. None are
constructed from a company's email pattern. Where only a name and phone number
were found, the Email column is left blank and the row sits in the phone-first
section rather than being padded with a guess.
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

FONT = "Arial"

INK = "1A1A1A"
MUTED = "6B6B6B"
ACCENT = "7A1F2B"
HEAD_FILL = PatternFill("solid", fgColor="7A1F2B")
BAND_FILL = PatternFill("solid", fgColor="F2EDEE")
WARN_FILL = PatternFill("solid", fgColor="FDF3D8")
STOP_FILL = PatternFill("solid", fgColor="FBE3E3")
GOOD_FILL = PatternFill("solid", fgColor="E8F1EA")
SUBTLE = PatternFill("solid", fgColor="F7F7F8")

thin = Side(style="thin", color="D8D8DC")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
UNDER = Border(bottom=Side(style="thin", color="D8D8DC"))


def title_block(ws, title, subtitle, width):
    ws["A1"] = title
    ws["A1"].font = Font(name=FONT, size=15, bold=True, color=INK)
    ws["A2"] = subtitle
    ws["A2"].font = Font(name=FONT, size=10, color=MUTED)
    ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=width)
    ws.row_dimensions[1].height = 22
    ws.row_dimensions[2].height = 30


def header_row(ws, row, headers):
    for i, h in enumerate(headers, start=1):
        c = ws.cell(row=row, column=i, value=h)
        c.font = Font(name=FONT, size=9, bold=True, color="FFFFFF")
        c.fill = HEAD_FILL
        c.alignment = Alignment(vertical="center", wrap_text=True)
        c.border = BOX
    ws.row_dimensions[row].height = 30


# ---------------------------------------------------------------------------
# Leads. source = where the address was read. verify = what to check first.
# ---------------------------------------------------------------------------

Lead = lambda *a: dict(zip(
    ("score", "org", "sector", "state", "person", "role", "email", "phone",
     "sell", "opener", "price", "note"), a))

LEADS = [
    Lead(94, "Charleston Trident Association of REALTORS", "REALTOR association", "SC",
         "Ryan Castle", "CEO", "ryan@charlestonrealtors.com", "(843) 793-5207",
         "Member service line + dues renewal chasing + CE class registration",
         "7,000 members and one member services desk. What happens to the calls that come in while your team is running a class?",
         "$8-15k + $2-3k/mo",
         "7,000 members, one of the larger local boards. Alt contact: Meghan Byrnes Weinreich, VP Operations, meghan@charlestonrealtors.com."),
    Lead(91, "Tucson Association of REALTORS", "REALTOR association", "AZ",
         "Romeo Arrieta", "CEO", "romeo@tucsonrealtors.org", "(520) 382-8814",
         "Member service line + education registration + new member onboarding",
         "How much of your member services team's week goes on questions they have answered a hundred times before?",
         "$8-15k + $2-3k/mo",
         "Runs MLSSAZ alongside the association. Alt contact: Lisa Nutt, Director of Member Services, LisaN@tucsonrealtors.org."),
    Lead(88, "Greater Chattanooga REALTORS", "REALTOR association", "TN",
         "Carol Seal", "CEO", "carol@gcar.net", "(423) 698-8001",
         "Member service line + dues renewal chasing + CE class registration",
         "When a member calls about dues or a CE class after five, where does that call go?",
         "$6-12k + $1.5-2.5k/mo",
         "Named CEO with a published direct address, which is the ideal shape for this sector."),
    Lead(86, "Osceola County Association of REALTORS", "REALTOR association", "FL",
         "Twis Lizasuain", "CEO", "tlizasuain@osceola-realtors.com", "(407) 846-0117",
         "Member service line + dues renewal chasing + bilingual enquiry handling",
         "Central Florida membership is growing fast. How is your member services desk keeping up with it?",
         "$6-12k + $1.5-2.5k/mo",
         "Bilingual member base is a genuine differentiator you can offer. Source was a 2022 staff listing, so confirm she is still CEO before sending."),
    Lead(84, "Ohio Home Builders Association", "Trade association", "OH",
         "Vincent J. Squillace", "Executive Vice President", "vsquillace@ohiohba.com", "(614) 228-1235",
         "Member enquiry handling + event registration + local HBA coordination",
         "You coordinate a network of local HBAs from one office. How much of that is answering the same questions twice?",
         "$8-15k + $2-3k/mo",
         "State-level body over many local HBAs, so a win here is a reference into all of them. General inbox build@ohiohba.com also published."),
    Lead(82, "East Tennessee Realtors", "REALTOR association", "TN",
         "Teresa Tillery", "Membership Director", "teresa@kaarmls.com", "(865) 588-3232",
         "Membership enquiry handling + application processing + renewal chasing",
         "How much of the membership team's day goes on application status questions?",
         "$6-12k + $1.5-2.5k/mo",
         "Formerly Knoxville Area Association of REALTORS. CEO is Lyle Irish, no published address found for him."),
    Lead(80, "Texas Society of Association Executives", "Association of associations", "TX",
         "Steven", "President and CEO", "steven@tsae.org", "(512) 444-1974",
         "Member enquiry handling + event registration + renewal chasing",
         "Your members are the people who would buy this next. What would it take to convince you first?",
         "$6-12k + $1.5-2.5k/mo",
         "Highest strategic value on the list. Every member is an association executive, so one happy customer here is a room full of prospects. Alt: brandon@tsae.org, membership."),
    Lead(78, "Georgia Society of Association Executives", "Association of associations", "GA",
         "Wendy W. Kavanagh, CAE", "President", "wendy@gsae.org", "(404) 577-7850",
         "Member enquiry handling + event registration + renewal chasing",
         "Your members are the people who would buy this next. What would it take to convince you first?",
         "$6-12k + $1.5-2.5k/mo",
         "Same strategic logic as TSAE. Address came from a 2019 directory, so confirm she is still President first. Alt: janeanne@gsae.org."),
    Lead(76, "Alabama Association of REALTORS", "REALTOR association", "AL",
         "Jeremy", "Executive Director", "jeremy@alabamarealtors.com", "",
         "Member service line + local board coordination + education registration",
         "How much of the state office's week goes on questions that came in through a local board?",
         "$8-15k + $2-3k/mo",
         "State-level body. Only a first name was published, so open with the address rather than a surname."),
    Lead(72, "Immigration Law Group LLC", "Immigration law", "OR",
         "", "", "info@emsylaw.com", "(866) 691-9894",
         "Speed-to-lead consultation booking + document chasing",
         "How quickly does someone hear back after they enquire about a consultation?",
         "$6-12k + $1.5-2.5k/mo",
         "Immigration is the best legal niche for this: high enquiry volume, huge document-chasing burden, no HIPAA."),
    Lead(70, "Sky USA Law", "Immigration law", "CA / NY",
         "", "", "info@skyusalaw.com", "(310) 496-5811",
         "Out-of-hours consultation booking across time zones + document chasing",
         "Your clients are all over the world. Who answers the enquiries that arrive at 3am Pacific?",
         "$6-12k + $1.5-2.5k/mo",
         "Serves clients globally, so the out-of-hours argument makes itself. Being UK-based is an advantage here, not a handicap."),
    Lead(68, "DFW Immigration", "Immigration law", "TX",
         "", "", "info@dfw-immigration.com", "(972) 445-4114",
         "Speed-to-lead consultation booking + document chasing",
         "You offer a free consultation. How many of those requests get a reply the same hour?",
         "$3-6k + $750-1.5k/mo",
         "Free-consultation model means high enquiry volume and a low cost per missed one, so lead with speed."),
    Lead(64, "Green Valley Sahuarita Association of REALTORS", "REALTOR association", "AZ",
         "Rebecca Brown", "Association Executive", "Rebecca@gvsar.com", "",
         "Member service line + education registration",
         "In a small office, who covers the phones when you are running a class?",
         "$3-6k + $750-1.5k/mo",
         "Small board. Budget is real but modest, so pitch the lower tier."),
    Lead(62, "Central Arizona Association of REALTORS", "REALTOR association", "AZ",
         "Jackie Rudder", "Association Executive", "jackie@caaraz.com", "",
         "Member service line + education registration",
         "In a small office, who covers the phones when you are running a class?",
         "$3-6k + $750-1.5k/mo",
         "Payson, AZ. Small board, same pitch as Green Valley."),
    Lead(60, "Bullhead City / Mohave Valley Association of REALTORS", "REALTOR association", "AZ",
         "Dana Walter", "Association Executive", "ae@bhcmvaor.org", "",
         "Member service line + education registration",
         "In a small office, who covers the phones when you are running a class?",
         "$3-6k + $750-1.5k/mo",
         "Small board. Role-based address, so the AE reads it directly."),
]

PHONE_ONLY = [
    ("Kansas City Regional Association of REALTORS", "REALTOR association", "KS / MO",
     "Kipp Cooper", "CEO", "(913) 266-5909",
     "Large regional board running Heartland MLS. Only an email pattern was published, never a real address, so this is a call."),
    ("Florida Society of Association Executives", "Association of associations", "FL",
     "President and CEO", "", "(850) 702-0944",
     "Same strategic value as TSAE and GSAE. Staff emails were not published, only direct dials."),
    ("Michigan Society of Association Executives", "Association of associations", "MI",
     "President and CEO", "", "(517) 225-3886 x800",
     "As above. Ask for the President by role when you call."),
    ("Colorado Restaurant Association", "Trade association", "CO",
     "President and CEO", "", "(303) 830-2972",
     "Restaurant associations run heavy member-service and event operations."),
    ("Tennessee Hospitality & Tourism Association", "Trade association", "TN",
     "President and CEO", "", "(615) 385-9970",
     "As above."),
    ("Western Ohio Home Builders Association", "Trade association", "OH",
     "Donna Cook", "Executive Director", "(937) 339-7963",
     "Local HBA. Smaller budget than the state body, but a named director who answers her own phone."),
    ("Aspire North REALTORS", "REALTOR association", "MI",
     "Alan Jeffries", "Association Executive", "(231) 947-2050",
     "Traverse City area."),
    ("Battle Creek Area Association of REALTORS", "REALTOR association", "MI",
     "Amanda Lankerd", "Association Executive", "(269) 962-5193",
     "Small board."),
    ("Antrim Charlevoix Kalkaska Association of REALTORS", "REALTOR association", "MI",
     "Kenneth Harris", "Association Executive", "(231) 237-6394",
     "Small board."),
]

SECTORS = [
    (1, "REALTOR and trade associations", 9, 8, 10, "Email, named AE or CEO",
     "The best US niche found. Roughly 1,000 local REALTOR boards plus thousands of trade "
     "associations, each with one Association Executive who is named, published, and can "
     "decide alone. Dues revenue funds real budgets. Member-service phone volume, dues "
     "renewal chasing, CE class registration and new-member onboarding are all textbook "
     "automation. No HIPAA. Members already have a consent relationship, which keeps TCPA simple.",
     "Nobody is selling into it. Every AI vendor is chasing HVAC and dental."),
    (2, "Associations of associations (state SAEs)", 8, 8, 10, "Email or phone to the President",
     "TSAE, GSAE, FSAE, MSAE and their sister societies. Small in themselves, but every "
     "single member is an association executive who would buy the same thing. One reference "
     "customer here is a speaking slot and a room full of prospects.",
     "Treat as business development, not revenue. Price it low and take the case study."),
    (3, "Immigration law", 8, 9, 7, "Email to info@, then phone",
     "High enquiry volume, brutal document-chasing burden, clients in every time zone, and "
     "free-consultation models that generate more leads than firms can answer. No HIPAA. "
     "Being in the UK is a selling point rather than a problem.",
     "TCPA applies the moment you text a lead. Keep the build to email and web chat at first."),
    (4, "Larger nonprofits ($5m+ revenue)", 7, 8, 6, "Email to a named program or ops lead",
     "92% of US nonprofits already use AI but only 7% report real strategic impact, and 76% "
     "name staff bandwidth rather than money as the constraint. Only 28% cite budget. That is "
     "the exact shape of a done-for-you implementation sale. The $25k charity deal you heard "
     "about is entirely plausible at this end of the market.",
     "Slow. Board approval, grant cycles, and overhead optics. Avoid anything under $2m revenue."),
    (5, "Independent insurance agencies", 8, 8, 5, "Phone, email rarely published",
     "Same play that works for you in the UK, and the US market is far larger. The problem is "
     "reachability: US agencies route everything through web forms and agent locators.",
     "Worth running your pipeline over agency names rather than hunting by hand."),
    (6, "Staffing agencies", 7, 8, 5, "Phone and LinkedIn",
     "CV screening is your cleanest demo and US staffing is enormous. But the big players "
     "already run Bullhorn plus an AI layer, and the small ones publish no addresses.",
     "Go LinkedIn-first, exactly as you would in the UK."),
    (7, "Home services (HVAC, plumbing, roofing)", 8, 10, 6, "Phone",
     "The need is real and enormous. It is also the single most saturated AI-answering market "
     "in the US: almost every statistic you will read about missed calls was published by a "
     "vendor selling the fix.",
     "AVOID as a beachhead. You would be the fiftieth caller this month."),
    (8, "Dental, med spa, private healthcare", 9, 9, 3, "Blocked by compliance",
     "The money and the need are both excellent. The problem is HIPAA: an AI agent handling "
     "patient calls is a Business Associate, which requires a signed BAA and makes you "
     "directly liable to the Office for Civil Rights.",
     "AVOID until you have a compliant stack and US-facing insurance. This is the biggest "
     "single difference from your UK business."),
]

LEGAL = [
    ("Getting paid", "", ""),
    ("Withholding tax",
     "None, if you file one form.",
     "Your US client will ask for a W-8BEN-E. It certifies the company is UK-resident with no "
     "US permanent establishment and claims Article 7 of the US-UK treaty. Without it they must "
     "withhold 30%. With it, 0%. Fill it in once and send the PDF to every client. Services "
     "performed entirely from the UK are foreign-source income anyway."),
    ("US corporation tax",
     "None, absent a permanent establishment.",
     "Under Article 7 your business profits are taxable only in the UK unless you create a US "
     "permanent establishment. A fixed place of business or a dependent sales agent in the US "
     "would do it. Working from Bristol for US clients would not."),
    ("US sales tax",
     "Not yet, but watch it.",
     "Economic nexus is generally $100,000 of sales into a single state ($500,000 in California "
     "and Texas). You will not approach that for a long time. States also disagree on whether "
     "SaaS and custom software services are taxable at all. Revisit when any one state passes "
     "roughly $75k."),
    ("UK VAT",
     "Outside the scope.",
     "B2B services to a US business customer are outside the scope of UK VAT because the place "
     "of supply is where the customer is. US sales do not count toward the £90k registration "
     "threshold either, which is a genuine advantage over UK work."),
    ("Actually receiving the money",
     "Wise Business or Revolut Business.",
     "Open a USD receiving account so clients pay a US account number by ACH rather than wiring "
     "internationally. A wire costs them $25-45 and makes you look small. Avoid taking the FX "
     "spread on a high-street business account, which runs 3-4%."),
    ("Professional indemnity insurance",
     "Check this before your first US invoice.",
     "Most UK PI policies exclude claims brought in the USA and Canada as standard. Selling into "
     "the US on a policy with that exclusion means you are uninsured for the work. Ring your "
     "broker and ask specifically for US jurisdiction cover. Expect the premium to rise."),
    ("", "", ""),
    ("Rules that change what you can build", "", ""),
    ("TCPA (calls and texts)",
     "The big one. $500-1,500 per message.",
     "Far stricter than UK PECR, with a large plaintiffs' bar behind it. AI voice calls count as "
     "artificial or prerecorded voice. Marketing calls and texts to mobiles need prior express "
     "written consent naming your client's company. Damages are per message with no cap, so a "
     "10,000-message campaign is $5-15m of exposure. Note carefully: as the platform, your "
     "client's compliance failure can become your liability."),
    ("Call recording consent",
     "Two-party consent in 11+ states.",
     "California, Florida, Pennsylvania, Washington and others require all parties to consent to "
     "recording. Any AI voice agent must announce itself and the recording at the start of every "
     "call. Build this in as a default rather than a setting."),
    ("HIPAA",
     "Rules out healthcare for now.",
     "An AI agent handling patient calls is a Business Associate. That requires a signed BAA "
     "before it processes a single call, plus encryption at rest and in transit, role-based "
     "access, and audit logs. Penalties run from $141 to over $71,000 per violation. Operating "
     "without a BAA is itself a violation whether or not anything leaks."),
    ("CAN-SPAM (cold email)",
     "Much easier than the UK. This is the good news.",
     "No prior consent needed for B2B cold email. You need honest headers and subject lines, a "
     "real physical postal address in every message, a working opt-out, and you must honour "
     "opt-outs within 10 business days. Penalties are up to $53,088 per email for getting it "
     "wrong, so put a real address and a real unsubscribe in the footer. Your current UK emails "
     "have neither and would need both."),
    ("", "", ""),
    ("Escort agencies", "", ""),
    ("The short answer",
     "Do not.",
     "FOSTA (18 U.S.C. 2421A) makes it a federal crime to own, manage or operate an interactive "
     "computer service with intent to promote or facilitate prostitution. Maximum ten years, "
     "rising to twenty-five where five or more people are involved. An AI receptionist that "
     "books appointments for an escort agency is close to the textbook example of the conduct "
     "the statute describes, and the intent element is satisfied by knowing what you are "
     "building it for."),
    ("The practical answer",
     "Even setting the statute aside, it does not work.",
     "Stripe, PayPal and every mainstream processor prohibit the category outright, so you would "
     "struggle to get paid. Your PI insurance would not cover it. And UK law is separate and "
     "also engaged. I have not included any leads in this sector."),
]


def build():
    wb = openpyxl.Workbook()

    # ---------------- Sheet 1: Leads -------------------------------------
    ws = wb.active
    ws.title = "US Leads"
    title_block(ws, "US leads, ranked",
                "Every address below was read from a published page or listing. None were built from a company's "
                "email pattern. Rows are ranked on budget, strength of need, and how directly you can reach "
                "someone who can say yes.", 12)

    headers = ["#", "Score", "Organisation", "Sector", "State", "Contact", "Role",
               "Email", "Phone", "What to sell", "Price band", "Note"]
    header_row(ws, 4, headers)

    r = 5
    for i, L in enumerate(LEADS, start=1):
        ws.cell(row=r, column=1, value=i)
        ws.cell(row=r, column=2, value=L["score"])
        ws.cell(row=r, column=3, value=L["org"])
        ws.cell(row=r, column=4, value=L["sector"])
        ws.cell(row=r, column=5, value=L["state"])
        ws.cell(row=r, column=6, value=L["person"] or "-")
        ws.cell(row=r, column=7, value=L["role"] or "-")
        ws.cell(row=r, column=8, value=L["email"])
        ws.cell(row=r, column=9, value=L["phone"] or "-")
        ws.cell(row=r, column=10, value=L["sell"])
        ws.cell(row=r, column=11, value=L["price"])
        ws.cell(row=r, column=12, value=L["note"])

        for c in range(1, 13):
            cell = ws.cell(row=r, column=c)
            cell.font = Font(name=FONT, size=10, color=INK,
                             bold=(c == 3))
            cell.alignment = Alignment(vertical="top", wrap_text=(c >= 10 or c == 3))
            cell.border = BOX
            if i % 2 == 0:
                cell.fill = SUBTLE
        ws.cell(row=r, column=2).alignment = Alignment(horizontal="center", vertical="top")
        ws.cell(row=r, column=1).alignment = Alignment(horizontal="center", vertical="top")
        ws.cell(row=r, column=8).font = Font(name=FONT, size=10, color="1E3A5F")
        if L["person"]:
            ws.cell(row=r, column=6).fill = GOOD_FILL
        ws.row_dimensions[r].height = 58
        r += 1

    note = ws.cell(row=r + 1, column=1,
                   value="Named contact highlighted in green means the email goes to a person rather than an inbox. "
                         "Open those with their first name.")
    note.font = Font(name=FONT, size=9, italic=True, color=MUTED)
    ws.merge_cells(start_row=r + 1, start_column=1, end_row=r + 1, end_column=12)

    src = ws.cell(row=r + 2, column=1,
                  value="Sources: each organisation's own staff or contact page, via web search, August 2026. "
                        "Two rows are flagged in the Note column where the source listing was several years old.")
    src.font = Font(name=FONT, size=9, italic=True, color=MUTED)
    ws.merge_cells(start_row=r + 2, start_column=1, end_row=r + 2, end_column=12)

    for col, w in zip("ABCDEFGHIJKL",
                      [4, 6, 30, 22, 9, 20, 20, 32, 18, 38, 18, 52]):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "C5"

    # ---------------- Sheet 2: Phone first -------------------------------
    ws2 = wb.create_sheet("Phone First")
    title_block(ws2, "Phone first, no published address",
                "Real organisations with a named decision maker but no email address I could verify. I have not "
                "guessed at one. Call these rather than skipping them: an Association Executive answers her own "
                "phone far more often than a managing director does.", 7)
    header_row(ws2, 4, ["#", "Organisation", "Sector", "State", "Contact", "Phone", "Note"])
    r = 5
    for i, (org, sec, st, person, role, phone, note) in enumerate(PHONE_ONLY, start=1):
        vals = [i, org, sec, st, (person + (", " + role if role else "")), phone, note]
        for c, v in enumerate(vals, start=1):
            cell = ws2.cell(row=r, column=c, value=v)
            cell.font = Font(name=FONT, size=10, color=INK, bold=(c == 2))
            cell.alignment = Alignment(vertical="top", wrap_text=(c in (2, 7)))
            cell.border = BOX
            if i % 2 == 0:
                cell.fill = SUBTLE
        ws2.cell(row=r, column=1).alignment = Alignment(horizontal="center", vertical="top")
        ws2.row_dimensions[r].height = 44
        r += 1
    for col, w in zip("ABCDEFG", [4, 34, 24, 10, 26, 20, 62]):
        ws2.column_dimensions[col].width = w
    ws2.freeze_panes = "B5"

    # ---------------- Sheet 3: Sectors -----------------------------------
    ws3 = wb.create_sheet("Sectors Ranked")
    title_block(ws3, "US sectors, ranked for you specifically",
                "Scored 1-10. Money is budget to spend. Need is how badly the problem bites. Access is whether you "
                "can reach a decision maker from Bristol without a US presence. Access is what reorders this list "
                "against the obvious answers.", 7)
    header_row(ws3, 4, ["#", "Sector", "Money", "Need", "Access", "Best channel", "Why, and the catch"])
    r = 5
    for (n, name, money, need, access, chan, why, catch) in SECTORS:
        ws3.cell(row=r, column=1, value=n)
        ws3.cell(row=r, column=2, value=name)
        ws3.cell(row=r, column=3, value=money)
        ws3.cell(row=r, column=4, value=need)
        ws3.cell(row=r, column=5, value=access)
        ws3.cell(row=r, column=6, value=chan)
        ws3.cell(row=r, column=7, value=why + "\n\nCatch: " + catch)
        for c in range(1, 8):
            cell = ws3.cell(row=r, column=c)
            cell.font = Font(name=FONT, size=10, color=INK, bold=(c == 2))
            cell.alignment = Alignment(vertical="top", wrap_text=(c in (2, 6, 7)))
            cell.border = BOX
        for c in (1, 3, 4, 5):
            ws3.cell(row=r, column=c).alignment = Alignment(horizontal="center", vertical="top")
        if n <= 3:
            for c in range(1, 8):
                ws3.cell(row=r, column=c).fill = GOOD_FILL
        if catch.startswith("AVOID"):
            for c in range(1, 8):
                ws3.cell(row=r, column=c).fill = STOP_FILL
        ws3.row_dimensions[r].height = 108
        r += 1
    for col, w in zip("ABCDEFG", [4, 30, 8, 8, 8, 24, 86]):
        ws3.column_dimensions[col].width = w

    # ---------------- Sheet 4: Money and law ------------------------------
    ws4 = wb.create_sheet("Money and Law")
    title_block(ws4, "Charging Americans, and what you may not build",
                "None of this is legal advice. It is the shape of the problem and the specific questions to put to "
                "your accountant and your insurance broker before the first US invoice.", 3)
    header_row(ws4, 4, ["Item", "Short answer", "Detail"])
    r = 5
    for item, short, detail in LEGAL:
        if item and not short and not detail:
            cell = ws4.cell(row=r, column=1, value=item.upper())
            cell.font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
            cell.fill = HEAD_FILL
            cell.alignment = Alignment(vertical="center")
            for c in (2, 3):
                ws4.cell(row=r, column=c).fill = HEAD_FILL
                ws4.cell(row=r, column=c).border = BOX
            ws4.cell(row=r, column=1).border = BOX
            ws4.row_dimensions[r].height = 22
            r += 1
            continue
        if not item and not short and not detail:
            ws4.row_dimensions[r].height = 8
            r += 1
            continue
        ws4.cell(row=r, column=1, value=item)
        ws4.cell(row=r, column=2, value=short)
        ws4.cell(row=r, column=3, value=detail)
        for c in range(1, 4):
            cell = ws4.cell(row=r, column=c)
            cell.font = Font(name=FONT, size=10, color=INK, bold=(c == 1))
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = BOX
        ws4.cell(row=r, column=2).font = Font(name=FONT, size=10, bold=True, color=ACCENT)
        if item in ("TCPA (calls and texts)", "HIPAA", "Professional indemnity insurance"):
            for c in range(1, 4):
                ws4.cell(row=r, column=c).fill = WARN_FILL
        if item in ("The short answer", "The practical answer"):
            for c in range(1, 4):
                ws4.cell(row=r, column=c).fill = STOP_FILL
        ws4.row_dimensions[r].height = 78
        r += 1

    for col, w in zip("ABC", [32, 34, 96]):
        ws4.column_dimensions[col].width = w

    # ---------------- Sheet 5: How to run it ------------------------------
    ws5 = wb.create_sheet("How To Run It")
    title_block(ws5, "Running US outreach from the UK",
                "The practical differences from what you are already doing.", 2)
    rows = [
        ("Time zones",
         "Eastern is UK minus 5, Pacific UK minus 8. A US business day starts at 2pm your time and runs to "
         "1am. Send email at 7am UK so it lands before their inbox fills, and keep calls to 3pm-6pm UK, "
         "which is 10am-1pm Eastern."),
        ("Your email footer must change",
         "CAN-SPAM requires a real physical postal address and a working opt-out in every commercial email. "
         "Your current signature has neither. Add your registered company address and one line offering to "
         "be removed. This is the single most likely thing to catch you out and it takes five minutes."),
        ("Sound local enough, don't pretend to be",
         "A UK company serving US clients is unremarkable in software. Do not fake a US address or a US "
         "number: get a US forwarding number so you are callable, and be straightforward about where you "
         "are. The out-of-hours pitch is stronger when you are awake at their 3am anyway."),
        ("Price in dollars, and price up",
         "US buyers in these sectors expect higher numbers than UK ones and read a low price as a small "
         "vendor. Your UK mid band of £3-6k plus £750-1.5k a month translates to roughly $6-12k plus "
         "$1.5-2.5k. Quote in USD and do not discount for being foreign."),
        ("Contracts",
         "US clients will often want their own MSA under their state's law. For deals at this size that is "
         "normally fine, but read the indemnity and limitation of liability clauses. Uncapped indemnities "
         "are common in US templates and are not acceptable at your size."),
        ("Where to start",
         "Send the fifteen emails on tab one over three days, then work the phone list. The association "
         "sector is the whole bet: if two of those fifteen reply, build the next hundred leads from the "
         "same well. There are roughly a thousand local REALTOR boards alone, and every one publishes its "
         "Association Executive."),
    ]
    header_row(ws5, 4, ["", "Notes"])
    r = 5
    for a, b in rows:
        ws5.cell(row=r, column=1, value=a)
        ws5.cell(row=r, column=2, value=b)
        for c in (1, 2):
            cell = ws5.cell(row=r, column=c)
            cell.font = Font(name=FONT, size=10, color=INK, bold=(c == 1))
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = BOX
        ws5.row_dimensions[r].height = 76
        r += 1
    ws5.column_dimensions["A"].width = 30
    ws5.column_dimensions["B"].width = 112

    for sheet in wb:
        sheet.sheet_view.showGridLines = False

    wb.save("US_LEADS.xlsx")
    print("wrote US_LEADS.xlsx")
    print("leads with verified email:", len(LEADS))
    print("phone-first rows:", len(PHONE_ONLY))


if __name__ == "__main__":
    build()
