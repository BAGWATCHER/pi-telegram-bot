# Catholic Market Eval Summary

- generated_at: `2026-05-02T03:57:15Z`
- base_url: `http://127.0.0.1:8110`
- pass: **NO**
- checks: `9/10`
- failed: `1`
- p95_ms: `2140.99`

## Check results

- [PASS] `health_gate` (2140.99 ms) — health endpoint valid
- [PASS] `catalog_gate` (10.73 ms) — catalog returned items
- [PASS] `destination_browse_gate` (32.48 ms) — destinations endpoint + filtered catalog valid
- [PASS] `ai_recommend_gate` (10840.11 ms) — recommendations returned
- [PASS] `social_gate` (9.64 ms) — social draft payload valid
- [FAIL] `mobile_html_gate` (15.27 ms) — missing bottom nav scaffold
- [PASS] `auth_saved_gate` (36.82 ms) — guest auth and save/unsave flow valid
- [PASS] `cart_checkout_intent_gate` (42.06 ms) — cart add/update + checkout intent idempotency valid
- [PASS] `checkout_order_ops_gate` (40.9 ms) — dry-run checkout + order ops valid
- [PASS] `analytics_gate` (15.16 ms) — post + summary valid (total: 10, event_id: dae9971f-7ffa-4b4c-aee1-606517fe5b38)
