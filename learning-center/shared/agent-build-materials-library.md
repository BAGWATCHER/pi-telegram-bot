# Agent Build Materials Library (Seed)

Purpose: keep a practical, reusable inventory of tools/services we can plug into future agents.

## How to use this
- Add only tools with a clear build use-case.
- Tag confidence as `verified`, `tested-local`, or `candidate`.
- Store at least one source URL for every entry.
- Prefer short implementation notes over marketing copy.

## Library

| Category | Tool | Link | Primary use in agents | Auth/hosting | Confidence | Notes |
|---|---|---|---|---|---|---|
| Coding harness | Pi Coding Agent | https://github.com/badlogic/pi-mono | Lightweight coding-agent runtime | OAuth/API keys | tested-local | Active in this VM |
| Workflow orchestration | Archon | https://github.com/coleam00/Archon | Multi-node harnesses, approval gates, replay | CLI + repo config | tested-local | Used for DemandGrid harnesses |
| Plan review HITL | Plannotator Pi extension | https://www.npmjs.com/package/@plannotator/pi-extension | Human review/approval for plans | Pi extension (`pi install`) | tested-local | Installed locally |
| Scheduling | Cal.diy | https://www.cal.diy/ | Self-hosted scheduling/calendar layer for booking agents | Self-hosted (see docs) | candidate | Added per user request; evaluate API + OAuth fit before production |
| LLM provider | Codex CLI | https://developers.openai.com/codex/cli | High-quality coding/analysis nodes | OAuth/API | tested-local | Usage limits can block long runs |
| LLM provider | Claude Code | https://claude.ai/code | Coding/review nodes | OAuth/API | tested-local | Current VM login not active in Archon title side-path |

## Next additions queue
- Calendar event APIs + webhook callbacks (for appointment state machines)
- Outbound comms connectors (email/SMS/voice)
- Browser automation backends with stable auth/session persistence
- Durable vector/graph memory stores with retrieval contracts
