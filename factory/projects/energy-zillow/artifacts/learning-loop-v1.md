# DemandGrid Learning Loop v1

Updated: 2026-04-18
Framework: `dg-learning-loop-v1`
Status: local scaffold

## What shipped
DemandGrid now has a first closed-loop learning surface on top of the existing outcome system.

## New endpoints
- `POST /api/v1/outcomes`
- `GET /api/v1/outcomes/summary`
- `POST /api/v1/learning/retrain-jobs`

## Outcome write contract
`POST /api/v1/outcomes` now supports:
- conversion stage
- objection
- win/loss reason
- realized revenue
- realized profit
- attribution channel
- attribution playbook id
- attribution orchestrator run id
- attribution signal keys
- attribution source session/job ids

## Summary contract
`GET /api/v1/outcomes/summary` returns:
- stage counts
- win/loss/response rates
- revenue + profit aggregates
- top products / objections / reasons
- top channels
- top signal keys
- attributed outcome count
- attribution completeness metrics
- promotion-readiness snapshot

## Learning job contract
`POST /api/v1/learning/retrain-jobs` currently creates a persisted learning job stub with safety checks for:
- minimum outcomes
- minimum attribution completeness
- approver presence for non-dry-run promotion

## Persistence
- outcomes remain in `data/processed/lead_outcomes.json`
- learning jobs persist to `data/processed/learning_jobs.json`

## Validation artifact
- `artifacts/learning-loop-smoke.json`

## Why this matters
This closes the loop enough for DemandGrid to stop being only a routing stack:
- outcomes can now be written through a learning-specific API
- summaries expose whether attribution is good enough to trust
- promotion/retrain jobs are blocked when quality gates are weak

## Current limitation
- this is still a policy-safe scaffold, not a real model retrainer
- promotion decisions are checklist-driven for now
- DG-010 should later harden role and approval enforcement around live promotion
