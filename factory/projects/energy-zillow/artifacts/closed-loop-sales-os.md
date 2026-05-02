# Closed-Loop Sales OS

DemandGrid is no longer just a scoring map. The intended operating loop is:

1. Target the best lead.
2. Tell the operator what to do next.
3. Capture what really happened.
4. Learn which lanes, objections, and ZIPs make money.
5. Feed that back into routing, messaging, and ranking.

## Live Pieces

- Site detail now leads with a plain-English playbook.
- Operators can save workflow state and structured lead outcomes.
- Outcome data includes:
  - stage
  - product
  - objection
  - win/loss reason
  - realized revenue
  - realized profit
- API now exposes:
  - `GET/PUT /api/v1/operator/outcome/{site_id}`
  - `GET /api/v1/operator/outcomes`
  - `GET /api/v1/operator/outcomes/summary`

## Current Operator Contract

For each lead, the UI should answer four things without making the rep think:

- What do I lead with?
- What exact step do I take now?
- What proof supports that move?
- What should I log after the touch?

The task-runner block is the current UI expression of that contract.

## Learning Contract

The learning layer should summarize:

- wins/losses by lane
- win rate by ZIP
- realized profit by ZIP and lane
- top objections
- top win/loss reasons

That summary should be usable both by the UI and by future reranking logic.

## Ranking Roadmap

Closed-loop feedback should affect ranking in stages:

1. Analytics only
- show outcome summaries and nearby win patterns
- do not alter scoring yet

2. Soft guidance
- adjust operator guidance based on logged objections, reasons, and wins
- examples:
  - if roofing is winning in a ZIP after storm triggers, push roofing first
  - if a lane is repeatedly lost on price, lower confidence and change the opener

3. Score influence
- add bounded boosts/penalties to routing and product choice from:
  - lane win rate
  - realized profit per win
  - objection frequency
  - loss reasons

4. Profit optimization
- optimize toward gross profit per operator hour, not just route score or close probability

## Guardrails

- Do not let sparse outcome data hijack ranking.
- Require minimum sample sizes before learning affects score.
- Keep product-readiness honesty intact; outcomes should not paper over missing trigger evidence.
- Preserve manual override for reps when field reality beats the model.
