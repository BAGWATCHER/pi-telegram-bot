# Catholic Shop Chat Architecture — Final Plan
## 2026-05-01 — Mr Chow

## Decision: Build with best primitives, don't clone a chat UI

After evaluating all major open-source chat UIs (Chatbot UI, LibreChat, Open WebUI, HuggingFace Chat UI, ChatGPT-Next-Web, big-AGI, chatbot-ollama, ollama-ui), none fit. They're either:
- Too coupled to their database (Chatbot UI = 33 Supabase files)
- Wrong database (LibreChat = MongoDB)
- Too massive to modify (Open WebUI = 363MB)
- Wrong license or unmaintained

## Stack Decision

| Layer | Choice | Why |
|-------|--------|-----|
| Chat engine | Vercel AI SDK (`useChat`) | Industry standard for streaming AI chat. Handles SSE, auto-scroll, loading, abort, retry. One hook = entire chat engine. |
| UI components | shadcn/ui + Radix | Same professional components Chatbot UI uses, but no database coupling. Accessible, keyboard-nav, dark mode, Tailwind-native. |
| Styling | Tailwind CSS | Already in use. Scriptorium theme applied via config. |
| State | React Context + Zustand | Cart, user preferences, UI state. |
| Frontend framework | React (Vite, not Next.js) | Lighter than Next.js for a single-page chat app. Vercel AI SDK works with both. |
| Backend | FastAPI (existing) | Already built. All routes, PI concierge integration, Stripe. |
| Database | SQLite → Postgres (SQLAlchemy) | Start SQLite, migrate when needed. Users, conversations, messages, carts, orders. |
| Auth | FastAPI JWT middleware | Simple, no third-party. |
| AI | PI Concierge → Ollama deepseek-v4-pro:cloud | Already working with multi-turn support planned. |

## Architecture

```
Frontend (React + Vite + shadcn/ui + Tailwind)
  chat.catholic.shop/
  ├── Chat page (primary shopping interface)
  │   ├── Message list (streaming via Vercel AI SDK)
  │   ├── Product cards (inline, with images/price/Add to Cart)
  │   ├── Quick-action chips (Baptism, Wedding, Healing, etc.)
  │   ├── Cart sidebar
  │   └── User profile / conversation history
  │
  └── Reuses Scriptorium design tokens from existing Alpine.js pages

Backend (FastAPI, existing)
  ├── POST /api/v1/chat/send          → Multi-turn chat with streaming
  ├── GET  /api/v1/chat/conversations → User's conversation list
  ├── GET  /api/v1/chat/conversation/{id} → Full conversation history
  ├── POST /api/v1/chat/cart/add      → Add to cart from chat
  ├── GET  /api/v1/chat/cart          → Current cart state
  ├── POST /api/v1/chat/checkout      → Create Stripe session
  ├── POST /api/v1/auth/login         → JWT auth
  ├── GET  /api/v1/auth/profile       → User profile + preferences
  └── All existing product/inventory routes

PI Concierge (Node.js, existing, port 8112)
  ├── Enhanced for multi-turn (conversation history in prompt)
  ├── Multi-agent: queries destination agents in parallel
  └── Returns structured JSON with product_card blocks

Existing Frontend (Alpine.js + Tailwind — UNCHANGED)
  ├── index.html       → Product browsing
  ├── product.html     → Codex product pages
  ├── sacraments.html  → Browse by Sacrament
  └── Links to chat for shopping experience
```

## What Makes This Novel

1. **Pilgrimage concierge persona** — AI interviews you, not the reverse. Draws out your story before showing products.
2. **Multi-agent orchestration** — Main concierge consults 6 destination agents (one per sacred site) in parallel.
3. **Memory across time** — Remembers your goddaughter's baptism date. Years later: "Sophia must be preparing for First Communion now..."
4. **Liturgical awareness** — Knows feast days, liturgical seasons. "The Feast of Our Lady of Lourdes is February 11th..."
5. **Generative artifacts** — Custom blessing certificates, personalized prayer cards, pilgrimage journals.
6. **Inline commerce** — Products render as beautiful cards in chat, not links. Add to cart, checkout without leaving conversation.

## Development Plan

| # | Task | Hours |
|---|------|-------|
| 1 | Scaffold React + Vite + shadcn/ui + Vercel AI SDK | 1 |
| 2 | Chat UI: streaming, markdown, code blocks, auto-scroll | 2 |
| 3 | Auth system: FastAPI JWT + login/signup UI | 2 |
| 4 | Conversations CRUD: FastAPI + SQLite via SQLAlchemy | 2 |
| 5 | Product card component: inline in chat with image/price/actions | 2 |
| 6 | Cart state management + Add to Cart flow | 2 |
| 7 | Quick-action chips + pilgrimage persona system prompt | 2 |
| 8 | Scriptorium theme: port design tokens to Tailwind config | 2 |
| 9 | Multi-agent orchestration: PI concierge → 6 destination agents | 3 |
| 10 | Stripe checkout from chat | 2 |
| **Total** | | **20 hours** |

## Key Endpoints (to build)

```
POST /api/v1/chat/send
  Body: { conversation_id, message, user_id }
  Streams: SSE with { type: "text" | "product_card" | "action", data: ... }

POST /api/v1/auth/register
  Body: { email, password, name }
  Returns: { access_token, user }

POST /api/v1/auth/login
  Body: { email, password }
  Returns: { access_token, user }

GET /api/v1/chat/conversations
  Header: Authorization: Bearer <token>
  Returns: [{ id, title, last_message, created_at, product_count }]

POST /api/v1/chat/cart/add
  Header: Authorization: Bearer <token>
  Body: { product_id, quantity, conversation_id }
  
POST /api/v1/chat/checkout
  Header: Authorization: Bearer <token>
  Body: { cart_id, conversation_id }
  Returns: { stripe_checkout_url }
```
