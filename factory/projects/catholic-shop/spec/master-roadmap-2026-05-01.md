# Catholic Marketplace — Master Roadmap
## 2026-05-01 · Status: Foundation laid, ready to scale execution

---

## Current State

| What | Status |
|------|--------|
| Frontend | Alpine.js + Tailwind, Scriptorium aesthetic, live |
| Products | 18 across 6 shops / 6 destinations |
| Product page | Codex concept proven (Lourdes water page live) |
| Cart | API exists, UI wired |
| Checkout | Stripe live key configured, not end-to-end tested |
| AI concierge | GPT endpoint exists, generic, not destination-aware |
| Saved items | localStorage + API |
| Shops | 6 hand-curated, no real shops onboarded |
| Data model | Flat JSON, no Codex fields (provenance, artisan, prayer, etc.) |
| Deployment | PM2 on Azure, Caddy reverse proxy at `/catholic-shop/` |
| Domain | Served via direct IP only (40.75.10.4) |

---

## Workstreams

### STREAM 1 — PRODUCT PAGES (high urgency, high impact)
**Owner:** TBD · **Est:** 2-3 days

The Codex product page is the differentiator. Currently only Lourdes water is rich; 17 products hit a generic fallback.

| Task | Est | Description |
|------|-----|-------------|
| 1.1 | 2h | Write Codex data for 5 hero products (one per remaining destination) |
| 1.2 | 3h | Expand backend data model: add `provenance_steps[]`, `artisan{}`, `blessing{}`, `prayer{}`, `holy_ground{}`, `packaging_description`, `sacrament_contexts[]` |
| 1.3 | 2h | Make product.html fully data-driven — read from API/embedded JSON, render Codex for any product |
| 1.4 | 1h | Add `tier` field to products (keepsake/devotional/heirloom) → render compact vs full Codex vs full + certificate |
| 1.5 | 1h | Fill remaining 12 products with at least tier-appropriate data |

**Deliverable:** 18 products, each with a Codex page that matches its tier. Tapping any card = rich experience.

---

### STREAM 2 — SACRAMENT & DISCOVERY (high impact)
**Owner:** TBD · **Est:** 2 days

People don't search for "olive wood rosary." They search for "baptism gift for my goddaughter." Discovery by life moment converts better than discovery by category.

| Task | Est | Description |
|------|-----|-------------|
| 2.1 | 3h | "Browse by Sacrament" page — 6 life moments (Baptism, First Communion, Confirmation, Wedding, Anointing/Sick, Home Blessing), each showing relevant products across all destinations |
| 2.2 | 2h | Sacrament-aware AI concierge — when user says "I'm attending a baptism Saturday," recommend baptism-appropriate gifts first |
| 2.3 | 2h | "Build a Prayer Corner" flow — guided multi-product selector (icon + crucifix + candle + rosary), assembles into one cart |
| 2.4 | 1h | Sacrament tag taxonomy — normalize tags across all 18 products, add missing ones |

**Deliverable:** Browseable by life moment. AI understands context. Prayer corner flow.

---

### STREAM 3 — CHECKOUT & TRANSACTIONS (critical path)
**Owner:** TBD · **Est:** 2 days

Nothing ships if people can't pay. Stripe is configured but untested. No order confirmation email, no shipping address collection, no tax.

| Task | Est | Description |
|------|-----|-------------|
| 3.1 | 2h | End-to-end Stripe checkout flow test — create intent → confirm → webhook → order created |
| 3.2 | 2h | Order confirmation page + email (transactional, Scriptorium-styled) |
| 3.3 | 2h | Shipping calculator — weight-based, international rate estimates |
| 3.4 | 1h | Address collection UX — shipping address form, saved addresses |
| 3.5 | 1h | Tax handling — basic sales tax by destination, or manual for now |

**Deliverable:** Someone can buy a Lourdes water bottle and receive order confirmation.

---

### STREAM 4 — SHOP ONBOARDING (growth lever)
**Owner:** TBD · **Est:** 3 days

Currently all 6 shops are fictional placeholders. Real shops = real products = real business. This is the hard work.

| Task | Est | Description |
|------|-----|-------------|
| 4.1 | 4h | Shop intake flow — form/page where a shop submits: name, location, story, product list with photos, shipping info, payout preference |
| 4.2 | 3h | Shop admin panel — simple dashboard: view orders, mark shipped, update inventory, see earnings |
| 4.3 | 2h | Payout system — Stripe Connect or manual (track earnings, trigger payout) |
| 4.4 | 4h | Outreach templates — 3 email/DM templates for approaching shops at Lourdes, Assisi, Fátima, Jerusalem, Kraków, Guadalupe |
| 4.5 | 2h | Shop verification checklist — what we need before listing (real photos, blessing verification, shipping capability) |

**Deliverable:** A real shop can sign up, list products, receive orders, and get paid.

---

### STREAM 5 — CONVERSATIONAL SHOPPING (CS-029 from wave 2)
**Owner:** TBD · **Est:** 3 days

Claude-artifact-style chat interface where products appear inline as the AI guides the shopper. This is the most forward-looking feature.

| Task | Est | Description |
|------|-----|-------------|
| 5.1 | 3h | Chat UI — message bubbles, typing indicator, scroll-to-bottom, mobile keyboard aware |
| 5.2 | 3h | Inline product cards — AI response includes `[product: id]` tokens → render Codex-lite card in chat stream |
| 5.3 | 2h | Context memory — AI remembers "you mentioned a wedding gift" across messages |
| 5.4 | 2h | "Surprise me" / "I need help" entry points — warm, low-pressure prompts |
| 5.5 | 2h | Cart integration — "Add that one" adds from chat to cart without leaving conversation |

**Deliverable:** A chat interface that feels like talking to a knowledgeable friend at a pilgrimage gift shop.

---

### STREAM 6 — EMAIL & SPIRITUAL RHYTHMS (retention)
**Owner:** TBD · **Est:** 2 days

E-commerce retention through prayer rhythms, not discount codes.

| Task | Est | Description |
|------|-----|-------------|
| 6.1 | 2h | Feast day emails — St. Francis day: "Your tau cross from Assisi was carved near his tomb." Optional, opt-in |
| 6.2 | 3h | Candle/oil lifecycle emails — "Your Peace Candle has been burning for 20 hours." → refill prompt |
| 6.3 | 1h | "Prayer saved" collection — user's saved prayers, accessible as a personal page |
| 6.4 | 1h | Blessing anniversary — "One year ago today, your rosary was blessed at the Holy Sepulchre" |

**Deliverable:** Retention emails that feel like spiritual accompaniment, not marketing.

---

### STREAM 7 — DOMAIN, BRAND & SEO (distribution)
**Owner:** TBD · **Est:** 1 day

Currently served via bare IP. No one discovers a raw IP address.

| Task | Est | Description |
|------|-----|-------------|
| 7.1 | 1h | Buy domain (suggestions: catholic.market, sanctorum.shop, provenancecatholic.com, pax-market.com) |
| 7.2 | 2h | SEO basics — title tags, meta descriptions, structured data (Product schema), sitemap |
| 7.3 | 2h | Brand name decision + logo (simple: wordmark in Cormorant Garamond, gold on parchment) |
| 7.4 | 1h | OG images — each product page generates shareable card (product image + location + "Blessed at...") |

**Deliverable:** A real domain, findable on Google, shareable on social.

---

### STREAM 8 — LIVING PRODUCTS (innovation)
**Owner:** TBD · **Est:** 2 days

Candles, oils, holy water — consumables with spiritual tracking. The most novel product concept.

| Task | Est | Description |
|------|-----|-------------|
| 8.1 | 2h | Intention-setting flow — when buying a candle: "Who or what are you lighting this for?" (private) |
| 8.2 | 2h | Burn journal — optional user diary tied to candle lifecycle |
| 8.3 | 1h | Refill prompts — intelligent timing based on average burn rate |
| 8.4 | 1h | Holy water usage suggestions — "Bless your door: trace a cross, pray the Magnificat" |

**Deliverable:** Consumable products with spiritual tracking that durable goods can't offer.

---

### STREAM 9 — INFRASTRUCTURE & QA
**Owner:** TBD · **Est:** 1 day

Foundation hardening before traffic.

| Task | Est | Description |
|------|-----|-------------|
| 9.1 | 1h | Error pages — styled 404/500 in Scriptorium aesthetic |
| 9.2 | 1h | API rate limiting — protect catalog endpoints |
| 9.3 | 1h | Backup — products.json, shops.json, orders daily |
| 9.4 | 1h | Monitoring — health check endpoint, PM2 memory alert |

---

## Priority Matrix

```
                    HIGH IMPACT          MEDIUM IMPACT         LOW IMPACT
                    ───────────          ─────────────         ──────────
HIGH URGENCY    │ STREAM 1 (pages)    STREAM 3 (checkout)   STREAM 9 (infra)
                │ STREAM 2 (discovery)                       

MED URGENCY     │ STREAM 5 (chat)     STREAM 7 (domain)     STREAM 6 (email)
                │ STREAM 4 (shops)    STREAM 8 (living)     

LOW URGENCY     │                     (none)                (none)
```

## Recommended Execution Order

### Phase A — THIS WEEK (Marketplace feels real)
1. **Stream 1** — 5 more hero Codex pages + data-driven template
2. **Stream 2** — Browse by Sacrament page
3. **Stream 3** — End-to-end checkout test + confirmation

### Phase B — NEXT WEEK (Growth mechanics)
4. **Stream 7** — Domain + brand + SEO
5. **Stream 5** — Conversational shopping chat (CS-029)
6. **Stream 4** — Shop intake flow (so real shops can join)

### Phase C — WEEK 3+ (Retention + innovation)
7. **Stream 6** — Email rhythms
8. **Stream 8** — Living products (candles, oil lifecycle)

### Ongoing
9. **Stream 9** — Infrastructure hardening (do piecemeal)

---

## Sub-Agent Allocation (proposed)

| Agent | Strengths | Suggested Streams |
|-------|-----------|-------------------|
| **Mr Chow** (Azure) | Full-stack, infra, deployment, fast iteration | Stream 1, 3, 7, 9 |
| **Hector** (Dell) | Heavy compute, separate context, LLM work | Stream 2 (sacrament AI), Stream 5 (chat), Stream 6 (email content) |
| **Adam** | Decisions, taste, domain knowledge, shop relationships | Brand name, outreach templates (4.4), product data review, taste approval on Codex pages |

---

## Immediate Decision Points

1. **Brand name** — What is this marketplace called? "Catholic Market" is placeholder. Options: Sanctorum, Pax Market, Provenance Catholic, The Pilgrim's Shelf, Sacristy, Holy Ground Market...
2. **Domain** — Buy now or wait for brand decision?
3. **First real shop** — Which destination should we actually attempt to onboard first? Jerusalem (English-speaking Christians), Lourdes (established sanctuary shops), or Fátima (accessible)?
4. **Hector involvement** — Do we want Hector on the Dell building the chat AI or sacrament features in parallel, or keep it all on Chow for now?
