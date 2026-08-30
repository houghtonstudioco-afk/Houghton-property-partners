# Running the pipeline with real network access

The pipeline is complete and tested. It has never been run against the live
web, because the cloud environment it was built in uses **Trusted** network
access, which allows package registries and GitHub but not arbitrary company
websites or the Companies House API.

## Option A - fix the cloud environment (recommended for cloud sessions)

1. Open <https://claude.ai/code>
2. Click the cloud icon showing the environment name, in the row above the
   message box. There is no settings page or direct URL for this selector.
3. Hover the environment, click the gear icon.
4. Set **Network access** to **Full**.
5. Save, then start a **new** session. A running session keeps the network
   policy it booted with.

**Full** rather than **Custom**: stage 2 fetches company domains that stage 1
has not discovered yet, so they cannot be allowlisted in advance. Custom would
only cover the two APIs.

## Option B - run it locally (fastest)

```bash
git clone -b claude/enrich-gas-oil-csv-1iyg92 \
  https://github.com/houghtonstudioco-afk/houghton-property-partners.git
cd houghton-property-partners
pip install -r requirements.txt
cp .env.example .env      # add COMPANIES_HOUSE_API_KEY, optionally a search key
python -m unittest discover -s tests -t . -q
python enrich_leads.py --stages 1 --limit 10   # check the URLs by hand first
python enrich_leads.py --stages all --export-webdev --export-outreach
```

## Verifying access before a long run

```bash
curl -sS -o /dev/null -w '%{http_code}\n' https://api.company-information.service.gov.uk/search/companies?q=test
```

401 means the network is fine and the key is missing or wrong. 000 with a
CONNECT/proxy error means egress is still blocked. The pipeline itself aborts
after 12 consecutive proxy failures rather than spending an hour marking every
company unreachable.

## Budget

- Brave free tier is 2,000 queries/month; the pipeline uses roughly 3 per
  company, so ~530 for the full list.
- Responses are cached for 14 days, so re-runs and stage reruns cost nothing.
- A full run at the polite 1-2s delay takes roughly 2-2.5 hours.
