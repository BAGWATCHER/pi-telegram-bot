# Artifact 03 — Patch Plan

## Patch Backlog (ordered)
1. Add endpoint timing instrumentation to eval harness (median/p95/worst).
2. Add repeated sampling mode (`N` runs) for production variance detection.
3. Investigate and mitigate prod 522 on `/api/v1/capabilities` (edge/origin reliability).

## Patch Selected Today
- Patch name: **Eval timing summary instrumentation**
- Why this first: Immediate observability gain with low risk; needed for Gauntlet-style measurable quality.
- Risk: Minimal (script-only change, no production endpoint behavior change).
- Rollback: Revert `scripts/eval-agentic-v1.ts`.

## Acceptance Criteria
- [x] Eval script prints timing summary on success
- [x] Eval script prints timing summary on failure
- [x] Local and prod runs provide measurable timing evidence
