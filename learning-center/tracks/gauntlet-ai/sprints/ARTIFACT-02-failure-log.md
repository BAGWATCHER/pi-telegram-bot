# Artifact 02 — Failure Log

## Failure 1
- Symptom: Production eval fails immediately on `GET /api/v1/capabilities` with `HTTP 522`.
- Repro steps:
  1. `cd /home/ubuntu/partsbrain/web`
  2. `BEARINGBRAIN_EVAL_BASE_URL=https://bearingbrain.com npm run -s eval:agentic-v1`
- Root cause hypothesis: Edge/origin connectivity issue (Cloudflare timeout between edge and origin), or intermittent origin unavailability under current route.
- Priority (H/M/L): **H**

## Failure 2
- Symptom: Endpoint-level latency metrics (median/P95) are not captured by current eval harness.
- Repro steps: Run current script and inspect output; only pass/fail status is emitted.
- Root cause hypothesis: Script currently focused on correctness/idempotency; no timing instrumentation per endpoint.
- Priority (H/M/L): **M**

## Failure 3
- Symptom: Production reliability baseline currently single-sample; no repeated runs for variance.
- Repro steps: Current run performed once per env.
- Root cause hypothesis: No looped sampling mode in harness.
- Priority (H/M/L): **M**
