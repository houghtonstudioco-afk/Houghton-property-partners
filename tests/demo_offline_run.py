#!/usr/bin/env python3
"""Seed the cache with SYNTHETIC pages, so the pipeline can be demonstrated
end-to-end without network access.

This exists to prove the plumbing at full scale: stage 1 discovery, stage 2
signal extraction, stage 3 Companies House matching and stage 4 rescoring all
run over the real 176-row CSV, but against invented pages.

    python tests/demo_offline_run.py          # seed a demo cache
    python enrich_leads.py --stages 1,2,3,4 --offline --cache .demo_cache/cache.sqlite \
        --output demo_enriched.csv

NOTHING it produces is real data about real companies. Never ship its output as
research. Delete .demo_cache/ and demo_enriched.csv when finished.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from leadgen.fetcher import normalise_url                       # noqa: E402
from leadgen.stage1_websites import DomainGuessProvider          # noqa: E402
from leadgen.store import Cache, CachedResponse, read_rows       # noqa: E402
from leadgen.textutil import location_city, postcode_area        # noqa: E402
from tests import fixtures                                       # noqa: E402

DEMO_CACHE = Path(".demo_cache/cache.sqlite")

# Reverse of config.POSTCODE_AREA_TO_CITY for building plausible addresses.
CITY_TO_POSTCODE = {
    "bristol": "BS1 4DJ", "birmingham": "B3 2TA", "aberdeen": "AB11 5BU",
    "glasgow": "G2 3AA", "leeds": "LS1 4AP", "nottingham": "NG1 5FS",
    "sheffield": "S1 2HH", "manchester": "M1 3BN", "kent": "ME14 1XX",
    "london": "EC1A 1BB", "devon": "EX1 1GE", "n yorkshire": "YO1 7HH",
}

# Which archetype each row gets, cycled deterministically so the demo output has
# a realistic spread rather than 176 identical rows.
ARCHETYPES = [
    ("modern", fixtures.MODERN_WELL_EQUIPPED, 200, None),
    ("dated", fixtures.DATED_JQUERY_SITE, 200, None),
    ("phone_only", fixtures.PHONE_ONLY_MINIMAL, 200, None),
    ("tawk_booking", fixtures.TAWK_AND_BOOKING_ROUTE, 200, None),
    ("dated", fixtures.DATED_JQUERY_SITE, 200, None),
    ("404", "", 404, None),
    ("phone_only", fixtures.PHONE_ONLY_MINIMAL, 200, None),
    ("zoho_acuity", fixtures.ZOHO_AND_ACUITY, 200, None),
    ("expired_ssl", fixtures.DATED_JQUERY_SITE, 200, "expired"),
    ("phone_only", fixtures.PHONE_ONLY_MINIMAL, 200, None),
    ("dns_dead", None, None, None),
    ("drift_crm", fixtures.DRIFT_PIPEDRIVE_SALESFORCE, 200, None),
    ("no_site", None, None, None),      # nothing seeded at all
    ("parked", fixtures.PARKED_DOMAIN, 200, None),
    ("phone_only", fixtures.PHONE_ONLY_MINIMAL, 200, None),
]


def personalise(html: str, row: dict[str, str]) -> str:
    """Inject this row's real name/phone/town so verification can succeed."""
    company = row["Company Name"]
    phone = row["Phone Number"]
    town = row["Location"]
    return (html
            .replace("The Gas Pro", company)
            .replace("MCR Gas", company)
            .replace("Gregor Heating, Electrical &amp; Renewable Energy", company)
            .replace("Plumbco Heating", company)
            .replace("Aberdeen Oilfield Services", company)
            .replace("Fab Co Leeds", company)
            .replace("07830 448127", phone)
            .replace("0161 660 6063", phone)
            .replace("0117 935 2400", phone)
            .replace("0117 901 2266", phone)
            .replace("+441179352400", phone.replace(" ", ""))
            .replace("tel:07830448127", f"tel:{phone.replace(' ', '')}")
            .replace("Bishopsworth, Bristol", town)
            .replace("Bury, Manchester", town)
            .replace("Warmley, Bristol", town))


def main() -> int:
    input_csv = Path("gas_oil_engineering_leads.csv")
    if not input_csv.exists():
        print(f"{input_csv} not found - run from the repository root.")
        return 1

    DEMO_CACHE.parent.mkdir(parents=True, exist_ok=True)
    if DEMO_CACHE.exists():
        DEMO_CACHE.unlink()
    cache = Cache(DEMO_CACHE)

    rows = read_rows(input_csv)
    guesser = DomainGuessProvider()
    tally: dict[str, int] = {}
    ch_payloads: dict[str, dict] = {}

    for index, row in enumerate(rows):
        kind, html, status, ssl_status = ARCHETYPES[index % len(ARCHETYPES)]
        tally[kind] = tally.get(kind, 0) + 1

        stems = guesser._stems(row["Company Name"])
        if not stems:
            continue
        url = normalise_url(f"https://{stems[0]}.co.uk")

        if kind == "no_site":
            continue                      # nothing cached: discovery finds nothing
        if kind == "dns_dead":
            cache.put_response(CachedResponse(url=url, error="dns_error: NXDOMAIN"))
            continue
        if kind == "404":
            cache.put_response(CachedResponse(url=url, status=404, final_url=url, body=""))
            continue

        body = personalise(html, row)
        cache.put_response(CachedResponse(
            url=url, status=status, final_url=url, body=body,
            ssl_status=ssl_status or "valid",
        ))

        # A matching Companies House record for two thirds of rows.
        if index % 3 != 2:
            city = location_city(row["Location"])
            postcode = CITY_TO_POSTCODE.get(city, "BS1 4DJ")
            ch_payloads[f"{row['Company Name']}|20"] = {
                "items": [{
                    "title": row["Company Name"].upper() + " LIMITED",
                    "company_number": str(1000000 + index).zfill(8),
                    "company_status": "active" if index % 7 else "dissolved",
                    "address_snippet": f"1 Demo Street, {city.title()}, {postcode}",
                    "address": {"locality": city.title(), "postal_code": postcode},
                }]
            }

    for key, payload in ch_payloads.items():
        cache.put_json("ch:search", key, payload)

    print(f"Seeded {DEMO_CACHE} with SYNTHETIC data for {len(rows)} rows:")
    for kind, n in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"   {kind:<14}{n:>4}")
    print(f"   Companies House records: {len(ch_payloads)}")
    print("\nNow run:")
    print("   COMPANIES_HOUSE_API_KEY=demo python3 enrich_leads.py \\")
    print("       --stages 1,2,3,4 --offline \\")
    print("       --cache .demo_cache/cache.sqlite --output demo_enriched.csv")
    print("\nReminder: this output is invented. Do not use it as research.")
    cache.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
