# DemandGrid — Agent Platform Context

Updated: 2026-04-21

## Direction
DemandGrid should be both:
- a dashboard/control room for humans
- a shared plugin/tool platform for agents

The UI remains important. It is the operator and manager workspace.

The backend should increasingly behave like a reusable sales-intelligence substrate that other agents can call directly.

## Architectural Stance
DemandGrid should not depend on one monolithic built-in agent.

Instead:
- DemandGrid owns data, scoring, contact state, execution state, next actions, and memory
- external agents consume DemandGrid through APIs/tool calls
- the UI is one client of the same system, not the only interface

This keeps the system usable from:
- the DemandGrid dashboard
- Chow
- voice agents
- outreach/email agents
- future coding/OpenClaw-style agents

## Chow Alignment
Chow should plug into DemandGrid as an execution agent, not drift as a separate system.

Target role for Chow:
- research businesses and leads
- fetch next-best leads/tasks from DemandGrid
- place calls through the external calling stack
- send emails/follow-ups through external execution paths
- report results back into DemandGrid
- escalate hot opportunities to the human operator

## Core Model
DemandGrid remains:
- dashboard + control room
- shared sales intelligence API/tool layer
- agent execution surface

That means:
- humans use the UI to inspect, guide, and approve
- agents use DemandGrid to decide and execute
- all outcomes come back into one shared memory loop

## Required Agent Surface
DemandGrid should expose clean agent-callable interfaces for:
- next task / next lead
- execution brief
- contact paths
- voice brief
- email brief
- next-best action
- interaction/result ingestion
- outcome logging
- live execution status

Representative examples:
- `GET /api/v1/agent/tasks/next`
- `POST /api/v1/agent/tasks/{id}/claim`
- `POST /api/v1/agent/tasks/{id}/result`
- `GET /api/v1/lead/{site_id}/execution-brief`

Exact endpoint shapes can evolve, but this is the intended contract direction.

## UI Requirement
Do not remove the UI.

The dashboard remains the command center for:
- manager mode
- territory control
- lead review
- contact history
- agent activity visibility
- approvals and overrides

The right model is:
- DemandGrid UI for supervision and control
- DemandGrid APIs/tools for agent execution

## Immediate Build Implication
Near-term architecture should support:
1. Chow using DemandGrid to start calling and emailing leads
2. DemandGrid showing live agent activity in the dashboard
3. One shared source of truth for tasks, outcomes, and next actions
4. Approval gates where autonomous actions need human control
