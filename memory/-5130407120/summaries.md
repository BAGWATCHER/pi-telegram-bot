[2026-03-27] User confirmed “go” on adjacent ingestion, then clarified strategy: prioritize bearing-adjacent discovery with execution, later pivoting away from transmission/automotive toward tolerance rings + bearing maintenance.
- Completed Wave 1 planning artifacts in `/home/ubuntu/partsbrain/web`: `docs/plans/adjacent-ingestion-wave-master-2026-03-26.csv` and `docs/plans/wave1-adjacent-ingestion-runbook-2026-03-26.md`.
- Built extraction pipeline: `scripts/extract-adjacent-wave1-links.mjs` produced `data/adjacent/wave1-links-master.csv` with 248 seed links (Timken 140, Dodge 88, Regal 20); Regal live crawl hit HTTP 403 so manual Regal seeds were used.
- Built normalization pipeline: `scripts/normalize-adjacent-wave1-records.mjs` created `data/adjacent/wave1-ingestion-records.csv` and summary JSON; final normalized set = 131 records (Timken 69, Dodge 43, Regal 19) after dropping static/irrelevant links.
- Added DB staging: migration `migrations/20260327_add_adjacent_source_staging.sql` created `adjacent_source_records` (unique key on `company, source_url`, wave default `wave_1`, indexed by wave/company/type/host/confidence).
- Loaded staging data via `scripts/ingest-adjacent-wave1.mjs`: 131 inserted, 0 updated; source_type distribution in DB: category 36, product_family 31, resource 27, tool 12, pdf 11, catalog 11, cad 3.
- Added read access layer: `lib/adjacent-sources.ts` and API `GET /api/adjacent-sources` (supports `wave`, `company`, `sourceType`, `includeRecords=1`, `limit`); lint check passed.
- Important infra/config observed: Postgres container `partsbrain-db` running; DB used `partsbrain`; loader uses `DATABASE_URL` or fallback `postgresql://partsbrain:partsbrain_dev_pw@localhost:5432/partsbrain`.
- Final scope pivot executed: created focused subset `data/adjacent/wave1-focus-tolerance-maintenance.csv` with 43 records (Dodge 28, Timken 12, Regal 3); next planned work is focused company discovery for tolerance rings and bearing maintenance (Smalley, Rotor Clip, Beneri/Seeger-Orbis, SKF maintenance, Schaeffler/FAG tools, NTN-SNR/NSK maintenance).

---

[2026-03-27] Discussed stabilizing mobile UI and adding tolerance-ring support cleanly (no UI regressions), plus earlier strategy to keep USA Tolerance Rings in quote-first assisted flow via John (“dad”) channel.
- Previously completed in this session: USA TR integration core (data in `data/tolerance/usa/`, `lib/tolerance-rings.ts`, `/api/tolerance-rings`, `/api/chat` `toleranceRings` payload, chat cards, click telemetry, and direct+contextual intent gating), with 50 TR rows loaded under wave `wave_usa_tolerance_2026_03_27`.
- Built/landed quote-channel plumbing for TR: added `sourcing_requests.metadata_json` migration (`migrations/20260327_add_sourcing_request_metadata.sql`) and index on `metadata_json->>'supplierChannel'`; TR quote submissions now persist placeholders for estimate/payment/handoff and `supplierChannel: john_usa_tr`.
- Added operator tooling for TR handoff: `supplierChannel` filter in `/api/operator/sourcing-requests`, Quote Desk filter UI, and new admin endpoint `/api/operator/sourcing-requests/[requestRef]/handoff` that returns a copyable John handoff packet.
- Validated TR channel flow end-to-end with test request `BBQ-20260327-3882`; metadata showed `supplierChannel: john_usa_tr`, `flowType: assisted_quote`, payment `captureStatus: not_started`, and handoff owner `john`.
- Mobile overflow fix work done: changed home header nav to wrap on small screens (`app/page.tsx` nav now `flex-wrap`) and hardened `/about` against horizontal spill (`overflow-x-hidden`, `break-all` on MCP URL).
- Added a clean new “Tolerance ring support” section to `app/about/page.tsx` describing direct-intent handling, context-gated suggestions, and assisted sourcing flow; lint passed with only pre-existing warnings; final build command was started but last output was not captured before archive.

---

[2026-03-27] Continued tolerance-ring integration review and Pi-architecture evaluation: confirmed TR logic/hooks are in place, quote handoff uses `supplierChannel: john_usa_tr`, and major multi-agent refactor is deferred in favor of low-risk hardening.
- Deep-read Pi docs and examples (README, compaction/settings/skills, subagent and plan-mode examples) and concluded your app’s `runPiText()` path is effectively single-shot/ephemeral (`--no-session` etc.), so per-request assembled context size is the key pressure point.
- Prompt-size discussion outcome: keep intelligence-first strategy (do not aggressively trim core reasoning), prefer surgical noise reduction only; user preference explicitly set to quality over speed.
- Ran baseline pre-change `/api/chat` tests (no code changes): mixed 14-prompt set had 14/14 HTTP 200, avg latency ~17.1s, max ~32.9s, with 5 contextual/direct TR-card misses (`D1`, `D3`, `C1`, `C3`, `E1`) and no false positives in that run.
- Ran stability spot checks: contextual TR query repeated 10x returned 200 each time with TR cards 10/10 (avg ~26.6s); negative fit query repeated 5x returned 200 with TR cards 0/5.
- Decision on QA process: avoid rerunning identical fixed tests every cycle; use a rotating eval approach (small smoke set + rotating/messy-user prompts + tracked FP/FN/timeout/p95 metrics).
- Checked reported website CSS issue live: could not reproduce server-side CSS failure; `bearingbrain.com` and `/_next/static/css/b1b57da924c2e3cc.css` both returned 200 on prod/local, major pages loaded with CSS reference intact.
- Logs review found historical Next build/runtime issues (e.g., missing `.next` build artifacts in older entries, telemetry/chat timeout/degraded logs) but no current active CSS/chunk 404 incident; no patch applied yet pending exact URL/device/screenshot reproduction.

---

[2026-03-30] Discussed BearingBrain production priorities with focus on AI discoverability, messaging accuracy, and moving from “cross-reference tool” perception to full engineering/reliability platform (including tolerance rings, seals, lubrication, maintenance).
- Implemented/updated discoverability surfaces in `/home/ubuntu/partsbrain/web`: `public/llms.txt`, `public/llms-full.txt`, `app/facts/route.ts`, `app/sitemap.ts`, `app/developers/page.tsx`, and added `app/api/v1/capabilities/route.ts` with explicit tolerance-ring + reliability-stack messaging.
- Added/created new website pages for canonical capability visibility: `app/capabilities/page.tsx`, `app/tolerance-rings/page.tsx`, `app/seals/page.tsx`, `app/lubrication/page.tsx`, `app/maintenance/page.tsx`; added release-process doc `docs/ops/feature-release-ai-discoverability-checklist.md`.
- Reapplied attribution link decision: all “Made by Adam” hrefs switched from `https://adamn.info` to `https://optimizedworkflow.dev` in `app/page.tsx`, `app/bearing/[mfr]/[pn]/page.tsx`, `app/pro/client.tsx`, `components/site-footer.tsx`.
- Messaging decision updated from staged language to immediate execution language (“active now” reliability-stack direction) per user request; user confirmed to continue website work without waiting for SKF extra API access.
- Reviewed external deep-research handoff doc at `/home/ubuntu/trenchfeed-trader/docs/planning/BEARINGBRAIN-SEALS-LUBES-MAINTENANCE-DEEP-RESEARCH-2026-03-28.md`; aligned direction: reliability stack, selector tools, ISO 15243 failure content, bundles.
- SKF access check: current configured key in `.env.local` (`SKF_API_KEY`, base `SKF_API_BASE=https://.../v1/pim`) works for `/v1/pim/details`; attempted additional paths (`/v1/product-cross-reference`, `/v1/cross-reference`, `/v1/product-information`, `/v1/availability`, `/v1/order`) returned `ApplicationNotFound` 404; quota violations observed during bulk probing.
- Current SKF DB snapshot from `partsbrain-db`: `parts_total=25771`, `specs_total=21275`, `specs_missing=4496`, `cross_refs_outbound=4545`, `supplier_listings_skf=446`; seals/linear-motion SKF spec tables currently 0.
- Ongoing status: code changes are local and not yet confirmed deployed live in this session; deployment/verification commands were prepared (`next build` with increased memory + `pm2 restart`) and next step is live endpoint validation after restart.

---

[2026-04-08] Continued BearingBrain “bearings-first” execution: completed Day 0–7 Step 1 and Step 2 foundations for mechanical case learning loop, then ran live random-user torture testing on production chat reliability.
- Built Step 1 ingestion artifacts in `/home/ubuntu/partsbrain/web`: `migrations/20260408_add_mechanical_case_records.sql`, `lib/mechanical-case-records.ts`, `app/api/mechanical-cases/route.ts`, `docs/research/schemas/mechanical-case-record-v1-2026-04-08.json`, and `docs/research/mechanical-case-ingestion-contract-v1-2026-04-08.md`.
- Built Step 2 review/export workflow: `app/api/operator/mechanical-cases/route.ts`, `app/api/operator/mechanical-cases/[caseRef]/route.ts`, `app/api/operator/mechanical-cases/export/route.ts`, `migrations/20260408_add_mechanical_case_training_export_view.sql`, and `docs/research/mechanical-case-review-workflow-v1-2026-04-08.md`; lint checks passed on new files.
- Live test results (non-destructive) against `https://bearingbrain.com/api/chat`: evidence file `/tmp/bb-random-user-torture-1775677118632.json`; sequential run 27 calls with 0 non-200 but 22 degraded (`assistant_runtime_error`), p50 ~4.8s, p95 ~12.4s, max 22.5s; burst run 20 concurrent calls produced 16×524 timeouts and 4 degraded 200s.
- Root reliability findings from PM2 logs (`partsbrain`, id `23`): frequent `openai-codex` token refresh failures (`refresh_token_reused` 401), plus Gemini fallback quota exhaustion (`gemini-3.1-pro` 429 `RESOURCE_EXHAUSTED`), causing degraded/timeout behavior.
- Key product decision during this turn: user wants AI-first stabilization (not deterministic-only fallback), align site runtime path with Chow-style auth/model approach, and add Gemini backup keys.
- Config/context discovered: `.env.local` has `PI_AGENT_MODEL` and `PARTS_CHAT_MODEL` set (redacted in summaries), `GOOGLE_GEMINI_API_KEY` configured; PM2 env shows `GEMINI_API_KEY` present; no `OPENAI_API_KEY` in PM2 env for `partsbrain`; current defaults in code still reference Gemini 3.1 Pro if unset.
- User requested model switch to Gemini key + 3.1 Flash; assistant confirmed capability and stated no change applied yet, noting live effect requires explicit approval for PM2 restart/deploy step.
- Memory file updated: `/home/ubuntu/pi-telegram-bot/memory/-5130407120/identity.md` with new directives, delivered artifacts, and production reliability incident signals; ongoing work status: ready to implement runtime model/config switch and failover patch upon explicit go-ahead.
