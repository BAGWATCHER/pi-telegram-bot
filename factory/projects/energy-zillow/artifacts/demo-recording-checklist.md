# Demo Recording Checklist + Shot List (EZ-009 close)

## Goal
Record a clean 3-minute walkthrough proving the full flow:
1) heatmap, 2) ranked sites by hex, 3) site recommendation card, 4) eval rigor.

## Pre-flight (5–8 min)
- [ ] Terminal A: API running
  - `python3 -m uvicorn backend.api.app:app --host 127.0.0.1 --port 8099`
- [ ] Terminal B: confirm latest artifacts
  - `python3 scripts/score_sites.py`
  - `python3 eval/run_eval.py --zip 78701`
- [ ] Browser opens at `http://127.0.0.1:8099/`
- [ ] `artifacts/eval-summary.md` open in second tab
- [ ] Screen recorder set to 1080p, system audio off, mic on
- [ ] Do one dry run before recording

## Shot list (timestamped)

### Shot 1 — Problem + product promise (0:00–0:25)
- Show app landing state.
- Voiceover: "DemandGrid turns a ZIP into actionable clean-energy opportunities: heatmap to ranked addresses to confidence-aware recommendations."

### Shot 2 — Heatmap interaction (0:25–1:05)
- Pan/zoom map briefly.
- Click a high-intensity H3 hex.
- Show ranked address list appears.
- Call out sorting by annual savings and confidence visibility.

### Shot 3 — Site detail card (1:05–2:00)
- Click top-ranked address.
- Highlight: `best_option`, `annual_kwh`, `annual_savings_usd`, `payback_years`, `npv_15y_usd`, `confidence`, `reasons`.
- Mention solar-first default + constrained wind/hybrid policy.

### Shot 4 — Engineering rigor/evals (2:00–2:35)
- Switch to `artifacts/eval-summary.md`.
- Point at PASS gates: coverage, ranking stability, honesty_wind, product flow, perf, explanation quality.

### Shot 5 — Honest limitations + next build (2:35–3:00)
- Show `artifacts/limitations.md`.
- State next step: PVWatts/NSRDB path in default scoring + multi-ZIP regression.

## Retake triggers
- API error popup / blank list
- Wrong tab or dead air > 3 seconds
- Any claim that exceeds current MVP limitations

## Output
- Save as: `artifacts/demo-recording-v1.mp4`
- Optional: add 5–8 frame screenshots to `frontend/screenshots/`
