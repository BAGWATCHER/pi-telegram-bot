# Catholic Market (v0)

Mobile-first Catholic marketplace scaffold:
- Curated global Catholic shop catalog
- AI concierge recommendations
- Social caption generation
- Shop onboarding intake

## Run locally
```bash
cd /home/ubuntu/pi-telegram-bot/factory/projects/catholic-shop
chmod +x scripts/start_demo_api.sh
./scripts/start_demo_api.sh
```

Local URL: `http://127.0.0.1:8110/`
Ops URL: `http://127.0.0.1:8110/ops`

## Dark-factory controls
- Manifest: `manifest.yaml`
- Queue: `queue.yaml`
- Lane claims: `artifacts/agent-lane-claims.json`
- Run status: `artifacts/run-status-2026-04-25.md`
- Eval command:
```bash
python3 eval/run_eval.py
```

## API
- `GET /health`
- `GET /api/v1/mobile/config`
- `GET /api/v1/catalog/feed` (supports `destination=` filter)
- `GET /api/v1/destinations`
- `GET /api/v1/products/{product_id}`
- `POST /api/v1/auth/guest-session`
- `GET /api/v1/users/{user_id}`
- `GET /api/v1/users/{user_id}/saved`
- `POST /api/v1/users/{user_id}/saved/{product_id}`
- `DELETE /api/v1/users/{user_id}/saved/{product_id}`
- `POST /api/v1/carts`
- `GET /api/v1/carts/{cart_id}`
- `POST /api/v1/carts/{cart_id}/items`
- `PUT /api/v1/carts/{cart_id}/items/{product_id}`
- `DELETE /api/v1/carts/{cart_id}/items/{product_id}`
- `POST /api/v1/checkout/intents`
- `POST /api/v1/checkout/buy-now`
- `GET /api/v1/orders`
- `GET /api/v1/orders/{order_id}`
- `POST /api/v1/orders/{order_id}/dispatch-note`
- `POST /api/v1/orders/{order_id}/status`
- `GET /api/v1/shops`
- `GET /api/v1/shops/{shop_id}`
- `POST /api/v1/shops/onboarding`
- `POST /api/v1/ai/recommend`
- `POST /api/v1/social/generate`

## Data files
- `data/processed/shops.json`
- `data/processed/products.json`
- `data/processed/shop_onboarding_leads.json`
- `data/processed/carts.json`
- `data/processed/orders.json`

## Starter inventory import
- Template: `data/raw/starter_inventory_intake.template.csv`
- Import script: `scripts/import_starter_inventory_csv.py`
- Run:
```bash
python3 scripts/import_starter_inventory_csv.py --input data/raw/starter_inventory_intake.csv
```
- Import summary artifacts:
  - `artifacts/inventory-import-summary.md`
  - `artifacts/inventory-import-summary.json`

## Notes
- Seed catalog is sample data only.
- Dad's item list import is intentionally deferred to CS-010 lane.
- UI is optimized for mobile first (single-column cards + bottom nav).
- Public demo route: `https://optimizedworkflow.dev/catholic-shop/`
- Stripe key loading for checkout uses `/home/ubuntu/.chow-secrets/stripe.env` via `scripts/start_demo_api.sh`.
