#!/usr/bin/env python3
"""New-industry leads: sectors that fit premium AI automation pricing.

Selection criteria, in the order that actually matters for this business:

  1. Can they pay?          Agencies target clients at roughly £400K-£16M
                            turnover. Below that, premium retainers are not
                            affordable however good the ROI story.
  2. Is one person enough?  A single owner, partner or practice manager who can
                            say yes, rather than a procurement process.
  3. Can I reach them?      A published email address. Sectors that hide behind
                            contact forms are unusable for cold email whatever
                            their fit - which ruled out car dealerships here.
  4. Does the pain cost real money?  High job value plus enquiry volume, so a
                            missed enquiry is a four-figure loss rather than an
                            annoyance.

Every address below was found by web search and read from a real source.
Nothing is constructed from an info@ pattern.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent

SIG_NAME = "Benjamin Houghton"
SIG_PHONE = "07444577053"
SIG_EMAIL = "Ben@Houghtonautomations.co.uk"
SIG_SITE = "houghtonautomations.co.uk"

# Price bands carried over from leadgen/pricing.py.
BAND_MID = "£3,000-6,000 setup + £750-1,500/mo"
BAND_UPPER = "£6,000-12,000 setup + £1,500-2,500/mo"
BAND_SMALL = "£500-1,500 setup + £199-399/mo"


SECTOR_PHRASE = {
    "Private hospital": "private hospitals",
    "Cosmetic surgery": "cosmetic surgery clinics",
    "Cosmetic clinic group": "cosmetic clinic groups",
    "Private dentistry": "private dental practices",
    "Aesthetics": "aesthetics clinics",
    "Medical aesthetics": "medical aesthetics clinics",
    "Law - conveyancing": "conveyancing firms",
    "Accountancy": "accountancy practices",
    "Recruitment": "recruitment agencies",
}


@dataclass
class Lead:
    company: str
    sector: str
    email: str
    source: str
    band: str
    why: str            # why this sector needs it, in money terms
    lead_with: str      # the one automation to open on
    also: str           # the wider range, one line
    hook: str           # the opening sentence
    note: str = ""      # anything to check before sending
    tags: list[str] = field(default_factory=list)


DENTAL_ALSO = ("Alongside that I build treatment-plan follow-up, recall and "
               "hygiene reminders, and review requests that go out on their own.")
CLINIC_ALSO = ("Alongside that I build consultation follow-up, pre-op document "
               "chasing, and reminders that cut no-shows.")
LEGAL_ALSO = ("Alongside that I build ID and document chasing, new-enquiry "
              "qualification, and out-of-hours call handling.")
ACCOUNTING_ALSO = ("Alongside that I build client onboarding, deadline and "
                   "filing reminders, and enquiry handling for new business.")
RECRUIT_ALSO = ("Alongside that I build candidate follow-up sequences, "
                "interview scheduling, and out-of-hours client enquiry handling.")


LEADS: list[Lead] = [
    # ---------------------------------------------------- private healthcare --
    Lead("North Bristol Private Hospital", "Private hospital", "info@nbph.co.uk",
         "northbristolprivatehospital.co.uk contact page", BAND_UPPER,
         "Self-pay surgery runs into five figures per case. An enquiry that "
         "goes unanswered over a weekend is a lost operation, not a lost call.",
         "an enquiry line that answers self-pay enquiries the moment they come "
         "in, day or night, and books the consultation",
         CLINIC_ALSO,
         "When a self-pay enquiry comes in at 8pm on a Saturday, what happens "
         "to it before Monday?",
         tags=["high job value", "24/7 gap"]),

    Lead("58 Queen Square", "Cosmetic surgery", "info@58queensquare.com",
         "bristolplasticsurgery.com contact page", BAND_MID,
         "Cosmetic surgery consultations convert slowly and enquirers shop "
         "around. Speed of first reply decides who gets the consultation.",
         "instant enquiry response and consultation booking, so the first "
         "reply is yours rather than the clinic down the road's",
         CLINIC_ALSO,
         "How quickly does someone hear back after enquiring about a "
         "procedure?",
         tags=["high job value", "speed to lead"]),

    Lead("The Private Clinic", "Cosmetic clinic group", "enquiries@theprivateclinic.co.uk",
         "theprivateclinic.co.uk contact page", BAND_UPPER,
         "Multi-site group with national advertising spend. Every unanswered "
         "enquiry is paid-for traffic wasted.",
         "enquiry triage across sites, so leads are qualified and routed to "
         "the right clinic without anyone rekeying them",
         CLINIC_ALSO,
         "With clinics across several cities, how are enquiries routed and "
         "chased at the moment?",
         note="Larger group - expect more than one decision maker.",
         tags=["multi-site", "ad spend"]),

    Lead("Clifton Dental Studio", "Private dentistry", "info@cliftonsmiles.co.uk",
         "cliftonsmiles.com contact page", BAND_MID,
         "Implant and cosmetic cases run to four and five figures. A missed "
         "call about implants is a £5,000 case going to another practice.",
         "a receptionist that answers implant and cosmetic enquiries out of "
         "hours and books the consultation while they are still interested",
         DENTAL_ALSO,
         "When someone rings about implants while the practice is closed, "
         "where does that call go?",
         tags=["high job value", "24/7 gap"]),

    Lead("Paul Wilson Aesthetics", "Aesthetics", "info@paulwilsonaesthetics.co.uk",
         "paulwilsonaesthetics.co.uk contact page", BAND_MID,
         "Consultant-led aesthetics: the surgeon is in clinic all day and "
         "cannot answer enquiries while operating.",
         "an enquiry line that answers and books while you are in clinic",
         CLINIC_ALSO,
         "While you're in clinic, who is answering the enquiries coming in?",
         tags=["owner is the bottleneck"]),

    Lead("Skin & Joints", "Medical aesthetics", "hello@skinjoints.co.uk",
         "skinjoints.co.uk", BAND_MID,
         "Clinician-led practice where the person delivering treatment is also "
         "the person answering the phone.",
         "an enquiry line that books consultations while you are treating",
         CLINIC_ALSO,
         "Who picks up when you're mid-treatment?",
         tags=["owner is the bottleneck"]),

    Lead("Bristol Aesthetics", "Aesthetics", "info@bristolaesthetics.org.uk",
         "bristolaesthetics.org.uk", BAND_MID,
         "Treatment-led clinic with repeat-course revenue that depends on "
         "rebooking, which is exactly what gets forgotten.",
         "automated rebooking and course reminders, so repeat treatments do "
         "not depend on anyone remembering to chase",
         CLINIC_ALSO,
         "How do you handle rebooking for repeat treatment courses?",
         tags=["recurring revenue"]),

    # --------------------------------------------------------------- legal ---
    Lead("Watkins Solicitors", "Law - conveyancing", "info@watkinssolicitors.co.uk",
         "watkinssolicitors.co.uk contact page", BAND_MID,
         "Conveyancing clients ring constantly for progress updates. That "
         "traffic is pure cost and it lands on fee earners.",
         "automated case-progress updates, so clients stop ringing to ask "
         "where things are",
         LEGAL_ALSO,
         "How much of the day goes on clients ringing to ask where their "
         "matter has got to?",
         tags=["admin drain", "proven AI adopter sector"]),

    Lead("AMD Solicitors", "Law - conveyancing", "info@amdsolicitors.com",
         "amdsolicitors.com contact page", BAND_MID,
         "Multi-office firm; the same update calls repeat across every branch.",
         "automated case-progress updates and document chasing across offices",
         LEGAL_ALSO,
         "Across your offices, how much time goes on progress-chasing calls "
         "and ID document collection?",
         tags=["multi-office", "admin drain"]),

    # ---------------------------------------------------------- accountancy --
    Lead("Milsted Langdon LLP", "Accountancy", "advice@milstedlangdon.co.uk",
         "milstedlangdon.co.uk Bristol office", BAND_UPPER,
         "Five offices and a January deadline crush. Chasing clients for "
         "records is the single biggest drain in the practice.",
         "automated records chasing, so the January self-assessment crush "
         "stops depending on staff manually nagging clients",
         ACCOUNTING_ALSO,
         "How much of December and January goes on chasing clients for their "
         "records?",
         note="LLP with five offices - likely a partner-level decision.",
         tags=["seasonal crunch", "multi-office"]),

    # ---------------------------------------------------------- recruitment --
    Lead("Future Engineering Recruitment Ltd", "Recruitment", "info@futureengineer.co.uk",
         "futureengineer.co.uk", BAND_MID,
         "Placement fees run to five figures. Consultants lose hours a day to "
         "reading CVs that were never a fit.",
         "a screener that reads inbound CVs against the spec, asks the "
         "qualifying questions, and hands over a shortlist",
         RECRUIT_ALSO,
         "How many CVs does a consultant read before finding one worth a call?",
         tags=["high fee value", "clear use case"]),

    # ------------------------------------------------------------- marginal --
    Lead("KW Bristol Beauty & Aesthetics", "Aesthetics",
         "kwbeautyandaesthetic@hotmail.com", "kwbeautyaesthetics.com", BAND_SMALL,
         "Single-operator salon. Real pain, but a Hotmail address and a mobile "
         "number say this is not a premium-retainer client.",
         "call answering and booking while you're with a client",
         "",
         "Who answers the phone while you're with a client?",
         note="LOW BUDGET - included for completeness, not recommended for a "
              "premium pitch.",
         tags=["too small"]),
]


def build_email(lead: Lead) -> tuple[str, list[str]]:
    subject = f"Quick question about {lead.company}'s enquiry handling"
    if "24/7 gap" in lead.tags:
        subject = f"{lead.company} - out-of-hours enquiries"
    elif "seasonal crunch" in lead.tags:
        subject = f"{lead.company} - chasing records before January"
    elif "clear use case" in lead.tags:
        subject = f"Sifting CVs at {lead.company}"

    paras = [
        "Hi there,",
        lead.hook,
        f"I build AI automations for "
        f"{SECTOR_PHRASE.get(lead.sector, lead.sector.lower())}. The one that "
        f"would suit you is {lead.lead_with}.",
    ]
    if lead.also:
        paras.append(lead.also)
    subject_of_demo = ("one of your live vacancies" if lead.sector == "Recruitment"
                       else "a real client file" if lead.sector.startswith("Law")
                       else "a real client record chase" if lead.sector == "Accountancy"
                       else "one of your own enquiries")
    paras.append(
        f"Would you have ten minutes for a call this week or next? I can walk "
        f"you through it on {subject_of_demo} so you can see exactly what it "
        f"does. What day suits you?"
    )
    return subject, paras


def to_text(paras: list[str]) -> str:
    return ("\n\n".join(paras) + "\n\nBest,\n\n"
            f"{SIG_NAME}\n{SIG_PHONE}\n{SIG_EMAIL}\n{SIG_SITE}")


def to_html(paras: list[str]) -> str:
    body = "".join(f'<p style="margin:0 0 14px 0">{p}</p>' for p in paras)
    return (
        '<div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;'
        'line-height:1.6;color:#222222">' + body
        + '<p style="margin:0 0 14px 0">Best,</p>'
        '<div style="border-top:1px solid #dddddd;padding-top:12px;margin-top:4px;'
        'font-size:13px;line-height:1.5;color:#444444">'
        f'<div style="font-weight:bold;color:#222222">{SIG_NAME}</div>'
        f'<div>{SIG_PHONE}</div>'
        f'<div><a href="mailto:{SIG_EMAIL}" style="color:#1E3A5F;'
        f'text-decoration:none">{SIG_EMAIL}</a></div>'
        f'<div><a href="https://{SIG_SITE}" style="color:#1E3A5F;'
        f'text-decoration:none">{SIG_SITE}</a></div></div></div>'
    )


def main() -> None:
    records = []
    for lead in LEADS:
        subject, paras = build_email(lead)
        records.append({
            "company": lead.company, "sector": lead.sector, "email": lead.email,
            "source": lead.source, "band": lead.band, "why": lead.why,
            "note": lead.note, "subject": subject,
            "text": to_text(paras), "html": to_html(paras),
        })

    (REPO / "new_leads.json").write_text(json.dumps(records, indent=2),
                                         encoding="utf-8")

    with (REPO / "NEW_LEADS.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=[
            "company", "sector", "email", "band", "why", "note", "subject", "source"])
        w.writeheader()
        for r in records:
            w.writerow({k: r[k] for k in w.fieldnames})

    out = ["# New-industry leads — verified emails, drafted outreach\n",
           f"{len(records)} leads, every address read from a real source.\n"]
    for r in records:
        out.append(f"\n---\n\n## {r['company']}  ·  {r['sector']}\n")
        out.append(f"**To:** `{r['email']}`  ")
        out.append(f"\n**Source:** {r['source']}  ")
        out.append(f"\n**Subject:** `{r['subject']}`  ")
        out.append(f"\n**Price band:** {r['band']}  ")
        out.append(f"\n**Why they fit:** {r['why']}")
        if r["note"]:
            out.append(f"  \n**Note:** {r['note']}")
        out.append("\n\n```\n" + r["text"] + "\n```\n")
    (REPO / "NEW_LEADS.md").write_text("\n".join(out), encoding="utf-8")

    print(f"{len(records)} new leads, all with a verified email")
    for r in records:
        print(f"  {r['email']:<44}{r['company'][:34]:<36}{r['sector']}")


if __name__ == "__main__":
    main()
