# DemandGrid — Free Ingestion Backlog

## Purpose

This file converts free/public-source research into an execution backlog Chow can work through without ambiguity.

The goal is not “more data” in the abstract.
The goal is to add the free data that most improves:
- lead ranking
- primary-product recommendation
- operator route quality
- sales urgency detection

## Execution Rule

For each source:
- ingest into a stable local artifact
- define join logic explicitly
- write the smallest useful derived fields first
- do not block on perfect coverage

Prefer shipping:
- one useful trigger layer live in scoring
over:
- five half-defined source integrations

## Backlog Order

### EZ-FREE-001 — NOAA Storm Events -> Roofing trigger

Priority:
- `P0`

Why first:
- best free urgency source
- strongest non-solar revenue unlock
- also helps battery and restoration later

Primary source:
- NOAA Storm Events Database
- https://www.ncei.noaa.gov/stormevents/
- bulk download: https://www.ncei.noaa.gov/stormevents/ftp.jsp

Local artifact target:
- `data/raw/noaa/storm_events_*.csv`
- derived artifact: `data/processed/property_triggers.csv`

Join method:
- geospatial join from event geometry/county/zone context to site lat/lon
- first acceptable version can use:
  - county-level storm recency
  - ZIP/county overlap proxy
  - distance to recent hail/high-wind events

Minimum derived fields:
- `storm_trigger_status`
- `storm_trigger_score`
- `storm_event_count_12m`
- `storm_event_count_36m`
- `hail_event_count_36m`
- `wind_event_count_36m`
- `recent_storm_days`
- `storm_severity_proxy`
- `trigger_notes`

Scoring impact:
- boosts `roofing`
- supports later `battery` and `restoration`

Done means:
- at least one non-empty storm-derived field is written into `property_triggers.csv`
- scorer consumes it without schema changes
- at least some addresses show `storm_trigger_status != missing`

### EZ-FREE-002 — OpenEI rates -> economics layer

Priority:
- `P0`

Why second:
- improves solar and battery money estimates directly
- better than generic tariff assumptions

Primary source:
- OpenEI utility rates API
- https://apps.openei.org/services/doc/rest/util_rates/

Secondary support source:
- EIA-861 utility lookup / utility metadata
- https://www.eia.gov/electricity/data/eia861/

Local artifact target:
- `data/processed/utility_rates.csv`
- optional: `artifacts/openei-rate-cache.json`

Join method:
- geography -> utility -> tariff mapping
- first acceptable version can be ZIP or county based if address-level lookup is not practical yet

Minimum derived fields:
- `utility_name`
- `rate_source`
- `blended_rate_usd_per_kwh`
- `tou_flag`
- `nem_flag`
- `battery_rate_signal`
- `rate_confidence`

Scoring impact:
- better `annual_savings_usd`
- better `profit_score`
- better `battery_backup` economics

Done means:
- scoring assumptions can use rate-derived values where available
- at least one geography-specific rate override exists in the pipeline

### EZ-FREE-003 — ACS + DOE LEAD -> HVAC / electrification neighborhood proxy

Priority:
- `P1`

Why third:
- best free HVAC signal stack
- helps close probability and lane selection even without address-level equipment age

Primary sources:
- ACS 5-year API
- DOE LEAD Tool / supporting data

Sources:
- https://www.census.gov/data/developers/data-sets/acs-5year.2023.html
- https://www.energy.gov/scep/low-income-energy-affordability-data-lead-tool

Local artifact target:
- `data/processed/census_tract_housing_signals.csv`
- `data/processed/site_neighborhood_signals.csv`

Join method:
- reverse geocode site lat/lon to census tract / block group
- attach tract-level age/fuel/burden signals to each site

Minimum derived fields:
- `tract_year_built_pre_1980_pct`
- `owner_occ_pct`
- `single_family_pct`
- `electric_heat_pct`
- `gas_heat_pct`
- `energy_burden_pct`
- `hvac_neighborhood_signal`
- `electrification_fit_signal`

Scoring impact:
- boosts `hvac_heat_pump`
- improves `close_probability`
- helps later panel / electrification lanes

Done means:
- sites have tract-level housing/electrification signals attached
- HVAC ranking is no longer only “big home + easy effort”

### EZ-FREE-004 — FEMA National Risk Index -> broad hazard prior

Priority:
- `P1`

Why fourth:
- multi-lane hazard prior
- lower precision than NOAA storms, but broad and cheap to ingest

Source:
- https://hazards.fema.gov/nri/
- https://hazards.fema.gov/nri/data-resources

Local artifact target:
- `data/processed/fema_nri_tract_signals.csv`

Join method:
- census tract join

Minimum derived fields:
- `nri_hail_score`
- `nri_wind_score`
- `nri_flood_score`
- `nri_wildfire_score`
- `resilience_need_signal`

Scoring impact:
- supports roofing
- supports battery
- supports waterproofing / restoration

Done means:
- tract-level hazard prior is available to scoring
- can be shown in UI as supportive evidence, not quote-grade evidence

### EZ-FREE-005 — FEMA NFHL -> flood / restoration trigger

Priority:
- `P2`

Why fifth:
- strong for waterproofing/restoration
- narrower than roofing/solar/HVAC, so slightly lower immediate value

Source:
- FEMA Flood Map Service Center / NFHL
- https://msc.fema.gov/portal

Local artifact target:
- `data/processed/flood_risk_signals.csv`

Join method:
- spatial overlay of site lat/lon against flood polygons

Minimum derived fields:
- `flood_trigger_status`
- `flood_risk_trigger_score`
- `nfhl_zone`
- `special_flood_hazard_area_flag`
- `flood_trigger_notes`

Scoring impact:
- future `waterproofing / foundation / restoration`
- later route warnings and urgency

Done means:
- at least a subset of sites carry non-missing flood risk values

### EZ-FREE-006 — CBP / QCEW -> commercial territory signal

Priority:
- `P2`

Why sixth:
- useful for expansion, but less immediate than homeowner lanes

Sources:
- CBP: https://www.census.gov/programs-surveys/cbp.html
- QCEW: https://www.bls.gov/cew/overview.htm

Local artifact target:
- `data/processed/commercial_territory_signals.csv`

Join method:
- ZIP / county aggregation

Minimum derived fields:
- `commercial_density_signal`
- `roofing_trade_density`
- `industrial_energy_signal`
- `commercial_hvac_signal`
- `commercial_priority_score`

Scoring impact:
- territory selection
- later commercial product expansion

Done means:
- can rank ZIPs/territories for commercial canvassing even before address-level commercial scoring is built

## Exact Field Additions

### Add to `property_triggers.csv` next

Storm fields:
- `storm_trigger_status`
- `storm_trigger_score`
- `storm_event_count_12m`
- `storm_event_count_36m`
- `hail_event_count_36m`
- `wind_event_count_36m`
- `recent_storm_days`
- `storm_severity_proxy`

Outage-adjacent / resilience placeholders:
- `outage_trigger_status`
- `outage_trigger_score`
- `utility_reliability_proxy`
- `battery_rate_signal`

HVAC neighborhood placeholders:
- `equipment_age_trigger_status`
- `equipment_age_trigger_score`
- `hvac_neighborhood_signal`
- `electrification_fit_signal`

Flood/restoration placeholders:
- `flood_risk_trigger_status`
- `flood_risk_trigger_score`
- `nfhl_zone`
- `special_flood_hazard_area_flag`

Shared notes:
- `trigger_notes`

## Recommended Chow Ownership

Chow should own:
- raw source acquisition
- first-pass normalization jobs
- writing processed join artifacts
- populating `property_triggers.csv` and tract/ZIP support tables

Main rollout should own:
- scoring formulas
- schema/API/UI changes
- eval updates
- route/priority behavior

## Immediate Next Task

If only one thing gets done next:

Do `EZ-FREE-001` first.

That means:
- download NOAA Storm Events source files
- create first storm enrichment script
- populate storm-derived fields in `property_triggers.csv`
- rerun scoring and check whether roofing starts surfacing honestly
