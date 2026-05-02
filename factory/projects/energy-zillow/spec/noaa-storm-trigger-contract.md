# DemandGrid — NOAA Storm Trigger Contract

## Purpose

This file defines the first practical free-data trigger implementation for roofing.

The objective is not perfect catastrophe modeling.
The objective is to create an honest, useful roofing urgency signal that improves targeting.

## Source

- NOAA Storm Events Database
- https://www.ncei.noaa.gov/stormevents/
- bulk CSV access: https://www.ncei.noaa.gov/stormevents/ftp.jsp

## First Acceptable Join Strategy

Version 1 can use a conservative geography-based approach:
- map each site to county
- aggregate storm events affecting that county
- weight hail and thunderstorm wind more heavily than generic events
- increase signal for recency

Required support input for the first pass:
- `data/raw/zip_county_crosswalk.csv`
- template now exists at `data/raw/zip_county_crosswalk.template.csv`

This is good enough for:
- roofing urgency proxy
- route prioritization
- identifying post-storm canvassing territory

## Event Types To Prioritize

Highest value:
- `Hail`
- `Thunderstorm Wind`
- `Tornado`

Useful secondary context:
- `Flash Flood`
- `Flood`
- `Hurricane`
- `Tropical Storm`
- `Strong Wind`

## Derived Fields

Required first-pass output into `property_triggers.csv`:
- `storm_trigger_status`
- `storm_trigger_score`
- `storm_event_count_12m`
- `storm_event_count_36m`
- `hail_event_count_36m`
- `wind_event_count_36m`
- `recent_storm_days`
- `storm_severity_proxy`
- `trigger_notes`

## Suggested Scoring Logic

Version 1 should favor:
- more recent events
- more hail events
- more severe wind events

Possible conservative pattern:
- hail in past 12 months = strongest boost
- thunderstorm wind in past 12 months = strong boost
- older events decay over time
- generic weather noise should not create a high roofing score alone

## Status Rules

Use:
- `missing`: no storm context joined
- `proxy`: county/ZIP storm context only
- `modeled`: stronger geospatial distance/impact model exists
- `verified`: reserved for later evidence beyond public NOAA screening

For the first version, expect:
- most populated rows to be `proxy`

## Product Behavior

Storm data should:
- increase `roofing_score`
- improve `sales_route_score` when roofing becomes the primary lane
- improve `why_now_summary` and `operator_action_summary`

Storm data should not:
- silently make roofing quote-grade
- erase missing roof-age limitations

## Success Condition

After first NOAA ingest:
- some rows should have `storm_trigger_status != missing`
- some rows should have non-empty `storm_trigger_score`
- at least a small number of addresses should move toward `roofing` primary or secondary in a defensible way

## Current Scaffold

Executable scaffold now exists:
- `scripts/enrich_noaa_storm_triggers.py`

Expected usage:
1. place NOAA CSV files in `data/raw/noaa/`
2. create `data/raw/zip_county_crosswalk.csv`
3. run the enrichment script
4. rerun scoring

## Current Local Status

Local first pass is now running with:
- NOAA detail files for 2023-2025 in `data/raw/noaa/`
- ZIP-to-county mappings for the active New England ZIP set in `data/raw/zip_county_crosswalk.csv`
- storm fields populated across all current sites in `data/processed/property_triggers.csv`

Important limitation of the current version:
- the signal is still county-level proxy data, not parcel-level impact data
- scoring was explicitly normalized to avoid maxing every county at `100`
- current storm score spread across active ZIPs is roughly:
  - `01730`: `69.8`
  - `06525`: `64.4`
  - `02667`: `22.7`
  - `05486`: `9.3`

Next improvement:
- replace or refine the county proxy with a more localized impact model before treating roofing as a mature lane
