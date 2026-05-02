# Artifact 01 — Baseline Metrics

Date: 2026-04-15
Environment:
- Local: `http://127.0.0.1:3001`
- Prod: `https://bearingbrain.com`
Commit/Version: working tree (no commit tagged in this run)

## Eval Summary
### Local
- Total checks attempted: 13 (+1 optional introspection skipped)
- Passed: 13
- Failed: 0
- Pass rate: 100%
- Total runtime: ~904ms

### Prod
- Total checks attempted: 1
- Passed: 0
- Failed: 1
- Pass rate: 0%
- Total runtime to fail: ~19.9s
- First failure: `capabilities failed (522)`

## Latency Snapshot
- Local total eval runtime: ~0.9s
- Prod runtime to first error: ~19.9s
- Endpoint-level median/P95: not instrumented in current eval script

## Endpoint Notes
- Local: all tested endpoints green, including quote/checkout idempotency.
- Prod: failed at first endpoint (`/api/v1/capabilities`) with HTTP 522.

## Raw Evidence
- command(s):
  - `npm run -s eval:agentic-v1`
  - `BEARINGBRAIN_EVAL_BASE_URL=https://bearingbrain.com npm run -s eval:agentic-v1`
- logs path:
  - local: `/tmp/tmp.tZfl1gWBC3`
  - prod: `/tmp/tmp.QUig4K5uHV`
