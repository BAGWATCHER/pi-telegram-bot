# Craigslist -> Chow Pilot Plan

Updated: 2026-04-24
Status: manual-first supervised pilot

## Why this lane exists
Craigslist job posts expose live operator pain:
- payroll
- AP / AR
- data entry
- admin assistant
- dispatcher

That pain can be converted into a practical first-touch automation offer from Chow.

## Current reality
- Craigslist RSS fetches from the Azure VM are still returning `403 Forbidden`.
- Because of that, the active pilot should **not** wait on automated RSS ingest.
- The lane should run `manual_first` until a non-datacenter fetch path or proxy is added.

## Pilot wedge
Target small-business back-office pain where the pitch is concrete:
- payroll workflow cleanup
- invoice / bill ingestion automation
- collections follow-up automation
- intake -> CRM sync
- scheduling / dispatch automation

Avoid broad "AI transformation" language.

## Working lane now
1. Manually import qualified Craigslist opportunities into DemandGrid.
2. Queue them for supervised review.
3. Review the generated Chow draft.
4. Dispatch the outreach email as Chow.
5. Watch replies in `chow@optimizedworkflow.dev`.

## API flow
1. Import opportunities
   - `POST /api/v1/signals/jobs/craigslist/import`
2. List scored opportunities
   - `GET /api/v1/signals/jobs/craigslist`
3. Queue one for outreach
   - `POST /api/v1/signals/jobs/craigslist/opportunity/{opportunity_id}/queue-outreach`
4. Inspect queue record
   - `GET /api/v1/signals/jobs/craigslist/outreach-queue/{queue_id}`
5. Dispatch the Chow email
   - `POST /api/v1/signals/jobs/craigslist/outreach-queue/{queue_id}/dispatch`

## Good first pilot size
- 5 to 10 opportunities
- Boston + Providence first
- only postings with a clear ops/admin pain angle
- only records with at least one usable contact email

## Good first send criteria
- automation score >= 0.70
- role family is `payroll_finance_admin` or `backoffice_data_ops`
- company name is usable
- contact hint email exists
- pitch can name a plausible first workflow win

## Not ready yet
- automatic inbox ingestion from Zoho into DemandGrid
- full email thread sync / reply drafting in-app
- RSS ingest from Azure without a non-datacenter path

## Next follow-on lane
1. Zoho inbound sync for `chow@optimizedworkflow.dev`
2. DemandGrid thread tracking for Craigslist outreach
3. supervised reply drafting as Chow
4. optional proxy / residential fetch path for Craigslist RSS
