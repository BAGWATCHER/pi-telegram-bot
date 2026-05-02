# DG-001 Revenue Graph Quality Snapshot

Updated: 2026-04-17

## Dataset snapshot
- Rows: **66,941**

## Identity quality
- Account ID collision rate: **0.0000**
- Contact ID collision rate: **0.0000**

## Provenance coverage
- `site_id`: **100.0%**
- `address`: **100.0%**
- `zip`: **100.0%**
- `h3_cell`: **100.0%**

## Endpoint scaffolds live
- `GET /api/v1/revenue-graph/site/{site_id}`
- `GET /api/v1/revenue-graph/account/{account_id}`
- `GET /api/v1/revenue-graph/contact/{contact_id}`

## Notes
- Current account/contact IDs are deterministic graph scaffolds for orchestration integration.
- Future hardening: business-entity/contact enrichment and true multi-site account merges.
