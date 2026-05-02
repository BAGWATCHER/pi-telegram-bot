# Demo Script (3 minutes) — Sales-Machine Version

## 0:00–0:30 — Problem + promise
- "DemandGrid is an operator console, not a consumer map: heatmap -> ranked addresses -> best product to pitch first."
- "Goal: spend next 4 field hours on higher-conversion houses."

## 0:30–1:15 — Territory to targets
1. Open `http://127.0.0.1:8099` (or `/energy-zillow/`).
2. Show `ALL` ZIP scope and explain map intensity as neighborhood opportunity.
3. Click one hex and show ranked list.
4. Point out lead-level fields now visible in flow: `lead_temperature`, `operator_next_step`, workflow status.

## 1:15–2:05 — Address recommendation card
1. Click top row.
2. Show primary/secondary product recommendation (roofing/solar/hvac/battery).
3. Show economics + confidence + reasons + trigger gaps.
4. Highlight operator framing: hot/warm/skip + next step (`work_now|follow_up|deprioritize`).

## 2:05–2:35 — Workflow persistence
1. Call status API quickly (or show pre-tagged row):
   - `PUT /api/v1/operator/status/{site_id}`
   - `GET /api/v1/operator/status?status=contacted`
2. Explain that statuses persist in `operator_status.json` with `updated_at` timestamps.

## 2:35–3:00 — Route-day execution + rigor
1. Show `GET /api/v1/operator/route-plan?max_stops=10`.
2. Explain route scoring blends priority + lead temperature + workflow state + distance sequencing.
3. Close with quality signal: `artifacts/eval-summary.md` is PASS (coverage/stability/honesty/operator labels/trigger contract).
