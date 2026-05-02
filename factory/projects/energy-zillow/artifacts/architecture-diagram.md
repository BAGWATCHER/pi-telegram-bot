# Architecture Diagram (Text) — DemandGrid MVP

```text
[ZIP Input] -> [Ingest Layer]
               - ZIP profile / candidate sites
               - (next) parcel/footprint imports

[Ingest Layer] -> [Scoring Engine]
                  - solar production estimate
                  - economics (savings/payback/npv)
                  - recommendation + confidence + reasons

[Scoring Engine] -> [H3 Aggregator]
                    - cell-level opportunity metrics

[Scoring Engine + H3] -> [API Layer]
                         GET /api/v1/zip/{zip}/heatmap
                         GET /api/v1/hex/{h3}/sites
                         GET /api/v1/site/{site_id}

[API Layer] -> [Frontend]
               - MapLibre basemap
               - deck.gl H3 heatmap
               - ranked site table
               - site recommendation card
```

## Current status
- Ingest bootstrap active (synthetic seed from ZIP centroid).
- Real parcel/building footprint ingest is next.
