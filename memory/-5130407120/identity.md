# Mr Chow — Group Chat Memory (-5130407120)
Last updated: 2026-04-23

## Context
- Group chat where Adam collaborates with Chow on BearingBrain + ops/research.

## Adam
- Telegram ID: 1340648617 (@hog_cranker)
- AI builder/consultant; moat focus = durable engineering intelligence
- Dad = John (mechanical engineer; bearing expert)
- Runtime preference: GPT-5.4 on Chow runtime
- Research-mode preference: GPT-5.3 high-reasoning for deep lanes
- Attribution preference: `https://optimizedworkflow.dev`
- About-page preference: tiny, non-promotional bottom attribution with `optimizedworkflow.dev` + `adam@bearingbrain.com`
- Ops directive: Chow owns production ops/analytics/traffic end-to-end; Adam provides missing access
- Cloudflare directive: Chow should manage full CF account/DNS end-to-end once access is provided
- Priority domains: `bearingbrain.com` and `optimizedworkflow.dev`
- Branding preference signal (2026-04-23): optimizedworkflow should use its own logo/favicon (not default triangle icon) in browser/search link surfaces

## Infra baseline
- Active production host: Azure VM `rico-prod-vm` (`20.122.197.143`, private `10.0.0.4`)
- AWS (`3.142.111.235`) is legacy/cooked
- Dad VM: `18.117.162.164`
- Anna VM: `3.17.57.39`

## BearingBrain (production)
- Domain: `bearingbrain.com`
- Stack: Next.js + Postgres + Caddy (app on `:3001`)
- Repo: `/home/ubuntu/partsbrain/web`
- PM2 app: `partsbrain`
- DB: `partsbrain` in container `partsbrain-db`
- Guardrail: read-only audit first; deploy/restart only with explicit user approval

### BearingBrain DNS/SSL status
- Authoritative NS: `aldo.ns.cloudflare.com`, `khloe.ns.cloudflare.com`
- Apex + `www` cutover to Azure completed
- Cloudflare hardening completed: `ssl=strict`, `always_use_https=on`, `min_tls_version=1.2`
- `bearingbrain.com` live 200 through CF; `www` 301 to apex
- Docs host recovered: `docs.bearingbrain.com` routed to main app (`:3001`) with docs rewrite + asset passthrough fix

### BearingBrain runtime/analytics status (new 2026-04-22)
- Runtime issue found in PM2 logs: `openai-codex/gpt-5.2-codex` unsupported on current ChatGPT Codex auth lane; caused parse/planner fallback and degraded timeouts
- Approved+executed config patch in `/home/ubuntu/partsbrain/web/.env.local`:
  - `PI_AGENT_MODEL=openai-codex/gpt-5.3-codex`
  - `PARTS_CHAT_MODEL=openai-codex/gpt-5.3-codex`
  - `PI_AGENT_FALLBACK_MODELS=google/gemini-3.1-flash,google/gemini-2.5-flash`
  - `PI_PARSE_FALLBACK_MODELS=google/gemini-3.1-flash,google/gemini-2.5-flash`
  - `PI_AGENT_TIMEOUT_MS=35000`, `PARTS_CHAT_TIMEOUT_MS=45000`, `PARTS_HELPER_TIMEOUT_MS=25000`
- Approved+executed restart: `pm2 restart partsbrain`
- Post-fix validation:
  - Sequential 8-call probe: 8/8 HTTP 200, 0 degraded
  - 6-way burst probe: 6/6 HTTP 200, 0 degraded
  - Evidence: `/tmp/bb-chat-check-postfix-1776899726.json`
  - `partsbrain-error.log` clean immediately after probe set
- Analytics verification refreshed:
  - `SiteTelemetry` mounted in `app/layout.tsx`
  - `.env.local` contains GA4 + Clarity IDs
  - Live JS assets on `bearingbrain.com` include `G-KSV8G3C2DC` and `w0nt4e4zbh`

## Optimized Workflow / adamn.info
- Domains: `optimizedworkflow.dev`, `adamn.info`
- App: `adam-landing`
- Repo: `/home/ubuntu/adam-landing`
- PM2 app: `adam-landing` (port `3000`)
- Caddy routes `optimizedworkflow.dev` + `adamn.info` to `127.0.0.1:3000`
- `www.optimizedworkflow.dev` has dedicated 301 redirect to apex
- `adamn.info` live on Azure origin with valid cert

### Optimized Workflow DNS risk (new 2026-04-22)
- Public NS set for `optimizedworkflow.dev` is mixed (Porkbun + Cloudflare) simultaneously
- Direct NS checks:
  - Cloudflare NS (`skip`,`tori`) serve expected records (`A 20.122.197.143`, `www -> apex`)
  - Porkbun NS return NOERROR/NODATA for apex/www (empty zone behavior)
- Resolver inconsistency confirmed:
  - Some public resolvers return apex A correctly
  - Others return no A (observed on `1.0.0.1`, `8.8.4.4`)
- Meaning: active split-brain/intermittent reachability risk until registrar NS is corrected
- Required fix path: set registrar nameservers to Cloudflare pair only (or mirror full records on Porkbun as temporary fallback)

### Optimized Workflow analytics verification
- `TrafficAnalytics` mounted in `src/app/layout.tsx`
- `.env.local` contains GA4 + Clarity IDs
- Live JS assets on `optimizedworkflow.dev` include `G-KSV8G3C2DC` and `w0nt4e4zbh`

### Optimized Workflow branding/favicon fix (2026-04-23)
- Replaced default Next.js `src/app/favicon.ico` (triangle icon) with icon generated from site `public/logo.png`
- Regenerated icon assets: `public/favicon-32.png`, `public/favicon-64.png`, `public/apple-touch-icon.png`, and `public/favicon.ico`
- Updated metadata icons in `src/app/layout.tsx` to include `/favicon.ico` + apple touch icon
- Build+restart executed: `npm run build` and `pm2 restart adam-landing`
- Live check confirms new favicon served on `https://optimizedworkflow.dev/favicon.ico`

## Product strategy memory
- Positioning goal: “bearing engineer in software” (not lookup chat)
- Strategic moat: proprietary high-quality data (coverage/completeness/freshness)
- Trust priorities: vague-input inference + deterministic why/why-not + application/failure context
- Learning-loop direction: explicit engineer feedback loop (shown/accept/reject/correct/outcome)
- QA preference: rotating/adversarial scenarios; avoid repetitive fixed prompt reruns
- Expansion focus: tolerance rings + maintenance/reliability (de-prioritize transmission-heavy/automotive)
- Revenue preference: USA Tolerance Rings lane matters (John relationship + commissions)
- Architecture preference: low-risk reversible changes; study Pi docs before major shifts
- CLI direction: CLI-first machine surface for agent workflows

## Active directives
- Continue autonomous compounding research execution
- Prioritize analysis-software lane (COBRA/ORBIS/ARMD parity)
- Keep compounding bearing + broader mechanical engineering intelligence
- Build best AI for mechanical engineering, starting with bearings
- Become comprehensive bearing-industry teaching copilot with source-backed practitioner intelligence
- Runtime directive: AI-first reliability; keep Pi runtime as orchestration layer

## Cloudflare/API notes
- Cloudflare account signal: `48a7a23931e78dc77f9a00e5bfca86e4` includes `bearingbrain.com`, `adamn.info`, `optimizedworkflow.dev`
- Prior shared CF/Groq/SMTP creds should be treated as exposed; rotate if still active
- Missing active creds on VM for some tooling: no persistent CF API token in env during latest checks

## John assistant (dad bot)
- Host: `18.117.162.164` (`ssh dad`)
- PM2 apps: `john`, `tolerance`
- Path: `/home/ubuntu/pi-bots/john/`
- Model: `openai-codex/gpt-5.3-codex`
- Allowed users: John (7241903437), Adam (1340648617)

## Incident guardrails
- Prior rollback to old commit caused regressions; preserve forward baseline
- Keep changes tiny, reversible, explicitly approved for deploy/restart
- For runtime/UX patch work: run/confirm tests before production deploy actions
- Preserve separate MCP tracks: general multi-AI profile vs ChatGPT-specific profile
