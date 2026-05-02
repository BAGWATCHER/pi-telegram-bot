# DemandGrid Playbook Compiler v1

Updated: 2026-04-18
Status: local scaffold shipped, no PM2 reload yet
Framework: `dg-playbook-compiler-v1`

## Purpose
Turn a scored site into an executable, guardrail-aware workflow that a rep or downstream agent can actually run.

## Endpoints
- `POST /api/v1/playbooks/compile`
- `GET /api/v1/playbooks/{playbook_id}`

## Compile input
```json
{
  "site_id": "site_ab25957991a6",
  "objective": "optional override",
  "execution_mode": "rep_assist",
  "preferred_channels": ["phone", "email"],
  "strict_guardrails": true
}
```

## Output contract
Compiler returns:
- playbook id + compile timestamp
- objective
- execution mode
- channel order
- guardrail flags
- stop conditions
- opportunity snapshot
- ordered steps with `guardrail_flags` on every step
- objection map
- refs back to decision / signals / investigation / outreach / revenue graph
- learning context summaries when outcome history exists

## Current step model
1. Review context and choose opener
2. Run first touch or manual review gate
3. Run follow-up touch if still active
4. Log outcome and realized value

## Guardrails
- Respect outreach policy and suppression flags
- Stop on terminal lead state (`won`, `lost`, `closed`, `skip`)
- Require manual review when policy/compliance/review flags are present
- Force outcome capture so the learning loop can use the touch

## Why this matters
This is the bridge from analytics to execution. DemandGrid now has:
- data + signals
- decisioning
- outreach/investigation payloads
- closed-loop outcomes
- an executable playbook object that can feed outreach/calling/orchestrator lanes

## Immediate next lane tie-ins
- DG-006 can consume compiled playbooks as job inputs for policy-safe outreach sends
- DG-007 can use the same object for pre-call briefs and post-call extraction prompts
- DG-008 can treat playbooks as deterministic action graphs for orchestration

## Validation done
- local compile endpoint smoke-tested on solar + roofing examples
- OpenAPI regenerated successfully
- `python3 eval/run_eval.py` still PASS after scaffold landed
