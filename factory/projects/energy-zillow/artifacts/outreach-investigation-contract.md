# Outreach + Investigation Contract (Phase-1)

Updated: 2026-04-17

## Purpose
Define the minimum output contract needed to connect DemandGrid intelligence to AI outreach/investigation systems.

## Investigation payload (required)
- `site_id`
- `address`
- `primary_product`
- `secondary_product`
- `priority_score`
- `confidence`
- `evidence[]`:
  - `source` (e.g., FEMA/OpenEI/permit)
  - `field`
  - `value`
  - `as_of`
  - `quality` (`verified|proxy|missing`)
- `risk_flags[]`
- `suppression_reasons[]` (if outreach should be blocked)

## Outreach payload (required)
- `site_id`
- `target_segment`
- `recommended_channel` (`field|phone|email|sms|partner`)
- `message_angles[]`
- `cta`
- `offer_priority` (`primary|secondary`)
- `compliance_flags[]`
- `handoff_context`:
  - `why_now_summary`
  - `operator_action_summary`
  - `investigation_ref`

## Safety rules (minimum)
- No auto-outreach if confidence below threshold.
- No auto-outreach if suppression reasons contain critical blocker.
- All generated outreach must carry evidence reference.

## Eval hooks to add
- `outreach_payload_contract`
- `investigation_traceability`
- `outreach_safety_guardrails`
- `action_handoff_contract`
- `closed_loop_feedback_contract`
