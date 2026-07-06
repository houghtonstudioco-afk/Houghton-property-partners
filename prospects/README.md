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
- Batch 15 (2026-07-04, 4 rows — database at 245): Horsham/Haywards Heath
  (West Sussex) estate agents, accountants, architects, dentists.
- Batch 16 (2026-07-04, 8 rows — database at 253): kitchen/bathroom design
  (Bath/Bristol/Surrey), removals (Bristol), funeral directors (Bristol/Bath),
  chiropractors/osteopaths (Guildford).
- Batch 17 (2026-07-04, 7 rows — database at 260): garden rooms (Bristol/
  Surrey), driveways/paving (Surrey), Somerset/Devon wedding venues, Tunbridge
  Wells IFA/mortgage broker.
- Batch 18 (2026-07-04, 5 rows — database at 265): Sevenoaks/Tunbridge Wells
  private GP, aesthetics, vets, personal training gyms.
- Batch 19 (2026-07-04, 4 rows — database at 269): Cotswolds market towns
  (Stow/Bourton/Chipping Norton) estate agents, Marlborough (Wiltshire) estate
  agents, wedding photography/videography (London/Surrey), Bristol commercial
  property litigation.
- Batch 20 (2026-07-04, 7 rows — database at 276): Whitstable/East Kent estate
  agents, Bristol architects, Sussex solar, Cheltenham/Cotswolds recruitment.
- Batch 21 (2026-07-04, 6 rows — database at 282): home cinema/AV installers
  (Surrey), curtains/soft furnishings (Bristol/Bath), Bristol wine merchant,
  London school-placement consultancy.
- Batch 22 (2026-07-04, 6 rows — database at 288): Epsom/Ashtead/Leatherhead
  estate agents, Surrey tutoring, Cotswolds/Gloucestershire wedding caterers.
- Batch 23 (2026-07-04, 7 rows — database at 295): Twickenham/Teddington
  estate agents, dentists, IFA, architects.
- Batch 24 (2026-07-04, 7 rows — database at 302): Richmond/Twickenham/
  Teddington private GPs, vets, personal training.
- Batch 25 (2026-07-04, 7 rows — database at 309): Kingston upon Thames/Surbiton estate agents, dentists, architects, accountants.
- Batch 26 (2026-07-04, 8 rows — database at 317): Bromley/Beckenham estate agents, dentists, accountants, architects.
- Batch 27 (2026-07-04, 9 rows — database at 326): Purley/South Croydon estate agents, Bromley/Beckenham GPs & vets, Surrey manor wedding venues.
- Batch 28 (2026-07-04, 6 rows — database at 332): Sutton/Cheam estate agents & dentists, Berkshire recruitment, SE London mortgage broker.
- Batch 29 (2026-07-04, 7 rows — database at 339): Reading/Wokingham estate agents, dentists, heritage architects, accountants.
- Batch 30 (2026-07-04, 8 rows — database at 347): Basingstoke estate agents/dentists/vets, Wokingham solar, Reading heating engineer.
- Batch 31 (2026-07-04, 8 rows — database at 355): Newbury estate agents & architects, Berkshire wedding venues (Hungerford/Maidenhead), Reading/Wokingham private GP.
- Batch 32 (2026-07-04, 8 rows — database at 363): Witney/Abingdon estate agents & dentists, Oxfordshire architects, Oxford accountants.
- Batch 33 (2026-07-04, 8 rows — database at 371): Banbury/Bicester estate agents & dentists, Oxfordshire vets, Aynho wedding venue.
- Batch 34 (2026-07-04, 8 rows — database at 379): Windsor/Maidenhead/Ascot estate agents, dentists, architects, IFA.
- Batch 35 (2026-07-04, 7 rows — database at 386): Amersham/Chesham (Bucks) estate agents & dentists, Ashford (Kent) estate agents, Amersham accountants.
- Batch 36 (2026-07-04, 8 rows — database at 394): dedicated recruitment/training/education push begins - healthcare recruitment, executive search, first aid training, teaching/supply agencies, construction recruitment, hospitality staffing.
- Batch 37 (2026-07-04, 6 rows — database at 400): finance recruitment, forklift/plant training, legal recruitment.
- Batch 38 (2026-07-04, 6 rows — database at 406): language school, engineering recruitment, business/sales coaching, HGV driver training.
- Batch 39 (2026-07-04, 4 rows — database at 410): Bristol tech recruitment, London/Surrey beauty & aesthetics training academies.
- Batch 40 (2026-07-05, 3 rows — database at 413): London medical aesthetics training, Bristol yoga teacher training, London creative/marketing recruitment.
- Batch 41 (2026-07-05, 6 rows — database at 419): Cotswolds & Kent architects and interior designers.
- Batch 42 (2026-07-05, 6 rows — database at 425): Cheltenham & Oxford private GP, dermatology and aesthetics clinics.
- Batch 43 (2026-07-05, 3 rows — database at 428): Cheltenham, Oxford & Windsor/Ascot independent estate agents.
- Batch 44 (2026-07-05, 2 rows — database at 430): Bristol & West London ADI driving-instructor training schools.
- Batch 45 (2026-07-05, 5 rows — database at 435): Kent, Hampshire, Wiltshire & Oxfordshire independent wedding barns/estates.
- Batch 46 (2026-07-05, 4 rows — database at 439): Surrey, Kent & Oxford independent IFAs and mortgage brokers.
- Batch 47 (2026-07-05, 3 rows — database at 442): Surrey, Kent & Oxfordshire independent vets.
- Batch 48 (2026-07-05, 5 rows — database at 447): Bristol, Bath & Surrey independent conveyancing solicitors.
- Batch 49 (2026-07-05, 6 rows — database at 453): Kent, Hampshire & Oxfordshire solar/heat pump installers.
- Batch 50 (2026-07-05, 6 rows — database at 459): Richmond, Cheltenham & Oxford independent gyms/Pilates/yoga studios.
- Batch 51 (2026-07-05, 5 rows — database at 464): London boutique immigration & private-client (HNW estate planning) law firms.
- Batch 52 (2026-07-05, 6 rows — database at 470): Surrey, Kent, Berkshire & Oxfordshire independent home care providers.
- Batch 53 (2026-07-05, 5 rows — database at 475): North London, Surrey & Bristol independent nurseries and tutors.
- Batch 54 (2026-07-05, 5 rows — database at 480): Surrey, Hertfordshire, Buckinghamshire & Berkshire independent IFAs/wealth managers.
- Batch 55 (2026-07-05, 5 rows — database at 485): Bristol, Bath, Reading & Oxford independent IT support MSPs and business consultants.
- Batch 56 (2026-07-05, 6 rows — database at 491): Bath & Cotswolds heritage trades (lime plastering, sash-window joinery, conservation building).
- Batch 57 (2026-07-05, 5 rows — database at 496): Surrey & Kent independent chiropractors, osteopaths and physiotherapists.
- Batch 58 (2026-07-05, 4 rows — database at 500): Buckinghamshire & Kent independent builders, roofers and electricians.
- Batch 59 (2026-07-05, 3 rows — database at 503): Cheltenham, Guildford & Esher independent dental/implant practices.
- Batch 60 (2026-07-05, 4 rows — database at 507): Winchester, Henley-on-Thames & Marlow independent estate agents, interior designers and aesthetics clinics.
- Batch 61-62 (2026-07-05, 6 rows — database at 513): Hampstead/Highgate estate agents, Notting Hill dentist & interior designer, Greenwich/Blackheath Pilates studio.
- Batch 63-64 (2026-07-05, 4 rows — database at 517): Bristol independent vets, Bath mortgage broker, Richmond private GP, Surrey/Cotswolds wedding barns.
- Batch 65 (2026-07-05, 4 rows — database at 521): Cotswolds/Cheltenham independent care homes, Guildford business consultancy.
- Batch 66 (2026-07-05, 2 rows — database at 523): Cheltenham & Oxfordshire independent chartered accountants.
- Batch 67 (2026-07-05, 2 rows — database at 525): Sussex/Kent/Cotswolds landscape designers, West Sussex solar installer.
- Batch 68 (2026-07-05, 6 rows — database at 531): Wimbledon & Dulwich independent tutors and nurseries.
- Batch 69 (2026-07-05, 6 rows — database at 537): Richmond & Wimbledon independent architects and interior designers.
- Batch 70 (2026-07-05, 6 rows — database at 543): Guildford & Sevenoaks independent medical aesthetics clinics.
- Batch 71 (2026-07-05, 4 rows — database at 547): Bristol & Bath independent IFAs/wealth managers and a leadership consultancy.
- Batch 72 (2026-07-05, 4 rows — database at 551): Surrey & Kent independent care homes and home care agencies.
- Batch 73 (2026-07-05, 5 rows — database at 556): Weybridge, Cobham & Esher independent estate agents.
- Batch 74 (2026-07-05, 3 rows — database at 559): Notting Hill, Islington & Kensington independent fitness studios.
- Batch 75 (2026-07-05, 6 rows — database at 565): Richmond & Wimbledon independent dental practices.
- Batch 76 (2026-07-05, 4 rows — database at 569): Guildford & Woking independent IT support MSPs.
- Batch 77 (2026-07-06, 4 rows — database at 573): Cheltenham & Bath independent physiotherapy and Pilates studios.
- Batch 78 (2026-07-06, 6 rows — database at 579): Bath & Bristol independent architects and interior designers.
- Batch 79 (2026-07-06, 5 rows — database at 584): Sevenoaks & Tunbridge Wells independent 11+/entrance-exam tutors.
- Batch 80 (2026-07-06, 6 rows — database at 590): Oxfordshire independent IFAs/wealth managers and architects.
- Batch 81 (2026-07-06, 4 rows — database at 594): Cheltenham & Bath independent gyms and fitness studios.
- Batch 82 (2026-07-06, 2 rows — database at 596): Windsor/Maidenhead/Ascot independent vets.
- Batch 83 (2026-07-06, 2 rows — database at 598): Maidenhead independent dental practices.
- Batch 84 (2026-07-06, 2 rows — database at 600): Reigate independent solicitors.

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
