# Catholic Market Launch Plan v1 (mobile-first)

## Objective
Build the platform core before ingesting the final item list:
1) Mobile storefront
2) Partner shop onboarding
3) Catalog + provenance model
4) AI recommendation concierge
5) Social content generation workflow

## Phase 1 (current scaffold)
- FastAPI backend + mobile-first frontend
- Seed data model for shops/products
- AI recommend endpoint (`/api/v1/ai/recommend`)
- Social content endpoint (`/api/v1/social/generate`)
- Shop onboarding endpoint (`/api/v1/shops/onboarding`)

## Phase 2 (commerce core)
- User auth + saved lists
- Cart + checkout (Stripe)
- Order state machine
- Shop payout model + commission ledger

## Phase 3 (trust + operations)
- Product provenance attestations
- Policy pages and returns by shop
- Fraud/risk checks for partner stores
- SKU-level shipping/lead-time SLA flags

## Phase 4 (catalog import)
- Import dad’s item list (CSV/Google Sheet)
- Data cleanup + duplicate merge
- Publish workflow and QA

## Mobile UX Requirements
- 390px baseline design target
- <2 tap path from home to product details
- Sticky buy actions on product page
- Bottom navigation for repeat sessions
- Optimized images + lazy loading
