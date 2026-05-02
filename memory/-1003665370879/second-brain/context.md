# Chow Context Bundle

# SOUL.md

## Identity
- Name: Mr Chow
- Mode: Server-side operator + coding/research assistant
- Scope: Chow-only implementation

## Non-Negotiables
- Protect identity continuity and operational memory
- Keep actions verifiable and reversible when possible
- Keep Jose isolated unless explicitly requested

## Current Runtime Snapshot
- Host: Ubuntu `/home/ubuntu`
- PM2 core includes `partsbrain`, `rico-*`, `chow`, `hive`, `horus-relay`, `energy-zillow-demo`, `catholic-shop-demo`
- Preferred VM target: Azure `40.75.10.4` (`ubuntu`, key `~/.ssh/azure_rico_key`)
- Azure: `awscli` installed; AWS creds still missing (`sts get-caller-identity` fails)
- GitHub state: no git remotes configured in `/home/ubuntu/partsbrain/web` or `/home/ubuntu/BAG-WATCHER-AI`; active `gh` account `BAGWATCHER`
- Archon/Pi tooling update (2026-04-21):
  - Archon CLI binary installed (`/usr/local/bin/archon`, v0.3.6, commit `59cda08e`) but this build rejects `provider: pi` in workflow validation
  - Bun installed (`~/.bun/bin/bun`, v1.3.13); Archon source clone at `/home/ubuntu/Archon` (commit `5ed38dc7`) with Pi-capable runner wrapper `/home/ubuntu/pi-telegram-bot/scripts/archon-pi.sh`
  - Repo `/home/ubuntu/pi-telegram-bot` initialized as git (`main`); repo-level Archon files at `.archon/{config.yaml,workflows/archon-plannotator-piv.yaml,workflows/archon-plannotator-piv-pi.yaml,workflows/e2e-pi-codex-smoke.yaml,workflows/demandgrid-*}`
  - Pi local package installed: `npm:@plannotator/pi-extension` (project-local via `.pi/settings.json`)
  - Pi model preference now set to full model `openai-codex/gpt-5.4` (not mini) across repo Archon config/workflows
  - Mixed-provider plannotator workflow hits Claude auth block; Pi-only variant `archon-plannotator-piv-pi` runs with Pi global login and reaches clarify/plan phases
  - Previous run `6d062cc9250eed2534b32226af9bc8a1` was abandoned to unblock model switch and fresh reruns; `.pi/agent/auth.json` was restored from backup after accidental zero-byte overwrite
  - Pi OAuth health revalidated (2026-04-21): direct `npx pi --model openai-codex/gpt-5.4 -p` and Archon workflow `e2e-pi-oauth-check` both PASS

## Last Reflected
- 2026-05-02T04:24:50.637Z

---

# USER.md

## Preferences Snapshot
- User preference section unavailable in identity snapshot

## Last Reflected
- 2026-05-02T04:24:50.637Z

---

# MEMORY.md

## Source of Truth
- Protected identity: /home/ubuntu/pi-telegram-bot/memory/-1003665370879/identity.md
- Rolling summaries: /home/ubuntu/pi-telegram-bot/memory/-1003665370879/summaries.md

## Projects Snapshot
- Projects section unavailable in identity snapshot

## Recent Summary Window
[2026-03-28] Discussed BearingBrain agent-side priorities: OAuth-ready MCP/API auth scaffolding, agent eval reliability harness, and discoverability polish while keeping changes low-collision because other agents are working in parallel.
- Implemented OAuth/discovery/auth scaffolds: `/.well-known/oauth-protected-resource`, `/.well-known/oauth-authorization-server`, `POST /api/v1/oauth/introspect`, extended `lib/external-api-auth.ts` for bearer scaffolding + introspection, added scopes `mcp.read`/`mcp.write`, and added MCP auth mode gate in `app/api/mcp/route.ts` (`BEARINGBRAIN_MCP_AUTH_MODE=none|required`, default non-breaking behavior).
- Updated discoverability surfaces and docs: `/.well-known/openapi.json` expanded (v1.1.0 + BearerAuth + OAuth metadata/introspection paths), `/api/v1/capabilities` auth metadata, `/facts` OAuth links, `robots.ts` allowlist additions, and `docs/external-api-and-agentic-commerce.md` with OAuth env/config notes.
- Built eval harness: new `scripts/eval-agentic-v1.ts` + `npm run eval:agentic-v1`; validated search/stats/feeds plus quote/checkout idempotency and status polling locally (`http://127.0.0.1:3001`) and production (`https://bearingbrain.com`) successfully.
- Deployment/validation: `npm run build` passed after fixes; `pm2 restart partsbrain` was executed for OAuth rollout; lint still has unrelated pre-existing errors outside this scope and was intentionally not refactored.
- Decided strategy: keep growth surfaces open for adoption, but keep transactional/write surfaces protected; user prefers open MCP for reach, with recommendation to add guardrails (rate limits/abuse controls) rather than immediate hard auth flip.
- Built developer onboarding Phase 1 artifacts: plan doc `docs/plans/developer-api-onboarding-mvp.md`, new public page `GET /developers`, signup stub `POST /api/developers/signup` (returns `developerLeadRef`, 202), and isolated key scaffolds `GET/POST /api/developers/keys`, `DELETE /api/developers/keys/{keyId}`, `POST /api/developers/keys/{keyId}/rotate` using `x-developer-lead-ref`/Bearer `devlead_...` placeholder auth and free-tier-only scopes.
- Added quick onboarding curl flow to `/developers` (signup → create key), kept edits additive/surgical, and avoided PM2 restart for latest developer-scaffold pass to reduce collision risk with concurrent agents.
- Important config/values surfaced: `BEARINGBRAIN_MCP_AUTH_MODE`, `BEARINGBRAIN_OAUTH_BEARER_TOKENS`, `BEARINGBRAIN_OAUTH_INTROSPECTION_KEY`, `BEARINGBRAIN_OAUTH_AUTHORIZATION_SERVER`; free-tier scopes `search.read, stats.read, feeds.read, mcp.read`; write scopes remain upgrade-gated (`quote.write`, `checkout.write`).
- VM GitHub check result: no git remotes configured in `/home/ubuntu/partsbrain/web` or `/home/ubuntu/BAG-WATCHER-AI`; `gh auth status` active account is `BAGWATCHER` (secondary `maddefientist` inactive), so no confirmed switch to a new BearingBrain-only GitHub account yet.

---

- [2026-04-02] Focus was continuing Jose as a high-volume “whole-life Telegram manager” (not crypto-only), moving from snapshot awareness to actionable triage with backpressure behavior while keeping Jose separate from Chow.
- Research-driven architecture direction was confirmed: MTProto ingest + compression/triage + grounded retrieval + observability; then implementation proceeded directly in `/home/ubuntu/pi-telegram-bot`.
- Built new triage module `src/jose-triage.ts` with category classification, entity extraction (URLs/tickers/CA-like strings/emails), urgency scoring, dedupe/novelty keys, topic lanes, load-mode detection (`normal|high|flood`), brief/urgent/topic/ask formatting, and triage-state model.
- Updated `src/bot.ts` to use triaged context instead of raw snapshot dump, added Jose commands `/brief`, `/urgent`, `/topics`, `/events`, `/ask <query>`, and added high-load context gating so flood mode injects urgent-only compact context into prompts.
- Enhanced `src/jose-tg-ingest.ts`: fixed `lastMessageAt` epoch conversion, added persistent triage artifact output `data/jose-telegram-triage-state.json`, reduced flood-wait pressure by limiting message-history fetches, and added NDJSON delta event logging (`dialog_seen`, `unread_delta`) at `data/jose-telegram-events.ndjson`.
- Updated runtime script `start-jose-ingest.sh` env exports: `JOSE_TG_TRIAGE_STATE_PATH=/home/ubuntu/pi-telegram-bot/data/jose-telegram-triage-state.json`, `JOSE_TG_EVENTS_PATH=/home/ubuntu/pi-telegram-bot/data/jose-telegram-events.ndjson`, `JOSE_TG_PREVIEW_FETCH_DIALOGS=8` (plus existing snapshot path/poll settings).
- Important operational values/status: PM2 processes `jose` (id 25) and `jose-ingest` (id 26) restarted successfully and online; ingest logs now show mode/urgent/events (e.g., `mode=flood`, `unreadDialogs≈40`, `urgent≈39`, `events≈20`); snapshot file remains at `/home/ubuntu/pi-telegram-bot/data/jose-telegram-snapshot.json`.
- Memory file updated to capture new deployed state and preferences: `/home/ubuntu/pi-telegram-bot/memory/-1003665370879/identity.md` now records phase-1/1.5 triage, load gating, `/topics` and `/events`, and ingest hardening.
- Ongoing work status: core phase requested in-session is complete and deployed; remaining future step (not yet built) is full streaming queue workers/auto-actions beyond snapshot+delta logs.

---

- [2026-04-16] Worked on three main threads: Telegram voice pipeline stabilization (Mr Chow bot), Gauntlet AI prep/research, and initial multi-project “dark factory” scaffolding.
- Rotated Chow’s Gemini key in `/home/ubuntu/pi-telegram-bot/.env`, fixed PM2 runtime issues by recreating `chow` (now healthy under PM2, process id 11), and verified runtime env was picking up the new key (masked check).
- Voice pipeline was debugged end-to-end: root cause of “0-second” Telegram voice notes was raw PCM/WAV handling from Gemini TTS; ffmpeg was installed and TTS flow was patched to convert PCM/WAV -> OGG/Opus before send, with shared send helper logic in `src/bot.ts`.
- Voice persona tuning was updated for a deeper masculine tone (`VOICE_PROVIDER=gemini`, `VOICE_REPLY_VOICE=Charon`), and live voice samples were sent; exact celebrity cloning was discussed as risky, while “Mr Chow energy” custom voice roadmap was documented.
- Researched existing “Mr Chow / Leslie Chow / Ken Jeong” options: found deployable entries on cvoice and Jammable; key candidate identified as cvoice `voice_id=99f2fa9b-e55a-4889-bb00-02bc590026f8` (API-key gated), with preview sent for evaluation.
- Saved the paused custom voice project plan at `learning-center/tracks/chow-voice/mr-chow-voice-project.md` with a clear resume checklist for future implementation.
- Expanded Gauntlet learning assets: deep source-backed research across gauntlet/apply/catalyst/challenger pages, parsed course bundle/PDF signals, and added new dark-factory video study pack under `learning-center/tracks/gauntlet-ai/video-studies/Xg0tNz9pICI/` (metadata, raw/clean transcript, study guide, question bank).
- Started Gauntlet Day-01 execution sprint for BearingBrain; baseline evals were run (local passed, prod failed immediately with HTTP 522 on `/api/v1/capabilities`), and the eval harness in `/home/ubuntu/partsbrain/web/scripts/eval-agentic-v1.ts` was improved to emit timing summary (`checks/median/p95/worst`) on both success and failure.
- A multi-project factory scaffold was created at `/home/ubuntu/pi-telegram-bot/factory` (manifest/policies/queue/templates + `npm run factory:status`), but current priority was explicitly reset to learning-focused Gauntlet prep over further factory automation.

---

[2026-04-16] Resynced Energy Zillow dark-factory context after parallel-agent work, aligned to sales-machine vision (operator ROI, multi-product ranking, honesty gates), and updated factory tracking (`projects.manifest.json`, `queue.yaml`, `decision-log.md`, `pending.ndjson`, run-status artifact).
- Completed EZ-009 close: generated `artifacts/demo-recording-v1.mp4` (+ `.webm`) via `scripts/record_demo.py`, ran `scripts/close_ez009.py`, and moved EZ-009 to `done-local`.
- Shipped operator workflow/product execution lanes: EZ-012 (`lead_temperature`, `operator_next_step`), EZ-013 (persisted workflow state with `GET/PUT /api/v1/operator/status*` to `data/processed/operator_status.json`), EZ-014 (route sequencing `GET /api/v1/operator/route-plan`), EZ-015 (frontend quick actions + `GET /api/v1/operator/route-plan.csv` export).
- Added trigger data pipeline: contract + merge + templates (`spec/trigger-feed-contract.md`, `scripts/merge_property_triggers.py`, `data/raw/property_triggers_external.template.csv`), plus storm feed adapter `scripts/fetch_nws_storm_triggers.py` with artifacts `artifacts/nws-trigger-fetch-summary.{md,json}`.
- Completed EZ-016 (trigger merge lane) and EZ-017 (outage lane) locally: added `scripts/fetch_eversource_outage_feed.py`, `scripts/project_state_outage_triggers.py`, `data/raw/state_outage_feed.template.csv`, generated `data/raw/state_outage_feed.csv`, projected/merged into `data/processed/property_triggers.csv`.
- Key dataset/runtime values: active baseline ZIPs `01730, 02667, 05486, 06525`; sites/scored `5800/5800`; H3 cells `102`; PM2 app `energy-zillow-demo` online; public URL `http://20.122.197.143/energy-zillow/`; eval command uses `--require-min-zips 2 --min-rows-per-zip 80 --min-zip-stability 0.90`.
- Latest quality state: eval PASS after each major change; outage trigger coverage now non-missing `5379/5800` (~92.7%), with remaining missing concentrated in ZIP `05486` (VT) due current outage-source coverage gap.
- Decisions/config updates: default factory build kept deterministic on `proxy` scoring path; PVWatts/NSRDB remains explicit calibration lane; trigger caveat updated from “stub” to “partially populated” (storm+outage loaded, equipment-age/flood still missing).
- Current ongoing work: EZ-018 created as next lane (`todo`) to integrate flood-risk (and remaining trigger gaps) for uncovered geographies while keeping merge+score+eval gates green.

---

[2026-05-02] Discussed professionalizing the company operation — user wants Chow & Adam run like an AI-first company with proper agent management, data handling, and evolution. Built Agent OS v1.0 at `/home/ubuntu/agent-os/` with agent registry (`registry.json` tracking Chow and Hector), protocol spec (`spec.md` for structured inter-agent messaging), ops dashboard (dark terminal UI at `http://40.75.10.4/agent-os/`), and Python API server (port 8200, PM2-managed). Updated Caddyfile to route `/agent-os` and `/api/agent-os` through reverse proxy. Hector's Tailscale IP is `100.99.154.47`, reverse SSH bridge exists on port 2222 but SSH server still pending activation on Dell side. Created comprehensive 5-phase company roadmap at `agent-os/artifacts/company-roadmap.md` covering GitHub versioning → agent fabric → Gauntlet/Ralph development ritual → autonomous ops → external face. Installed `gh` CLI v2.92.0 on Azure VM. User confirmed BAGWATCHER GitHub account for repo hosting. Blocked on GitHub PAT from user to complete `gh auth login` and begin Phase 1 repo pushes.

## Last Reflected
- 2026-05-02T04:24:50.637Z

---

## Recent Daily Logs

### 2026-04-09.md

# Daily Log — 2026-04-09

- Initialized Chow second-brain scaffold.
- Next: run reflection sync from identity.md + summaries.md.

## 2026-04-09T04:03:54.749Z
- Initial Cole-style Chow adaptation
- Synced SOUL.md / USER.md / MEMORY.md from identity + summaries.

## 2026-04-09T04:04:43.816Z
- Fix section parsing
- Synced SOUL.md / USER.md / MEMORY.md from identity + summaries.

## 2026-04-09T04:23:29.270Z
- Phase2 wiring check
- Synced SOUL.md / USER.md / MEMORY.md from identity + summaries.

## 2026-04-09T06:00:22.431Z
- Phase 3 validation sync
- Synced SOUL.md / USER.md / MEMORY.md from identity + summaries.

---

### 2026-04-14.md

# Daily Log — 2026-04-14

## 2026-04-14T20:23:19.988Z
- Phase 3 shipped: structured memory + /brain ops + daily consolidation
- Synced SOUL.md / USER.md / MEMORY.md from identity + summaries.

---

### 2026-04-16.md

# Daily Log — 2026-04-16

## 2026-04-16T03:36:47.355Z
- Auto-reflect after session rotation
- Synced SOUL.md / USER.md / MEMORY.md from identity + summaries.

## 2026-04-16T22:31:14.176Z
- Auto-reflect after session rotation
- Synced SOUL.md / USER.md / MEMORY.md from identity + summaries.

---

## Structured Event Memory (Phase 3)

- [2026-05-02 04:24] (chow/session_rotation | imp:3 | tags:rotation,summary,phase) Session rotated with archived summary — [2026-05-02] Discussed professionalizing the company operation — user wants Chow & Adam run like an AI-first company with proper agent management, data handling, and evolution. Built Agent OS v1.0 at `/home/ubuntu/agent-os/` with agent registry (`registry.json` tracking Chow and Hector), protocol spec (`spec.md` for structured inter-agent messaging), ops dashboard (dark terminal UI at `http://40.75.10.4/agent-os/`),…
- [2026-05-02 03:11] (bagwatcher/assistant_result | imp:3 | tags:result,token,bagwatcher) Cool. — Cool. BAGWATCHER it is. I just need that token — `repo` scope is all I need. Go grab it and paste it here, I'll take it from there.
- [2026-05-02 02:50] (other/assistant_result | imp:2 | tags:result,token) `gh` v2.92.0 installed. — `gh` v2.92.0 installed. **Step 1.2 — Authentication.** Couple ways to do this. The cleanest without a browser on this headless VM: you create a **GitHub Personal Access Token** (classic) with `repo` scope, and I feed it in. Instructions for you (30 seconds): 1. Go to: **github.com → Settings → Developer settings → Personal access tokens → Tokens (classic)** 2. Generate new token → check `repo` → generate 3. Paste it…
- [2026-05-02 02:47] (other/assistant_result | imp:4 | tags:result,phase) Done. — Done. Five phases, each with a clear gate: ``` Phase 1 ░░░░░░░░░░ GitHub everything ("Versioned Truth") Phase 2 ░░░░░░░░░░ Agent fabric ("Connected Machines") Phase 3 ░░░░░░░░░░ Gauntlet loop ("Plan→Build→Eval→Debrief") Phase 4 ░░░░░░░░░░ Autonomous ops ("Agents run the company") Phase 5 ░░░░░░░░░░ External face ("The company exists") ``` Full plan saved at `agent-os/artifacts/company-roadmap.md`. --- **Right now we…
- [2026-05-02 02:45] (bearingbrain/assistant_result | imp:1 | tags:result,bearingbrain) Here's the raw picture: ``` ❌ partsbrain — no git ⚠️ pi-telegram-bot — git init'd, no remote, 48 dirty files… — Here's the raw picture: ``` ❌ partsbrain — no git ⚠️ pi-telegram-bot — git init'd, no remote, 48 dirty files ❌ trenchfeed-trader — no git ❌ adam-landing — no git ❌ hive — no git ❌ agent-os — no git ❌ dell-bridge — no git ❌ agent-machines — no git ❌ www-static — no git ``` Also: `gh` CLI isn't installed on this VM. --- **Baby step plan:** | Step | What | Who | |------|------|-----| | **1** | Install `gh` CLI on this…
- [2026-05-02 02:34] (other/assistant_result | imp:2 | tags:result) We have the ingredients but we're not running the playbook. — We have the ingredients but we're not running the playbook. Here's the honest assessment: **What Gauntlet AI & Cole Medin teach:** | Principle | We Have | We're Doing | |-----------|---------|-------------| | **Weekly ship cycle** — Plan → Build → Eval → Debrief | ✅ Sprint template | ❌ Not running consistently | | **PRD → Architecture → Build → Eval** | ✅ Gauntlet docs, Archon | ❌ Ad-hoc, no ritual | | **Ralph/BMAD…
- [2026-05-02 02:25] (chow/assistant_result | imp:4 | tags:result,deploy,shipped) Agent OS is live. — Agent OS is live. Here's what shipped: --- **◈ AGENT OS v1.0 — Deployed** **Public Dashboard:** `http://40.75.10.4/agent-os/` **Registry API:** `http://40.75.10.4/api/agent-os/registry` **What's in it:** | Layer | Status | Detail | |-------|--------|--------| | **Agent Registry** | ✅ | `agents/registry.json` — Chow (Azure) + Hector (Dell) fully defined with roles, capabilities, services, locations | | **Protocol Spe…
- [2026-05-02 02:23] (chow/assistant_result | imp:2 | tags:result,status,chow) Got it — you're talking about the **operating system** underneath everything. — Got it — you're talking about the **operating system** underneath everything. The agent fabric itself. Right now we're winging it. Chow does this, Hector does that, data lives wherever it was last saved. That doesn't scale. We need: **1. Agent Registry & Identity** Every agent has a known ID, location, capabilities, and status. No more "which agent is running where." **2. Inter-Agent Protocol** Standardized handoffs…

## Daily Consolidations

### 2026-05-02.md

# Brain Consolidation — 2026-05-02 - Generated: 2026-05-02T02:18:39.213Z - Reason: runtime - Events today: 0 ## Top Highlights - No notable events captured today. ## By Project - No project buckets for this date.
