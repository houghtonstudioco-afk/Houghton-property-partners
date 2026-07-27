# Lead enrichment pipeline

Enriches `gas_oil_engineering_leads.csv` (176 UK gas, oil and industrial
engineering companies) with live web signals, Companies House numbers and a
rescored lead score.

The input file is opened read-only and never written to. All output goes to
`gas_oil_engineering_leads_enriched.csv`.

## Install

```bash
pip install -r requirements.txt
cp .env.example .env      # then fill in your keys
```

`.env` is gitignored. Nothing reads a hardcoded credential.

| Variable | Stage | Needed? |
|---|---|---|
| `COMPANIES_HOUSE_API_KEY` | 3 | Required for stage 3 (free, [register here](https://developer.company-information.service.gov.uk/)) |
| `BRAVE_SEARCH_API_KEY` | 1 | One search provider strongly recommended |
| `SERPER_API_KEY` | 1 | Alternative to Brave |
| `GOOGLE_CSE_KEY` + `GOOGLE_CSE_CX` | 1 | Alternative to Brave |

With no search key set, stage 1 falls back to scraping DuckDuckGo's HTML
endpoint plus domain guessing. That works, but DDG rate-limits aggressively and
the hit rate is materially lower. Brave's free tier (2,000 queries/month)
covers this list comfortably.

## Run

```bash
python enrich_leads.py --stages all          # everything, ~50-70 min
python enrich_leads.py --stages 1            # just website discovery
python enrich_leads.py --stages 2,4          # audit then rescore
python enrich_leads.py --stages 1 --limit 10 # test on 10 rows first
python enrich_leads.py --stages 4            # rescore only, no network
python enrich_leads.py --stages 2 --offline  # replay from cache, no requests
python enrich_leads.py --report              # summarise current output
```

**Start with `--limit 10`.** Check the discovered URLs by hand before spending
an hour on the full list.

Stages are independent and resumable. Every stage reloads the output CSV if it
exists, so an interrupted run picks up where it stopped and re-running a stage
skips rows that already have values. `Ctrl-C` checkpoints before exiting.

## The four stages

### 1 — Website discovery

Queries the configured search provider with name + location, and independently
constructs candidate domains from the company name (`thegaspro.co.uk`,
`gas-pro.co.uk`, …). Directory and social hosts (Yell, Checkatrade, Facebook,
Gas Safe Register, …) are discarded before scoring.

Every surviving candidate is then fetched and scored against the row's own
verified data. Nothing is written to `Website` unless it clears the gate:

| Evidence | Points |
|---|---|
| The row's verified phone number appears in the page source | +5 |
| Strong company-name match in `<title>` / `og:site_name` | +3 |
| Moderate name match | +2 |
| The Location town appears on the page | +2 |
| Domain closely resembles the company name | +2 |
| Domain loosely resembles the company name | +1 |
| Page looks parked or placeholder | −3 |
| Free site-builder host (Wix, Weebly, `business.site`, …) | −2 |

Acceptance needs ≥5 points **and** either a phone match, or a name match
corroborated by town or domain. A phone match alone is near-conclusive and
records `high` confidence; name+town without a phone records `medium`.

Anything else leaves `Website` blank and logs why. This is deliberate — per
your instruction, a blank costs you one manual lookup, whereas a wrong domain
silently corrupts stages 2 and 4.

### 2 — Site audit

One request to the homepage, plus the linked contact page when there is one.
Records:

- **HTTP status** and a `Site Health` verdict: `ok`, `insecure`, `broken`,
  `placeholder`, `unreachable`
- **TLS**: expired, hostname mismatch, self-signed, untrusted chain. Expired
  certificates are detected by reading the certificate directly, so the exact
  expiry date is available, and the page is still audited over the bad
  connection so its other signals are not lost.
- **Live chat**: Intercom, Drift, Tawk.to, Crisp, LiveChat, Zendesk, HubSpot
  chat (plus Olark, Freshchat, Smartsupp, Chatra, Tidio, WhatsApp)
- **Online booking**: Calendly, Acuity, Cal.com, SimplyBook, Setmore,
  YouCanBookMe, Housecall Pro, ServiceM8, Commusoft, or a `/book` `/booking`
  `/schedule` `/appointment` route in the site's own navigation
- **CRM**: HubSpot, Salesforce/Pardot, Pipedrive, Zoho
- **Outdated score 1–10** (see below)
- **Contact method**: `form`, `mailto`, `phone` or `none`. Search boxes are
  excluded — a `role="search"` form is not a contact form. Embedded third-party
  forms (Google Forms, Jotform, Typeform, Gravity Forms, …) count as forms.

Outdated score, capped to 1–10:

| Signal | Points |
|---|---|
| No responsive `meta viewport` | +3 |
| jQuery with no modern framework/bundler | +2 |
| jQuery 1.x specifically | +1 |
| Table-based layout (nested tables or `cellpadding`/`bgcolor`) | +2 |
| Six or more layout tables | +1 |
| Legacy tags (`<font>`, `<center>`, `<marquee>`, framesets) | +1 |
| Flash remnants (`.swf`, `swfobject`, shockwave embeds) | +2 |
| Copyright year 5+ years stale | +2 |
| Copyright year 2–4 years stale | +1 |
| No HTTPS | +2 |
| HTTPS with an invalid certificate | +2 |

Which signals fired is recorded per row in `Outdated Signals`, so a score is
always auditable rather than a bare number.

### 3 — Companies House

Searches `/search/companies` and applies two independent gates before writing a
number:

1. **Name**: similarity ≥ 0.72 after stripping `LIMITED`/`LTD`/`PLC`/`HOLDINGS`
   etc. Two firms that share only generic trade words (`gas`, `engineering`,
   `services`) are explicitly rejected — that check exists because raw string
   similarity rates "Smith & Sons Gas Engineers" against "Jones Gas Engineers"
   at 0.79, comfortably above threshold.
2. **Address**: the registered-office town matches your `Location`, **or** the
   registered postcode area maps to the same city. The postcode fallback is
   there because your Location column mixes granularity — a company filed at
   "Hengrove, BS14" is the Bristol company you meant.

`Companies House Match Basis` records which gate carried the match, so
postcode-only matches remain auditable. Active companies are preferred over
dissolved ones, and a dissolved match is written but flagged in the failure log.
Scottish and NI prefixes (`SC`, `NI`, `OC`) are preserved; plain numeric numbers
are zero-padded to 8 digits.

Unmatched rows are left blank and the reason recorded — typically *"name matched
3 companies but none registered in 'Bury, Manchester'"*, which is exactly the
wrong-company failure the address gate exists to prevent.

### 4 — Rescore

`Lead Score /100` measures **unmet need, not company quality**. A firm with live
chat, online booking, a modern site and a CRM has already solved the problem
being sold, so it scores near zero.

| Component | Max | Full points when |
|---|---|---|
| Site presence & health | 28 | No site, or DNS failure / 404 / 5xx |
| No live chat | 18 | No chat widget found |
| Outdated technology | 18 | Outdated score 10/10 |
| No online booking | 14 | No booking tool or route |
| Contact friction | 12 | Form-only, or no contact route at all |
| No CRM | 10 | No CRM tracking script |

Health bands within the 28: no site / unreachable 28, broken 26, invalid TLS 24,
placeholder 22, http-only 20, healthy 0.

Contact friction: none 12, **form-only 12**, mailto 9, phone 7. Form-only scores
at the top because enquiries queue in an inbox with nobody answering live —
which is the pitch.

`Lead Score Breakdown` shows the arithmetic per row. `Lead Score Confidence` is
`high` when the site was actually audited, `low` when no website was found and
the stage-2 components had to be inferred.

**Companies with no website score ~91, not 100.** A live-but-terrible site can
score higher than no site at all, because a dated site with no chat, no booking
and no CRM evidences all six components while a missing site only evidences
presence. Sort by `Lead Score Confidence` alongside the score.

## Output columns

The 24 original columns keep their exact names and order, so existing sheet
formulas and CRM import mappings still line up. 21 columns are appended.

Blank original columns that get filled: `Website`, `Companies House Number`,
`Uses CRM (unverified)`, `Online Booking (unverified)`,
`Live Chat (unverified)`, `Website Outdated Score (unverified)`.

The `(unverified)` headers are left as-is on purpose — the values in them are
now verified, but renaming a header breaks every downstream mapping. Treat those
four as verified once `Site Checked At` is populated.

`Lead Score /100` is overwritten in stage 4 (the one overwrite authorised). The
pre-existing value is preserved in `Lead Score (Original)` so you can diff.
Every other non-blank value is protected: writes go through a single
`set_if_blank` choke point rather than direct assignment.

## Politeness

- 1–2 s randomised delay between requests, enforced globally **and** per host
- `robots.txt` fetched, cached for 7 days and honoured; disable with
  `--ignore-robots` if you have a reason
- Identifiable user agent with a contact address, overridable via
  `LEADGEN_USER_AGENT`
- Two retries with escalating backoff for transient failures only, never for 4xx
- HTTP 429 respected via `Retry-After`
- Every response cached in `.enrichment_cache/cache.sqlite` for 14 days, so
  re-runs and stage reruns cost nothing. Failures are cached too — a re-run does
  not re-attempt 176 dead domains.

**One exception, stated plainly:** `robots.txt` is honoured for company
websites, but the DuckDuckGo fallback in stage 1 requests `/html/`, which DDG's
own robots.txt disallows. That path is a best-effort fallback for users without
a search key. Set a search API key and stage 1 uses a sanctioned API instead.

## Failure log

Every failure is appended to `enrichment_failures.log` as
`timestamp | stage | row | company | code | detail`:

```
2026-07-27T14:22:07+0100 | stage1 | 47 | Ace Gas Services | website_not_found | best=https://acegas.co.uk/ insufficient_evidence(score=2) evidence=name-moderate(0.71)
2026-07-27T14:31:55+0100 | stage2 | 12 | Northern Pipework | ssl_expired | https://northernpipework.co.uk -> ssl_error: certificate has expired
2026-07-27T14:48:02+0100 | stage3 | 63 | MCR Gas | ch_no_verified_match | location='Bury, Manchester' name matched 3 companies but none registered in 'Bury, Manchester'
```

Useful triage:

```bash
grep website_not_found enrichment_failures.log | wc -l
grep -E 'ssl_|dns_error|timeout' enrichment_failures.log     # strongest prospects
grep ch_no_verified_match enrichment_failures.log            # need manual CH lookup
cut -d'|' -f5 enrichment_failures.log | sort | uniq -c | sort -rn
```

A row appearing in this log is not a bug — `website_not_found` is the pipeline
correctly refusing to guess.

## Tests

```bash
python -m unittest discover -s tests -t . -v
```

85 tests, no network required. HTTP responses are seeded into the cache, so the
full pipeline runs end to end against known-good fixture pages covering each
site archetype in this dataset: a modern well-equipped site, a table-layout
jQuery site with Flash remnants, a phone-only single-pager, a parked domain, a
directory listing, and a same-trade different-company page that must be
rejected.

## Known limitations

- **Certificate detection needs a direct connection.** Behind an intercepting
  TLS proxy the proxy's own certificate is what gets inspected, which masks
  expired origin certificates. Run stage 2 somewhere with direct egress.
- Signals are detected in server-rendered HTML. A chat widget injected only by
  a consent manager after user interaction will not be seen, which biases
  `Live Chat` slightly toward false negatives — conservative in the right
  direction here, since a false negative inflates a lead score rather than
  hiding a prospect.
- Companies House search is fuzzy free text. Companies registered at an
  accountant's address in another town will fail the address gate and stay
  blank by design.
- Domain guessing is UK-TLD biased (`.co.uk` first, then `.com`).
