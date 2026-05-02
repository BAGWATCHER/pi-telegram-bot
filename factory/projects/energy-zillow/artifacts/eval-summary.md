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
- ✅ **investigation_traceability** — trace_ok=40/40 (100.0%)
- ✅ **permit_evidence_contract** — permit_ok=20/20 (100.0%)
- ✅ **outreach_safety_guardrails** — auto_candidates=40, auto_suppressed=0, violations=0
- ✅ **action_handoff_contract** — handoff_ok=40/40 (100.0%)
- ✅ **closed_loop_feedback_contract** — entries=25, invalid=0, summary_ok=True, next_action_ok=True, phase=workflow_plus_learning

## Dataset Snapshot

- sites: 66941
- scored: 66941
- h3 cells: 1000
- zip count: 64

## Per-ZIP Coverage

- `01450`: sites=412, scored=412, coverage=100.00%, stability=1.000
- `01451`: sites=405, scored=405, coverage=100.00%, stability=1.000
- `01720`: sites=1426, scored=1426, coverage=100.00%, stability=1.000
- `01730`: sites=2173, scored=2173, coverage=100.00%, stability=1.000
- `01740`: sites=351, scored=351, coverage=100.00%, stability=1.000
- `01741`: sites=470, scored=470, coverage=100.00%, stability=1.000
- `01748`: sites=1083, scored=1083, coverage=100.00%, stability=1.000
- `01770`: sites=495, scored=495, coverage=100.00%, stability=1.000
- `01772`: sites=951, scored=951, coverage=100.00%, stability=1.000
- `01776`: sites=1184, scored=1184, coverage=100.00%, stability=1.000
- `01778`: sites=846, scored=846, coverage=100.00%, stability=1.000
- `01827`: sites=358, scored=358, coverage=100.00%, stability=1.000
- `01886`: sites=831, scored=831, coverage=100.00%, stability=1.000
- `01890`: sites=3763, scored=3763, coverage=100.00%, stability=1.000
- `01921`: sites=436, scored=436, coverage=100.00%, stability=1.000
- `01940`: sites=1885, scored=1885, coverage=100.00%, stability=1.000
- `01949`: sites=1019, scored=1019, coverage=100.00%, stability=1.000
- `01965`: sites=575, scored=575, coverage=100.00%, stability=1.000
- `01983`: sites=990, scored=990, coverage=100.00%, stability=1.000
- `01985`: sites=486, scored=486, coverage=100.00%, stability=1.000
- `02030`: sites=689, scored=689, coverage=100.00%, stability=1.000
- `02043`: sites=1525, scored=1525, coverage=100.00%, stability=1.000
- `02052`: sites=1529, scored=1529, coverage=100.00%, stability=1.000
- `02056`: sites=1023, scored=1023, coverage=100.00%, stability=1.000
- `02061`: sites=527, scored=527, coverage=100.00%, stability=1.000
- `02067`: sites=1405, scored=1405, coverage=100.00%, stability=1.000
- `02090`: sites=1579, scored=1579, coverage=100.00%, stability=1.000
- `02118`: sites=2998, scored=2998, coverage=100.00%, stability=1.000
- `02139`: sites=1825, scored=1825, coverage=100.00%, stability=1.000
- `02186`: sites=3043, scored=3043, coverage=100.00%, stability=1.000
- `02332`: sites=364, scored=364, coverage=100.00%, stability=1.000
- `02339`: sites=1129, scored=1129, coverage=100.00%, stability=1.000
- `02420`: sites=2182, scored=2182, coverage=100.00%, stability=1.000
- `02468`: sites=581, scored=581, coverage=100.00%, stability=1.000
- `02482`: sites=2535, scored=2535, coverage=100.00%, stability=1.000
- `02492`: sites=2725, scored=2725, coverage=100.00%, stability=1.000
- `02493`: sites=541, scored=541, coverage=100.00%, stability=1.000
- `02575`: sites=549, scored=549, coverage=100.00%, stability=1.000
- `02637`: sites=731, scored=731, coverage=100.00%, stability=1.000
- `02667`: sites=1953, scored=1953, coverage=100.00%, stability=1.000
- `02903`: sites=246, scored=246, coverage=100.00%, stability=1.000
- `03087`: sites=387, scored=387, coverage=100.00%, stability=1.000
- `03249`: sites=150, scored=150, coverage=100.00%, stability=1.000
- `03253`: sites=191, scored=191, coverage=100.00%, stability=1.000
- `03854`: sites=74, scored=74, coverage=100.00%, stability=1.000
- `04006`: sites=72, scored=72, coverage=100.00%, stability=1.000
- `04101`: sites=2966, scored=2966, coverage=100.00%, stability=1.000
- `05486`: sites=421, scored=421, coverage=100.00%, stability=1.000
- `06103`: sites=745, scored=745, coverage=100.00%, stability=1.000
- `06510`: sites=512, scored=512, coverage=100.00%, stability=1.000
- `06525`: sites=1253, scored=1253, coverage=100.00%, stability=1.000
- `06820`: sites=338, scored=338, coverage=100.00%, stability=1.000
- `06824`: sites=2139, scored=2139, coverage=100.00%, stability=1.000
- `06831`: sites=523, scored=523, coverage=100.00%, stability=1.000
- `06840`: sites=618, scored=618, coverage=100.00%, stability=1.000
- `06870`: sites=433, scored=433, coverage=100.00%, stability=1.000
- `06877`: sites=1367, scored=1367, coverage=100.00%, stability=1.000
- `06878`: sites=631, scored=631, coverage=100.00%, stability=1.000
- `06880`: sites=340, scored=340, coverage=100.00%, stability=1.000
- `06883`: sites=739, scored=739, coverage=100.00%, stability=1.000
- `06890`: sites=1454, scored=1454, coverage=100.00%, stability=1.000
- `06896`: sites=99, scored=99, coverage=100.00%, stability=1.000
- `06897`: sites=593, scored=593, coverage=100.00%, stability=1.000
- `06903`: sites=1078, scored=1078, coverage=100.00%, stability=1.000

Status: **PASS**
