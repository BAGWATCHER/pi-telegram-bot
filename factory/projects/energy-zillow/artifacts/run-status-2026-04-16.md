# DemandGrid — Dark Factory Run Status (2026-04-16, resumed)

## Current baseline
- Dataset scope: **4 New England ZIPs** (`01730`, `02667`, `05486`, `06525`)
- Coverage: **5,800 / 5,800 scored**
- H3 cells: **102**
- Demo API: PM2 `energy-zillow-demo` online (`127.0.0.1:8099`)
- Public demo URL: `http://20.122.197.143/energy-zillow/`

## Completed lanes
- **EZ-001..EZ-008**: core spec, ingest, scoring, H3, API, frontend, wind policy, eval harness
- **EZ-010**: PVWatts/NSRDB integration path (bounded per-cell calibration)
- **EZ-011**: multi-ZIP regression orchestration + gates
- **EZ-012**: operator workflow labels shipped
  - Added `lead_temperature` (`hot|warm|skip`)
  - Added `operator_next_step` (`work_now|follow_up|deprioritize`)
  - Wired through scorer -> CSV contract -> API -> frontend
  - Added eval gate `operator_workflow_labels`
- **EZ-013**: operator workflow persistence shipped
  - Added `GET/PUT /api/v1/operator/status*` endpoints
  - Added JSON status store `data/processed/operator_status.json`
  - Added query filters by ZIP/H3/status and timestamped updates
- **EZ-014**: route-day planning output shipped
  - Added `GET /api/v1/operator/route-plan` (ZIP/H3 scoping)
  - Uses lead/status-aware priority weighting + nearest-neighbor sequencing
  - Demo/interview artifacts updated for route workflow narrative
- **EZ-015**: operator quick-actions + route export shipped
  - Frontend detail card can update workflow status directly
  - Topbar route actions added (`Route Top 10`, `Route CSV`)
  - Added `GET /api/v1/operator/route-plan.csv` export endpoint
- **EZ-016**: trigger merge adapter shipped
  - Added `scripts/merge_property_triggers.py` for safe external-feed overlay by `site_id`
  - Added external feed schema doc `spec/trigger-feed-contract.md`
  - Added starter input template `data/raw/property_triggers_external.template.csv`
  - Added NWS feed adapter `scripts/fetch_nws_storm_triggers.py` -> `data/raw/property_triggers_external.csv`
  - Emitted feed summary artifact `artifacts/nws-trigger-fetch-summary.md`
  - Preserves full contract-complete trigger output even when no external feed is present
- **EZ-017**: outage trigger lane shipped
  - Added utility outage adapter `scripts/fetch_eversource_outage_feed.py` -> `data/raw/state_outage_feed.csv`
  - Added projection adapter `scripts/project_state_outage_triggers.py` to map state feed onto site rows
  - Outage trigger now non-missing on ~92.7% of sites (CT/MA covered; VT still missing)
- **EZ-018**: flood trigger lane shipped for outage-gap geography
  - Added flood overlay adapter `scripts/project_nws_flood_triggers.py` (NWS flood-focused events)
  - Generated flood artifacts `artifacts/nws-flood-trigger-summary.md` + `artifacts/flood-trigger-coverage.md`
  - Flood trigger now non-missing on 100% of sites, including VT ZIP `05486`
  - Added eval gate `flood_gap_coverage` to enforce continued coverage in outage-gap ZIPs
- **EZ-019**: equipment-age trigger lane shipped
  - Added Census proxy adapter `scripts/project_census_equipment_age_triggers.py`
  - Generated cache `data/raw/zip_equipment_age_feed.csv` + artifacts `artifacts/equipment-age-trigger-summary.md` and `artifacts/equipment-age-trigger-coverage.md`
  - Equipment-age trigger now non-missing across all current ZIPs (ZIP-level proxy)
  - Added eval gate `equipment_age_coverage` and wired regression/runbook trigger refresh chain
- **EZ-020A**: pi-style agent copilot shipped
  - Added `GET /api/v1/agent/capabilities` + `POST /api/v1/agent/chat` (`pi-tool-router-v1`)
  - Agent supports: top leads, site explain, route planning, heatmap summary, workflow status update
  - Added frontend AI Copilot panel with contextual scope + clickable returned cards
  - Added eval gate `agent_copilot_contract` (tool-routed top-leads + why-this-site smoke)

## Eval state
- Latest `artifacts/eval-summary.md`: **PASS**
- Passing gates include:
  - coverage
  - ranking_stability
  - multi_zip_regression
  - operator_workflow_labels
  - trigger_layer_contract
  - honesty/product/perf/explanation gates

## In progress / next
- **EZ-009**: closed-local (recording captured at `artifacts/demo-recording-v1.mp4`).
- Next data lane candidate: parcel-level floodplain and parcel/equipment record upgrades beyond ZIP/event proxies.

## Caveats
- Trigger data is **partially populated**: storm/outage/flood-event/equipment-age are data-backed, but outage is territory-limited and equipment-age is ZIP-level proxy.
- Flood lane is active-alert based (NWS), not parcel-level floodplain risk modeling.
- Current outage source is utility-territory-dependent (Eversource), so non-covered geographies can remain `missing` on outage specifically.
- Copilot is currently deterministic tool-routing (no external LLM synthesis yet); grounded and auditable, but less free-form than model-native chat.
- OSM ingestion at scale can hit rate-limit `509`; larger refreshes need paced retry/backoff.
