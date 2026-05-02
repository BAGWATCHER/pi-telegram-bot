# DemandGrid Orchestrator Runbook

Updated: 2026-04-18
Status: local scaffold validated

## What shipped
DemandGrid now has an orchestrator stub that connects the earlier lane outputs into one stateful run object.

### Endpoints
- `POST /api/v1/orchestrator/runs`
- `GET /api/v1/orchestrator/runs/{run_id}`
- `POST /api/v1/orchestrator/actions/{action_id}/approve`

## Current behavior
### On run creation
- compiles a playbook for the requested site
- creates a deterministic action graph
- persists the run to `data/processed/orchestrator_runs.json`
- supports `site_id + idempotency_key` replay

### Action graph
1. compile playbook
2. create outreach job
3. create calling session
4. schedule follow-up review

### Approval-required mode
- outreach + calling actions start in `awaiting_approval`
- approving an action executes it and records downstream refs
- this blocks autonomous execution when configured, which is the intended safety behavior

### Auto-execute mode
- if approval is not required and `auto_execute=true`, ready actions execute automatically
- downstream refs are attached for outreach job and calling session
- follow-up review remains visible as the next human/operator node

## Validation
Artifact: `artifacts/orchestrator-smoke.json`

### Approval path
- created run for `site_ab25957991a6`
- initial state: `awaiting_approval`
- approved outreach action -> downstream job created
- approved calling action -> downstream session created
- run idempotency replay returned existing run

### Auto-execute path
- created run for `site_9dc98e41c5af`
- `approval_required=false`, `auto_execute=true`
- ready actions executed automatically
- run remained `in_progress` with follow-up review node still visible

## Why this matters
This is the first whole-system control object for DemandGrid:
- playbooks are no longer isolated artifacts
- outreach and calling are no longer isolated connectors
- one run object now describes what happened, what is blocked, and what is next

## Immediate next follow-on
- DG-009 learning pipeline can ingest orchestrator action attribution
- DG-010 governance can harden role checks and approval policy validation
- later provider workers can hang off the same orchestrator action refs instead of inventing a new contract
