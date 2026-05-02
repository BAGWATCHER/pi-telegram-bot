# Wind Confidence Policy (EZ-007)

## Intent
Keep recommendations honest: wind/hybrid should only appear when confidence clears an explicit threshold.

## Current rule
- `wind_min_confidence = 0.70`
- If `wind_confidence < 0.70` -> wind add-on is withheld.
- Hybrid can only be selected when:
  1. wind add-on is enabled (`annual_kwh_wind` present), and
  2. overall site confidence clears threshold, and
  3. hybrid economics passes comparison guardrail.

## Data-source caps
- Synthetic bootstrap data caps wind confidence at `0.65`.
- Non-synthetic sources can score higher (up to `0.90` cap).

## Practical outcome now
- With current synthetic ingest, wind add-ons are intentionally suppressed.
- Default recommendations remain solar-first (`solar` / `solar+battery` / `no-go`).

## Next upgrade path
- Replace synthetic ingest with real parcel/footprint + local wind evidence.
- Re-evaluate threshold and calibration with measured outcomes.
