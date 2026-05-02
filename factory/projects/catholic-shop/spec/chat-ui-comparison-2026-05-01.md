# Open-Source Chat UI Comparison — Catholic Marketplace
## Research for @hog_cranker — 2026-05-01
### Goal: Find an open-source chat UI we can clone and modify (not build from scratch)

---

## Winner: ollama-ui/ollama-ui 🏆

| Metric | Value |
|--------|-------|
| **Stars** | 1,125 |
| **License** | MIT ✅ |
| **Repo size** | 339 KB |
| **Stack** | Pure HTML + vanilla JS + Bootstrap CSS |
| **Build step** | None — edit files, refresh browser |
| **Dependencies** | Bootstrap, jQuery, Marked.js, DOMPurify (all CDN) |
| **GitHub** | https://github.com/ollama-ui/ollama-ui |

### File structure (14 source files):
```
index.html       — Main chat UI (Bootstrap layout)
chat.js          — All chat logic (~600 lines)
api.js           — Ollama API calls (getModels, postRequest, streaming)
chat.css         — Message bubbles, dark theme
background.js    — Chrome extension background
manifest.json    — Chrome extension manifest
build.sh         — Builds Chrome extension
```

### What it already does:
- ✅ Talks to Ollama via `/api/generate` with streaming
- ✅ Model selection dropdown (fetches from Ollama)
- ✅ System prompt support
- ✅ Chat history: save, load, delete conversations (localStorage)
- ✅ File upload (images + text files, base64-encoded)
- ✅ Markdown rendering (Marked.js + DOMPurify)
- ✅ Code blocks with syntax highlighting + copy button
- ✅ Dark theme (Bootstrap dark mode)
- ✅ Chrome extension support
- ✅ Mobile responsive

### What we'd modify:
1. **Replace API endpoint** — Point to our FastAPI `/api/v1/chat/send` instead of Ollama `/api/generate`
2. **Add product card rendering** — Detect when the response contains product data and render inline cards
3. **Add cart sidebar/indicator** — Shopping cart state + "Add to Cart" buttons
4. **Add quick-action chips** — [Baptism 🕊️] [Wedding 💍] etc.
5. **Restyle** — Scriptorium aesthetic (Cormorant Garamond, parchment colors, grain texture)
6. **Swap Bootstrap for Tailwind** (optional — can keep Bootstrap since it's already working)
7. **Add conversation ID** — Replace localStorage-based history with server-side sessions

### Why it's the clear winner:
- **339KB total** — you can read the entire codebase in 20 minutes
- **MIT license** — can commercialize freely
- **No npm install, no node_modules, no webpack/vite** — just edit and deploy
- **Already streams** — the hard part (SSE parsing) is done
- **Vanilla JS** — no React/Vue/Svelte learning curve for modifications
- **Bootstrap** — if we keep it, styling is already handled

---

## Runner-Up: ivanfioravanti/chatbot-ollama

| Metric | Value |
|--------|-------|
| **Stars** | 1,880 |
| **License** | NOASSERTION ⚠️ (unclear if commercial use OK) |
| **Repo size** | 743 KB |
| **Stack** | Next.js + TypeScript + React + Tailwind |
| **Build step** | `next build` required |

### Pros:
- More features: folders, prompts library, temperature control, i18n (20+ languages)
- Next.js/React — familiar stack for many devs
- Tailwind already integrated
- Docker + k8s deployment files

### Cons:
- **No clear license** — can't safely commercialize
- Next.js build step adds complexity
- Heavier: needs npm, node_modules, build pipeline
- Over-engineered for our needs (folders, prompts, temperature sliders = irrelevant)

---

## Also Evaluated

| Project | Stars | Size | License | Verdict |
|---------|-------|------|---------|---------|
| **mckaywrigley/chatbot-ui** | 33k | 3.6MB | MIT | Requires Supabase database — not self-contained |
| **open-webui/open-webui** | 135k | 363MB | None | Massive Docker monolith, 363MB — completely unmodifiable |
| **huggingface/chat-ui** | 10.6k | 11MB | Apache 2.0 | Production grade (HuggingChat), SvelteKit, heavy |
| **big-AGI** | 6.9k | 40MB | MIT | Full AI suite, 40MB — way more than chat |
| **xtekky/chatgpt-clone** | 3.5k | 174KB | GPL-3.0 | GPL-3.0 is restrictive. Also Python backend, not needed. |
| **WongSaang/chatgpt-ui** | 1.6k | 2.8MB | MIT | Vue + Docker, multi-user, database-dependent |
| **dkruyt/webollama** | 74 | 769KB | None | Flask + templates, chat is secondary feature |
| **Vercel AI Chatbot** | — | — | — | Reference/template, not a working app |

---

## Recommendation

**Clone `ollama-ui/ollama-ui` and modify it.**

Estimated effort:
| Task | Time |
|------|------|
| Clone + understand codebase | 30 min |
| Re-point API from Ollama to our FastAPI | 30 min |
| Add product card rendering in chat | 1 hr |
| Add cart state + "Add to Cart" buttons | 1 hr |
| Add quick-action chips | 30 min |
| Restyle to Scriptorium aesthetic | 1–2 hrs |
| Wire server-side conversation memory | 1 hr |
| **Total** | **~5–6 hours** |

Compare: building from scratch would be 2–3 days.
