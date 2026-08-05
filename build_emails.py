#!/usr/bin/env python3
"""Generate outreach emails for both lists.

Two audiences with different legal footing and different pitches:

  Estate / letting agents  - 30 names from outreachemails.html, mostly limited
                             companies, so fair game for B2B cold email
  Gas & heating trades     - the 66 ICP-qualified rows from QUALIFIED_LEADS.csv,
                             many of them sole traders, which under PECR are
                             individual subscribers needing consent

Every email address here was found by hand and verified against a real source.
None are constructed from a pattern. A guessed info@ address bounces, hurts the
sending domain's reputation, and can reach the wrong company entirely, so a
blank is left where nothing was found.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent

SIG_NAME = "Benjamin Houghton"
SIG_PHONE = "07444577053"
SIG_EMAIL = "Ben@Houghtonautomations.co.uk"
SIG_SITE = "houghtonautomations.co.uk"

# ---------------------------------------------------------------- addresses --
# Verified by web search, 2 Aug 2026. Source noted for each.
VERIFIED_EMAILS: dict[str, tuple[str, str]] = {
    "CJ Hole": ("bishopston@cjhole.co.uk", "cjhole.co.uk branch listing (Bishopston)"),
    "Ocean Estate Agents": ("customercare@oceanhome.co.uk", "oceanhome.co.uk contact page"),
    "Hobbs Property Agents": ("michaelhobbs219@gmail.com", "Rightmove / directory listing"),
    "Milburys": ("mil_thornburysales@milburys.co.uk", "allAgents Thornbury branch listing"),
    "Cobb Farr": ("bath@cobbfarr.com", "cobbfarr.com contact page"),
    "Reside Bath": ("info@residebath.co.uk", "Cylex Bath listing"),
}

# Checked and no published address found - do not invent one.
NO_EMAIL_FOUND = {"Crisp Cowley"}

AGENCIES = [
    "CJ Hole", "Howard Independent Estate Agents", "Garrett & Bradly",
    "Boardwalk Property Co", "TLS Estate Agents", "Holbrook Moran",
    "Airsat Real Estate", "DSB Estate Agents", "Vibe Properties",
    "Bristol Property Centre", "Assured Property Rentals", "Country Property",
    "Hobbs Property Agents", "Bundy and Bond", "Edison Ford Property",
    "M. Coleman Estate Agents", "Brunt & Fussell", "React Property Management",
    "Ocean Estate Agents", "Michael Nicholas Estate Agents",
    "Abode Property Management", "Bonds of Thornbury", "Milburys",
    "Aquarius Homes", "Hensons", "Crisp Cowley", "Bath Stone Property",
    "Cobb Farr", "Reside Bath", "Wentworth Estate Agents",
]

# Firms confirmed to advertise 24/7 while running on one mobile - the sharpest
# hook available, verified rather than assumed.
ADVERTISES_247 = {
    "HydroGreen Heating and Gas Engineering",
    "Pipe Guys (Bham) Ltd",
    "Blaymires Plumbing & Heating",
    "Secure Gas 247",
}

WEAK_SITE = {
    "HydroGreen Heating and Gas Engineering": "a free Wix page",
    "Blaymires Plumbing & Heating": "a UENI page",
}

INCORPORATED = re.compile(r"\b(ltd|limited|plc|llp|group|holdings)\b", re.I)

SIGNATURE_TEXT = (
    f"Best,\n\n{SIG_NAME}\n{SIG_PHONE}\n{SIG_EMAIL}\n{SIG_SITE}"
)


def signature_html() -> str:
    return (
        '<p style="margin:0 0 14px 0">Best,</p>'
        '<div style="border-top:1px solid #dddddd;padding-top:12px;margin-top:4px;'
        'font-size:13px;line-height:1.5;color:#444444">'
        f'<div style="font-weight:bold;color:#222222">{SIG_NAME}</div>'
        f'<div>{SIG_PHONE}</div>'
        f'<div><a href="mailto:{SIG_EMAIL}" style="color:#1E3A5F;text-decoration:none">'
        f'{SIG_EMAIL}</a></div>'
        f'<div><a href="https://{SIG_SITE}" style="color:#1E3A5F;text-decoration:none">'
        f'{SIG_SITE}</a></div></div>'
    )


def to_html(paras: list[str]) -> str:
    body = "".join(
        f'<p style="margin:0 0 14px 0">{p}</p>' for p in paras
    )
    return ('<div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;'
            'line-height:1.6;color:#222222">' + body + signature_html() + "</div>")


# ------------------------------------------------------------ estate agents --

def possessive(name: str) -> str:
    """Milburys -> Milburys', Cobb Farr -> Cobb Farr's.

    A name ending in s taking 's is the sort of thing that makes a cold email
    read as machine-generated, which is the one impression it cannot afford.
    """
    return name + ("'" if name.rstrip().endswith(("s", "S")) else "'s")


def estate_email(company: str) -> tuple[str, list[str]]:
    subject = f"Quick question about {possessive(company)} enquiry handling"
    # Naming the company in the body matters: thirty identical emails to thirty
    # agents in one city reads as a blast and lands in Promotions.
    paras = [
        "Hi there,",
        f"I came across {company} while looking at agents around Bristol and "
        f"Bath. I build AI receptionists for estate and letting agents — they "
        f"answer new enquiries, viewing requests and tenant maintenance calls "
        f"instantly, including evenings and weekends, so nothing sits in a "
        f"voicemail box until Monday.",
        "Most agents I speak to aren't losing applicants on price. They're "
        "losing them because someone else replied first.",
        "Would you have ten minutes for a call this week or next? I can walk "
        "you through it on a real enquiry so you can see exactly how it would "
        "handle one of your own. What day suits you?",
    ]
    return subject, paras


# --------------------------------------------------------------- gas trades --

def gas_email(row: dict[str, str]) -> tuple[str, list[str]]:
    company = row["Company"]
    reviews = row.get("Reviews", "").strip()
    product = row.get("SELL THEM", "")

    # Lead with the 24/7 contradiction where it is confirmed - it is specific,
    # verifiable, and they made the claim publicly.
    if company in ADVERTISES_247:
        subject = f"{company} - who answers at 2am?"
        opener = (
            f"Your website says you're available 24/7, and with {reviews} Google "
            f"reviews I don't doubt the demand is there. What I wondered is who "
            f"actually picks up at 2am, or when you're under a boiler at 3pm."
        )
    elif reviews.isdigit() and int(reviews) >= 150:
        subject = f"Quick question about {possessive(company)} call handling"
        opener = (
            f"You've got {reviews} Google reviews, so you're clearly busy. That "
            f"usually means calls come in while you're mid-job and go to "
            f"voicemail."
        )
    else:
        subject = f"Quick question about {possessive(company)} call handling"
        opener = (
            "When a call comes in while you're on a job, what happens to it at "
            "the moment?"
        )

    second = (
        "I build AI systems for gas and heating firms that answer the phone "
        "around the clock, take the job details properly, and text them "
        "straight through to you. It doesn't replace you on the phone, it "
        "replaces the voicemail people currently get."
    )
    if product.startswith("Speed-to-Lead"):
        second = (
            "I build AI systems for gas and heating firms that get quotes back "
            "out the same hour instead of the same week. When someone's "
            "collecting three quotes, whoever replies first usually wins the "
            "job."
        )
    elif product.startswith("Online Booking"):
        second = (
            "I build AI systems for gas and heating firms that chase service and "
            "safety certificate renewals automatically, and let customers book "
            "themselves in. Your past customers are a renewal list most "
            "engineers never work."
        )

    third = (
        "The reason I'm getting in touch now rather than in November is that "
        "you've got about eight weeks before the heating season starts and the "
        "phone stops ringing off the hook. Far easier to have this running "
        "before October than to set it up in the middle of it."
    )

    if company in WEAK_SITE:
        third = (
            f"I also noticed you're on {WEAK_SITE[company]} rather than your own "
            f"domain, which for a business your size is leaving money on the "
            f"table. Worth covering off at the same time."
        )

    fourth = (
        "Would you have ten minutes for a call this week or next? Early morning "
        "or after five suits most engineers I speak to. What works for you?"
    )

    return subject, ["Hi there,", opener, second, third, fourth]


# -------------------------------------------------------------------- build --

def build() -> list[dict]:
    out: list[dict] = []

    for company in AGENCIES:
        email, source = VERIFIED_EMAILS.get(company, ("", ""))
        subject, paras = estate_email(company)
        out.append({
            "list": "Estate agents",
            "company": company,
            "email": email,
            "email_source": source,
            "email_status": ("verified" if email
                             else "checked - none published" if company in NO_EMAIL_FOUND
                             else "NOT LOOKED UP YET"),
            "legal": "Ltd - B2B cold email permitted under PECR"
                     if INCORPORATED.search(company) else
                     "Check if sole trader before emailing",
            "subject": subject,
            "text": "\n\n".join(paras) + "\n\n" + SIGNATURE_TEXT,
            "html": to_html(paras),
        })

    qualified = REPO / "QUALIFIED_LEADS.csv"
    if qualified.exists():
        for row in csv.DictReader(qualified.open(encoding="utf-8-sig")):
            company = row["Company"]
            subject, paras = gas_email(row)
            incorporated = bool(INCORPORATED.search(company))
            out.append({
                "list": "Gas & heating",
                "company": company,
                "email": "",
                "email_source": "",
                "email_status": "NOT LOOKED UP YET",
                "legal": ("Ltd - B2B cold email permitted under PECR"
                          if incorporated
                          else "LIKELY SOLE TRADER - needs consent, do not cold email"),
                "phone": row.get("Phone", ""),
                "subject": subject,
                "text": "\n\n".join(paras) + "\n\n" + SIGNATURE_TEXT,
                "html": to_html(paras),
            })

    return out


if __name__ == "__main__":
    data = build()
    (REPO / "drafted_emails.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8")
    verified = sum(1 for d in data if d["email"])
    sole = sum(1 for d in data if "SOLE TRADER" in d["legal"])
    print(f"{len(data)} emails drafted")
    print(f"  with a verified address : {verified}")
    print(f"  address still needed    : {len(data) - verified}")
    print(f"  likely sole traders (do not cold email): {sole}")
