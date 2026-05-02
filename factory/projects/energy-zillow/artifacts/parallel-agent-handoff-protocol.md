# DemandGrid Parallel-Agent Handoff Protocol

Updated: 2026-04-17

## Goal
Maximize dark-factory throughput with Codex + Chow in parallel while minimizing edit collisions.

## Operating Model
- Work in **lane slices** (data ingest, join quality, eval/policy, API contracts).
- Keep commits/artifacts **additive** where possible.
- Prefer short cycles: ship -> eval -> record artifact -> move to next slice.

## Lane Claim Rules
1. Before starting a lane, append a claim entry to `artifacts/agent-lane-claims.json`.
2. Claim includes:
   - `agent` (`chow` / `codex`)
   - `lane`
   - `scope_files` (prefix list)
   - `started_at`
   - `status` (`active|done|blocked`)
3. If another active claim overlaps your target files, pick a different lane or wait.

## Low-Collision File Boundaries
- `frontend/*`: single-agent at a time
- `backend/api/app.py`: single-agent at a time
- `eval/run_eval.py`: single-agent at a time
- `scripts/fetch_*` and `scripts/project_*`: parallel-safe if different scripts
- `artifacts/*`: parallel-safe (append/update summaries)
- `data/raw/*`, `data/processed/*`: regenerate only after announcing in claim

## Required End-of-Cycle Output
Each cycle should produce:
1. Updated artifacts (`artifacts/*-summary.*`, `artifacts/eval-summary.md` as applicable)
2. Queue/progress update (`factory/queues/pending.ndjson` + `queue.yaml` timestamp)
3. Runtime check (health + relevant endpoint smoke)

## Conflict Recovery
If conflict detected (unexpected file drift in your lane):
1. Stop edits in conflicted file.
2. Re-read latest file state.
3. Re-apply only minimal delta.
4. Re-run eval gate.
5. Log collision note in `pending.ndjson` summary.

## Current Chow lane
- Lane: EZ-022 join-quality hardening
- Focus: permit address/parcel fallback matching + municipality expansion + eval stability
