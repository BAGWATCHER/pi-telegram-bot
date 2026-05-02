# DemandGrid — North Star (Superhuman Sales OS)

Updated: 2026-04-17

## 1) Mission
Build the most advanced AI sales operating system for any vertical, so an entry-level rep can execute at top-rep level and teams can scale revenue with fewer manual bottlenecks.

DemandGrid is a **whole-system revenue engine** (data + decisions + execution + learning), not a chatbot product.

## 2) Product Definition (End State)
A closed-loop, multi-agent sales system that:
1. Detects high-probability opportunities from real-world signals.
2. Investigates and validates each opportunity with evidence.
3. Selects best offer, channel, timing, and sequence.
4. Executes outreach (AI-assisted + autonomous modes).
5. Learns from outcomes and continuously improves conversion + profit.

## 3) What DemandGrid Is / Is Not
### Is
- Channel-agnostic sales OS (field, phone, email, SMS, partner, inbound follow-up)
- Vertical-extensible (roofing, solar, HVAC, battery, future domain packs)
- Multi-agent-ready (research, outreach, calling, follow-up, manager intelligence)
- Outcome-optimized (profit + win rate + operator productivity)

### Is Not
- Door-to-door-only tool
- LLM chat layer without execution loops
- Lead list generator without evidence and feedback learning

## 4) System Architecture (North Star)
## A. Revenue Graph (Truth Layer)
- Unified entity graph: property/site, business/account, contacts, offers, interactions, outcomes
- Identity resolution + dedupe + provenance tracking
- Coverage/freshness/quality scores per entity

## B. Signal Mesh (Intelligence Inputs)
- Trigger feeds: permits, weather, outages, flood risk, tariff/utility, market events
- Behavioral signals: channel engagement, response history, cadence state
- Ops signals: rep actions, SLA, route context, stage changes

## C. Decision Engine (Brains)
- Opportunity score (value, fit, urgency, confidence)
- Next-best-action policy (what to do now)
- Offer/channel/timing recommendation
- Risk/guardrail policy (suppress weak or unsafe sends)

## D. Execution Layer (Agent Workforce)
- Outreach agent(s): message generation + sequence execution
- Calling agent(s): pre-call brief, live objection support, post-call extraction
- Follow-up agent(s): reminders, reactivation, no-response strategy
- Manager agent: forecast/risk/coaching interventions

## E. Learning Layer (Moat)
- Outcome capture: contacted, replied, qualified, booked, won/lost + reason
- Attribution by signal + playbook + channel + rep/agent
- Continuous model/policy updates with eval gates

## F. Governance Layer
- Auditability, permissioning, compliance flags, human approval thresholds
- Brand/policy constraints for autonomous actions
- Rollback and safe-mode controls

## 5) Operating Loops
### Loop 1 — Opportunity Intelligence
Ingest + score + rank high-value leads with explainable evidence.

### Loop 2 — Investigation
Attach traceable evidence package and confidence level; suppress low-confidence leads.

### Loop 3 — Outreach / Calling Execution
Generate machine-usable payloads for outreach/calling agents with channel and compliance guidance.

### Loop 4 — Workflow Guidance
Drive rep/agent next step with explicit action, script angle, verification checklist, and risk note.

### Loop 5 — Closed-Loop Learning
Feed outcomes back into ranking, routing, sequencing, and messaging.

## 6) Current Stage (as of 2026-04-17)
### Foundation Shipped
- Broad scored board + trigger overlays
- Investigation/outreach APIs
- Pi-style copilot surface (`pi-tool-router-v1`)
- Workflow status + route planning + eval harness

### In Progress
- Permit/data join-quality hardening (EZ-022)
- Chat reliability parity and stronger grounding behavior

### Not Yet Complete
- Full multi-agent orchestration
- Deep calling-agent integration
- High-autonomy execution with robust approvals/risk controls

Interpretation: **DemandGrid is at foundation + guided execution stage, moving toward autonomous execution stage.**

## 7) North Star Metrics (Platform-Level)
1. Revenue per 1,000 scored opportunities
2. Qualified-opportunity rate in top-ranked cohort
3. Time-to-first-meaningful-contact
4. Win rate uplift vs non-AI baseline
5. False-positive outreach rate (must remain low)
6. Gross profit per operator hour
7. Autonomous action success rate (for approved auto-actions)
8. New-rep performance lift vs historical baseline

## 8) Data Moat Priorities
1. Parcel/address/business identity quality
2. Trigger evidence depth + recency + provenance
3. Contactability and channel-reachability context
4. Utility/tariff + economics normalization
5. Outcome telemetry completeness and quality

## 9) Product Principles (Non-Negotiables)
- Evidence-first: recommendations must be explainable and traceable.
- Automation-safe: autonomy only with confidence + policy guardrails.
- Channel/vertical agnostic: core system reusable across sales motions.
- Outcome-first: optimize for conversion + margin, not activity vanity metrics.
- Noob-amplifying UX: system should make correct actions obvious.
- Eval-gated shipping: no lane closes without measurable pass criteria.

## 10) Dark-Factory Alignment Rule
A lane is in-scope only if it improves at least one:
- Qualified opportunity quality/volume
- Outreach precision/safety
- Sales effort efficiency
- Conversion/profit outcomes
- Autonomous execution reliability

If none apply, deprioritize.

## 11) Build Phasing (Directional)
### Phase A — Reliable Foundation
Data quality, evidence contracts, deterministic scoring, operator workflows, eval reliability.

### Phase B — Superhuman Guidance
Next-best-action excellence, objection intelligence, playbook compilation, rep uplift.

### Phase C — Autonomous Revenue Pods
Connected outreach/calling/follow-up agents with approval policies and safe autonomy.

### Phase D — Self-Improving Sales Network
Cross-vertical model/policy learning, manager autopilot, enterprise governance at scale.

## 12) Immediate Execution Focus
1. Finish EZ-022 data hardening and coverage quality.
2. Raise copilot grounding/reliability to BearingBrain-level discipline.
3. Introduce universal sales schema for multi-vertical expansion.
4. Stand up agent orchestration contract for outreach + calling + follow-up lanes.
5. Expand closed-loop training pipeline from outcomes to policy/model updates.

## 13) Agent Platform Rule
DemandGrid should be built as both:
- a human dashboard/control room
- a reusable plugin/tool platform for agents

This means the UI stays important, but the backend must increasingly expose agent-callable contracts so systems like Chow, voice agents, and future coding/OpenClaw-style agents can execute through the same DemandGrid truth layer.

Chow is expected to plug into DemandGrid as an execution agent for calling, emailing, research, and result reporting rather than operating as a separate drifting system.
