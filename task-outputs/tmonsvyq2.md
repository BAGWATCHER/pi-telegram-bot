# Task: DeepSeek Lane A — Catholic Shop Analytics Foundation

Project path: /home/ubuntu/pi-telegram-bot/factory/projects/catholic-shop

Read first:
- spec/deepseek-agent-build-plan-2026-05-02.md
- backend/api/app.py route list and helpers
- eval/run_eval.py

Task:
Implement the analytics/event logging foundation for the Catholic Shop without breaking existing endpoints.

Rules:
- Uptime-first, additive changes.
- Do not enable live Stripe or change payment behavior.
- No emoji UI icons.
- Preserve all existing API response contracts.
- Avoid large rewrites of backend/api/app.py. Add focused helpers/routes only.
- If you create new files, keep them simple and stdlib-only unless dependencies already exist.

Deliverables:
1. Add a durable event log store. Prefer JSONL at data/processed/analytics_events.jsonl for this first lane unless SQLite is already safely established. Each event should include: event_id, event_type, timestamp, session_id/user_id if provided, path/source if provided, and sanitized payload.
2. Add backend helper(s) to append events with privacy guardrails: cap long strings, omit token/password/auth fields, tolerate write errors.
3. Add POST /api/v1/analytics/events that accepts client events and writes them.
4. Add GET /api/v1/analytics/summary that returns useful counts: total events, counts by event_type, top product IDs, top shop IDs, recent chat queries/no-result queries if available.
5. Auto-log safe backend events in existing endpoints where low risk:
   - product detail viewed/fetched
   - shop detail viewed/fetched
   - chat message submitted (cap message text)
   - AI recommendation request/result count
6. Add or update eval/run_eval.py with analytics gates: post a test event, fetch summary, assert event count/type present.
7. Update artifacts/eval-summary.* by running the local eval if the service is reachable.

Acceptance:
- Existing eval gates should not regress. If mobile_html_gate is already failing before your changes, mention that as pre-existing and do not spend time on it unless trivial.
- curl POST /api/v1/analytics/events returns 200.
- curl GET /api/v1/analytics/summary returns analytics data.
- End final response with DONE: concise summary, or BLOCKED: specific blocker.

Project: catholic-shop
Path: /home/ubuntu/pi-telegram-bot/factory/projects/catholic-shop
Started: 2026-05-02T03:47:14.809Z
Elapsed: 11m 4s

## Output

Let me continue reading the rest of `app.py` and check existing project structure.Now I have a full picture. Let me note: `mobile_html_gate` is already failing pre-existing (missing bottom nav scaffold). I'll document that and not fix it.

Let me implement everything now.

**Step 1: Create the analytics store helper.****Step 2: Add analytics routes and auto-logging to app.py.**

First, let me add the import:Now add the analytics Pydantic model:Now add the analytics routes at the end of the file:Now add auto-logging in `product_detail`:Now add auto-logging in `get_shop`:Now add auto-logging in `chat_send`:Now add auto-logging in `ai_recommend` — both the PI success path and the fallback path:Add auto-logging for the fallback path of `ai_recommend`:**Step 3: Update eval/run_eval.py with analytics gates.****Step 4: Verify service is running and test endpoints.**Let me verify the new code compiles correctly:Now test the analytics endpoints:Both analytics endpoints work. Now test the auto-logging by hitting a product detail endpoint:Check that auto-logging events are now in the summary:Auto-logging for product views is working. Let me test the remaining auto-log endpoints:All auto-logging working. Now run the full eval suite:Everything looks great. Let me verify the JSONL file format:Let me also verify the privacy guardrails work as expected:Privacy guardrails are working correctly. Let me also quickly verify the `chat_send` auto-logging works. Since chat uses streaming, I'll just send a request and check if the event was logged:All auto-logging verified. Let me do a final clean run of the eval to ensure artifacts are updated:Let me clean up the extra uvicorn on port 8099 and confirm the final state:Everything is working. Let me provide the final summary.

---

**What was delivered:**

1. **`backend/api/analytics_store.py`** — Durable JSONL event store at `data/processed/analytics_events.jsonl` with thread-safe writes, full privacy guardrails (redacts `password`, `token`, `auth`, `stripe` fields; caps all strings at 500 chars), and a `compute_summary()` function returning total event counts, counts by event_type, top product/shop IDs, and recent chat/no-result queries.

2. **`POST /api/v1/analytics/events`** and **`GET /api/v1/analytics/summary`** routes added to `backend/api/app.py` — the POST accepts client events with sanitization and returns `accepted: true` plus the `event_id`; the GET returns full analytics summary with all requested dimensions.

3. **Auto-logging** woven into 4 existing endpoints without changing response contracts: `product_detail` → `product_view`, `get_shop` → `shop_view`, `chat_send` → `chat_message` (message text capped), `ai_recommend` → `ai_recommend` (with result_count, both PI and fallback paths logged).

4. **`eval/run_eval.py`** — new `analytics_gate` that posts a test event, fetches the summary, and asserts event count >= 1 and the `eval_test` type is present. Artifacts updated at `artifacts/eval-summary.json` and `artifacts/eval-summary.md`.

**Eval results:** 9/10 gates pass. The sole failure is the pre-existing `mobile_html_gate` (missing bottom nav scaffold) — unchanged by these additions. All existing gates (`health`, `catalog`, `destination_browse`, `ai_recommend`, `social`, `auth_saved`, `cart_checkout_intent`, `checkout_order_ops`) continue to pass. No Stripe or payment behavior was touched.

DONE: Added JSONL-based analytics event store with privacy guardrails, POST/GET analytics endpoints, auto-logging in 4 key backend routes (product view, shop view, chat message, AI recommend), and a new analytics eval gate. All 9 existing eval gates preserve their pass/fail status — only the pre-existing `mobile_html_gate` failure remains.