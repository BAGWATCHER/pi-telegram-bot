# DemandGrid lane context - EZ-022

- timestamp_utc: 2026-04-21T21:05:08.815679+00:00
- queue_updated_at: 2026-04-18T07:04:31Z
- status: in-progress
- lane: data
- priority: p0
- risk: medium

## title
Add parcel permit-history lane (roof/HVAC/solar timing signals)

## done_when
- permit feed normalizes to site_id or deterministic parcel/address key
- roofing/HVAC recency triggers populate non-trivial share of active sites
- trigger notes include permit recency fields and source provenance
- merge + score + eval pass with permit lane enabled

## artifacts
- scripts/fetch_boston_permit_feed.py
- scripts/fetch_providence_permit_feed.py
- scripts/fetch_cambridge_permit_feed.py
- scripts/project_parcel_permit_triggers.py
- data/raw/parcel_permit_feed.template.csv
- data/raw/parcel_permit_feed.csv
- data/raw/property_triggers_external.csv
- artifacts/boston-permit-fetch-summary.md
- artifacts/boston-permit-fetch-summary.json
- artifacts/providence-permit-fetch-summary.md
- artifacts/providence-permit-fetch-summary.json
- artifacts/cambridge-permit-fetch-summary.md
- artifacts/cambridge-permit-fetch-summary.json
- artifacts/permit-trigger-summary.md
- artifacts/permit-trigger-summary.json
- artifacts/permit-trigger-coverage.md
- artifacts/eval-summary.md

## eval-summary.md (head)
```text
# Eval Summary

## Gate Results

- ✅ **coverage** — 100.00% (threshold >= 80%)
- ✅ **ranking_stability** — 1.000 (threshold >= 0.90)
- ✅ **multi_zip_regression** — zips=64 req>=25, min_rows_per_zip=20, min_zip_stability=1.000 req>=0.90, rows_ok=True, coverage_ok=True
- ✅ **product_flow** — scored+h3+api-samples+frontend map/list/detail flow present
- ✅ **agent_copilot_contract** — skipped_large_board rows=66941
- ✅ **honesty_wind** — violations=0
- ✅ **honesty_product_readiness** — missing=0, proxy_lane_mismatch=0
- ✅ **operator_workflow_labels** — missing=0, invalid=0
- ✅ **operator_route_usability** — route_score_missing=0, top200_hot=200
- ✅ **widened_product_mix** — top100={'roofing': 18, 'solar': 82}
- ✅ **solar_first_default** — hybrid=29997, violations=0
- ✅ **perf_api** — p95=2.20ms (threshold <= 700ms)
- ✅ **explanation_quality** — 100.00% (threshold >= 98%)
- ✅ **assumption_traceability** — scoring_assumptions=True, limitations=True
- ✅ **trigger_layer_contract** — trigger_rows=66941, sites=66941
- ✅ **battery_reliability_prior** — loaded_rows=66941, scored_rows=66941
- ✅ **flood_gap_coverage** — outage_gap_zips=['01450', '01451', '01720', '01730', '01740', '01741', '01748', '01770', '01772', '01776', '01778', '01827', '01886', '01890', '01921', '01940', '01949', '01965', '01983', '01985', '02030', '02043', '02052', '02056', '02061', '02067', '02090', '02118', '02139', '02186', '02332', '02339', '02420', '02468', '02482', '02492', '02493', '02575', '02637', '02667', '02903', '03087', '03249', '03253', '03854', '04006', '04101', '05486', '06103', '06510', '06525', '06820', '06824', '06831', '06840', '06870', '06877', '06878', '06880', '06883', '06890', '06896', '06897', '06903'], flood_covered_gap_zips=['01450', '01451', '01720', '01730', '01740', '01741', '01748', '01770', '01772', '01776', '01778', '01827', '01886', '01890', '01921', '01940', '01949', '01965', '01983', '01985', '02030', '02043', '02052', '02056', '02061', '02067', '02090', '02118', '02139', '02186', '02332', '02339', '02420', '02482', '02492', '02493', '02575', '02637', '02667', '02903', '03087', '03854', '04006', '04101', '05486', '06103', '06510', '06525', '06824', '06831', '06877', '06883', '06890', '06896', '06897', '06903']
- ✅ **equipment_age_coverage** — zips_with_equipment=['02118', '02139', '02903']
- ✅ **outreach_policy_config_contract** — version=2026-04-17-v1, source=/home/ubuntu/pi-telegram-bot/factory/projects/energy-zillow/config/outreach_policy.json, confidence_min=0.65, product_overrides=4
- ✅ **outreach_payload_contract** — contract_exists=True, payload_ok=40/40 (100.0%)
```
