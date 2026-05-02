# Trigger Feed Contract (EZ-016)

## Purpose
Define the external trigger CSV schema that `scripts/merge_property_triggers.py` can ingest and merge onto site-level scoring.

## Input file path (default)
- `data/raw/property_triggers_external.csv`

## Required columns
- `site_id`
- `storm_trigger_status`
- `outage_trigger_status`
- `equipment_age_trigger_status`
- `flood_risk_trigger_status`

## Optional score columns
- `storm_trigger_score`
- `outage_trigger_score`
- `equipment_age_trigger_score`
- `flood_risk_trigger_score`

## Optional metadata
- `trigger_notes`

## Allowed status values
- `missing`
- `low`
- `medium`
- `high`
- `event_detected`

Values outside this set are normalized to `missing`.

## Merge behavior
- Merge key: `site_id`.
- If external row exists, values overlay default trigger contract row.
- If external row is missing, output preserves a complete `missing` row so eval contracts remain stable.

## NWS storm adapter (implemented)
Build a real storm feed file from NWS active alerts:

```bash
python3 scripts/fetch_nws_storm_triggers.py \
  --sites-csv data/processed/sites.csv \
  --output data/raw/property_triggers_external.csv
```

Notes:
- Uses `api.weather.gov/alerts/active?area=<STATE>`.
- Emits state-projected storm trigger rows per site.
- `low` with score `0.0` indicates feed loaded and no active severe alerts at fetch time.

## Outage adapters

### A) Real utility outage feed (implemented: Eversource)
```bash
python3 scripts/fetch_eversource_outage_feed.py \
  --output data/raw/state_outage_feed.csv
```

Notes:
- Pulls state outage percentages from Eversource outage map thematic-region feed.
- Coverage is utility-territory dependent (currently material for CT/MA, not VT).

### B) State-feed projection to site rows
```bash
python3 scripts/project_state_outage_triggers.py \
  --sites-csv data/processed/sites.csv \
  --external data/raw/property_triggers_external.csv \
  --state-feed data/raw/state_outage_feed.csv \
  --output data/raw/property_triggers_external.csv
```

Template:
- `data/raw/state_outage_feed.template.csv`

## Flood adapter (implemented: NWS flood-focused alerts)
```bash
python3 scripts/project_nws_flood_triggers.py \
  --sites-csv data/processed/sites.csv \
  --external data/raw/property_triggers_external.csv \
  --output data/raw/property_triggers_external.csv
```

Notes:
- Uses `api.weather.gov/alerts/active?area=<STATE>` and filters flood-specific events (`flood`, `flash flood`, `coastal flood`, etc.).
- Projects state flood-alert signal to site rows to eliminate geography blind spots where outage sources are unavailable.
- `low` with score `0.0` means feed loaded with no active flood alerts at fetch time.
- This is event-trigger coverage, not parcel-level FEMA floodplain modeling.

## Equipment-age adapter (implemented: Census ZIP median-year-built proxy)
```bash
python3 scripts/project_census_equipment_age_triggers.py \
  --sites-csv data/processed/sites.csv \
  --external data/raw/property_triggers_external.csv \
  --output data/raw/property_triggers_external.csv
```

Notes:
- Uses Census ACS table `B25035_001E` (median year structure built) by ZIP/ZCTA.
- Converts ZIP median structure age to `equipment_age_trigger_status/score` as screening proxy.
- Feed cache is stored at `data/raw/zip_equipment_age_feed.csv` for resilience when Census endpoint is slow.
- This is ZIP-level proxy coverage, not parcel-level HVAC/roof equipment records.

## Merge command
```bash
python3 scripts/merge_property_triggers.py \
  --sites-csv data/processed/sites.csv \
  --external data/raw/property_triggers_external.csv \
  --output data/processed/property_triggers.csv
```
