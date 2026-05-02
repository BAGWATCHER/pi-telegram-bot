# Day 01 — BearingBrain Gauntlet Sprint

Date: 2026-04-15
Mode: Project-first, ship-first, evidence-first

## Sprint Objective (today)
Prove Gauntlet-style execution by shipping a measurable reliability artifact for BearingBrain agent APIs.

## Project Slice
"Agent Reliability Baseline + Hardening Plan" for:
- `GET /api/v1/search`
- `GET /api/v1/stats`
- `GET /api/v1/feeds/health`
- `POST /api/v1/quotes` + `GET /api/v1/quotes/{quoteId}`
- `POST /api/v1/agentic/checkout-intents` + status polling

## Done Criteria (must all be true)
1. Baseline eval run completed against local OR prod
2. Baseline metrics captured (pass rate, error count, median latency)
3. Top 3 failure modes documented with concrete reproduction
4. Hardening patch list created (ordered by impact)
5. One patch shipped today (small but real)
6. Post-patch re-run shows measurable improvement OR clean evidence why not

## Required Artifacts
1. `ARTIFACT-01-baseline-metrics.md`
2. `ARTIFACT-02-failure-log.md`
3. `ARTIFACT-03-patch-plan.md`
4. `ARTIFACT-04-post-patch-results.md`

## Build Loop (Gauntlet style)
1. Plan (15 min)
2. Build (60–90 min)
3. Eval (20 min)
4. Debrief (15 min)

## Command Starter
```bash
cd /home/ubuntu/partsbrain/web
npm run eval:agentic-v1
```

If needed, run on both:
- `http://127.0.0.1:3001`
- `https://bearingbrain.com`

## Scoring Rubric (0–2 each)
- Scope discipline
- Technical correctness
- Eval rigor
- Failure analysis quality
- Communication clarity

Target score today: **8+/10**

## Interview Link
This sprint directly trains interview signal:
- real execution evidence
- eval rigor
- failure + correction story
- measurable outcomes
