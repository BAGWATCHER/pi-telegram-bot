[2026-03-06] Deployed bearingbrain.com with Cloudflare DNS + Caddy reverse proxy pointing to the PM2-hosted Next.js app on port 3001 and ensured www redirects to the apex domain.  
Updated search AI to use Gemini 3.1 Pro Preview via the @google/genai SDK, cleaned up JSON parsing, raised token limits, and wired the stored API key (AIzaSyCVcjjJUCDZMc9Wf6QYqjrJxw2NMeDMXVM).  
Swapped PM2 to run `pnpm exec next start -p 3001 -H 0.0.0.0`, ensured production build works, and confirmed `partsbrain-db` container with 468 parts/cross-refs is healthy.  
Verified `/api/search` returns real results for both `6204-2RS` and natural-language queries (bore=20mm, seal=2rs) and that the frontend fetches those results.  
Documented the new domain and deployment details in identity memory for future reference.  
Noted current ongoing work: monitoring Caddy for SSL renewals, Amazon/Zoro affiliate approval, and planned SEO/Dad-demo tasks.

---

[2026-03-06] Diagnosed the outage concern: site/API were up, PM2 + Caddy healthy, Curl and DB checks confirmed live data endpoints.  
Added brand-specific Amazon search URLs (KOYO (JTEKT) "6204-2RS" bearing + tag adamnorm13-20) so clicked brands go to exact listings; clarified affiliate/legal copy.  
Reworked AI parser to run via pi CLI first (openai-codex/gpt-5.1-codex-mini, GEMINI fallback gemini-3.1-pro-preview) with deterministic post-processing and cleaner bare part-number extraction, then rebuilt/restarted.  
Implemented a mobile-first UI: stacked search/search button on phones, responsive hero, wrapping summary, stacked pricing cards, more tap-friendly supplier buttons, and added device-width viewport metadata.  
Clarified pricing UI copy to explain “No live price yet—tap suppliers below” because supplier_listings currently have zero numeric price_usd entries in the DB.  
Preset queries (FAG/SKF/Timken/NSK patterns) now parse correctly and return results thanks to the improved fast-path extraction.

---

[2026-03-27] We discussed expanding BearingBrain’s Spec Finder beyond dimensions/closure: you approved adding unit support plus the “other things” previously proposed (type filter, tolerance, sorting), with emphasis on a clean UI and no regressions.  
- Built and shipped Spec Finder UI upgrades in `app/spec-finder/client.tsx`: mm/inch toggle with live value conversion, tolerance (±) input, bearing type filter, sort selector, and richer result rows (dual-unit dimensions + speed/load highlights).  
- Upgraded backend filtering/ranking in `app/api/spec-search/route.ts`: added `tolerance`, `bearing_type`, and `sort` query support; retained closure support; added fit-delta scoring for `best_fit`; kept closure normalization (`open`, `sealed→2rs`, `shielded→zz/2rz`).  
- Updated page metadata copy in `app/spec-finder/page.tsx` to reflect new capabilities (unit support + tolerance/type filters).  
- Validation/deploy done: TypeScript check passed, production build passed (after one transient DB timeout on first build attempt), PM2 app `partsbrain` restarted successfully on port `3001`, and local/remote API smoke tests confirmed new filters/sorting behavior.  
- Important config/runtime values used: PM2 process `partsbrain`, app port `3001`, API endpoint `/api/spec-search`, DB connection remained local Postgres (`partsbrain` user/db) for verification queries.  
- Memory was updated (`/home/ubuntu/pi-telegram-bot/memory/-1003363120939/identity.md`) to record shipped Spec Finder closure + unit/tolerance/type/sort upgrades; ongoing work is not blocked, but noted follow-ups are server-side `unit=in` API support and additional filters (min RPM/load, brand preference).

---

- [2026-04-23] Focus was turning the “set it up so we can use it” request into a usable bot feature, specifically wiring a materials-library command into the existing `pi-telegram-bot` Telegram runtime.
- Implemented `/materials [query]` in `/home/ubuntu/pi-telegram-bot/src/bot.ts`, including: registry loading from `learning-center/data/agent-build-materials.json`, help/overview mode, category filter, confidence filter, keyword search, formatted result output, and chunked replies.
- Added supporting parsing/formatting types and helpers in `bot.ts` (`AgentBuildMaterial`, `AgentBuildMaterialsRegistry`, `loadAgentBuildMaterialsRegistry`, `materialSearchText`, etc.) and introduced config path constant `MATERIALS_REGISTRY_PATH`.
- Updated `/start` command help text so users can discover `/materials` directly from bot command docs.
- Persisted memory update in `/home/ubuntu/pi-telegram-bot/memory/-1003363120939/identity.md` noting that `/materials` is now available for category/confidence/keyword lookup.
- Runtime status: restart was attempted with `pm2 restart chow` to apply changes, but command output was not returned/confirmed in-session, so live deployment verification is still pending (next check: confirm PM2 process healthy and test `/materials` in Telegram).
