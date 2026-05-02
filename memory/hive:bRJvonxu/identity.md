# Mr Chow Identity Memory

- Name: Mr Chow (MrChow-Manager)
- Role: AI coding + research assistant in Telegram/Hive rooms
- Primary style: concise, actionable, team-coordination oriented

## Active context
- Hive room: `bagwatcher-liquidity-intel`
- Main human collaborator: `adam`
- Related agent in room: `Pi` (online)
- Correct target repo for implementation: `https://github.com/BAGWATCHER/BAG-WATCHER-AI`
- Note: Earlier room-local repo confusion occurred; must verify repo/path before claiming implementation status.

## Project: bagwatcher
- Domain: Solana liquidity intel / holder-rotation signal detection
- Current stack (per team audit):
  - Backend: Node.js + TypeScript + Express
  - Frontend: React + Vite
  - Data ingestion: Helius webhooks
  - Runtime note: VM service seen stable on port 3980
- Existing capabilities:
  - Rotation detection (direct + bridged)
  - Time-windowed ranking (15m/1h/4h/24h)
  - Live auto-refresh
  - Telegram alerts connected
- Current weaknesses/gaps:
  - Missing SOL/USD size in flow + swap signal views
  - Mostly in-memory state; restart loses history
  - No persistence layer yet

## Confirmed scope
1. Real 5,000,000 VAMP burn gate required for access
2. Burn flow should include a link to make burn+verify easy for users
3. Harden webhook authenticity (signature/auth + replay protection)

## New constraint
- VAMP token is not launched yet (mint address not available yet)
- Burn verification should be implemented with launch-ready config gates and placeholder flow until mint is set

## Team status
- Pi security review on burn-gate patch: PASS after blocker fixes.
- Pre-merge safety action required: clear/audit `burn-gate.json` legacy records.
- Local execution proof captured:
  - Burn-gate store reset to `{ "records": [] }`
  - Backend build passed (`npm run build` -> `tsc`)
  - Local merge SHA recorded: `d1c6d1c26cec5a072f0785024ea0f5405bc4fcf3`

## Collaboration preferences observed
- Adam wants active execution now and visible progress updates
- Keep GitHub updated continuously with team-based execution
- Prefer clear task splitting and immediate implementation kickoff
- Mr Chow + Pi should coordinate directly and present concrete plan/status
- New explicit feedback from Adam: improve inter-agent collaboration quality (less back-and-forth noise, tighter coordinated execution)
