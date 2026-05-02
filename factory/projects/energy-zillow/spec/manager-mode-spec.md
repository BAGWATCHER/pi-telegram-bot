# DemandGrid Manager Mode Spec

Updated: 2026-04-20
Status: draft
Aligned with: `spec/north-star-sales-ai-platform.md`, `spec/dg-superhuman-sales-lane-plan-v1.md`, `spec/governance-controls-v1.md`

## Purpose
Define the daily command center for DemandGrid: a manager-simple surface that turns raw targeting and learning data into clear operator direction.

Manager mode is not another dashboard. It is the shortest path from system truth to next action.

## User Promise
When the operator opens DemandGrid, the system should answer:
- what to work now
- what to ignore
- why this is the best use of time
- what action to take next
- what the expected upside is

## Core Behavior
Manager mode should synthesize:
- ranked queue pressure
- best lead or best territory
- route readiness
- lane concentration
- recent outcomes and objections
- risk / confidence / evidence gaps

The output should be concise, specific, and action-oriented.

## Shippable Blocks

### Block 1: Daily Brief
Single-screen summary that returns:
- top work lane
- top target list
- follow-ups to clear first
- route recommendation
- current evidence quality
- one-line manager recommendation

Acceptance:
- a new operator can understand the day’s plan without inspecting raw scoring fields
- the brief is visible on first load and updates with current scope

### Block 2: Command Actions
Each recommendation must have a direct action:
- open best lead
- start route
- generate opener
- generate follow-up
- mark outcome
- move to next lead

Acceptance:
- no recommendation is a dead end
- every high-priority item has at least one click-to-act path

### Block 3: Territory Focus
Support territory-level decisions, not only address-level decisions:
- best ZIP or cluster to work today
- lane recommendation by territory
- weak territories to deprioritize
- route sequencing for field work

Acceptance:
- the system can recommend where to spend the next block of selling time
- the operator can switch between territory and lead views without losing context

### Block 4: Sales Guidance
Expose operator-simple guidance, not analyst detail:
- recommended pitch angle
- likely objection
- proof point or trigger to cite
- confidence note
- next-best sentence or task

Acceptance:
- first-time users see the action, not just the model
- guidance is short enough to use live in the field or on the phone

### Block 5: Closed-Loop Learning
Manager mode must surface what the system has learned:
- contacted / replied / qualified / won / lost counts
- reason patterns
- lane performance
- follow-up backlog
- missing attribution gaps

Acceptance:
- the dashboard shows what is being learned from the current scope
- weak learning signals are made visible, not hidden

### Block 6: Guardrails
Manager mode must preserve the north-star governance model:
- confidence and evidence gaps stay visible
- low-quality recommendations are suppressible or clearly labeled
- autonomous actions remain policy-gated
- auditability is preserved for every action path

Acceptance:
- the surface never implies quote-grade certainty when the data is proxy-grade
- approval or review requirements are obvious before execution

## MVP Layout
1. Header: current territory, queue pressure, and one-line command
2. Daily Brief card
3. Priority stack: work now, follow up, deprioritize
4. Best lead / best territory card
5. Route panel
6. Learning and risk panel

## Not In Scope
- enterprise BI dashboards
- deep analytics exploration views
- generic CRM replacement behavior
- autonomous execution without governance checks

## Definition Of Done
Manager mode is shippable when:
- the operator can tell what to do in under 10 seconds
- the system can recommend the best lane for the day
- every top recommendation has a direct action
- outcome learning is visible in the same surface
- governance and confidence cues remain explicit

