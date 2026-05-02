# Mr Chow — Memory for @hog_cranker (1340648617)
Last updated: 2026-05-02

## Who I Am / Role
- Mr Chow = Adam's primary 24/7 server agent + system orchestrator.
- Primary runtime host: Azure `20.122.197.143` (`rico-prod-vm`).
- Owns infra, Rico ops, deployments, VM management, bot orchestration.

## Operating Oath
- Tell Adam true system state; never fake completion.
- Uptime first: smallest safe change, minimal restart, verify outcomes.
- Execute end-to-end; surface blockers early.

## Core Paths
- `~/pi-telegram-bot/` (this bot)
- `~/trenchfeed-trader/` (Rico + planning)
- `~/trenchfeed-trader/dark-factory/` (Autonomous orchestration loop)
- `/backup/cua-selfhost/` (Cua self-host pilot)

## Current Model & Framework
- **Framework:** `@mariozechner/pi-coding-agent` 0.71.0
- **Model:** Adam reported switching Chow to `gpt-5.5` on 2026-05-02; verify runtime config before declaring server-side model state.
- **Previous known model:** `ollama/glm-5.1:cloud`
- **Thinking level:** `xhigh` (~32k tokens)

## Porkbun API Access
- Keys stored in `~/pi-telegram-bot/.env` (PORKBUN_API_KEY, PORKBUN_SECRET_API_KEY)
- API v3 fully working: ping valid, domain list OK, DNS CRUD enabled
- Domains managed: `optimizedworkflow.dev` (A `40.75.10.4`), `trenchfeed.fun` (A `20.122.197.143`)
- Account balance: $0.00

## Dell / Hector Setup
- Dell machine: WSL2 Ubuntu 24.04 on `DESKTOP-01RQ5CD`, Tailscale `100.99.154.47`
- Reverse SSH tunnel: `ssh -i ~/.ssh/jose_azure_to_aws_recover_ed25519 -p 2222 adam@127.0.0.1`
- Agent config: `~/agent-machines/dell.json`
- Hector project: `/home/adam/hector-telegram-bot`
- Hector model: `openai-codex/gpt-5.5`
- Dell local Ollama models: qwen3.5:9b, qwen2.5-coder:7b, gemma3:4b

## War Room Vision
- Goal: Team group chat where Chow + Hector + other agents interact in one TG group
- Needs: BotFather privacy mode OFF, anti-loop logic, both bots in group
- Status: Not yet implemented

## Dark Factory
- Components (`~/trenchfeed-trader/dark-factory/`): meet-sidecar, tg-brain, cua-bridge, orchestrator.js

## Rico (AI memecoin trading)
- Models: `RICO_V3_PI_MODEL=gemini-2.5-pro`, `RICO_V3_EXIT_MODEL=gemini-2.5-pro`

## BearingBrain / PartsBrain
- Domain: `bearingbrain.com`. A1/A2/A3 + B1 (rate limits) shipped and live.
- External API rate limiting live-verified (write 60 RPM, read 120 RPM).

## Web Properties
- `optimizedworkflow.dev` / `adamn.info`: Hosted on Azure.
- BOBO: Community narrative site at `/bobo` and direct IP.
- KUAILE landing: at `/kuaile`.
- BagWatcher: at `/bagwatcher`.

## Telegram / Bot Ops
- Bot: `@Hog_hector_bot`
- ALLOWED_CHAT_IDS is empty (open to all chats)
- Group filter: only responds when @mentioned or replied-to in groups
- `src/agent-runner.ts` patched for pi-coding-agent 0.71 `DefaultResourceLoader` API (`cwd` + `agentDir`) and supports `--model provider/model` for DeepSeek build agents.

## Catholic Marketplace
- **Location:** `~/pi-telegram-bot/factory/projects/catholic-shop/`
- **PM2 processes:**
  - `catholic-shop-demo` — FastAPI on port 8110 (Python, ~2000 lines)
  - `catholic-concierge` — PI-powered AI concierge on port 8112 (Node.js, ~350 lines)
- **Stack:** FastAPI + Uvicorn, Alpine.js + Tailwind (CDN) for product pages, React + Vite + shadcn/ui patterns for chat
- **Data:** 6 shops, 18 products, 6 destinations
- **Caddy routes:** `/catholic-shop/` → FastAPI on 8110 using `handle_path` (prefix stripped)
- **Next approved build wave:** Adam approved workstreams 2-6: analytics/event logging, shop profile + product detail pages, SQLite catalog migration, concierge eval/ranking upgrade, and real shop/product onboarding. He wants DeepSeek agents used for build lanes.
- **DeepSeek agent wave:** Plan saved at `factory/projects/catholic-shop/spec/deepseek-agent-build-plan-2026-05-02.md`; Lane A analytics task `tmonsvyq2` DONE. Added `backend/api/analytics_store.py`, `/api/v1/analytics/events`, `/api/v1/analytics/summary`, auto-logs product/shop/chat/AI recommendation events to `data/processed/analytics_events.jsonl`, eval is 9/10 with only pre-existing `mobile_html_gate` fail.
- **Main storefront audit (2026-05-02):** Alpine static pages still need hardening: absolute `/api` and `/product` paths break under public `/catholic-shop` mount; main/sacrament/product pages still use emoji/symbol UI markers; product page has typo `text-rubic`; sacrament page is emoji-heavy and less aligned with chat design. Fix before wider traffic.
- **Chat architecture (LIVE 2026-05-02):**
  - Frontend: React + Vite + Zustand, Scriptorium theme, 6 components
  - Streaming: SSE from PI concierge → FastAPI proxy → browser
  - Messages: No bubbles — user text right-aligned bold, AI with gold left border accent
  - QuickActions: Subtle chip row below header with gradient scroll arrows
  - Welcome: Flows as text (not centered modal), 4 suggestion chips
  - Auth: JWT signup/login (PyJWT), PBKDF2 password hashing
  - Conversation storage: JSON flat files
  - Cart: API_BASE = `/catholic-shop`, proper SVG icons
  - **Backend fix (2026-05-02):** `shouldShowProducts()` now also checks the new user message (not just context history). Fixes product cards=0 on first message.
  - Build: 219KB JS + 17KB CSS
  - **Zero emojis in UI** — all icons use inline SVG (`Icon.tsx`, 19 icons)
  - **Escape key** closes both sidebar and cart drawer
- **Design rules from Adam:** No emojis as UI icons (emojis only for chat messages). No "bubble/box" message styling. Clean, professional, text-forward design. Avoid AI slop patterns.
- **Mission line:** "Thank you for supporting Catholic shops and artisans around the world."

## PM2 Processes
- `chow` — main bot
- `partsbrain` — BearingBrain Next.js
- `catholic-shop-demo` — Catholic shop FastAPI (port 8110)
- `catholic-concierge` — Catholic shop PI concierge (port 8112)

## Preferences
- Proactive, high-signal, execution-heavy.
- Prefer Cloudflare Email Routing for optimizedworkflow.dev.
- Model switching from Telegram chat is desired (not yet implemented).
