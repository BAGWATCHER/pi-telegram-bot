# DemandGrid — Dark Factory Run Status (2026-04-18)

## Snapshot
- Dataset scope: **64 ZIPs**, **66,941 scored sites**, **1,000 H3 cells**
- Demo API baseline remains PM2 `energy-zillow-demo` on `127.0.0.1:8099`
- Codex is actively testing the current stack, so Chow is staying on **low-collision local lane work** until that test cycle clears

## Active lanes
- **EZ-022** permit expansion remains active for next municipality + parcel-key fallback hardening
- **EZ-028** closed-loop sales OS layer remains active
- **DG-005** playbook compiler v1 moved to **in-progress-local**
- **DG-006** outreach connector moved to **in-progress-local**
- **DG-007** calling connector moved to **in-progress-local**
- **DG-008** orchestrator moved to **in-progress-local**
- **DG-009** learning loop moved to **in-progress-local**
- **DG-010** governance layer moved to **in-progress-local**

## DG-005 progress (today)
- Added local playbook compiler scaffold in `backend/api/app.py`:
  - `POST /api/v1/playbooks/compile`
  - `GET /api/v1/playbooks/{playbook_id}`
- Compiler now assembles one executable playbook object from:
  - decision output
  - investigation payload
  - outreach payload
  - signal summary
  - current operator / outcome state
  - available closed-loop learning summaries
- Compiled payload includes:
  - objective
  - execution mode (`rep_assist` / `agent_assist` / `agent_autonomous`)
  - ordered channel sequence
  - guardrail flags
  - stop conditions
  - ordered steps with guardrails on every step
  - objection map
  - refs back to revenue graph / signals / decision / outreach / investigation
- Added artifacts:
  - `artifacts/playbook-compiler-v1.md`
  - `artifacts/playbook-examples.json`
- Regenerated OpenAPI locally and updated `README.md`
- Regression check after scaffold: `python3 eval/run_eval.py` -> **PASS**

## DG-006 progress (today)
- Added local outreach connector scaffold in `backend/api/app.py`:
  - `POST /api/v1/agents/outreach/jobs`
  - `GET /api/v1/agents/outreach/jobs/{job_id}`
  - `POST /api/v1/agents/outreach/events`
- Added persisted job store `data/processed/outreach_jobs.json` with:
  - idempotency replay by `site_id + idempotency_key`
  - channel resolution
  - policy decision snapshot
  - delivery state
  - append-only event log inside each job record
- Policy-safe behavior now enforced in local connector stub:
  - allowed lead smoke test queued normally
  - suppressed lead smoke test persisted as `blocked` with explicit reason (`lead_skip`)
- Added docs/artifacts:
  - `spec/agent-outreach-contract.md`
  - `artifacts/outreach-job-lifecycle.md`
- Regenerated OpenAPI locally and kept eval green: `python3 eval/run_eval.py` -> **PASS**

## DG-007 progress (today)
- Added local calling connector scaffold in `backend/api/app.py`:
  - `POST /api/v1/agents/calling/sessions`
  - `GET /api/v1/agents/calling/sessions/{session_id}`
  - `POST /api/v1/agents/calling/events`
- Added persisted calling session store `data/processed/calling_sessions.json` with:
  - pre-call brief
  - live assist state
  - event log
  - outcome sync metadata
- Calling events now support structured post-call extraction into the lead outcome schema:
  - `qualified`, `won`, `lost` sync directly
  - `follow_up_needed` falls back to `responded`
  - `no_answer` falls back to `contacted`
- Added docs/artifacts:
  - `spec/agent-calling-contract.md`
  - `artifacts/calling-session-eval.md`
  - `artifacts/calling-session-smoke.json`
- Smoke validation:
  - created session for `site_9dc98e41c5af`
  - moved `ready -> live -> completed`
  - synced `lead_outcome.status=qualified`
- Regenerated OpenAPI locally and kept eval green: `python3 eval/run_eval.py` -> **PASS**

## DG-008 progress (today)
- Added local orchestrator scaffold in `backend/api/app.py`:
  - `POST /api/v1/orchestrator/runs`
  - `GET /api/v1/orchestrator/runs/{run_id}`
  - `POST /api/v1/orchestrator/actions/{action_id}/approve`
- Added persisted run store `data/processed/orchestrator_runs.json` with:
  - deterministic action graph
  - approval gating metadata
  - idempotent run replay by `site_id + idempotency_key`
  - downstream refs to playbook / outreach job / calling session
- Action graph currently emits:
  - `compile_playbook`
  - `create_outreach_job`
  - `create_calling_session`
  - `schedule_follow_up_review`
- Approval-required behavior validated:
  - new runs start in `awaiting_approval`
  - approving outreach/calling actions executes those nodes and persists downstream refs
- Auto-execute behavior validated:
  - with `approval_required=false` and `auto_execute=true`, ready actions execute automatically
- Added docs/artifacts:
  - `spec/orchestrator-state-machine.md`
  - `artifacts/orchestrator-runbook.md`
  - `artifacts/orchestrator-smoke.json`
- Regenerated OpenAPI locally and kept eval green: `python3 eval/run_eval.py` -> **PASS**

## DG-009 progress (today)
- Added learning loop scaffold in `backend/api/app.py`:
  - `POST /api/v1/outcomes`
  - `GET /api/v1/outcomes/summary`
  - `POST /api/v1/learning/retrain-jobs`
- Extended lead outcome contract with attribution fields:
  - `attribution_channel`
  - `attribution_playbook_id`
  - `attribution_orchestrator_run_id`
  - `attribution_signal_keys`
  - `attribution_source_session_id`
  - `attribution_source_job_id`
- Learning summary now reports:
  - top channels
  - top signal keys
  - attributed outcome count
  - attribution completeness metrics
  - promotion-readiness snapshot
- Added persisted learning job store `data/processed/learning_jobs.json`.
- Learning job endpoint now enforces scaffolded promotion safety checks:
  - minimum outcome count
  - minimum attribution completeness
  - approver required for non-dry-run promotion
- Added docs/artifacts:
  - `artifacts/learning-loop-v1.md`
  - `artifacts/policy-promotion-checklist.md`
  - `artifacts/learning-loop-smoke.json`
- Smoke validation:
  - wrote attributed `won` outcome for `site_ab25957991a6`
  - summary returned updated attribution metrics
  - dry-run retrain job completed
  - stricter live promotion request blocked as expected
- Regenerated OpenAPI locally and kept eval green: `python3 eval/run_eval.py` -> **PASS**

## DG-010 progress (today)
- Added governance + manager command scaffold in `backend/api/app.py`:
  - `GET /api/v1/governance/policies`
  - `POST /api/v1/governance/policies/validate`
  - `GET /api/v1/manager/command`
- Added governance config file:
  - `config/governance_policy.json`
- Approval endpoint `POST /api/v1/orchestrator/actions/{action_id}/approve` now enforces role-aware governance validation before action execution.
- Orchestrator runs now maintain queryable `governance_audit[]` records for:
  - run creation
  - policy validation
  - approval validation
  - action execution
- Manager command now surfaces:
  - approval-queue risk
  - blocked-action risk
  - low-confidence risk
  - low-attribution-completeness risk
  - coaching actions tied to pipeline truth
- Added docs/artifacts:
  - `spec/governance-controls-v1.md`
  - `artifacts/manager-command-spec.md`
  - `artifacts/governance-smoke.json`
- Smoke validation:
  - governance validate correctly denied `rep` role and allowed `manager`
  - approval endpoint returned `403` for unauthorized role
  - manager command returned risk/coaching payload
- Regenerated OpenAPI locally and kept eval green: `python3 eval/run_eval.py` -> **PASS**

## Operating note
- No PM2 reload yet for DG-005/DG-006/DG-007/DG-008/DG-009/DG-010 changes because Codex is testing the currently running build.
- Safe next move after tests finish: reload demo app and smoke playbook + outreach + calling + orchestrator + learning + governance endpoints live.

## Immediate next steps
1. Let Codex finish current test pass on the live stack.
2. If green, reload PM2 and expose DG-005 + DG-006 + DG-007 + DG-008 + DG-009 + DG-010 live.
3. Then harden closure criteria and live-smoke all DG-005..DG-010 surfaces together before pushing deeper autonomy.
