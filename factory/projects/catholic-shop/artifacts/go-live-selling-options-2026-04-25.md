# Go-Live Selling Options (2026-04-25)

## Recommendation
Start with **Buy-Now Checkout + Partner-Managed Inventory** and run first paid orders immediately.

Why:
- Lowest integration complexity
- Fastest speed to first revenue
- Compatible with small global Catholic shops

## Option A — Buy-Now checkout (live now)
- Product-level checkout links via Stripe Checkout Session
- Persisted order records with status transitions
- Partner dispatch notes captured in API

API now live:
- `POST /api/v1/checkout/buy-now`
- `GET /api/v1/orders`
- `GET /api/v1/orders/{order_id}`
- `POST /api/v1/orders/{order_id}/dispatch-note`
- `POST /api/v1/orders/{order_id}/status`

## Option B — Full cart + checkout intents (next)
- Better conversion and AOV optimization
- Requires CS-005 completion

## Option C — Shopify backend hybrid (later)
- Lower tax/shipping risk long-term
- Slower to launch than Option A

## Inventory model to run now
- `in_stock`, `low_stock`, `made_to_order` states
- daily CSV/Sheet sync from partner shops
- lead times mandatory for made-to-order products

## First-week execution checklist
1. Load 20–50 SKUs using starter template/import script.
2. Verify price + inventory + image + provenance fields.
3. Launch destination pages (Assisi/Kraków/Guadalajara) with paid checkout.
4. Process dispatch notes and status updates for each order.
5. Track conversion + cancellation reasons; feed into CS-013 optimization lane.
