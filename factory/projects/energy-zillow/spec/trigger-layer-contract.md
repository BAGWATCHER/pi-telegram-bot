# DemandGrid — Trigger Layer Contract

## Purpose

This file defines the first stable input contract for non-solar trigger data.

The scorer already ranks `roofing`, `hvac / heat pump`, `battery / backup power`, and future restoration lanes.
Those lanes should eventually be driven by real event data, not just property proxies.

## Input File

- Path: `data/processed/property_triggers.csv`
- Key: `site_id`
- Producer: initial scaffold from `scripts/bootstrap_property_triggers.py`
- Future producers: storm, outage, equipment-age, and flood/drainage enrichment jobs

## Required Columns

- `site_id`
- `zip`
- `storm_trigger_status`
- `outage_trigger_status`
- `equipment_age_trigger_status`
- `flood_risk_trigger_status`
- `storm_trigger_score`
- `outage_trigger_score`
- `equipment_age_trigger_score`
- `flood_risk_trigger_score`
- `trigger_notes`

## Status Semantics

Valid status values for each trigger family:
- `missing`
- `proxy`
- `modeled`
- `verified`

Interpretation:
- `missing`: no usable trigger layer is loaded yet
- `proxy`: weak or inferred signal exists
- `modeled`: computed or geospatially derived trigger signal exists
- `verified`: evidence-backed trigger signal exists and can support stronger claims

## Score Semantics

Trigger scores should be:
- numeric `0..100` when present
- blank when not available

Current lane usage:
- `storm_trigger_score` boosts `roofing`
- `outage_trigger_score` boosts `battery / backup power`
- `equipment_age_trigger_score` boosts `hvac / heat pump`
- `flood_risk_trigger_score` is stored now for restoration/foundation lanes later

## Build Rule

Do not hide missing trigger data behind generic confidence language.
If a trigger layer is absent:
- keep the lane visible if proxy ranking is still useful
- mark it as proxy-based or screening-grade
- preserve the missing-trigger explanation in API and UI output
