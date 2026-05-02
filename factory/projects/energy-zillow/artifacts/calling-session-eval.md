# DemandGrid Calling Session Eval

Updated: 2026-04-18
Status: local scaffold validated

## What shipped
DemandGrid now has a persisted calling connector stub that can:
- create a call session from a site or compiled playbook
- expose a pre-call brief
- record live session events
- sync qualifying outcomes into the lead outcome schema

## Endpoints
- `POST /api/v1/agents/calling/sessions`
- `GET /api/v1/agents/calling/sessions/{session_id}`
- `POST /api/v1/agents/calling/events`

## Persistence
- calling session store: `data/processed/calling_sessions.json`
- lead outcome sync target: `data/processed/lead_outcomes.json`

## Smoke validation
Artifact: `artifacts/calling-session-smoke.json`

### Session create
- site: `site_9dc98e41c5af`
- result: `200`
- session state: `ready`
- pre-call brief populated with:
  - objective
  - opener
  - next best action
  - objection map

### Live transition
- event: `session_started`
- result: `200`
- session state moved to `live`
- latest transcript excerpt persisted into live assist context

### Outcome extraction + sync
- event: `qualified`
- result: `200`
- session state moved to `completed`
- `lead_outcome.status` synced to `qualified`
- objection and reason fields persisted through sync

## Why this matters
This gives DG-007 a real bridge into the learning loop:
- call workflows now have durable state
- post-call extraction is no longer hand-wavy
- orchestration can treat calls as explicit stateful actions
- outcomes can feed closed-loop policy and ranking lanes later

## Next follow-on
- add list/query surfaces for active sessions if operator queue needs it
- attach real telephony adapter later behind the same event model
- let DG-008 orchestrator call this contract directly as one action node
