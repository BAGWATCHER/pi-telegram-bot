# DemandGrid Agent Calling Contract v1

Updated: 2026-04-18
Framework: `dg-agent-calling-v1`
Status: local scaffold

## Purpose
Provide a machine-usable interface for running a calling workflow from a compiled DemandGrid playbook, with pre-call context, live session state, and structured outcome sync.

## Endpoints
- `POST /api/v1/agents/calling/sessions`
- `GET /api/v1/agents/calling/sessions/{session_id}`
- `POST /api/v1/agents/calling/events`

## Create session input
```json
{
  "site_id": "site_9dc98e41c5af",
  "playbook_id": "optional_existing_playbook_id",
  "execution_mode": "agent_assist",
  "objective": "optional override",
  "preferred_channels": ["phone"],
  "strict_guardrails": true,
  "call_direction": "outbound"
}
```

## Create session behavior
- Compiles a playbook on demand when none is supplied.
- Generates a pre-call brief from the playbook.
- Persists session state in `data/processed/calling_sessions.json`.
- Prepares outcome sync target to `/api/v1/operator/outcome/{site_id}`.

## Session payload expectations
Every session should include:
- `session_id`
- `site_id`
- `playbook_id`
- `status`
- `call_direction`
- `pre_call_brief`
- `live_assist`
- `outcome_sync`
- `event_log[]`

## Event types accepted
- `session_started`
- `live_assist_requested`
- `transcript_note`
- `objection_logged`
- `no_answer`
- `follow_up_needed`
- `qualified`
- `won`
- `lost`
- `completed`
- `cancelled`
- `failed`

## Outcome sync behavior
- `qualified`, `won`, `lost` map directly into the lead outcome schema.
- `follow_up_needed` maps to `responded` when no explicit outcome override is provided.
- `no_answer` maps to `contacted` when no explicit outcome override is provided.
- Structured fields for objection, reason, transcript, and realized economics can be persisted during sync.

## Safety rules
- Keep the session queryable even if the call never connects.
- Preserve explicit event history rather than mutating away prior call state.
- Never let autonomous calling bypass playbook guardrails or operator stop conditions.
- Treat delivery/voice-provider wiring as a later adapter behind this contract.
