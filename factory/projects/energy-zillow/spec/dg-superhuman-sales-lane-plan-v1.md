# DemandGrid — Superhuman Sales OS Lane Plan v1 (DG-001..DG-010)

Updated: 2026-04-17
Owner: Mr Chow (coordination), parallel dark-factory lanes

Purpose: translate north-star vision into executable, parallel-safe lanes with clear ownership, API contracts, and eval gates.

## Stage Map
- **Now:** Foundation + guided execution
- **Next:** Connected multi-agent execution (outreach + calling + follow-up)
- **Target:** Safe autonomy with closed-loop self-improvement

---

## DG-001 — Revenue Graph Core
- **Goal:** unify site/business/contact/outcome entities with provenance + dedupe confidence.
- **Primary owner:** data-core-agent
- **API contract:**
  - `GET /api/v1/revenue-graph/site/{site_id}`
  - `GET /api/v1/revenue-graph/account/{account_id}`
  - `GET /api/v1/revenue-graph/contact/{contact_id}`
- **Eval gates:**
  - identity collision rate < 1%
  - provenance coverage >= 95% populated rows
  - no schema regression on existing site detail endpoints
- **Artifacts:** `schema/revenue-graph.schema.json`, `artifacts/revenue-graph-quality.md`

## DG-002 — Signal Mesh Normalization
- **Goal:** normalize triggers/behavioral/ops signals into one scoring-ready event contract.
- **Primary owner:** data-ingestion-agent
- **API contract:**
  - `GET /api/v1/signals/site/{site_id}`
  - `GET /api/v1/signals/coverage`
- **Eval gates:**
  - recency fields present for >= 90% active signal rows
  - source provenance attached per signal type
  - merge runs do not drop existing trigger contract columns
- **Artifacts:** `spec/signal-mesh-contract.md`, `artifacts/signal-mesh-coverage.md`

## DG-003 — Decision Engine v1 (Opportunity + NBA)
- **Goal:** compute opportunity score, win probability proxy, and next-best-action policy.
- **Primary owner:** scoring-policy-agent
- **API contract:**
  - `GET /api/v1/decision/site/{site_id}`
  - `POST /api/v1/decision/batch`
- **Eval gates:**
  - ranked cohort precision uplift vs current baseline
  - deterministic replay stability >= 0.95 on fixed snapshot
  - false-positive outreach rate non-increasing vs baseline
- **Artifacts:** `artifacts/decision-engine-v1.md`, `artifacts/decision-delta-vs-baseline.md`

## DG-004 — Universal Sales Schema (Vertical-Agnostic)
- **Goal:** make core sales entities reusable across energy + non-energy verticals.
- **Primary owner:** schema-platform-agent
- **API contract:**
  - `GET /api/v1/schema/sales-core`
  - `GET /api/v1/schema/vertical/{vertical_id}`
- **Eval gates:**
  - at least 2 vertical packs pass schema validation
  - no breaking changes to current energy routes
  - missing-field fallback policy documented and tested
- **Artifacts:** `schema/sales-core.schema.json`, `schema/vertical-pack.schema.json`, `spec/vertical-pack-contract.md`

## DG-005 — Playbook Compiler v1
- **Goal:** compile strategy into executable, role-safe playbooks (rep + agent modes).
- **Primary owner:** workflow-agent
- **API contract:**
  - `POST /api/v1/playbooks/compile`
  - `GET /api/v1/playbooks/{playbook_id}`
- **Eval gates:**
  - playbook includes objective, steps, channel order, objection map, stop conditions
  - compile latency p95 < 800ms for single lead context
  - guardrail flags present in 100% compiled outputs
- **Artifacts:** `artifacts/playbook-compiler-v1.md`, `artifacts/playbook-examples.json`

## DG-006 — Outreach Agent Connector
- **Goal:** connect DemandGrid outreach payloads to autonomous/semi-autonomous send pipeline.
- **Primary owner:** outreach-agent-integration
- **API contract:**
  - `POST /api/v1/agents/outreach/jobs`
  - `GET /api/v1/agents/outreach/jobs/{job_id}`
  - `POST /api/v1/agents/outreach/events`
- **Eval gates:**
  - delivery lifecycle states persisted end-to-end
  - suppression policy respected on all blocked examples
  - reply handling round-trip updates lead state correctly
- **Artifacts:** `spec/agent-outreach-contract.md`, `artifacts/outreach-job-lifecycle.md`

## DG-007 — Calling Agent Connector
- **Goal:** add call workflow interface (pre-call brief, live assist, post-call extraction).
- **Primary owner:** calling-agent-integration
- **API contract:**
  - `POST /api/v1/agents/calling/sessions`
  - `GET /api/v1/agents/calling/sessions/{session_id}`
  - `POST /api/v1/agents/calling/events`
- **Eval gates:**
  - pre-call brief quality checklist PASS on sample set
  - post-call extraction captures objection/outcome/reason consistently
  - call outcomes sync into lead outcome schema with no loss
- **Artifacts:** `spec/agent-calling-contract.md`, `artifacts/calling-session-eval.md`

## DG-008 — Multi-Agent Orchestrator v1
- **Goal:** coordinate decision -> outreach -> calling -> follow-up actions with policy controls.
- **Primary owner:** orchestration-agent
- **API contract:**
  - `POST /api/v1/orchestrator/runs`
  - `GET /api/v1/orchestrator/runs/{run_id}`
  - `POST /api/v1/orchestrator/actions/{action_id}/approve`
- **Eval gates:**
  - run graph emits deterministic state transitions
  - approval-required policies block autonomous execution when required
  - retry/idempotency behavior validated
- **Artifacts:** `spec/orchestrator-state-machine.md`, `artifacts/orchestrator-runbook.md`

## DG-009 — Closed-Loop Outcomes + Learning Pipeline
- **Goal:** capture outcomes and feed policy/model updates safely.
- **Primary owner:** learning-loop-agent
- **API contract:**
  - `POST /api/v1/outcomes`
  - `GET /api/v1/outcomes/summary`
  - `POST /api/v1/learning/retrain-jobs`
- **Eval gates:**
  - outcome completeness >= 90% for completed opportunities
  - attribution fields populated (signal/playbook/channel)
  - offline learning pass required before policy promotion
- **Artifacts:** `schema/lead-outcome.schema.json`, `artifacts/learning-loop-v1.md`, `artifacts/policy-promotion-checklist.md`

## DG-010 — Trust/Governance + Manager Command Layer
- **Goal:** enterprise-safe autonomy with audit, controls, and manager intelligence.
- **Primary owner:** governance-agent
- **API contract:**
  - `GET /api/v1/governance/policies`
  - `POST /api/v1/governance/policies/validate`
  - `GET /api/v1/manager/command`
- **Eval gates:**
  - every autonomous action has audit trail + policy decision record
  - role-based permission checks enforced for approval endpoints
  - manager risk alerts align with pipeline truth data
- **Artifacts:** `spec/governance-controls-v1.md`, `artifacts/manager-command-spec.md`

---

## Parallel Execution Wave Plan
- **Wave 1 (now):** DG-001, DG-002, DG-003, DG-004
- **Wave 2:** DG-005, DG-006, DG-007
- **Wave 3:** DG-008, DG-009, DG-010

Dependencies:
- DG-003 depends on DG-001/002
- DG-005 depends on DG-003/004
- DG-006/007 depend on DG-005
- DG-008 depends on DG-006/007
- DG-009 depends on DG-008 + outcome schema readiness
- DG-010 runs in parallel with DG-008/009 but must gate autonomous production mode

## Promotion Rules (Dark Factory)
- No lane close without:
  1. endpoint contract implemented,
  2. eval gate pass artifact,
  3. rollback note,
  4. update to `artifacts/run-status-YYYY-MM-DD.md`.
- No autonomous execution expansion without DG-010 governance checks PASS.
