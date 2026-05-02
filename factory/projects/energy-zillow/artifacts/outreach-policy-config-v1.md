# Outreach Policy Config v1

Updated: 2026-04-17

## Goal
Make outreach behavior tunable without API code edits.

## Config path
- `config/outreach_policy.json`

## Supported controls
- `default.confidence_min`: minimum confidence required for auto outreach.
- `default.confidence_high_min`: threshold for `confidence_band=high`.
- `default.channel_map`: recommended channel by lead temperature.
- `default.block_operator_statuses`: statuses that suppress auto outreach.
- `default.block_lead_temperatures`: lead segments that suppress auto outreach.
- `default.block_risk_flags`: risk flags that hard-block auto outreach.
- `default.review_risk_flags`: risk flags that stay visible as review flags (soft guardrail).

## Product-lane overrides
`products.{primary_product}` can override any default control (e.g. `solar`, `roofing`, `hvac_heat_pump`, `battery_backup`).

## Runtime surfaces
- `GET /api/v1/outreach/policy` returns loaded policy + source path.
- `GET /api/v1/investigation/site/{site_id}` includes policy snapshot + suppression/review flags.
- `GET /api/v1/outreach/payloads` includes policy metadata and per-item policy snapshots.

## Reload behavior
- `POST /api/v1/admin/reload` now clears outreach policy cache and reloads from file.
