# DemandGrid Manager Command Spec

Updated: 2026-04-18
Status: local scaffold

## Endpoint
- `GET /api/v1/manager/command?run_id=...`
- `GET /api/v1/manager/command?site_id=...`

## Purpose
Give a human manager or future manager-agent a compact command surface for risk review and coaching.

## Current output
- `risk_alerts[]`
- `coaching_actions[]`
- `pipeline_truth`
- policy source/version

## Current alert sources
- orchestrator run waiting on approval
- blocked actions in the run graph
- low site confidence
- low attribution completeness in the learning loop

## Current coaching sources
- approve or review queued actions
- resolve blocked actions instead of forcing execution
- improve attribution logging when learning quality is weak
- log outcomes when execution happened but learning state is still sparse

## Why this matters
This is the first manager-readable control object across execution + learning. It gives DG-010 a simple but useful surface before full autonomy controls exist.

## Validation artifact
- `artifacts/governance-smoke.json`
