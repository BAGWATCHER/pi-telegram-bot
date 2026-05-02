# Mr Chow — Identity & Project Memory

## Who I Am
- AI coding + research assistant in Telegram, powered by pi + Claude
- Helping build PartsBrain / BearingBrain and related AI businesses

## PRIMARY PROJECT: PartsBrain / BearingBrain
- AI-powered industrial parts search platform; “Octopart for mechanical parts”
- User enters part number or natural-language query → AI finds cross-references across brands → shows specs/confidence/supplier links
- Starting niche: bearings; later fasteners, seals, linear motion
- Biggest moat = normalized data + confidence-weighted cross-reference graph, not chat UX
- Dad has 20 years as bearing consultant + industry relationships

## Business Model
- Phase 1: affiliate commissions — Amazon `adamnorm13-20` live, Zoro via CJ pending
- Phase 2: direct manufacturer partnerships — catalog data + CPC deals
- Phase 3: SaaS for procurement teams (BOM cross-referencing, supply chain resilience)

## Dad Validation / User Feedback
- Dad reported real pain finding in-stock bearings across multiple sites
- He independently described PartsBrain flow: specs → inventory → alternatives if unavailable
- Feedback: Amazon clicks should land on brand-specific results; branded rows need branded destinations
- Concern: legal risk using brands + part numbers on site
- User wants major UX improvements, hybrid chat UI, strong mobile experience, and voice later
- User flagged speed spec trust issues; grease values should generally not exceed oil

## Live Deployment: BearingBrain
- Domain: `bearingbrain.com` (Cloudflare)
- `www.bearingbrain.com` → 301 redirect to apex
- Reverse proxy: Caddy `/etc/caddy/Caddyfile` → `127.0.0.1:3001`
- App path: `/home/ubuntu/partsbrain/web`
- Stack: Next.js + TypeScript + PostgreSQL + pgvector
- PM2 process: `partsbrain`
- Runtime: `pnpm exec next start -p 3001 -H 0.0.0.0`
- Health: site + `/api/search` confirmed working; 2026-03-26 outage fixed by killing orphan `next-server` on 3001
- Current runtime note (2026-04-18): PM2 `partsbrain` online; recent logs show SKF PIM API 500s on some bearing detail fetches

## Recent BearingBrain/Product Fixes
- Amazon links are now brand-aware (brand + quoted part number + bearing)
- Mobile-first UI pass shipped
- Preset query parsing fixed (`FAG 6204-2RS cross reference` style)
- Pricing fallback shipped (`~$` + Estimated when no live `price_usd`)
- Spec Finder shipped closure filter, mm/inch toggle, tolerance, bearing type, sort modes, dual-unit display
- Known data issue: SKF ingest likely mismaps limiting/reference speed fields in `scripts/ingest-skf-bulk.mjs`

## AI / Agent Integrations
- User preference: use pi for site agent/workflow direction
- `lib/ai.ts` uses pi CLI as primary parser/explainer provider
- Default pi model in app code: `openai-codex/gpt-5.1-codex-mini`
- Gemini fallback: `@google/genai` with `gemini-3.1-pro-preview`
- Fast-path regex handles bare part numbers and manufacturer-prefixed queries
- Deterministic post-processing exists (e.g. dusty/wet → `seal_type=2rs`)

## Key Config
- DB URL: `postgresql://partsbrain:partsbrain_dev_pw@localhost:5432/partsbrain`
- Docker DB container: `partsbrain-db`
- Caddy config: `/etc/caddy/Caddyfile`
- PartsBrain port: `3001`
- PartsBrain path: `/home/ubuntu/partsbrain/web`
- Gemini env key present as `GOOGLE_GEMINI_API_KEY`
- Optional pi env overrides: `SITE_AGENT_PROVIDER`, `PI_AGENT_MODEL`, `PI_AGENT_TIMEOUT_MS`, `PI_AGENT_THINKING`

## SECONDARY PROJECTS / EXPLORATION
- Bioprocessing filtration cross-reference/catalog idea (separate from BearingBrain)
- References: `jco-inc.com/store` and Cytiva TFF category pages
- Direction: TFF systems, cassettes, holders, accessories

## OPTIMIZED WORKFLOW / ADAM LANDING
- `optimizedworkflow.dev` and `www.optimizedworkflow.dev` are live on the VM
- Caddy serves `adamn.info`, `www.adamn.info`, `optimizedworkflow.dev`, `www.optimizedworkflow.dev` → `127.0.0.1:3000`
- App path: `/home/ubuntu/adam-landing`
- Stack: Next.js
- PM2 process: `adam-landing`
- Runtime: `npm start -- -p 3000`
- Positioning: AI agency/landing site for custom AI agents, bots, and workflow automation
- Current offer copy: builds from `$3K`, `$375/hr`
- Home page includes BearingBrain spotlight and links to `/bearingbrain/distributors` and `/bearingbrain/mro-procurement`
- Site includes routes for manufacturing, telecom, payments, pricing, learn pages, partners, chat, pulse, and referral tracking
- Current runtime note (2026-04-18): PM2 `adam-landing` online; recent logs show Next.js “Failed to find Server Action” errors and at least one primary-model fallback to Gemini 2.5 Flash

## Strategic Direction: Layer 2 → Layer 1
- Current framing:
  - Layer 2 = app/services layer
  - Layer 1 = compute/infrastructure layer
- We are already emerging in Layer 2 with:
  - BearingBrain
  - Optimized Workflow
  - custom AI/workflow/service capability
- Core strategy: do NOT abandon Layer 2; use Layer 2 revenue, customers, and proof to fund and de-risk entry into Layer 1
- Planned Layer 1 entry path:
  1. customer-owned private AI rigs/workstations
  2. on-prem/local AI installs
  3. networking/power/cooling setup
  4. recurring support/monitoring/maintenance
  5. managed private compute
  6. later, hosted compute / small managed compute provider
- Important principle: avoid fighting hyperscalers directly on generic cloud/model scale; compete on deployment, private/hybrid setups, customization, trust, and real-world infrastructure work
- User wants this strategic frame preserved in memory and adjusted as the world changes

## User Background / Edge
- User has strong hands-on background in tower work, fiber, power, steel, plumbing, wireless, lineman-type infrastructure work
- User likely can self-perform much physical buildout work for AI infra / hosted compute / on-prem setups
- This physical-world capability is a major moat when combined with AI/software

## Broader User Interests
- Interested in voice interaction, persistent memory, local LLM hardware, wearables, smart glasses, and always-on AI copilot ideas
- Exploring OBD/car integrations and AI tied to vehicle diagnostics
- Interested in infrastructure-side AI opportunities and future compute demand
- Plans to use an agent orchestrator to run deep research across a large list of strategic topics, then bring back a shared research file for synthesis/review
- Cost-sensitive on research token spend; open to using cheaper models (e.g. GPT mini class) for broad research and reserving stronger models for synthesis
- New preference (2026-04-18): for agent-orchestrated research, default to GPT-5.4-mini class where sensible and escalate only for synthesis/hard reasoning
- New strategic view (2026-04-18): user expects market timelines to compress (often 1–2 years vs legacy 2–4), with strong customer pressure for lower inference/hardware prices as AI efficiency gains accelerate
- New strategic view (2026-04-18): user sees meaningful 1–2 year disruption risk where a smaller player could rapidly challenge Nvidia dominance due to volatility, fast AI capability gains, and anti-monopoly market dynamics
- New technical thesis (2026-04-18): a focused AI system for compiler development/translation could accelerate cross-platform stack progress much faster than prior cycles
- New operating belief (2026-04-18): AI leverage can compress required engineering headcount dramatically (roughly prior 100-person output now achievable by ~5–10 strong AI-enabled engineers for certain software scopes)

## AI Research Handoff Pack (2026-04-18)
- User approved immediate execution pass ("Ok go") after handoff review
- Execution artifacts generated under `/home/ubuntu/ai_research_handoff/execution/`:
  - `EXECUTION_90_DAY_PLAN.md`
  - `FIRST_OFFER_PACKAGE_INDUSTRIAL.md`
  - `PILOT_EXECUTION_CHECKLIST.md`
  - `PROPERTY_DILIGENCE_CHECKLIST.md`
  - `MODEL_ROUTING_SPEC_V1.md`
  - `ORCHESTRATION_RUN_2026-04-18.md`
- Workspace: `/home/ubuntu/ai_research_handoff/`
- Control docs: `MASTER_HANDOFF.md` + `COVERAGE_AUDIT.md`
- Structure: 6 core tracks + 5 second-wave deepening memos
- Program-level conclusion: local-first, event-driven copilot; selective premium cloud escalation; Android-first practical stack
- Strategy conclusion: keep Layer 2 wedge, validate demand, then selectively move toward Layer 1 scarcity/control points
- Commercial ranking from memo: industrial distributors/MRO/machine shops first; boutique law second; healthcare later after compliance maturity
- Geography ranking from memo: Ohio default (Columbus first; Cleveland/Akron second), Indiana/Iowa as top alternates
- Buildout ranking from memo: light industrial first for real deployments; garage only for tiny pilots; house worst long-term fit
- Trust-policy conclusion: tiered memory + explicit permission controls + delete-everywhere semantics + strict no-surprise physical actuation

## Near-Term Lead / Outreach Opportunity
- Potential industrial-service lead identified (2026-04-23): Andrews Construction (NH), role posted for Payroll & Administrative Coordinator (`scrane@andrewsconst.com`)
- Hypothesis: sell workflow automation augmentation (payroll/AP/AR/compliance admin copilot) rather than replacement framing
- User wants outbound email to include a booking link; user stated a new calendar tool exists in "agent tools" and should be wired into outreach flow

## Agent Build Materials Library (Learning Center)
- New library added (2026-04-23): `/home/ubuntu/pi-telegram-bot/learning-center/shared/agent-build-materials-library.md`
- Structured registry: `/home/ubuntu/pi-telegram-bot/learning-center/data/agent-build-materials.json`
- Source and note records appended in `sources.ndjson` and `notes.ndjson`
- Onboarding rule updated in `/home/ubuntu/pi-telegram-bot/learning-center/shared/agent-onboarding.md` to require adding newly discovered tools to the materials library
- Cal.diy added under Scheduling with confidence `candidate` pending API/OAuth fit validation
- New Telegram command support added: `/materials [query]` in Chow bot for category/confidence/keyword lookup against the materials registry

## Affiliate / Supplier Config
- Amazon Associates tag: `adamnorm13-20`
- Zoro advertiser ID: `10046064`
- Current Zoro link: `https://www.zoro.com/search?q={PART_NUMBER}`
- CJ publisher approval pending
- Amazon PA-API is closed to new users; likely future path is Amazon Creators API after account qualification

## Critical Next Actions
1. Keep hardening search UX + mobile polish from real usage
2. Add favicon + branding pass (PartsBrain vs BearingBrain)
3. Implement SEO landing pages per bearing family
4. Add Amazon Associates compliance/legal pages
5. Publish trademark/nominative-use disclaimer for brand/part references
6. Replace estimated pricing with live supplier price ingestion/feed
7. Get CJ approval and tracked Zoro deep links
8. Prepare Dad demo with his real-world queries
9. Implement hybrid chat UI over existing search APIs
10. Fix SKF speed ingest mapping and add `oil >= grease` sanity-check guardrail
11. Improve optimizedworkflow.dev reliability around Next server actions / deployed action IDs
12. Prepare Layer 1 entry by designing a first solid private/local AI rig offer and support package
