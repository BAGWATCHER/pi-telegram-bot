# PVWatts Cell Calibration (Scoring Path)

- mode: **pvwatts-cell-blend**
- cells total: **925**
- cells with PVWatts result: **0**
- cells with NSRDB resource enrichment: **0**
- sites calibrated: **0 / 61834**
- sites fallback proxy: **61834**
- ratio median: **None**
- ratio range: **None .. None**
- NSRDB confidence adjustment median: **None**
- NSRDB confidence adjustment range: **None .. None**

## Notes
- Per-cell PVWatts/NSRDB calls are bounded by number of H3 cells, not number of sites.
- Conservative PVWatts ratio clamp [0.65, 1.35] reduces overcorrection risk.
- NSRDB signal nudges confidence only (bounded), not direct economics multipliers.
- Fallback remains proxy when external APIs are unavailable.
