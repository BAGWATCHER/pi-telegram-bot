# Catholic Market — Dark Factory Lane Plan v1

## Operating Model
- Team style: parallel lane execution with low-collision file ownership.
- Merge strategy: small additive diffs + eval gates before promotion.
- Cadence: each lane emits artifact evidence every cycle.

## Lane Ownership
1. **Platform Lane**
   - Scope: API primitives, data contracts, frontend integration.
   - Files: `backend/api/*`, `frontend/*`, `data/processed/*`
2. **Commerce Lane**
   - Scope: cart, checkout intents, order lifecycle, payment adapters.
   - Files: `backend/api/*`, `spec/checkout-*`, `data/processed/orders*`
3. **AI Lane**
   - Scope: recommendation quality, social generation, policy guardrails.
   - Files: `backend/api/*`, `spec/ai-*`, `artifacts/ai-*`
4. **Partner Ops Lane**
   - Scope: shop onboarding pipeline, review queue, partner SLA states.
   - Files: `data/processed/shop_onboarding_*`, `spec/onboarding-*`
5. **Trust + Compliance Lane**
   - Scope: provenance standards, suppression rules, policy docs.
   - Files: `spec/provenance-*`, `backend/api/*`, `artifacts/trust-*`
6. **Eval Lane**
   - Scope: objective quality gates, regressions, release scorecard.
   - Files: `eval/*`, `artifacts/eval-*`

## Handoff Contract
- Every lane handoff must include:
  1) what changed,
  2) risk notes,
  3) smoke/eval evidence,
  4) exact files touched.

## Quality Gates (must pass)
1. API health + core endpoints reachable.
2. Mobile viewport gate: critical UI elements visible at 390x844.
3. AI recommendation gate: non-empty ranked results for known intents.
4. Social generation gate: draft payload contract valid.

## Promotion Rules
- `done-local` requires eval PASS + run-status update.
- `ready-for-review` requires no unresolved blocker in lane claims.
- `deploy-candidate` requires manager approval and smoke on public route.

## Immediate Wave-1 Priorities
1. CS-004 auth + saved items.
2. CS-005 cart + checkout intent scaffold.
3. CS-006 onboarding review states.
4. CS-007 recommendation eval suite.
