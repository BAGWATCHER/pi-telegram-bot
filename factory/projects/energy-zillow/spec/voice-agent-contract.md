# DemandGrid Voice Agent Contract v1

Updated: 2026-04-21
Framework: `dg-voice-bridge-v1`
Status: local integration-ready scaffold

## Purpose

Provide a narrow integration contract so an external voice/telephony system can:
- fetch a clean call brief from DemandGrid
- push call lifecycle status back into DemandGrid
- push final call results back into DemandGrid

The voice system is treated as an execution adapter.

DemandGrid remains the decision layer, contact-intelligence layer, and learning sink.

## Endpoints

- `GET /api/v1/voice/site/{site_id}/brief`
- `POST /api/v1/voice/calls/status`
- `POST /api/v1/voice/calls/result`

## Voice Brief

The brief should give the external voice system:
- lead identity
- phone path when available
- fallback channel if voice is not possible
- product to pitch
- opener / script angle
- why now
- desired outcome
- objection expectations
- stop / transfer rules
- latest known call session summary

## Status Update Input

```json
{
  "site_id": "site_123",
  "session_id": "optional_existing_call_session",
  "provider_call_id": "optional_provider_call_id",
  "status": "dialing|ringing|answered|live|voicemail|busy|no_answer|completed|cancelled|failed",
  "detail": "optional status note",
  "transcript_excerpt": "optional live transcript snippet",
  "metadata": {}
}
```

## Result Update Input

```json
{
  "site_id": "site_123",
  "session_id": "optional_existing_call_session",
  "provider_call_id": "optional_provider_call_id",
  "disposition": "voicemail|no_answer|follow_up|callback|qualified|won|lost|completed|transferred_human",
  "detail": "optional result note",
  "transcript_excerpt": "optional transcript excerpt",
  "objection": "optional objection",
  "reason": "optional win/loss/follow-up reason",
  "outcome_status": "optional explicit DemandGrid outcome override",
  "callback_at": "optional ISO timestamp",
  "needs_human": false,
  "next_best_action": "optional next step",
  "human_transfer_target": "optional closer/team",
  "realized_revenue_usd": null,
  "realized_profit_usd": null,
  "metadata": {}
}
```

## Result Behavior

On a result write, DemandGrid should:
- update the underlying calling session
- sync lead outcome when appropriate
- create a phone interaction record
- update operator workflow when there is a clear next state

Current workflow mapping:
- `won` -> `closed`
- `qualified`, `follow_up`, `callback`, `transferred_human`, or `needs_human=true` -> `follow_up`
- `voicemail`, `no_answer`, `busy` -> `contacted`

## Transfer / Handoff Expectations

The external voice system should escalate to a human when:
- prospect explicitly asks for a person
- prospect is qualified and wants inspection, quote, or pricing now
- objection handling exceeds the voice agent’s allowed scope

DemandGrid exposes this as guidance in the voice brief, not hard telephony logic.

## Integration Notes

- If no active session exists, DemandGrid can bootstrap one automatically from the site and playbook context.
- If the lead has no primary phone, DemandGrid will surface `voice_ready=false` and provide a fallback channel recommendation.
- This contract is intentionally adapter-friendly so LiveKit, Asterisk, Twilio, or another external system can connect without changing DemandGrid’s core model.
