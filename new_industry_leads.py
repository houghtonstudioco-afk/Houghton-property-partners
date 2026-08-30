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
    "Insurance broking": "insurance brokers",
    "Veterinary": "independent veterinary practices",
}


def possessive(name: str) -> str:
    """Fernlea Vets -> Fernlea Vets', Quinn Clinic -> Quinn Clinic's."""
    return name + ("'" if name.rstrip().endswith(("s", "S")) else "'s")


# Where the verified address belongs to a named person rather than a general
# inbox, greet them by name - it is the single cheapest personalisation there
# is, and "Hi there" to a named address reads as a mailmerge.
FIRST_NAMES = {
    "Fernlea Vets": "Robin",
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

    # ------------------------------------------------------ insurance broking --
    Lead("Somerset Bridge Group", "Insurance broking", "Enquiries@sbgl.co.uk",
         "somersetbridgegroup.com contact page", BAND_UPPER,
         "Brokers lose 29-39 hours a week to admin, 8-10 of that on email "
         "alone. Their revenue is commission and renewals, so every hour "
         "reclaimed converts directly.",
         "renewal and servicing automation, so policy requests and renewal "
         "notices stop eating producer time",
         "Alongside that I build out-of-hours new-business capture, quote "
         "chasing, and client document collection.",
         "How many hours a week does your team lose to policy requests and "
         "renewal admin?",
         tags=["admin drain", "recurring revenue"]),

    # ------------------------------------------------------------ recruitment --
    Lead("Pamela Neave", "Recruitment", "enquiries@pamela-neave.co.uk",
         "pamela-neave.co.uk", BAND_MID,
         "Independent consultancy where the founder is still fee-earning. "
         "Screening time comes straight out of billing time.",
         "a screener that reads inbound CVs against the spec and hands back a "
         "shortlist",
         RECRUIT_ALSO,
         "How many CVs land for a role before you find one worth calling?",
         tags=["high fee value", "clear use case"]),

    # ------------------------------------- dentistry, wider catchment ---------
    Lead("Green Park Dental", "Private dentistry", "reception@greenparkdental.co.uk",
         "bathdentists.co.uk", BAND_MID,
         "Cosmetic and implant work from whitening through to veneers and "
         "implants - four-figure cases where the first reply usually wins.",
         "a receptionist that answers implant and cosmetic enquiries out of "
         "hours and books the consultation",
         DENTAL_ALSO,
         "When someone rings about implants after you've closed, where does "
         "that call go?",
         tags=["high job value", "24/7 gap"]),

    Lead("Bath Spa Dentistry", "Private dentistry", "reception@bathspadentistry.com",
         "bathspadentistry.com contact page", BAND_MID,
         "City-centre private practice; enquiries arrive while the chair is "
         "occupied.",
         "an enquiry line that books consultations while the practice is busy",
         DENTAL_ALSO,
         "Who picks up when reception is with a patient?",
         tags=["24/7 gap"]),

    Lead("South Wales Specialist Oral Surgery", "Private dentistry",
         "info@specialist.wales", "specialist.wales contact page", BAND_MID,
         "Specialist oral surgery and implant centre taking referrals as well "
         "as direct enquiries - two intake streams, both manual.",
         "referral and enquiry intake that captures the detail properly first "
         "time",
         DENTAL_ALSO,
         "How do referrals and direct enquiries reach you at the moment?",
         tags=["high job value", "referral intake"]),

    Lead("Park Place Dental", "Private dentistry", "reception@parkplacedental.co.uk",
         "parkplacedental.co.uk", BAND_MID,
         "Implant-led Cardiff practice. Implant cases are four and five "
         "figures, so a missed enquiry is an expensive one.",
         "a receptionist that answers implant enquiries out of hours and books "
         "the consultation",
         DENTAL_ALSO,
         "What happens to implant enquiries that come in overnight?",
         tags=["high job value", "24/7 gap"]),

    Lead("Contemporary Dental", "Private dentistry", "care@contemporarydental.co.uk",
         "contemporarydental.co.uk", BAND_MID,
         "Private practice in Devon with a wide catchment - patients travel, "
         "so a slow reply loses them to somewhere closer.",
         "instant enquiry response and consultation booking",
         DENTAL_ALSO,
         "How quickly does someone hear back after enquiring?",
         tags=["speed to lead"]),

    Lead("Meliora Dental", "Private dentistry", "reception@melioradental.co.uk",
         "melioradental.co.uk", BAND_MID,
         "Implant-focused Leeds practice; the same four-figure-case logic "
         "applies.",
         "a receptionist that answers implant enquiries out of hours and books "
         "the consultation",
         DENTAL_ALSO,
         "When an implant enquiry comes in on a Sunday, what happens to it?",
         tags=["high job value", "24/7 gap"]),

    Lead("Infinity Dental Clinic", "Private dentistry",
         "info@infinitydentalclinic.co.uk", "infinitydentalclinic.co.uk", BAND_MID,
         "Cosmetic-led Leeds clinic where treatment plans need chasing to "
         "convert.",
         "treatment-plan follow-up, so quoted work does not quietly go cold",
         DENTAL_ALSO,
         "How do you follow up treatment plans that patients have not booked "
         "yet?",
         tags=["conversion gap"]),

    # ------------------------------------ cosmetic surgery, wider catchment ---
    Lead("UKSKIN", "Cosmetic surgery", "info@ukskin.co.uk",
         "ukskin.co.uk contact page", BAND_UPPER,
         "Surgery hubs in Birmingham, London and Manchester. Multi-site "
         "enquiry routing done by hand is where paid-for leads get lost.",
         "enquiry triage and routing across your surgery hubs",
         CLINIC_ALSO,
         "With hubs in three cities, how are enquiries routed and chased?",
         note="Multi-site - may involve more than one decision maker.",
         tags=["multi-site", "ad spend"]),

    Lead("My Cosmetics Clinic", "Cosmetic surgery", "contact@mccsurgery.com",
         "mycosmeticclinics.com contact page", BAND_MID,
         "Manchester surgical clinic; consultations are the bottleneck and "
         "enquirers shop around while they wait.",
         "instant enquiry response and consultation booking",
         CLINIC_ALSO,
         "How long does an enquirer wait before someone gets back to them?",
         tags=["speed to lead"]),

    # -------------------------------------------------- accountancy, vets -----
    Lead("Charlton Baker", "Accountancy", "info@charltonbaker.co.uk",
         "charltonbaker.co.uk", BAND_MID,
         "Nine offices across the South West and Thames Valley. Records "
         "chasing multiplies with every location.",
         "automated records chasing across offices, so January stops "
         "depending on manual nagging",
         ACCOUNTING_ALSO,
         "Across nine offices, how much of January goes on chasing clients for "
         "records?",
         tags=["multi-office", "seasonal crunch"]),

    Lead("Avenue Veterinary Centre", "Veterinary", "enquiries@avenue-vets.com",
         "avenue-vets.com", BAND_MID,
         "Independent practice - increasingly rare, as most UK vets are now "
         "group-owned with central procurement. Independent means the owner "
         "can still decide.",
         "an enquiry and booking line that answers when the phones are "
         "swamped, and chases vaccination and check-up recalls",
         "Alongside that I build recall reminders, post-op follow-up, and "
         "out-of-hours triage routing.",
         "How often do clients give up because the phone was engaged?",
         tags=["independent owner", "recall revenue"]),

    # ------------------------------------------- batch 3: not yet contacted ---
    Lead("The Campbell Clinic", "Private dentistry", "info@campbell-clinic.co.uk",
         "campbell-clinic.co.uk contact page", BAND_MID,
         "Specialist practice with implant surgeons, orthodontists and "
         "periodontists in six surgeries, and three implant pricing tiers. "
         "Implant and Invisalign cases are four and five figures.",
         "a receptionist that answers implant and Invisalign enquiries out of "
         "hours and books the consultation while they are still interested",
         DENTAL_ALSO,
         "With three implant pricing levels and Invisalign on the list, how do "
         "enquiries get handled when the practice is closed?",
         tags=["high job value", "24/7 gap", "not yet contacted"]),

    Lead("Quinn Clinics", "Aesthetics", "info@quinnclinics.co.uk",
         "quinnclinics.co.uk contact page", BAND_MID,
         "CQC-registered and running since 2006, so an established book of "
         "repeat patients that depends on rebooking.",
         "an enquiry line that books while you are treating, plus automated "
         "rebooking for repeat courses",
         CLINIC_ALSO,
         "Who picks up the phone when you're mid-treatment?",
         tags=["owner is the bottleneck", "not yet contacted"]),

    Lead("Azthetics Clinic", "Aesthetics", "info@aztheticsclinic.co.uk",
         "aztheticsclinic.co.uk contact page", BAND_MID,
         "Doctor-led across three sites in Bristol, Taunton and Weston. "
         "Enquiries arriving for the wrong site get lost in the handover.",
         "enquiry routing across your three clinics, so nothing gets lost "
         "between sites",
         CLINIC_ALSO,
         "With three clinics, how do enquiries get routed to the right one?",
         tags=["multi-site", "not yet contacted"]),

    Lead("Fernlea Vets", "Veterinary", "robin@fernleavets.co.uk",
         "fernleavets.co.uk - named contact", BAND_MID,
         "Independent since 1986 across two Bristol sites - increasingly rare, "
         "as most UK practices are now group-owned with central procurement.",
         "an enquiry and booking line for when the phones are swamped, plus "
         "automated vaccination and check-up recalls",
         "Alongside that I build post-op follow-up, out-of-hours triage "
         "routing, and reminders that bring lapsed clients back.",
         "How often do clients give up because the phone was engaged?",
         note="Named contact rather than a general inbox - address him directly.",
         tags=["independent owner", "not yet contacted"]),

    Lead("Motts Insurance Brokers", "Insurance broking", "info@mottsinsurance.com",
         "mottsinsurance.com contact page", BAND_MID,
         "Independent commercial broker. Brokers lose 29-39 hours a week to "
         "admin, and their revenue is commission and renewals, so every hour "
         "reclaimed converts directly.",
         "renewal and servicing automation, so policy requests stop eating "
         "producer time",
         "Alongside that I build out-of-hours new-business capture, quote "
         "chasing, and client document collection.",
         "How many hours a week go on policy requests and renewal admin?",
         tags=["admin drain", "not yet contacted"]),

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
    subject = f"Quick question about {possessive(lead.company)} enquiry handling"
    if "24/7 gap" in lead.tags:
        subject = f"{lead.company} - out-of-hours enquiries"
    elif "seasonal crunch" in lead.tags:
        subject = f"{lead.company} - chasing records before January"
    elif "clear use case" in lead.tags:
        subject = f"Sifting CVs at {lead.company}"

    greeting = FIRST_NAMES.get(lead.company)
    paras = [
        f"Hi {greeting}," if greeting else "Hi there,",
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
