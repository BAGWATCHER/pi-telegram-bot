# Artifact 04 — Post-Patch Results

## What changed
- Files touched:
  - `/home/ubuntu/partsbrain/web/scripts/eval-agentic-v1.ts`
- Summary:
  - Added timing sample capture per request
  - Added summary print (`checks`, `median`, `p95`, `worst`)
  - Ensured summary prints on both success and failure paths

## Re-run Results
### Local (`http://127.0.0.1:3001`)
- Correctness pass rate before: 100%
- Correctness pass rate after: 100%
- Timing summary after: `checks=13 median=7ms p95=477ms worst=477ms`

### Prod (`https://bearingbrain.com`)
- Correctness pass rate before: fail at first check (522)
- Correctness pass rate after: fail at first check (522)
- Timing summary after: `checks=1 median=19619ms p95=19619ms worst=19619ms`

## Outcome
- Improved? **Yes** (observability improved; correctness unchanged)
- Evidence:
  - Harness now emits quantifiable timing metrics for both pass and fail runs
  - Production failure remains reproducible with latency evidence
- Next action:
  1. Add repeated sampling mode (e.g., 5 runs)
  2. Trace prod edge/origin path for 522 at `/api/v1/capabilities`
