# Limitations & Assumptions (MVP)

## Current limitations
- **Geography scope**: currently validated on ZIPs `01730`, `02667`, `05486`, and `06525`; not yet citywide/countywide production coverage.
- **Input fidelity**: OSM-derived address/building data is useful for MVP but not a substitute for authoritative parcel + roof geometry datasets.
- **Wind modeling**: wind/hybrid output is confidence-gated and conservative; no rooftop CFD / micrositing simulation in this MVP.
- **Economic model scope**: payback/NPV are simplified and assumption-driven (install cost/tariff/incentives), not quote-grade financing outputs.
- **Multi-product triggers**: `property_triggers.csv` is now populated with storm (NWS), outage (Eversource state-projected), flood-event (NWS flood alerts), and equipment-age (Census ZIP median-year-built proxy) signals; equipment-age is still ZIP-level proxy and flood data remains event-triggered (not parcel-level floodplain risk).
- **Operational constraints not modeled**: permitting timelines, interconnection queue, HOA/local restrictions, and installer labor capacity are not yet represented.

## Key assumptions
- Solar-first recommendation is the default unless explicit wind evidence supports hybrid.
- Reason codes must be present for recommendation transparency.
- Confidence is reduced when required inputs are weak/partial.

## What must be upgraded before production claims
1. Authoritative parcel/roof datasets + shading features.
2. PVWatts/NSRDB-calibrated pipeline in main scoring path.
3. Utility-tariff and incentive normalization by address.
4. Expanded evals on multiple ZIPs/cities with regression snapshots.
5. Installer/ops constraints and uncertainty intervals in recommendations.
