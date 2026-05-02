DeepSeek Lane A — Catholic Shop Analytics Foundation

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
