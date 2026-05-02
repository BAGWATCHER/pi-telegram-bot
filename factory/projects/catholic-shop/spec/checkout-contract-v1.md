# Checkout Contract v1 (CS-005)

## Scope
Mobile cart primitives + deterministic checkout intent creation for Catholic Shop.

## Endpoints

### 1) Create cart session
`POST /api/v1/carts`

Request:
```json
{
  "user_id": "user_..." 
}
```

Response:
```json
{
  "cart": {
    "cart_id": "cart_...",
    "user_id": "user_...",
    "status": "active",
    "items": [],
    "total_quantity": 0,
    "subtotal_cents": 0,
    "currency": "USD"
  }
}
```

### 2) Cart item mutation
- `POST /api/v1/carts/{cart_id}/items` (add quantity)
- `PUT /api/v1/carts/{cart_id}/items/{product_id}` (set quantity)
- `DELETE /api/v1/carts/{cart_id}/items/{product_id}` (remove)
- `GET /api/v1/carts/{cart_id}` (read)

Rules:
- rejects unknown product IDs
- rejects out-of-stock items
- enforces `quantity_on_hand` when available
- returns hydrated cart totals (`total_quantity`, `subtotal_cents`)

### 3) Checkout intent
`POST /api/v1/checkout/intents`

Request:
```json
{
  "cart_id": "cart_...",
  "user_id": "user_...",
  "idempotency_key": "client-key-1",
  "customer_email": "buyer@example.com",
  "success_url": "https://...",
  "cancel_url": "https://...",
  "dry_run": false
}
```

Response:
```json
{
  "intent_id": "ord_...",
  "order_id": "ord_...",
  "cart_id": "cart_...",
  "status": "checkout_pending",
  "checkout_url": "https://checkout.stripe.com/...",
  "checkout_mode": "stripe_live",
  "reused": false,
  "order": { "...": "persisted order draft" }
}
```

Idempotency behavior:
- if same `cart_id + idempotency_key` is replayed, API returns prior intent with `reused=true`
- order draft persisted in `data/processed/orders.json`

## Persistence
- cart store: `data/processed/carts.json`
- checkout/order drafts: `data/processed/orders.json`

## Notes
- Buy-now endpoint remains available for single-item fast checkout:
  - `POST /api/v1/checkout/buy-now`
