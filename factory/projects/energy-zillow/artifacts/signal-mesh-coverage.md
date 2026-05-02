# DG-002 Signal Mesh Coverage Snapshot

Updated: 2026-04-17
Rows evaluated: **66,941**

## Coverage by signal
- storm: verified `0`, proxy `1,056`, missing `65,885` (proxy-or-better `1.58%`)
- outage: verified `0`, proxy `0`, missing `66,941` (proxy-or-better `0.00%`)
- equipment_age: verified `0`, proxy `1,478`, missing `65,463` (proxy-or-better `2.21%`)
- flood_risk: verified `912`, proxy `62,747`, missing `3,282` (proxy-or-better `95.10%`)
- permit: verified `1,192`, proxy `711`, missing `65,038` (proxy-or-better `2.84%`)

## Endpoints live
- `GET /api/v1/signals/site/{site_id}`
- `GET /api/v1/signals/coverage`

## Notes
- Flood-risk has strongest board-wide coverage due FEMA expansion.
- Permit and outage remain active hardening targets under EZ-022+.
