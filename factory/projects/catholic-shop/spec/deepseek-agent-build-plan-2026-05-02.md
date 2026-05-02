# Catholic Shop — DeepSeek Agent Build Plan
## 2026-05-02 · Approved Workstreams 2-6

## Adam's Direction
Proceed on workstreams **2, 3, 4, 5, 6**:
2. Analytics/event logging
3. Shop profile + product detail pages
4. SQLite catalog migration
5. Concierge eval/ranking upgrade
6. Real shop/product onboarding

Explicitly do **not** make live Stripe checkout the center of this wave. Stripe remains parked until real inventory exists.

---

## Operating Principle
Use DeepSeek agents as implementation workers, but keep Chow as architect/integrator. Avoid letting multiple agents freely edit `backend/api/app.py` at the same time; it is a ~2000-line central file and is the highest collision risk.

## Non-Negotiable Design Rules
- No emoji UI icons. Use inline SVGs or text.
- No chat bubbles / boxed AI-message styling.
- Keep the Scriptorium aesthetic: parchment, ink, restrained gold, editorial Catholic tone.
- Mobile baseline: 390px wide.
- Uptime first: additive changes, JSON fallback, minimal PM2 restarts.

---

## Target Architecture After This Wave

### Data
- `data/processed/catalog.sqlite3` becomes the catalog runtime store.
- Existing JSON files remain as backup/export and migration input:
  - `shops.json`
  - `products.json`
  - `shop_onboarding_leads.json`
- New analytics file/table records market signal:
  - visitor/session event
  - chat query
  - products shown
  - product click
  - shop view
  - add-to-cart
  - no-result query

### Pages
- `/catholic-shop/product/{product_id}`: richer Codex-style detail page, fully data-driven.
- `/catholic-shop/shop/{shop_id}`: shop profile with story, location, verification, products, and concierge CTA.
- `/catholic-shop/partner` or `/catholic-shop/shops/onboarding`: real shop intake flow.
- `/catholic-shop/ops`: internal signal dashboard additions.

### AI
- Concierge should not just react to product name mentions.
- It should rank catalog products deterministically first, then ask DeepSeek to explain why.
- Product cards should come from explicit product IDs, not fragile text matching.
- Eval prompts should test baptism, confirmation, wedding, grief/healing, home blessing, destination-specific requests, budget, and no-match honesty.

---

## Agent Lanes

### Lane A — Platform + Analytics Foundation
**Model:** DeepSeek V4 Pro  
**Collision risk:** high — owns backend integration first.

**Files owned**
- `backend/api/app.py`
- new `backend/api/analytics_store.py` if useful
- `data/processed/analytics_events.jsonl` or SQLite `analytics_events`
- `frontend/ops.html` for summary view, if time

**Deliverables**
1. `POST /api/v1/analytics/events`
2. `GET /api/v1/analytics/summary`
3. Backend helper `log_event(event_type, payload)`
4. Auto-log backend views where safe:
   - product detail fetch
   - shop detail fetch
   - chat send
   - AI recommendations
5. Privacy guardrails: cap text fields, no passwords/tokens, no raw auth headers.

**Acceptance tests**
- `curl POST /api/v1/analytics/events` returns 200.
- Summary shows counts and top products/queries.
- Existing eval still passes.

---

### Lane B — Shop + Product Page Realness
**Model:** DeepSeek V4 Pro  
**Collision risk:** medium — avoid backend edits unless route/page serving is needed.

**Files owned**
- `frontend/product.html`
- new `frontend/shop.html`
- possibly `frontend/index.html` for links
- minimal route additions in `backend/api/app.py` only after Lane A merged

**Deliverables**
1. Data-driven product detail page with:
   - product image
   - shop name + location
   - story/provenance
   - materials
   - sacrament tags
   - lead time/inventory status
   - CTA into chat: “Ask the concierge about this item”
2. Shop profile page with:
   - shop story
   - city/country
   - verification marker in text/SVG, not emoji
   - product grid
   - shipping regions
   - CTA to concierge
3. Product cards link to product detail; shop name links to shop profile.

**Acceptance tests**
- `/product/{id}` loads known product.
- `/shop/{shop_id}` loads known shop.
- Mobile layout works at 390px.
- No emoji icons.

---

### Lane C — SQLite Catalog Migration
**Model:** DeepSeek V4 Pro  
**Collision risk:** high if it touches app helpers; run after Lane A.

**Files owned**
- `scripts/migrate_catalog_to_sqlite.py`
- new `backend/api/catalog_store.py` or similar
- `data/processed/catalog.sqlite3`
- `backend/api/app.py` helper replacement only after backup

**Deliverables**
1. Migration from `products.json` + `shops.json` into SQLite.
2. Tables:
   - `shops`
   - `products`
   - `product_tags`
   - `product_sacrament_tags`
   - `product_materials`
   - `analytics_events` if Lane A chooses SQLite
3. Runtime read helpers preserving current JSON-shaped response contracts.
4. JSON fallback if SQLite missing/corrupt.
5. Export script or backup path so data never gets trapped.

**Acceptance tests**
- Existing `/api/v1/catalog/feed`, `/api/v1/products/{id}`, `/api/v1/shops`, `/api/v1/shops/{id}` responses still work.
- Eval passes.
- DB can be deleted and app falls back to JSON.

---

### Lane D — Concierge Ranking + Eval Upgrade
**Model:** DeepSeek V4 Pro  
**Collision risk:** low/medium — mostly sidecar and eval.

**Files owned**
- `backend/pi-concierge/index.js`
- `eval/run_eval.py`
- new `eval/chat_cases.json` or `eval/recommendation_cases.json`
- `artifacts/eval-*`

**Deliverables**
1. Deterministic catalog ranker before LLM explanation.
2. Explicit product ID product-card emission.
3. No hallucinated products; if no fit, say closest match or ask question.
4. Eval cases for:
   - baptism goddaughter
   - confirmation teen boy
   - Catholic wedding gift
   - grief/healing Lourdes
   - home blessing crucifix/candle
   - Marian devotion/Fátima/Guadalupe
   - under-$40 budget
   - no-match query
5. Eval output includes pass/fail per case and recommended product IDs.

**Acceptance tests**
- Product cards show on first relevant message.
- Known prompts return non-empty product IDs.
- No-match prompt does not invent products.
- Existing chat streaming still works.

---

### Lane E — Real Shop/Product Onboarding
**Model:** DeepSeek V4 Pro  
**Collision risk:** medium — mostly frontend + intake data.

**Files owned**
- `frontend/ops.html`
- new `frontend/partner.html` or onboarding section
- `data/raw/starter_inventory_intake.template.csv`
- `scripts/import_starter_inventory_csv.py`
- `spec/inventory-sourcing-playbook-v1.md`

**Deliverables**
1. Partner intake page with:
   - shop identity
   - location
   - Catholic/artisan story
   - contact info
   - shipping capability
   - product upload notes
   - verification checklist
2. Better onboarding lead schema:
   - status
   - verification state
   - sample product count
   - shipping regions
   - payout preference/manual Stripe Connect placeholder
3. Product import template upgraded for real vendors.
4. Ops page can review onboarding leads.

**Acceptance tests**
- Submit onboarding form → lead stored.
- Ops can see lead.
- CSV import still works.

---

## Recommended Execution Order

### Step 0 — Chow Preflight
- Snapshot current files.
- Run existing eval.
- Confirm PM2 process names/ports.

### Step 1 — Dispatch Lane A first
Analytics foundation changes the backend and gives us signal logging primitives.

### Step 2 — Dispatch B + D in parallel
Shop/product pages and AI ranking touch mostly separate files.

### Step 3 — Dispatch C after A
SQLite migration should come after analytics shape is settled.

### Step 4 — Dispatch E after B/C
Onboarding should write into the new data shape, not the old one.

### Step 5 — Chow Integration
- Review diffs.
- Resolve collisions.
- Build chat UI.
- Run evals.
- Restart only affected PM2 processes.
- Verify public route.

---

## Deployment Gates
1. `python3 eval/run_eval.py --base-url http://127.0.0.1:8110` passes.
2. `npm run build` passes in `chat-ui` if touched.
3. `curl /health` shows expected product/shop counts.
4. Product + shop pages return 200 on local and public route.
5. Analytics summary returns data after test events.
6. No live Stripe activation.

---

## Success Definition
After this wave, the site should feel less like a demo and more like a real Catholic marketplace testbed:
- We can see what visitors ask for.
- Every product and shop has a credible story page.
- Catalog data is ready to scale beyond hardcoded JSON.
- The concierge makes trustworthy product recommendations.
- Real shops have a path to submit inventory.
