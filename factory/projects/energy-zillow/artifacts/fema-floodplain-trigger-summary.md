# FEMA Floodplain Trigger Summary

- generated_at: `2026-04-17T17:37:03Z`
- sites: **64581**
- floodplain feed: `/home/ubuntu/pi-telegram-bot/factory/projects/energy-zillow/data/raw/fema_floodplain_site_feed.csv`
- floodplain feed rows: **63659**
- matched sites: **63659**
- output: `/home/ubuntu/pi-telegram-bot/factory/projects/energy-zillow/data/raw/property_triggers_external.csv`

## Flood status counts

- `low`: 62747
- `missing`: 922
- `verified`: 912

## Notes
- This lane upgrades flood triggers using parcel/site-level FEMA feed when provided.
- If feed rows are zero, event-based NWS flood triggers remain the active flood proxy.
