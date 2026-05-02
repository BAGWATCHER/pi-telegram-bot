# DemandGrid Orchestrator State Machine v1

Updated: 2026-04-18
Framework: `dg-orchestrator-v1`
Status: local scaffold

## Purpose
Coordinate deterministic multi-step execution from a DemandGrid decision into concrete downstream actions.

## Endpoints
- `POST /api/v1/orchestrator/runs`
- `GET /api/v1/orchestrator/runs/{run_id}`
- `POST /api/v1/orchestrator/actions/{action_id}/approve`

## Run create input
```json
{
  "site_id": "site_ab25957991a6",
  "idempotency_key": "optional-client-key",
  "approval_required": true,
  "auto_execute": false,
  "execution_mode": "agent_assist",
  "objective": "optional override",
  "preferred_channels": ["phone", "email"],
  "strict_guardrails": true,
  "call_direction": "outbound"
}
```

## Deterministic action graph
Every run builds the same ordered graph shape:
1. `compile_playbook`
2. `create_outreach_job`
3. `create_calling_session`
4. `schedule_follow_up_review`

## Action states
- `completed`
- `awaiting_approval`
- `ready`
- `pending`
- `blocked`
- `failed`

## Run states
- `awaiting_approval`
- `in_progress`
- `completed`
- `attention_required`
- `planned`

## Approval behavior
- When `approval_required=true`, outreach and calling actions begin as `awaiting_approval`.
- `POST /api/v1/orchestrator/actions/{action_id}/approve` records approver metadata and executes the action.
- Approval is currently scoped to action-level execution only; governance/role enforcement can later harden this in DG-010.

## Auto-execution behavior
- When `approval_required=false` and `auto_execute=true`, the run executes all currently-ready actions automatically.
- The follow-up review action stays as a separate visible node for later operator review.

## Idempotency behavior
- Run creation reuses an existing run when `site_id + idempotency_key` matches a stored run.
- This allows safe retries from upstream managers or future orchestration workers.

## Persistence
- orchestrator store: `data/processed/orchestrator_runs.json`
- downstream refs:
  - playbooks: `data/processed/compiled_playbooks.json`
  - outreach jobs: `data/processed/outreach_jobs.json`
  - calling sessions: `data/processed/calling_sessions.json`

## Current safety posture
- deterministic, auditable state only
- no live external provider execution yet
- approval-required mode blocks autonomous downstream execution as designed
