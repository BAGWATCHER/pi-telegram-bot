# EZ-010 — PVWatts/NSRDB Default-Path Integration Plan

## Objective
Upgrade scoring from proxy-only to a bounded-call PVWatts + NSRDB-informed path while preserving deterministic fallback.

## Implemented
- Added `--solar-model` switch to `scripts/score_sites.py`:
  - `proxy` (default stable path)
  - `pvwatts-cell-blend` (bounded-call calibrated path)
- Implemented bounded PVWatts calibration:
  - One PVWatts call per H3 cell centroid (not per-site)
  - Per-cell ratio `pvwatts_cf / proxy_cf`
  - Conservative ratio clamp `[0.65, 1.35]`
  - Fallback to proxy when PVWatts unavailable
- Implemented NSRDB resource enrichment:
  - Added `backend/scoring/nsrdb_hook.py` (NREL solar resource endpoint)
  - Captures annual `GHI`/`DNI` per H3 cell
  - Applies bounded confidence-only adjustment (no direct economics multiplier)
- Added scoring output fields:
  - `solar_model`
  - `pvwatts_ratio`
  - `nsrdb_ghi_annual`
  - `nsrdb_dni_annual`
  - `nsrdb_confidence_adjustment`
- Added/updated artifacts:
  - `artifacts/pvwatts-calibration.json`
  - `artifacts/pvwatts-calibration.md`
  - `artifacts/scoring-assumptions.md`

## Validation (latest local)
- `scripts/check_pvwatts_key.py` PASS for both PVWatts and NSRDB resource check.
- `scripts/score_sites.py --solar-model pvwatts-cell-blend`:
  - `cells_with_pvwatts = 20/20`
  - `cells_with_nsrdb = 20/20`
  - `sites_proxy_fallback = 0`
- `eval/run_eval.py` PASS.

## Remaining upgrades
1. Add explicit NSRDB weather-year selection + cache for reproducible runs.
2. Calibrate by utility territory/tariff segment instead of global utility-rate placeholder.
3. Add uncertainty intervals to confidence and economics outputs.
