# DemandGrid Signal Mesh Contract (DG-002)

Updated: 2026-04-17

## Purpose
Normalize trigger + behavioral + ops signals into one stable, scoring-ready contract.

## Site-level endpoint
- `GET /api/v1/signals/site/{site_id}`

Response shape:
- `framework`: `dg-signal-mesh-v1`
- `site_id`, `zip`
- `signals[]` entries:
  - `signal_key` (`storm|outage|equipment_age|flood_risk|permit`)
  - `status`
  - `quality` (`verified|proxy|missing`)
  - `score` (nullable)
  - `source`
  - `as_of` (nullable)
- `summary`:
  - `quality_counts`
  - `trigger_data_gaps`
  - `has_actionable_outage_data`
  - utility context fields

## Coverage endpoint
- `GET /api/v1/signals/coverage?zip=&h3_cell=`

Response shape:
- `framework`: `dg-signal-mesh-v1`
- `scope`
- `row_count`
- `signals.{signal_key}`:
  - `verified`
  - `proxy`
  - `missing`
  - `verified_pct`
  - `proxy_or_better_pct`

## Quality rules
- Preserve full trigger contract columns after every overlay merge.
- Emit explicit `missing` status instead of null/blank.
- Keep provenance and recency (`source`, `as_of`) where available.
