# DemandGrid

## Quickstart

```bash
cd /home/ubuntu/pi-telegram-bot/factory/projects/energy-zillow
cp .env.example .env   # optional but required for PVWatts/NSRDB mode
# optional fresh ingest for one ZIP
./scripts/ingest_zip_osm.py --zip 01730 --half-span-deg 0.02 --min-records 80
./scripts/score_sites.py --solar-model proxy
# trigger contract / external trigger merge adapter
python3 scripts/fetch_nws_storm_triggers.py
python3 scripts/fetch_eversource_outage_feed.py --output data/raw/state_outage_feed.csv
# optional outage projection (state feed -> site rows)
python3 scripts/project_state_outage_triggers.py --state-feed data/raw/state_outage_feed.csv || true
# optional flood projection (NWS flood-focused alerts -> site rows)
python3 scripts/project_nws_flood_triggers.py || true
# optional FEMA parcel/site floodplain overlay (authoritative lane)
python3 scripts/fetch_fema_floodplain_site_feed.py --zips 01730,02667,05486,06525 || true
python3 scripts/project_fema_floodplain_triggers.py --floodplain-feed data/raw/fema_floodplain_site_feed.csv || true
# optional equipment-age projection (Census ZIP median-year-built proxy -> site rows)
python3 scripts/project_census_equipment_age_triggers.py || true
# optional parcel permit-history overlay (examples: Boston + Cambridge + Providence)
python3 scripts/fetch_boston_permit_feed.py --zips 02118 --output data/raw/parcel_permit_feed.csv || true
python3 scripts/fetch_cambridge_permit_feed.py --zips 02139 --output data/raw/parcel_permit_feed.csv || true
python3 scripts/fetch_providence_permit_feed.py --zips 02903 --output data/raw/parcel_permit_feed.csv || true
python3 scripts/project_parcel_permit_triggers.py --permit-feed data/raw/parcel_permit_feed.csv || true
# optional utility/tariff baseline (OpenEI utility rates; uses OPENEI_API_KEY or PVWATTS key if provided)
python3 scripts/fetch_openei_utility_tariff_feed.py --output data/raw/utility_tariff_feed.csv || true
python3 scripts/project_utility_tariff_baseline.py --tariff-feed data/raw/utility_tariff_feed.csv || true
python3 scripts/merge_property_triggers.py --external data/raw/property_triggers_external.csv
# optional PVWatts path (requires valid PVWATTS_API_KEY)
./scripts/check_pvwatts_key.py
./scripts/score_sites.py --solar-model pvwatts-cell-blend
./scripts/export_openapi.py
python3 eval/run_eval.py
# regression run across current New England baseline ZIPs
python3 eval/run_multi_zip_regression.py --zips 01730,02667,05486,06525 --solar-model pvwatts-cell-blend
# one-command demo prep + API launch (preferred)
./scripts/demo_recording_runbook.sh
# auto-record demo video (Playwright)
python3 scripts/record_demo.py --output artifacts/demo-recording-auto.mp4
# manual API launch alternative
python3 -m uvicorn backend.api.app:app --host 127.0.0.1 --port 8099
```

## API Endpoints
- `GET /health`
- `GET /api/v1/zip/{zip}/heatmap`
- `GET /api/v1/heatmap`
- `GET /api/v1/hex/{h3}/sites`
- `GET /api/v1/site/{site_id}`
- `GET /api/v1/investigation/site/{site_id}`
- `GET /api/v1/outreach/policy`
- `GET /api/v1/outreach/site/{site_id}`
- `GET /api/v1/outreach/payloads`
- `GET /api/v1/agent/capabilities`
- `POST /api/v1/agent/chat`
- `GET /api/v1/operator/status`
- `GET /api/v1/operator/status/{site_id}`
- `PUT /api/v1/operator/status/{site_id}`
- `GET /api/v1/operator/route-plan`
- `GET /api/v1/operator/route-plan.csv`
- `GET /api/v1/revenue-graph/site/{site_id}`
- `GET /api/v1/revenue-graph/account/{account_id}`
- `GET /api/v1/revenue-graph/contact/{contact_id}`
- `GET /api/v1/signals/site/{site_id}`
- `GET /api/v1/signals/coverage`
- `POST /api/v1/signals/jobs/craigslist/refresh`
- `GET /api/v1/signals/jobs/craigslist`
- `GET /api/v1/signals/jobs/craigslist/opportunity/{opportunity_id}`
- `POST /api/v1/signals/jobs/craigslist/opportunity/{opportunity_id}/research-refresh`
- `POST /api/v1/signals/jobs/craigslist/import`
- `GET /api/v1/signals/jobs/craigslist/outreach-queue`
- `GET /api/v1/signals/jobs/craigslist/outreach-queue/{queue_id}`
- `PUT /api/v1/signals/jobs/craigslist/outreach-queue/{queue_id}/review`
- `POST /api/v1/signals/jobs/craigslist/opportunity/{opportunity_id}/queue-outreach`
- `POST /api/v1/signals/jobs/craigslist/outreach-queue/{queue_id}/dispatch`
- `GET /api/v1/decision/site/{site_id}`
- `POST /api/v1/decision/batch`
- `GET /api/v1/schema/sales-core`
- `GET /api/v1/schema/vertical/{vertical_id}`
- `POST /api/v1/playbooks/compile`
- `GET /api/v1/playbooks/{playbook_id}`
- `POST /api/v1/agents/outreach/jobs`
- `GET /api/v1/agents/outreach/jobs/{job_id}`
- `POST /api/v1/agents/outreach/events`
- `GET /api/v1/inbox/status`
- `GET /api/v1/inbox/threads`
- `GET /api/v1/inbox/threads/{thread_id}`
- `POST /api/v1/inbox/import`
- `POST /api/v1/inbox/poll`
- `POST /api/v1/agents/calling/sessions`
- `GET /api/v1/agents/calling/sessions/{session_id}`
- `POST /api/v1/agents/calling/events`
- `POST /api/v1/orchestrator/runs`
- `GET /api/v1/orchestrator/runs/{run_id}`
- `POST /api/v1/orchestrator/actions/{action_id}/approve`
- `POST /api/v1/outcomes`
- `GET /api/v1/outcomes/summary`
- `POST /api/v1/learning/retrain-jobs`
- `GET /api/v1/governance/policies`
- `POST /api/v1/governance/policies/validate`
- `GET /api/v1/manager/command`

## Current data mode
- Real OSM-derived site ingest is active (latest baseline uses New England ZIPs `01730`, `02667`, `05486`, `06525`).
- Still not authoritative parcel-grade production data; upgrade path remains city/county parcel + roof/shading enrichment.
- Economics outputs are screening-grade estimates; see `artifacts/economics-field-glossary.md` for field meanings.
- Outreach guardrails/channels are now config-driven via `config/outreach_policy.json` (product-lane confidence thresholds + channel map).

## AI copilot mode
- Frontend includes an `AI Copilot` panel using `pi-tool-router-v1`.
- Copilot is currently **grounded tool-routing** (no external LLM dependency in default path).
- It can rank leads, explain a site, plan routes, summarize heatmap scope, and update workflow status (`mark site_x contacted`).
- Wave-2 playbook compiler scaffold is live locally via `POST /api/v1/playbooks/compile` to turn site context into executable next-step workflows with guardrails.
- Outreach connector scaffold is also live locally via `POST /api/v1/agents/outreach/jobs` with persisted job state, idempotency, and policy-safe blocking for suppressed leads.
- Calling connector scaffold is live locally via `POST /api/v1/agents/calling/sessions` with pre-call brief generation, live session state, and lead-outcome sync on qualifying events.
- Orchestrator scaffold is live locally via `POST /api/v1/orchestrator/runs` with deterministic action graphs, approval gating, and idempotent run creation.
- Learning loop scaffold is live locally via `POST /api/v1/outcomes` and `POST /api/v1/learning/retrain-jobs` with attribution-aware summaries and promotion safety checks.
- Governance + manager scaffold is live locally via `GET /api/v1/governance/policies` and `GET /api/v1/manager/command` with role validation, approval gating, and queryable audit-aware control surfaces.

## Live email adapter
- DemandGrid now supports a real `resend` email adapter for supervised outreach dispatch.
- Required env vars:
  - `RESEND_API_KEY`
  - `EMAIL_FROM`
  - optional: `EMAIL_REPLY_TO`
- Optional inbox / reply-ingestion env vars for IMAP polling:
  - `MAILBOX_PROVIDER` (`imap` or `zoho_imap` when ready)
  - `MAILBOX_IMAP_HOST`
  - `MAILBOX_IMAP_PORT`
  - `MAILBOX_IMAP_USERNAME`
  - `MAILBOX_IMAP_PASSWORD`
  - `MAILBOX_IMAP_MAILBOX`
- Live send still depends on:
  - a lead having `primary_email`
  - a supervisor dispatching with `promote_to_live=true`
  - a permitted actor role per `config/dispatch_adapters.json`

## Craigslist research pipeline
- The active pilot scope is now NH-centered New England via `config/craigslist_job_signal_config.json` (`nh`, `boston`, `worcester`, `maine`, `providence`, `vermont`).
- Raw signals still land in `data/processed/craigslist_job_signals.json`.
- Company enrichment now runs via `scripts/enrich_craigslist_opportunities.py` and writes `data/processed/craigslist_company_research.json`.
- Operator feedback memory now lives in `data/processed/craigslist_research_feedback.json`; bad company matches can be suppressed so future enrichment runs avoid known-wrong hosts.
- Email thread state now lives in `data/processed/email_threads.json`, and mailbox poll history lives in `data/processed/mailbox_sync_state.json`.
- The dashboard now includes a Craigslist review lane in the workspace detail panel with:
  - research visibility
  - contact-path transparency
  - editable Chow drafts
  - operator review labels
  - send / reply state visibility
  - imported inbox thread history on the selected queue record
  - manual pasted-reply import for thread testing / operator triage
  - one-click Chow inbox poll when IMAP credentials are configured
  - one-click `Rerun Chow research` for the selected opportunity
  - dispatch from the reviewed queue record
- Example run:

```bash
cd /home/ubuntu/pi-telegram-bot/factory/projects/energy-zillow
python3 scripts/enrich_craigslist_opportunities.py --market-ids nh,boston,worcester --limit 20
```

- Design note: see `artifacts/craigslist-research-architecture-2026-04-24.md`.

## Main artifacts
- `spec/product-contract.md`
- `spec/north-star-sales-ai-platform.md`
- `spec/dg-superhuman-sales-lane-plan-v1.md`
- `artifacts/outreach-investigation-contract.md`
- `artifacts/parallel-agent-handoff-protocol.md`
- `artifacts/agent-lane-claims.json`
- `queue.yaml`
- `evals.yaml`
- `artifacts/eval-summary.md`
- `artifacts/data-coverage.md`
- `artifacts/craigslist-research-architecture-2026-04-24.md`
