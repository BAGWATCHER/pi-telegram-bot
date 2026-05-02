# DemandGrid Governance Controls v1

Updated: 2026-04-18
Framework linkage: `dg-orchestrator-v1`
Status: local scaffold

## Purpose
Add explicit approval policy, validation, and manager-readable control surfaces so autonomous execution stays bounded.

## Endpoints
- `GET /api/v1/governance/policies`
- `POST /api/v1/governance/policies/validate`
- `GET /api/v1/manager/command`
- enforced via `POST /api/v1/orchestrator/actions/{action_id}/approve`

## Current policy model
Config file: `config/governance_policy.json`

Current controls:
- approval role allowlists by action type
- actor id required on approval validation
- approval-required mode cannot be bypassed by auto-execute
- audit records should be attached to orchestrator runs
- manager command risk thresholds for attribution completeness + site confidence

## Validation contract
`POST /api/v1/governance/policies/validate` checks:
- run exists
- action exists
- actor role is allowed for the action type
- actor id is present
- action is still awaiting approval

## Approval enforcement
`POST /api/v1/orchestrator/actions/{action_id}/approve` now:
- runs governance validation first
- persists validation result into the orchestrator audit trail
- blocks unauthorized roles with `403`
- only executes action after governance validation passes

## Queryable audit trail
Orchestrator runs now carry `governance_audit[]` entries for:
- run creation
- explicit policy validation calls
- approval validation decisions
- action execution records

## Scope note
This is governance scaffolding, not enterprise IAM.
DG-010 v1 goal here is policy visibility, role gating, and auditability.
Full enterprise role systems can sit behind the same contracts later.
