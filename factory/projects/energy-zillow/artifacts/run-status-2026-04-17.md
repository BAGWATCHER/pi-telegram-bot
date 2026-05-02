# DemandGrid — Dark Factory Run Status (2026-04-17)

## Current baseline
- Dataset scope: **64 ZIPs**, **66,941 / 66,941 scored**
- H3 cells: **1,000**
- Demo API: PM2 `energy-zillow-demo` online (`127.0.0.1:8099`)
- Public demo URL: `http://20.122.197.143/energy-zillow/`

## Mission focus (factory)
- Core platform data lanes prioritized by default; UI polish resumed only on explicit request.
- Core platform data lanes now prioritized:
  - **EZ-022** parcel permit history expansion
  - **EZ-027+** outreach policy replay tuning against richer data

## EZ-021 progress (today)
- Added `scripts/fetch_fema_floodplain_site_feed.py` (NFHL ArcGIS point-query lane).
- Expanded FEMA feed from baseline-only to broad-board coverage using resume mode:
  - rows targeted/written: **63,659**
  - newly fetched in expansion run: **57,859**
  - elapsed: **1,764s** (~29.4m)
  - status mix: **62,747 low / 912 verified / 0 missing in feed rows**
- Applied floodplain overlay via `scripts/project_fema_floodplain_triggers.py`:
  - external trigger rows: **64,581**
  - FEMA-matched rows: **63,659**
  - residual missing flood rows: **922** (non-geocoded/no FEMA row)
- Trigger merge + score + eval rerun completed PASS (`artifacts/eval-summary.md`).
- EZ-021 moved to **done-local** in `queue.yaml`.


## EZ-022 progress (today)
- Permit ingest adapters active:
  - `scripts/fetch_boston_permit_feed.py` (Boston approved permits)
  - `scripts/fetch_providence_permit_feed.py` (Providence DIS permits)
  - `scripts/fetch_cambridge_permit_feed.py` (Cambridge Inspectional Services datasets)
- Municipal slices currently loaded:
  - Boston `02118/02186/02468`: `31,285` raw scanned -> `2,391` mapped rows, `847/6,622` matched scope sites (`12.8%`), fallback-matched rows `472`
  - Providence `02903`: `8,959` raw scanned -> `909` mapped rows, `138/246` matched sites (`56.1%`), fallback-matched rows `580`
  - Cambridge `02139`: `7,928` raw scanned across roof/solar/mechanical/gas/plumbing -> `4,171` mapped rows, `918/1,825` matched sites (`50.3%`), fallback-matched rows `1,505`
- Combined permit feed now `7,471` rows in `data/raw/parcel_permit_feed.csv`.
- Permit trigger overlay covers 3 high-signal ZIP slices (`02118`, `02139`, `02903`) with expanded match depth.
- Join-quality hardening shipped in all permit fetchers (`scripts/fetch_{boston,providence,cambridge}_permit_feed.py`):
  - house-number range and multi-number token support (e.g., `180-186`, `77;79`)
  - nearest-house same-street fallback matching with parity-aware preference.
- Trigger schema hardening remains active for overlay stability:
  - `scripts/project_fema_floodplain_triggers.py` and `scripts/project_parcel_permit_triggers.py` preserve full trigger contract columns (prevents permit-field loss during FEMA/permit overlay sequencing).
- Re-ran permit overlay + trigger merge + score + eval on latest board snapshot: **PASS** (`64 ZIPs`, `66,941` sites, widened mix gate now `top100={roofing:18, solar:82}`).
- EZ-022 remains **in-progress** for next municipality expansion + second-pass parcel-key fallback strategy beyond street normalization.

## EZ-023 progress (today)
- Added OpenEI utility ingest adapter `scripts/fetch_openei_utility_tariff_feed.py`.
- Ran full-board utility/tariff mapping using project key (`.env` key path):
  - ZIP status: `48 mapped`, `7 no_items`
  - feed rows written: `53,965`
- Projected feed into baseline artifact via `scripts/project_utility_tariff_baseline.py`:
  - `utility_mapped=53,965/61,834` (**87.3%**)
  - `rate_filled=53,965/61,834` (**87.3%**)
- Upgraded tariff delta artifact from placeholder to measured comparison vs pre-tariff baseline (site utility feed disabled):
  - `non_zero_delta=53,965/61,834` (**87.3%**)
  - total modeled annual savings delta: **+$20.86M**
  - median per-site annual savings delta: **+$280**
  - artifacts: `artifacts/tariff-impact-delta.{md,json}`
- EZ-023 moved to **done-local** after delta close + eval PASS.


## EZ-024 progress (today)
- Added north-star mission spec `spec/north-star-sales-ai-platform.md` to anchor channel-agnostic sales AI direction.
- Added outreach/investigation handoff contract `artifacts/outreach-investigation-contract.md`.
- Updated eval catalog (`evals.yaml`) with outreach/investigation-aligned gates:
  - `outreach_payload_contract`
  - `investigation_traceability`
  - `outreach_safety_guardrails`
  - `action_handoff_contract`
  - `closed_loop_feedback_contract`
- Linked north-star doc from `manifest.yaml` and marked EZ-024 `done-local` in queue.
- Implemented runtime checks in `eval/run_eval.py` for the new gates and validated PASS in `artifacts/eval-summary.md`.


## EZ-025 progress (today)
- Added new API surface in `backend/api/app.py`:
  - `GET /api/v1/investigation/site/{site_id}`
  - `GET /api/v1/outreach/site/{site_id}`
  - `GET /api/v1/outreach/payloads`
- Wired `eval/run_eval.py` outreach/investigation gates to call these endpoints via FastAPI `TestClient`.
- Regenerated OpenAPI and updated README endpoint list.
- Validated eval PASS with endpoint-backed gate details now emitted in `artifacts/eval-summary.md`.


## EZ-026 progress (today)
- Usability unblock adjustments shipped in `backend/api/app.py`:
  - Auto-outreach suppression now blocks on low confidence / workflow terminal state / lead-skip (not blanket survey/proxy suppression).
  - Address normalization added for API responses (`;` -> `-`) plus address-quality ranking penalty to reduce malformed top-lead surfacing.
- Immediate impact check (local API):
  - `/api/v1/outreach/payloads?limit=200&include_suppressed=true` -> `auto_outreach_eligible=200/200` in broad scope.
  - Semicolon address artifacts removed from sampled top cards (sanitized output format).
- Added economics clarity artifact `artifacts/economics-field-glossary.md` and linked in README.
- Re-ran eval harness with all gates passing.


## EZ-027 progress (today)
- Added config-driven outreach policy layer:
  - New config file `config/outreach_policy.json` with default + product-lane overrides.
  - New endpoint `GET /api/v1/outreach/policy` to expose active config + source.
- Updated investigation/outreach payload builders in `backend/api/app.py`:
  - Per-product confidence thresholds (`confidence_min`, `confidence_high_min`).
  - Channel selection by lead segment from policy map.
  - Policy-based suppression reasons and soft `review_flags`.
  - Item-level policy snapshot attached in investigation/outreach responses.
- Updated evals:
  - Added `outreach_policy_config_contract` gate in `eval/run_eval.py` and `evals.yaml`.
  - Re-ran eval: PASS with policy contract gate green.
- Demo API reloaded via PM2 restart and OpenAPI regenerated.

## Eval hotfix (resume session)
- Fixed runtime regression in `eval/run_eval.py` where permit evidence gate referenced undefined variable `rows`.
- Updated permit contract sampling to use `scored` rows (`permit_trigger_status != missing`).
- Result: outreach/investigation + permit + closed-loop gates restored to PASS in `artifacts/eval-summary.md`.

## DemandGrid UI clarity pass (explicit request)
- Applied BearingBrain-style aesthetic pass in `frontend/index.html`:
  - Warm paper + typography-first palette alignment (`#f9f7f4`, `#1a1a1a`, brown/link accents retained)
  - Flattened controls/tags (reduced rounded card feel) and simplified visual hierarchy
  - Added explicit operator workflow guidance and dynamic ranked-list context metadata
  - Renamed mobile tab to `Workspace` and action labels to `Plan Route` / `Export CSV`
- Mobile post-pass bugfixes shipped:
  - Resolved summary/list overlap on narrow screens (flex-shrink fix on ordered mobile sections)
  - Stacked list toolbar controls and truncated long hex token display
  - Prevented copilot launcher from covering detail content by hiding floating launcher in workspace mode and adding inline `AI Copilot` action button
- Restarted PM2 `energy-zillow-demo`; live page reflects updates at `http://20.122.197.143/energy-zillow/`.

## DG lane activation (whole-system Sales OS)
- Activated superhuman-sales lane plan from `spec/dg-superhuman-sales-lane-plan-v1.md` into execution queue.
- Added `DG-001..DG-010` tasks in `queue.yaml` with API contracts, eval-aligned done criteria, and wave dependencies.
- Linked lane plan in `manifest.yaml` (`goal.lane_plan_doc`) for top-level planning continuity.
- Updated `artifacts/agent-lane-claims.json` with wave-1 queued claims:
  - `DG-001` revenue graph core
  - `DG-002` signal mesh normalization
  - `DG-003` decision engine v1
  - `DG-004` universal sales schema
- Coordination rule: keep `EZ-022` permit hardening active in parallel while DG wave-1 scaffolding starts low-collision.
- Implemented DG wave-1 API scaffolds in `backend/api/app.py`:
  - `GET /api/v1/revenue-graph/site/{site_id}`
  - `GET /api/v1/revenue-graph/account/{account_id}`
  - `GET /api/v1/revenue-graph/contact/{contact_id}`
  - `GET /api/v1/signals/site/{site_id}`
  - `GET /api/v1/signals/coverage`
  - `GET /api/v1/decision/site/{site_id}`
  - `POST /api/v1/decision/batch`
  - `GET /api/v1/schema/sales-core`
  - `GET /api/v1/schema/vertical/{vertical_id}`
- Generated wave-1 contracts/artifacts and reran eval: **PASS** (`python3 eval/run_eval.py`).
- Restarted PM2 `energy-zillow-demo` and smoke-validated live DG endpoints on `127.0.0.1:8099` (`/api/v1/schema/sales-core`, `/api/v1/decision/site/{site_id}`).

## New/updated artifacts
- `frontend/index.html`
- `artifacts/outreach-policy-config-v1.md`
- `config/outreach_policy.json`
- `artifacts/economics-field-glossary.md`
- `eval/run_eval.py`
- `backend/api/app.py`
- `scripts/fetch_boston_permit_feed.py`
- `scripts/fetch_providence_permit_feed.py`
- `scripts/fetch_cambridge_permit_feed.py`
- `scripts/project_fema_floodplain_triggers.py`
- `scripts/project_parcel_permit_triggers.py`
- `artifacts/parallel-agent-handoff-protocol.md`
- `artifacts/agent-lane-claims.json`
- `artifacts/outreach-investigation-contract.md`
- `spec/north-star-sales-ai-platform.md`
- `spec/dg-superhuman-sales-lane-plan-v1.md`
- `spec/signal-mesh-contract.md`
- `spec/vertical-pack-contract.md`
- `schema/revenue-graph.schema.json`
- `schema/sales-core.schema.json`
- `schema/vertical-pack.schema.json`
- `artifacts/revenue-graph-quality.md`
- `artifacts/signal-mesh-coverage.md`
- `artifacts/decision-engine-v1.md`
- `artifacts/decision-delta-vs-baseline.md`
- `manifest.yaml`
- `queue.yaml`
- `artifacts/providence-permit-fetch-summary.md`
- `artifacts/providence-permit-fetch-summary.json`
- `artifacts/cambridge-permit-fetch-summary.md`
- `artifacts/cambridge-permit-fetch-summary.json`
- `artifacts/openei-utility-fetch-summary.md`
- `artifacts/openei-utility-fetch-summary.json`
- `artifacts/fema-floodplain-fetch-summary.md`
- `artifacts/fema-floodplain-fetch-summary.json`
- `artifacts/fema-floodplain-trigger-summary.md`
- `artifacts/fema-floodplain-trigger-summary.json`
- `artifacts/fema-floodplain-coverage.md`
- `spec/production-data-upgrade-roadmap.md`
- `artifacts/tariff-impact-delta.md`
- `artifacts/tariff-impact-delta.json`
- `artifacts/utility-tariff-summary.json`
- `artifacts/utility-tariff-summary.md`
- `artifacts/permit-trigger-coverage.md`
- `artifacts/permit-trigger-summary.json`
- `artifacts/boston-permit-fetch-summary.md`
- `artifacts/boston-permit-fetch-summary.json`
- `artifacts/permit-trigger-summary.md`

## Next factory steps
1. Keep EZ-022 active: expand permit feeds beyond Boston/Cambridge/Providence and ship geospatial fallback with conservative radius guardrails.
2. Launch DG wave-1 implementation lanes in parallel: DG-001 (revenue graph), DG-002 (signal mesh), DG-003 (decision engine), DG-004 (universal schema).
3. Add initial endpoint scaffolds for DG wave-1 in `backend/api/app.py` without breaking existing EZ surfaces.
4. Tune outreach policy by lane using conversion-oriented replay now that FEMA + permit lanes are richer.
5. Keep `artifacts/agent-lane-claims.json` current before touching shared files.
