# Interview Brief — DemandGrid (Gauntlet-style, sales-machine framing)

## 30-second pitch
I built DemandGrid as a property-intelligence sales machine: map heatmap -> ranked addresses -> per-address primary/secondary product recommendation with confidence/economics, then workflow persistence and route planning so an operator can convert insights into field execution.

## What I built
- Multi-ZIP OSM ingest baseline (New England scope).
- Scoring pipeline with priority components (`profit`, `close_probability`, `fit`, `effort`) plus product ranking.
- Operator labels: `lead_temperature` (`hot|warm|skip`) and `operator_next_step`.
- FastAPI surfaces for map/list/detail + operator workflow persistence:
  - `GET/PUT /api/v1/operator/status*`
  - `GET /api/v1/operator/route-plan`
- Pi-style copilot surface (`pi-tool-router-v1`):
  - `GET /api/v1/agent/capabilities`
  - `POST /api/v1/agent/chat` (grounded tool routing with auditable `tool_calls`)
- Frontend flow that keeps map -> list -> detail actionable on mobile, now with embedded chat copilot.
- Eval harness with explicit quality gates and PASS artifact.

## Hard decisions
- Kept deterministic proxy mode as default eval path; PVWatts/NSRDB retained as explicit calibration lane.
- Enforced honesty constraints for non-solar/trigger-limited lanes.
- Prioritized operator execution surfaces over extra UI polish.

## Evidence / metrics
- Eval status: **PASS** (`artifacts/eval-summary.md`).
- Coverage: **100%** (5,800/5,800).
- Ranking stability: **1.000** top-set repeatability.
- API perf: **~2.2ms p95** local for tested gate.
- Trigger-layer contract: row-aligned file present for all scored sites.
- Trigger coverage progress: flood + equipment-age now non-missing across all current ZIPs; outage remains ~92.7% due utility-territory limits.
- Agent copilot contract gate: PASS (top-leads + why-this-site smoke).

## Known gaps (explicit)
- Trigger lanes are loaded, but still screening-grade: outage is territory-limited, equipment-age is ZIP proxy, flood is event-based.
- Not parcel-authority + full roof/shading fidelity yet.
- No CRM sync yet (local JSON persistence currently).

## Next upgrades
1. Upgrade from ZIP/event proxies to parcel-level trigger sources (floodplain + equipment records).
2. Add CRM/webhook sync for operator status events.
3. Add optional LLM layer over tool-router while preserving strict grounding + traceability.

## Gauntlet signal
- Shipped a complete execution loop (intelligence -> workflow -> route plan).
- Used eval gates to control regressions.
- Can articulate tradeoffs and data-truth boundaries without hype.
