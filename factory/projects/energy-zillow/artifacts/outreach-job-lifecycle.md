# DemandGrid Outreach Job Lifecycle

Updated: 2026-04-18
Status: local scaffold validated

## What shipped
DemandGrid now has a persisted outreach connector stub that sits between compiled playbooks and future delivery providers.

### Endpoints
- `POST /api/v1/agents/outreach/jobs`
- `GET /api/v1/agents/outreach/jobs/{job_id}`
- `POST /api/v1/agents/outreach/events`

### Persistence
- Store path: `data/processed/outreach_jobs.json`
- Playbooks remain stored in `data/processed/compiled_playbooks.json`

## Lifecycle behavior
### Job creation
- Accepts `site_id` and optional `playbook_id`
- Compiles a playbook automatically if needed
- Resolves channel from requested channel or playbook recommendation
- Applies suppression/compliance policy before queuing
- Supports `idempotency_key` reuse for safe retries

### Policy outcomes
- `allow` -> job enters `queued`
- `manual_review` -> job still records as `queued`, but `auto_send_allowed` is false in playbook context
- `blocked` -> job is persisted as `blocked` with explicit reasons

### Event transitions
- `queued -> sent -> delivered -> replied/completed`
- `queued/sent/delivered -> failed`
- `queued/sent/delivered -> cancelled`
- blocked jobs reject non-terminal send transitions

## Smoke validation run
### Allowed job
- site: `site_ab25957991a6`
- create -> `queued`
- get -> `queued`
- event `sent` -> `sent`
- idempotent replay with same key -> reused existing job

### Blocked job
- site: `site_6fad7a96b7b2`
- create -> `blocked`
- reason -> `lead_skip`

## Why this matters
This gives DG-006 a real object for downstream execution instead of hand-wavy connectors:
- the playbook compiler now has a machine consumer
- future delivery workers can poll/update one persisted lifecycle record
- orchestration can reason over explicit state instead of ad hoc prompts

## Next follow-on
- expose list/query endpoints if operators need queue browsing
- wire actual provider adapters behind the same event contract
- add eval coverage for suppression enforcement + lifecycle replay
