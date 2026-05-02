# DG Craigslist Job Signal Lane v1

## Goal
Convert Craigslist job postings into outbound AI-automation opportunities with compliance-first guardrails.

## Ingest Strategy
- Primary: Craigslist RSS search URLs (`format=rss`) via `scripts/fetch_craigslist_job_signals.py`
- Fallback: manual seed/import (`POST /api/v1/signals/jobs/craigslist/import`) when RSS is blocked/rate-limited
- Current observed runtime behavior on Azure VM: Craigslist RSS returns `403 Forbidden` for tested job queries

## Core Files
- Config: `config/craigslist_job_signal_config.json`
- Fetch script: `scripts/fetch_craigslist_job_signals.py`
- Research/enrichment script: `scripts/enrich_craigslist_opportunities.py`
- Processed signal store: `data/processed/craigslist_job_signals.json`
- Research store: `data/processed/craigslist_company_research.json`
- Research feedback / suppression store: `data/processed/craigslist_research_feedback.json`
- Email thread store: `data/processed/email_threads.json`
- Mailbox sync state: `data/processed/mailbox_sync_state.json`
- Raw signal CSV: `data/raw/craigslist_job_signals.csv`
- Summary artifacts: `artifacts/craigslist-job-signal-summary.{md,json}`
- Research architecture note: `artifacts/craigslist-research-architecture-2026-04-24.md`
- Outreach queue store: `data/processed/craigslist_outreach_queue.json`

## API Surface
- `POST /api/v1/signals/jobs/craigslist/refresh`
  - Runs the Craigslist RSS ingest script.
- `GET /api/v1/signals/jobs/craigslist`
  - Lists scored opportunities with filters (`min_score`, `market_id`, `channel`, `limit`).
  - Includes `ingest_warnings` to surface query-level fetch errors.
- `GET /api/v1/signals/jobs/craigslist/opportunity/{opportunity_id}`
  - Returns one opportunity.
  - When research exists, the paired research packet now carries a structured `superhuman_sales_brief` with company read, role analysis, bottlenecks, highest-leverage AI opportunity, outreach strategy, and ranking scores.
- `POST /api/v1/signals/jobs/craigslist/opportunity/{opportunity_id}/research-refresh`
  - Reruns company enrichment for one opportunity, updates `data/processed/craigslist_company_research.json`, and refreshes any linked queue records so the dashboard sees the new research immediately.
- `POST /api/v1/signals/jobs/craigslist/import`
  - Manual seed path for opportunities when automated source ingestion is blocked.
- `GET /api/v1/signals/jobs/craigslist/outreach-queue`
  - Lists queued outreach tasks.
- `GET /api/v1/signals/jobs/craigslist/outreach-queue/{queue_id}`
  - Returns one queue record including draft copy, review metadata, recipient preview, research packet, and dispatch state.
- `PUT /api/v1/signals/jobs/craigslist/outreach-queue/{queue_id}/review`
  - Saves operator edits + review labels (`research_quality`, `company_match`, `contact_path_status`, `draft_status`, draft fields, optional recipient override).
  - Marks bad company matches into `data/processed/craigslist_research_feedback.json` so future enrichment runs can suppress known-wrong hosts.
- `POST /api/v1/signals/jobs/craigslist/opportunity/{opportunity_id}/queue-outreach`
  - Adds a supervised outreach draft to queue with compliance-review flag.
  - Queue records now include the resolved company research packet when `data/processed/craigslist_company_research.json` has a matching `opportunity_id`, and draft copy is generated from that enriched context.
  - That research packet now includes a `what_matters_summary`, `recommended_ai_workflow`, and nested `superhuman_sales_brief` so Chow can reason from a more explicit opportunity diagnosis instead of only raw role/pain strings.
- `POST /api/v1/signals/jobs/craigslist/outreach-queue/{queue_id}/dispatch`
  - Sends the queued outreach email as Chow through the live email adapter when `promote_to_live=true` and a contact hint email or trusted research email exists.
  - Also records the outbound send into the shared inbox-thread store so replies can attach to the queue record later.
- `GET /api/v1/inbox/status`
  - Shows mailbox provider readiness and missing IMAP requirements.
- `GET /api/v1/inbox/threads`
  - Lists stored Chow email threads.
- `GET /api/v1/inbox/threads/{thread_id}`
  - Returns one stored Chow email thread with messages.
- `POST /api/v1/inbox/import`
  - Imports one or more inbound/outbound email messages into the thread store and can link them to a Craigslist queue record or outreach job.
- `POST /api/v1/inbox/poll`
  - Polls an IMAP inbox when mailbox credentials are configured, then imports matching messages through the same inbox contract.

## Guardrails
- Queue records default to `requires_compliance_review=true`.
- Minimum score threshold for queueing is `0.55` unless `force=true`.
- Source policy included on each queue record for auditability.
- No blind auto-send; sending still requires supervised dispatch with `promote_to_live=true`.
- Dispatch requires at least one reachable email, either from `contact_hint_emails` on the opportunity or a public email found in the matched company research packet.
- Research marked as a wrong company match is treated as non-trustworthy immediately in the queue review lane and is also suppressed in future enrichment runs.
- Reply ingestion is still supervised: the dashboard can import a pasted reply immediately, and IMAP polling remains gated on mailbox credentials being present.

## Next Steps
1. Run the new research pass against the NH-centered New England pilot markets so Chow works from enriched company packets instead of raw job posts.
2. Add proxy/provider adapter if Craigslist RSS must run from non-datacenter IP.
3. Add role-specific ROI calculator (hours saved + annualized value).
4. Add suppression + opt-out registry for CAN-SPAM/TCPA workflow safety.
5. Wire real Zoho/IMAP credentials so `POST /api/v1/inbox/poll` can import live replies to `chow@optimizedworkflow.dev`.
6. Add thread-aware reply drafting / send controls on top of the new inbox-thread store.
