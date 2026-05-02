# DG-003 Decision Engine Delta vs Baseline (Bootstrap)

Updated: 2026-04-17

## Snapshot
- Rows scored: **66,941**
- `win_probability_proxy` median: **0.399**
- `win_probability_proxy` p95: **0.483**
- `win_probability_proxy` max: **0.602**

## Baseline interpretation
- Baseline (pre-DG) had no explicit `win_probability_proxy` surface.
- DG-003 introduces deterministic, inspectable win-proxy outputs for routing and orchestration.

## Next delta pass
- Compare conversion/reply uplift after outcome telemetry accumulation (DG-009).
- Replace heuristic weights with learned/calibrated policy after offline replay pass.
