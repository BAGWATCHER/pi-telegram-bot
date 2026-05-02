# DemandGrid Agent Outreach Contract v1

Updated: 2026-04-18
Framework: `dg-agent-outreach-v1`
Status: local scaffold

## Purpose
Provide a machine-usable contract for turning a compiled DemandGrid playbook into a policy-safe outreach job with persisted lifecycle state.

## Endpoints
- `POST /api/v1/agents/outreach/jobs`
- `GET /api/v1/agents/outreach/jobs/{job_id}`
- `POST /api/v1/agents/outreach/events`

## Create job input
```json
{
  "site_id": "site_ab25957991a6",
  "playbook_id": "optional_existing_playbook_id",
  "idempotency_key": "optional-client-key",
  "requested_channel": "phone",
  "execution_mode": "agent_assist",
  "objective": "optional override",
  "preferred_channels": ["phone", "email"],
  "strict_guardrails": true,
  "dry_run": true
}
```

## Create job behavior
- Reuses an existing job when `site_id + idempotency_key` matches a stored record.
- Compiles a playbook on demand when `playbook_id` is not provided.
- Applies outreach policy and playbook guardrails before creating a sendable job.
- Blocks jobs when compliance/suppression rules fail.

## Job state model
- `blocked`
- `queued`
- `sent`
- `delivered`
- `replied`
- `failed`
- `cancelled`
- `completed`

## Event types accepted
- `queued`
- `sent`
- `delivered`
- `reply_received`
- `replied`
- `bounced`
- `failed`
- `cancelled`
- `completed`

## Job payload expectations
Every job should include:
- `job_id`
- `site_id`
- `playbook_id`
- `status`
- `dispatch_mode`
- `requested_channel`
- `resolved_channel`
- `policy.decision`
- `policy.block_reasons`
- `send_context.channel_order`
- `delivery.*`
- `event_log[]`

## Safety rules
- Never create a sendable job that bypasses DemandGrid suppression/compliance flags.
- Keep blocked jobs queryable for audit and operator review.
- Preserve idempotency so downstream connectors can retry safely.
- Treat this v1 lane as connector scaffolding; actual external delivery providers can be wired later behind the same contract.
