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

- Batch 1 (2026-07-04, 24 rows): estate agents (Bristol), mortgage brokers (London),
  dentists (Bristol), law firms (Bristol), aesthetics clinics (London),
  architects (Bath/Bristol), physios (SW London), solar installers (Bristol),
  recruitment (Bristol), accountants (Bath), vets (London), interior design (London).
- Batch 2 (2026-07-04, 16 rows): letting agents (Bristol), wedding venues (Cotswolds),
  cosmetic clinics (Bristol), pilates studios (Bristol), financial advisers
  (Bristol), private tutors (London), osteopaths (SW London), design & build
  firms (Bristol/Somerset).
- Batch 3 (2026-07-04, 60 rows — database at 100): private GPs (London/Bristol),
  roofers/heating/electricians (Bristol/Bath), caterers (London), home care
  (Bristol), nurseries (Bristol), PT studios (Chelsea/Kensington), family law
  (London/Bath), chiropractors (Hampstead), mortgage brokers (Bristol), vets
  (Bristol), estate & letting agents (Dulwich/Richmond/Bath/N16), dentists &
  orthodontists (Fulham/City), interior designers (Bath), garden/landscape
  design (Surrey/Cotswolds), architects (Richmond/Surrey), gyms & physios
  (Bristol), aesthetics clinics (Richmond), solar (Surrey), tutors (Bristol),
  recruitment (London), business consultants (Bristol).
- Batch 4 (2026-07-04, 28 rows — database at 128): Wimbledon/Chiswick estate agents,
  employment law (London), surveyors (London), Bath dentists & physios, Surrey
  builders, SW London nurseries, Bath recruiters, osteopaths (Bristol), events
  agencies (London), IFA (Wimbledon), premium plumbers (Chelsea).
- Batch 5 (2026-07-04, 31 rows — database at 159): Cheltenham estate agents,
  dentists & aesthetics clinics, Oxford estate agents & mortgage brokers,
  Cotswolds architects (Cheltenham/Tewkesbury), Guildford/Surrey vets, Bath
  heritage trades (sash windows), Bristol IT/MSP support, Cheltenham personal
  training studios, N London nurseries (Highgate/Islington), Surrey/Oxfordshire
  live-in care, Kent & Hampshire wedding venues, immigration law firms (London),
  Bristol conveyancing solicitors, Cotswolds/Broadway private GP membership group.
- Batch 6 (2026-07-04, 15 rows — database at 174): Henley/Marlow/Beaconsfield
  estate agents & IFAs, Blackheath & Notting Hill estate agents, Winchester
  dentists, Henley architects, Guildford private GP, Oxfordshire/Cotswolds
  wedding venues (Bicester, Chipping Norton).
- Batch 7 (2026-07-04, 12 rows — database at 186): Tunbridge Wells & Sevenoaks
  estate agents/dentists/accountants/physios/vets, St Albans estate agents/
  accountants/physios/architects.
- Batch 8 (2026-07-04, 11 rows — database at 197): Cobham/Virginia Water/
  Beaconsfield/Chalfont St Giles estate agents, Weybridge dentists & aesthetics
  clinics, Weybridge/Esher/Cobham vets & architects.
- Batch 9 (2026-07-04, 9 rows — database at 206): Guildford/Weybridge
  recruitment & wealth management/IFA, Surrey electricians & roofers,
  Wiltshire wedding venues (Salisbury/Downton).
- Batch 10 (2026-07-04, 8 rows — database at 214): Guildford/Godalming,
  Reigate/Redhill/Dorking, Wandsworth/Balham/Clapham, Ealing estate agents.
- Batch 11 (2026-07-04, 6 rows — database at 220): Balham/Chiswick dentists,
  Balham physio, Battersea/Wandsworth architects.
- Batch 12 (2026-07-04, 8 rows — database at 228): independent opticians
  (Chelsea/Clerkenwell/Fulham), Canterbury/Maidstone estate agents, North
  Somerset (Portishead/Nailsea/Clevedon) estate agents, London dermatology.
- Batch 13 (2026-07-04, 7 rows — database at 235): Primrose Hill/St John's
  Wood/South Kensington estate agents, Guildford/Weybridge pilates studios.
- Batch 14 (2026-07-04, 6 rows — database at 241): Guildford nursery & IT/MSP
  support, East London wills/probate solicitors, Surrey business consultancy.

## Suggested next niches (pool for future batches — rotate through these)

Geographies still under-covered: Cheltenham, Oxford, Windsor/Ascot, Sevenoaks,
St Albans, Tunbridge Wells, Esher/Cobham, Henley, Marlow, Winchester,
Hampstead/Highgate, Notting Hill, Islington, Greenwich/Blackheath.

- Immigration & private-client solicitors (London)
- Conveyancing firms (Bristol, Bath, Surrey)
- Accountants & tax advisers (London villages, Cheltenham, Oxford)
- IFAs & mortgage brokers (Surrey, Kent, Oxford)
- Estate/letting agents (all under-covered geographies above)
- Dentists, orthodontists, implant clinics (Cheltenham, Oxford, Surrey, N London)
- Private GPs, dermatology, physio, osteo, chiro (all geographies)
- Vets (Surrey, Kent, Oxfordshire)
- Aesthetics clinics (Cheltenham, Marlow, Esher)
- Architects, interior designers, landscape designers (Cotswolds, Kent, Bucks)
- Builders, roofers, electricians, heating, driveways, windows (premium areas)
- Solar & heat pump installers (Kent, Hampshire, Oxfordshire)
- Wedding venues & caterers (Kent, Hampshire, Wiltshire, Oxfordshire)
- Nurseries, tutors, tuition centres (N London, Surrey, Bristol suburbs)
- Care providers & retirement services (Home Counties)
- Recruitment agencies (Reading, Oxford, Cheltenham)
- Gyms, PT, pilates, yoga studios (all geographies)
- Business consultants, marketing-adjacent B2B, IT support MSPs (regional)
- Wealth managers & private banks' independent rivals (Home Counties)
- Specialist trades: lime plastering, sash windows, listed-building joinery (Bath/Cotswolds)
