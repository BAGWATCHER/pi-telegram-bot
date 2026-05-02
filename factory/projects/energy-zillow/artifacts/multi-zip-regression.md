# Multi-ZIP Regression

- status: **PASS**
- zips: `01730, 02667, 05486, 06525`
- solar model: `proxy`

## Steps

- ✅ `python3 scripts/ingest_multi_zip_osm.py --zips 01730,02667,05486,06525 --half-span-deg 0.02 --min-records-per-zip 80` (rc=0)
- ✅ `python3 scripts/fetch_nws_storm_triggers.py --sites-csv data/processed/sites.csv --output data/raw/property_triggers_external.csv` (rc=0)
- ✅ `python3 scripts/fetch_eversource_outage_feed.py --output data/raw/state_outage_feed.csv` (rc=0)
- ✅ `python3 scripts/project_state_outage_triggers.py --sites-csv data/processed/sites.csv --external data/raw/property_triggers_external.csv --state-feed data/raw/state_outage_feed.csv --output data/raw/property_triggers_external.csv` (rc=0)
- ✅ `python3 scripts/project_nws_flood_triggers.py --sites-csv data/processed/sites.csv --external data/raw/property_triggers_external.csv --output data/raw/property_triggers_external.csv` (rc=0)
- ✅ `python3 scripts/project_census_equipment_age_triggers.py --sites-csv data/processed/sites.csv --external data/raw/property_triggers_external.csv --output data/raw/property_triggers_external.csv` (rc=0)
- ✅ `python3 scripts/merge_property_triggers.py --sites-csv data/processed/sites.csv --external data/raw/property_triggers_external.csv --output data/processed/property_triggers.csv` (rc=0)
- ✅ `python3 scripts/score_sites.py --solar-model proxy` (rc=0)
- ✅ `python3 eval/run_eval.py --require-min-zips 4 --min-rows-per-zip 80 --min-zip-stability 0.90` (rc=0)
