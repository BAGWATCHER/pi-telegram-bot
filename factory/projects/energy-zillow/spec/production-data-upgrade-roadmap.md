# DemandGrid — Production Data Upgrade Roadmap

Updated: 2026-04-17

## Objective
Move from screening-grade multi-product ranking to production-grade operator intelligence by upgrading address/parcel truth, hazards, permits, and economics.

## Current State (MVP+)
- Site coverage and trigger contract are complete for current board (59 ZIPs / 64,581 sites snapshot).
- Flood now includes parcel/site FEMA overlay on top of event-based NWS feed; residual unmatched rows remain where FEMA rows are unavailable.
- Equipment age still has Census proxy baseline, partially upgraded by permit-backed recency in Boston/Providence/Cambridge slices.
- Tariff/utility layer is normalized for a large majority of sites (OpenEI-backed), with remaining ZIP-level no-item gaps.

## Priority Lanes

### EZ-021 (done-local) — FEMA parcel floodplain lane
- Goal: authoritative flood risk overlay at parcel/site level.
- Input target: `data/raw/fema_floodplain_site_feed.csv`
- Output path: `data/raw/property_triggers_external.csv` (`flood_risk_trigger_status`, `flood_risk_trigger_score`, `trigger_notes` with FEMA provenance)
- Script: `scripts/project_fema_floodplain_triggers.py`
- Coverage gates:
  - `fema_matched/sites` by ZIP
  - `verified` flood status count by ZIP

### EZ-022 (in-progress) — Parcel permit-history lane
- Goal: convert roof/HVAC timing from coarse proxy to permit-backed recency signal.
- Input target: `data/raw/parcel_permit_feed.csv`
- Output path: `data/raw/property_triggers_external.csv` (`equipment_age_trigger_status`, `storm_trigger_status` adjustments where permit evidence exists)
- Script targets: `scripts/fetch_boston_permit_feed.py`, `scripts/fetch_providence_permit_feed.py`, `scripts/fetch_cambridge_permit_feed.py`, `scripts/project_parcel_permit_triggers.py`
- Coverage gates:
  - permit-matched sites by ZIP
  - non-missing permit-derived equipment/roof timing status

### EZ-023 (done-local) — Utility territory + tariff lane
- Goal: normalize savings/payback from generic assumptions to address-level utility/rate priors.
- Input target: `data/raw/utility_tariff_feed.csv`
- Output path: score features consumed in `scripts/score_sites.py`
- Script target: `scripts/project_utility_tariff_baseline.py`
- Coverage gates:
  - utility mapping coverage by ZIP
  - tariff-filled sites by ZIP
  - economics deltas vs baseline tracked in artifact

## Definition of “Production-Ready Data Core”
Minimum required before strong production claims:
1. Parcel identity backbone (deterministic site↔parcel mapping)
2. Parcel floodplain risk (FEMA/NFHL) live in scoring/triggers
3. Permit-backed equipment/roof timing signals
4. Utility/tariff normalization in economics path
5. Regression artifacts showing coverage + ranking stability + honesty still PASS

## Artifacts to maintain per lane
- `artifacts/*-summary.md`
- `artifacts/*-coverage.md`
- `artifacts/eval-summary.md`
- `artifacts/limitations.md` (honest caveats per lane)
