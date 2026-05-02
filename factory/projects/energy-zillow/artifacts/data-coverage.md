# EZ-002 Data Coverage

- ZIP: `06870` (Old Greenwich, CT)
- Candidates: **433**
- With site_id+lat/lon: **433**
- Coverage: **100.00%**
- Source mode: **real OSM address/footprint ingest**
- Output: `/home/ubuntu/pi-telegram-bot/factory/projects/energy-zillow/data/processed/sites_06870_osm.csv`

## Source + Method
- Source APIs:
  - `https://api.zippopotam.us/us/06870` (ZIP center)
  - `https://api.openstreetmap.org/api/0.6/map` (address-tagged nodes/ways)
- Spatial query: bounding box around ZIP centroid (`half_span_deg=0.006`)
- Post-filter: keep records in/near ZIP by `addr:postcode` prefix or local bounds

## Breakdown
- `node`: **431**
- `way`: **2**

## Next Upgrade
- Add true parcel boundaries from county/city GIS where available
- Attach rooftop geometry/shading features for higher-confidence scoring
