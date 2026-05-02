# DemandGrid Vertical Pack Contract (DG-004)

Updated: 2026-04-17

## Purpose
Enable vertical-agnostic scaling while keeping one shared sales core.

## Endpoints
- `GET /api/v1/schema/sales-core`
- `GET /api/v1/schema/vertical/{vertical_id}`

## Core schema
Defined in `schema/sales-core.schema.json`.

Required entity groups:
- `site`
- `account`
- `contact`
- `opportunity`
- `outcome`

## Vertical pack schema
Defined in `schema/vertical-pack.schema.json`.

Minimum required fields per pack:
- `vertical_id`
- `required_signal_keys[]`
- `offer_types[]`
- `primary_kpis[]`

## Initial packs
- `energy`
- `roofing`
- `saas` (generic B2B template)

## Compatibility rule
Vertical packs may add fields but must not break sales-core required fields.
