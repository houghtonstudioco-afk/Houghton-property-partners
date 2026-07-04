# Aeora Prospect Database

Master prospect list for Aeora's SEO / AEO / GEO outreach (£249+/month packages).
Targets: independent & regional UK businesses in London, Bristol and surrounding
high-value areas (Bath, Richmond, Clifton, Kensington, etc.) where one new
customer is worth hundreds or thousands of pounds.

## Files

| File | Purpose |
|---|---|
| `aeora_prospects.csv` | **Master table - the single source of truth.** All edits and new rows go here. |
| `aeora_prospects.xlsx` | Formatted Excel copy (filters, frozen header, priority colour-coding, summary sheet). Regenerated from the CSV - don't hand-edit. |
| `build_xlsx.py` | Rebuilds the .xlsx from the .csv: `python3 build_xlsx.py` (needs `pip install openpyxl`). |

## Workflow for adding new batches

1. Open `aeora_prospects.csv` (any spreadsheet app or text editor; keep CSV format).
2. Check the business isn't already listed (search by name and by website domain).
3. Append one row per new prospect using the 20 columns below. Only add
   businesses scoring **6/10 or higher**.
4. Run `python3 build_xlsx.py` to refresh the Excel copy.
5. Commit both files.

## Columns

1. Business name
2. Category
3. Location
4. Website
5. Contact email (use "via website contact form" if none published)
6. Phone number
7. Decision-maker name
8. LinkedIn
9. Instagram/Facebook
10. Why they are a good fit
11. Estimated ability to pay: Low / Medium / High
12. Website quality: Poor / Average / Good
13. SEO opportunity: Low / Medium / High
14. AEO/GEO opportunity: Low / Medium / High
15. Signs they may already pay for marketing
16. Possible pain point
17. Suggested outreach angle
18. Priority score /10 (only ≥6 gets added)
19. Date added (YYYY-MM-DD)
20. Notes

## Qualification rules

**Include:** independents/regionals relying on local leads, competitive markets,
high customer value (estate agents, clinics, dentists, law firms, accountants,
architects, trades, recruiters, vets, wedding venues, etc.), decent-but-not-amazing
websites, plausibly overpaying an old SEO agency.

**Exclude:** national chains, corporate-owned branches (Bupa, mydentist, Connells /
Sequence brands, CVS/Medivet vets…), cheap cafes, hobby businesses, no-website
businesses, dropshipping stores, anyone who obviously can't afford £249/month.

## Niches covered so far

- Batch 1 (2026-07-04): estate agents (Bristol), mortgage brokers (London),
- Batch 2 (2026-07-04): letting agents (Bristol), wedding venues (Cotswolds),
  cosmetic clinics (Bristol), pilates studios (Bristol), financial advisers
  (Bristol), private tutors (London), osteopaths (SW London), design & build
  firms (Bristol/Somerset).
  dentists (Bristol), law firms (Bristol), aesthetics clinics (London),
  architects (Bath/Bristol), physios (SW London), solar installers (Bristol),
  recruitment (Bristol), accountants (Bath), vets (London), interior design (London).

## Suggested next niches

- Letting agents (Bristol BS6/BS7, London zones 2-3)
- Cosmetic clinics & dental implant clinics (Bristol)
- Wedding venues & event companies (Cotswolds / Somerset / Surrey)
- Private tutors & tuition centres (London)
- Gyms / PT / pilates studios (Clifton, Chelsea, Richmond)
- Financial advisers / wealth managers (Bath, Bristol)
- Builders / premium home services (Surrey, Berkshire commuter belt)
- Care providers & nurseries (SW London)
- Osteopaths & chiropractors (London villages: Dulwich, Wimbledon, Hampstead)
- Business consultants & B2B services (Bristol)
