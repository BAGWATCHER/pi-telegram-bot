# Scoring Assumptions (Bootstrap)

- Solar model: `proxy`
- Utility rate: `$0.140` per kWh
- Install cost: `$2200` per kW
- Discount rate: `8.0%`
- Annual degradation: `0.5%`
- H3 resolution: `8`
- Wind confidence threshold: `0.70`
- Wind add-on cost multiplier: `30%` of solar install

## Notes
- `proxy` model uses deterministic rooftop-capacity and CF proxies for speed/repeatability.
- `pvwatts-cell-blend` model calibrates each H3 cell against PVWatts at cell centroid and scales outputs conservatively.
- NSRDB enrichment uses NREL solar-resource annual GHI/DNI as a bounded confidence signal (small adjustment only).
- Wind add-on is policy-gated and confidence-constrained by design.
- Replace with full roof-area, tilt, azimuth, shading, and local wind evidence in production path.
