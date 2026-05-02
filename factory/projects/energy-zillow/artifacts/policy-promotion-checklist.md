# DemandGrid Policy Promotion Checklist

Updated: 2026-04-18
Status: local scaffold

Before allowing non-dry-run promotion from the learning loop, verify:

## Data quality
- Outcome count meets the minimum configured threshold.
- Attribution completeness meets the configured threshold.
- Outcome rows include channel + signal/playbook provenance for enough samples.

## Safety
- Promotion request has an explicit approver.
- Promotion intent is documented in the job note.
- Latest eval remains PASS on the current board snapshot.

## Commercial sanity
- Realized profit is not being inferred from sparse wins only.
- Top reasons/objections are coherent with recent field activity.
- No single ZIP or tiny cohort is dominating the signal unfairly.

## Execution
- Use `dry_run=true` first.
- Review `checks[]` from `POST /api/v1/learning/retrain-jobs`.
- Only proceed with live promotion when every required check passes.

## Current state
This checklist is enforced as a scaffolded policy gate in the learning job endpoint; it is not yet a full governance system.
DG-010 should later own enterprise-safe role and approval enforcement.
