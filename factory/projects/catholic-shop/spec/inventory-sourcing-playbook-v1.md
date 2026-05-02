# Inventory Sourcing Playbook v1 (Catholic Market)

## Goal
Get real sellable items listed quickly with a practical inventory process before full catalog ingestion.

## Fastest viable models

## Model A — Partner-managed inventory (recommended start)
- Shop owns stock and fulfillment.
- We list product + show live-ish inventory state (`in_stock`, `low_stock`, `out_of_stock`, `made_to_order`).
- Inventory sync via CSV/Sheet upload 1-2x daily.

Pros:
- Fast to launch, low capital risk.
- Works with small shops globally.

Cons:
- Inventory freshness depends on partner update cadence.

## Model B — Inquiry inventory (for rare artisan items)
- No strict quantity; item marked `made_to_order` or `limited_batch`.
- Lead times are mandatory.

Pros:
- Good for handmade/limited devotional items.

Cons:
- Slower checkout fulfillment expectations.

## Model C — Central stock (later)
- We hold inventory and ship ourselves.

Pros:
- Highest control and conversion.

Cons:
- Highest operational complexity and cash tied in stock.

## Recommended launch path
1. Start with Model A + some Model B for artisan pieces.
2. Require each partner to provide:
   - SKU
   - quantity_on_hand (or inventory_mode)
   - lead_time_days
   - price + image + provenance fields
3. Update inventory twice daily during launch.

## Data contract (minimum)
- `sku`
- `title`
- `shop_id`
- `price_usd`
- `currency`
- `country`, `city`
- `inventory_mode` (`in_stock|low_stock|out_of_stock|made_to_order|preorder`)
- `quantity_on_hand`
- `lead_time_days`
- `image_url`

## Operational guardrails
- Never list as `in_stock` with `quantity_on_hand=0`.
- If quantity unknown, use `made_to_order` + lead time.
- Auto-downgrade to `low_stock` when qty <= 2.
- Keep a timestamped import log for accountability.

## Immediate execution checklist
- [x] intake CSV template created
- [x] import script created
- [ ] partner sends first CSV batch (10–30 SKUs)
- [ ] import to `data/processed/products.json`
- [ ] QA pass: image links, price sanity, stock sanity
