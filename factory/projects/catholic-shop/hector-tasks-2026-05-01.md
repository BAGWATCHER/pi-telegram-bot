# Hector Task Queue — Catholic Marketplace
Assigned: 2026-05-01 20:15 UTC
Priority: Phase A
Status: PENDING

## Task 1: Browse by Sacrament Page (STREAM 2)
**Est:** 3h · **File:** Create `factory/projects/catholic-shop/frontend/sacraments.html`

### What to build
A standalone page at `/sacraments` that lets users browse products by life moment instead of by destination.

### Design
- Same Scriptorium aesthetic as the main marketplace (Cormorant Garamond, parchment/ink/gold/rubrication, noise grain)
- Mobile-first
- Copy the `<head>` section from the main `frontend/index.html` for Tailwind + Alpine config + Google Fonts

### Life moments (6 categories):

| Category | Icon | Products to show |
|----------|------|------------------|
| **Baptism** | 🕊️ | Lourdes water, Jerusalem cross, Assisi tau cross, Fátima statue |
| **First Communion** | 🕯️ | Kraków Divine Mercy icon, Guadalupe medal, Lourdes rosary |
| **Confirmation** | 🔥 | Jerusalem cross, Assisi San Damiano crucifix, Fátima medal |
| **Wedding** | 💍 | Kraków Madonna icon, Guadalupe rosary, Lourdes miraculous medal |
| **Healing / Sick** | 🕯️ | Lourdes water, Jerusalem anointing oil, Assisi St. Francis candle |
| **Home Blessing** | 🏠 | Jerusalem cross, Lourdes water, Fátima statue |

### UX
- Each category is a card with the icon, name, and 1-line description
- Tapping a card shows products for that sacrament in a grid (same card style as index.html)
- Product cards link to `/product/{product_id}` (the Codex page)
- Back button returns to sacrament selection

### Data source
Fetch from the API: `GET /api/v1/catalog/feed` — products have `sacrament_tags` array. Filter client-side by tag match.
Or if the API doesn't support filtering, fetch all and filter in Alpine.

Sacrament tags used in our data:
- baptism, first_communion, confirmation, wedding, anointing, home_blessing, devotion, protection, healing

---

## Task 2: Sacrament-Aware AI Concierge (STREAM 2)
**Est:** 2h · **Modify:** `backend/api/app.py` (the AI route)

### Current state
The AI concierge at `/api/v1/ai/recommend` is generic — it doesn't know about sacraments.

### What to add
When a user message mentions a life event ("I need a baptism gift"), the AI's system prompt should:
1. Detect the sacrament context from the user's message
2. Filter/prioritize products with matching `sacrament_tags`
3. Present those products first in the response
4. Explain WHY each product is appropriate for that sacrament

### System prompt enhancement
Add to the AI system prompt:
```
You are a Catholic gift concierge. When a customer mentions a specific life event or sacrament, prioritize products tagged for that event. Explain the spiritual connection between each recommended product and the sacrament. Be warm, reverent, and knowledgeable — like a sacristan helping a parishioner choose a gift.
```

---

## Product Reference (for both tasks)
The 6 destinations and their products:

1. **Assisi, Italy** — Tau Olive Cross ($28), San Damiano Crucifix ($42), St. Francis Peace Candle ($18)
2. **Kraków, Poland** — Divine Mercy Rosary ($39), Our Lady Desk Icon ($89), Divine Mercy Print ($22)
3. **Guadalajara, Mexico** — Brown Scapular ($14), Patron Saint Prayer Cards ($18), Our Lady of Guadalupe Medal ($32)
4. **Lourdes, France** — Holy Water Bottle ($16), Miraculous Medal ($28), Blue Rosary ($34)
5. **Fátima, Portugal** — Our Lady Statue ($58), Shepherd Children Medal ($22), Cork Oak Rosary ($26)
6. **Jerusalem, Israel** — Olive Wood Rosary ($48), Anointing Oil ($24), Jerusalem Cross ($36)

---

## How to submit work
- Write files to `/home/adam/hector-telegram-bot/factory/projects/catholic-shop/`
- Create the directory if it doesn't exist
- When done, post a summary to Adam in Telegram
- If blocked on anything, message Adam immediately
