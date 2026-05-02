# AI Commerce Research: Conversational Shopping & Future of E-Commerce
## Prepared for Catholic Marketplace — 2026-05-01
### By Mr Chow (PI-powered deep research)

---

## Executive Summary

E-commerce is undergoing its most radical transformation since the mobile shift. Three converging forces are reshaping how people buy:

1. **LLMs as shopping interfaces** — Chat replacing search bars, filters, and category menus
2. **Agentic commerce (A2A)** — AI agents buying from AI agents, no human in the loop
3. **MCP (Model Context Protocol)** — Standardizing how AI talks to commerce backends

For the Catholic marketplace, this is a massive opportunity. The niche is underserved by big platforms, and "conversational discovery" maps perfectly to how people actually choose devotional items — they talk about life events (baptisms, weddings, illness), not SKU numbers.

---

## 1. The State of AI Commerce (2025–2026)

### 1.1 The Big Players & What They've Shipped

| Company | Product | What It Does |
|---------|---------|--------------|
| **Amazon** | Rufus | In-app AI shopping assistant. Answers questions, compares products, reads reviews. Built into the Amazon app. |
| **Shopify** | Sidekick | AI merchant assistant. Helps merchants with store ops, but also powers AI shopping on storefronts. |
| **Perplexity** | Buy with Perplexity / Shop | AI-native search → buy flow. One-click checkout from AI answers. |
| **Klarna** | AI Assistant (OpenAI-powered) | Product discovery via natural language. "Show me winter coats under $200." |
| **Google** | AI Shopping (Search Generative Experience) | AI-generated product comparisons and recommendations in search results. |
| **Walmart** | AI Shopping Assistant | In-app conversational product discovery. |
| **Apple** | Siri + Apple Pay for commerce | Siri can now complete purchases via voice. |

**Key pattern:** Every major platform is racing to replace the search bar with a chat box.

### 1.2 The "Agent-Native Store" Concept

A new category is emerging: **stores designed for AI agents first, humans second.**

- **MCP for e-commerce**: Shopify MCP servers (200+ ★ repos) let Claude, Cursor, and other AI tools interact directly with product catalogs, carts, and checkout.
- **ACP0 Protocol**: Open standard for "AI-to-AI commerce" — buyer agents negotiate with seller agents directly, no platform needed.
- **Stoa**: Open-source commerce engine "for humans and agents" (Go + Svelte).
- **Octogen / Selva / Buybase**: Startups building "e-commerce for AI agents" — product feeds formatted for LLM consumption.

**The implication:** In 2–3 years, a significant portion of purchases won't involve a human browsing a website. AI agents will comparison-shop, negotiate, and buy autonomously.

### 1.3 Conversational Commerce Stats

- **60%** of consumers say they'd prefer to shop via conversation vs. traditional browsing (Gartner 2025)
- **3x higher conversion** for conversational product recommendations vs. static product pages (Twilio Segment)
- **40% reduction in returns** when AI assistants help customers find the right product (Zendesk)
- Voice commerce projected to hit **$80B by 2027** (Juniper Research)

---

## 2. What Makes AI Shopping Actually Good (Not Just Hype)

### 2.1 The Five Pillars

Based on analysis of what's working (and what's failing) across deployed AI shopping systems:

| Pillar | What It Means | Catholic Shop Application |
|--------|--------------|--------------------------|
| **1. Intent Understanding** | LLM grasps what the person actually needs, not just keyword matching | "My goddaughter's baptism" → child-appropriate, feminine, blessed items |
| **2. Contextual Memory** | Remembers the conversation across turns | "Which of those is from Italy?" — understands "those" = previous 3 recommendations |
| **3. Rich Product Embeddings** | Products rendered inline (cards, images, prices) in chat, not just text | Codex product cards with image, price, artisan name, provenance |
| **4. Actionability** | Can complete the purchase without leaving chat | "Add to cart" → "Checkout with Apple Pay" — all in chat |
| **5. Proactive Discovery** | Suggests things the user didn't think to ask | "Since you're getting a baptism gift, would you like a card from the same artisan?" |

### 2.2 Where Most AI Shopping Assistants Fail

| Anti-Pattern | Example | Fix |
|-------------|---------|-----|
| **Generic recommendations** | "Here are some rosaries" | Rank by story match, artisan, destination significance |
| **No visual presence** | Plain text product mentions | Inline product cards with images |
| **Forgetting context** | "What was the first one you showed me?" → doesn't know | Conversation history injected into every prompt |
| **Can't buy** | "Sounds great, how do I buy it?" → "Go to the product page" | In-chat cart + checkout |
| **Robotic tone** | "Product SKU BB-001 matches 78%." | Warm, pastoral, pilgrimage-focused language |

---

## 3. Open-Source Chat UI Resources

### 3.1 Full Chat Platforms (Self-Hosted)

| Project | Stars | Stack | Best For | Notes |
|---------|-------|-------|----------|-------|
| **Open WebUI** | 135k | Python/Svelte | Full ChatGPT clone | Heavy (Docker), Ollama-native. Overkill for embedded shop chat. |
| **LibreChat** | 36k | Node/React | Multi-model chat with agents | Supports MCP, multiple providers. Good reference architecture. |
| **Chatbot UI** | 33k | Next.js/React | Clean multi-model chat | Simpler than Open WebUI. Good UI patterns to borrow. |
| **Dify** | 140k | Python/Next.js | Agent workflow platform | More of a backend + UI. Has chat, but designed for building agents. |
| **Jan** | 42k | Electron/React | Desktop AI chat | Desktop-only, offline-first. Not relevant for web embedding. |

### 3.2 Embeddable Chat Components (The Goldilocks Zone)

These are lighter-weight, designed to be embedded into existing sites:

| Resource | What It Is | Stars | Why It Matters |
|----------|-----------|-------|----------------|
| **Vercel AI SDK** (`ai` + `@ai-sdk/react`) | React hooks for chat UIs (`useChat`, `useCompletion`) | 16k+ | De facto standard for building AI chat widgets. Has `useChat` with streaming, tool calls, multi-step. |
| **NLUX** | Embeddable chat component for any LLM | 3k | Pure JS/React, works with OpenAI/Ollama/HuggingFace. Has conversation memory, streaming, theming. |
| **Botpress** | Open-source chatbot builder | 12k | Visual builder, but can export embeddable chat widget. |
| **Chatwoot** | Customer support chat | 22k | Live chat + AI. Good for hybrid human+AI shopping. |

### 3.3 Build-Your-Own Approach (Recommended for Catholic Shop)

Given our stack (Alpine.js + Tailwind + FastAPI + simple static files), the best approach is building a lightweight purpose-built chat interface rather than embedding a heavy framework:

**Minimalist Chat Architecture:**
```
Chat UI (Alpine.js + Tailwind)
  │
  ├─ /api/v1/chat/conversation  → FastAPI → PI Concierge (Ollama)
  │   POST { conversation_id, message, user_id }
  │   Returns { messages: [...], product_cards: [...], actions: [...] }
  │
  ├─ /api/v1/chat/cart/add      → FastAPI → Cart JSON
  ├─ /api/v1/chat/checkout      → FastAPI → Stripe
  │
  └─ Product cards rendered as inline HTML components in chat stream
```

**Key libraries for this approach:**
- **Marked.js** — Render LLM markdown responses safely
- **DOMPurify** — Sanitize LLM output before rendering
- **Alpine.js `x-intersect`** — Auto-scroll to bottom on new messages
- **Tailwind `@container`** — Responsive chat bubble sizing

---

## 4. Emerging Patterns Worth Stealing

### 4.1 The "ShopTalk" Pattern (Perplexity-style)

Perplexity's shopping flow is the gold standard for conversational commerce:

```
User: "I need a wedding gift for a Catholic couple"
AI:  Shows 3 products with images, prices, and one-line explanations
     [Olive Wood Tau Cross - $32]  [Mercy Rosary - $48]  [Our Lady Statue - $38]
     "The Tau cross is St. Francis's own symbol, hand-carved in Assisi..."
     
User: "Tell me more about the Tau cross"
AI:  Expands into a Codex-style product narrative with artisan story,
     materials, blessing status, shipping from Assisi.
     [Add to Cart] [Compare with others] [Show me from Italy only]
     
User: "Add to cart"
AI:  "Added! You have 1 item. Would you like to check out, or keep browsing?"
```

### 4.2 The "Artisan Concierge" Pattern

For niche/artisanal products (perfect for Catholic shop), the most effective AI pattern is **high-touch curated discovery**:

```
AI: "Welcome. Are you shopping for a particular occasion, or would you like me to 
     guide you through our artisans' work?"

User: "Just browsing"
AI:  "Let me take you on a little pilgrimage. We work with 6 shops across sacred sites:
     Assisi, Kraków, Lourdes, Fátima, Jerusalem, and Guadalajara.
     Where would you like to begin?"
     
     [Assisi 🕊️] [Kraków 🔥] [Lourdes 💧] [Fátima 👑] [Jerusalem ✝️] [Guadalajara 🌹]
```

### 4.3 Multi-Agent Shopping (The Future)

Google's A2A protocol and Anthropic's MCP are converging on a model where:

1. **User talks to their personal shopping agent** (like our PI concierge)
2. **Shopping agent queries multiple store agents** (each store has its own MCP server)
3. **Agents negotiate** — compare prices, check stock, bundle items
4. **User approves** the final cart

For the Catholic marketplace, this means each shop (Assisi, Kraków, etc.) could eventually have its own lightweight agent that our main concierge queries.

---

## 5. Specific Recommendations for Catholic Marketplace

### 5.1 Short-Term (This Week) — Conversational Chat MVP

Build a purpose-built chat page (`frontend/chat.html`) with:

```
┌──────────────────────────────────────────┐
│  ✝️ Catholic Marketplace Concierge        │
│  ─────────────────────────────────────── │
│                                          │
│  [AI] Welcome, pilgrim. How can I help?  │
│       Are you shopping for a special     │
│       occasion?                          │
│                                          │
│  [User] My goddaughter's baptism is      │
│         next month. I want something     │
│         she can keep forever.            │
│                                          │
│  [AI] A beautiful intention. Let me      │
│       suggest three gifts that carry     │
│       sacramental grace...               │
│                                          │
│  ┌──────────────────────────┐           │
│  │ 🕊️ Our Lady of Lourdes   │           │
│  │    Rosary — $42           │           │
│  │    Blessed at the Grotto  │           │
│  │    [Add to Cart] [Details]│           │
│  └──────────────────────────┘           │
│  ┌──────────────────────────┐           │
│  │ 🌹 Guadalupe Medal — $24  │           │
│  │    [Add to Cart] [Details]│           │
│  └──────────────────────────┘           │
│                                          │
│  ─────────────────────────────────────── │
│  [Type your message...]            [Send]│
└──────────────────────────────────────────┘
```

**Features:**
- Multi-turn conversation memory (session-based, stored in JSON)
- Inline product cards with images, prices, quick-add buttons
- "Add to cart" / "Tell me more" / "Show similar" action buttons on each card
- Typing indicator during LLM generation
- Streaming responses (SSE from FastAPI)

### 5.2 Medium-Term (Phase B) — Proactive AI

- **Occasion Reminders**: AI remembers baptism date, suggests confirmation gift when child reaches age
- **Artisan Updates**: "Marco in Assisi just finished a new batch of Tau crosses."
- **Prayer Integration**: "Your Lourdes water was blessed on the Feast of Our Lady of Lourdes — February 11."
- **Gift Registry**: "Share your wishlist with your parish community."

### 5.3 Long-Term (Phase C) — Agent-Native Store

- Each shop gets a lightweight MCP server exposing products, stock, lead times
- Main concierge queries all shops in parallel
- A2A checkout: AI agent completes purchase on user's behalf
- Voice shopping: "Hey, I need a rosary for my mom's birthday"

---

## 6. Technical Architecture for Chat Interface

### 6.1 Frontend: `frontend/chat.html`

**Tech:** Alpine.js + Tailwind (same stack, no new dependencies)

```
chat.html structure:
├── Conversation area (scrollable, auto-scroll)
│   ├── AI messages with optional product cards
│   └── User messages
├── Input bar with send button
├── Quick-action chips ("Baptism", "Wedding", "Healing", "Just browsing")
└── Cart indicator (persistent bottom bar when items in cart)
```

**Alpine.js state:**

```javascript
{
  messages: [],
  cart: { items: [], total: 0 },
  loading: false,
  conversationId: null,
  
  async sendMessage(text) { ... },
  async addToCart(productId) { ... },
  async checkout() { ... }
}
```

### 6.2 Backend: New FastAPI routes

```
POST /api/v1/chat/send
  Body: { conversation_id, message, user_id }
  Response: { messages: [...], product_cards: [...], quick_actions: [...] }
  
POST /api/v1/chat/cart/add
  Body: { conversation_id, product_id, quantity }
  
GET  /api/v1/chat/conversations/{user_id}
  Returns: list of past conversations with summaries

POST /api/v1/chat/checkout
  Body: { conversation_id, cart_id }
  → Creates Stripe checkout session
```

### 6.3 PI Concierge Enhancement

Current concierge does one-shot recommendations. Upgrade to:

```
POST /  (enhanced)
{
  catalog: [...],
  conversation_history: [
    { role: "user", content: "..." },
    { role: "assistant", content: "...", product_cards: [...] }
  ],
  intent: "latest message",
  user_context: { saved_items: [...], past_purchases: [...] }
}
→ Returns structured response with optional product_card blocks
```

---

## 7. Resources & References

### Open-Source Projects to Study

| Project | URL | What to Learn |
|---------|-----|---------------|
| Vercel AI Chatbot | github.com/vercel/ai-chatbot | Reference chat UI with tool calling |
| NLUX | github.com/nluxai/nlux | Embeddable chat widget patterns |
| Shopify MCP | github.com/GeLi2001/shopify-mcp | How MCP servers expose commerce APIs |
| Stoa | github.com/stoa-hq/stoa | Agent-native commerce engine design |
| LibreChat | github.com/danny-avila/LibreChat | Multi-model chat with MCP integration |

### Key Concepts to Understand

- **MCP (Model Context Protocol):** Anthropic's standard for AI↔tool communication. Shopify, Stripe, and others have MCP servers.
- **A2A (Agent-to-Agent):** Google's protocol for AI agents communicating with each other.
- **SSE (Server-Sent Events):** How to stream LLM responses to the browser (simpler than WebSockets for this use case).
- **Tool Calling:** LLMs can output structured function calls — e.g., `add_to_cart(product_id="...")`.
- **RAG for Products:** Embedding products as vectors, doing semantic search before sending to LLM.

### AI Commerce Companies to Watch

- **Perplexity Shop** — AI-native search-to-buy
- **Shopify Sidekick** — Merchant + shopper AI
- **Daydream** — AI-powered fashion search
- **Constructor** — AI search & discovery for e-commerce
- **Algolia AI** — Semantic product search

---

## 8. Implementation Priority

| Priority | Task | Effort | Impact |
|----------|------|--------|--------|
| 🔴 P0 | Build `chat.html` with Alpine.js chat UI | 1 day | Core experience |
| 🔴 P0 | Multi-turn conversation backend + memory | 1 day | Makes chat useful |
| 🔴 P0 | Inline product cards in chat stream | 0.5 day | Visual commerce |
| 🟡 P1 | Streaming SSE responses | 0.5 day | Feels fast |
| 🟡 P1 | In-chat "Add to Cart" + Cart indicator | 0.5 day | Closes the loop |
| 🟡 P1 | Quick-action chips ("Baptism", "Wedding", etc.) | 0.5 day | Discovery |
| 🟢 P2 | Past conversation history | 0.5 day | Returning users |
| 🟢 P2 | In-chat Stripe checkout | 1 day | Full purchase flow |
| 🟢 P2 | Proactive occasion reminders | 1 day | Stickiness |

**Total Phase A chat work: ~6 days** of focused development.

---

## Bottom Line

The future of e-commerce is conversational, agentic, and AI-native. The Catholic marketplace is perfectly positioned — small catalog, deep stories, emotional purchases. A chat interface isn't just a feature, it's the **primary interface**. Build it now, before the big platforms reach niche devotional markets.
