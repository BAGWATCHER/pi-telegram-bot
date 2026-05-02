# Catholic Marketplace — UI Framework & Storefront Research
**Date:** 2026-05-01 | **Context:** Evaluating open-source frameworks to clone/modify for the Catholic shop

---

## Current State
- Vanilla HTML/JS (`frontend/index.html` + `ops.html`)
- FastAPI backend on port 8110
- JSON flat-file data
- 390px mobile-first approach
- No build step, no framework

---

## OPTION A: Alpine.js + Tailwind CSS (⭐ RECOMMENDED)

### What it is
Alpine.js = tiny (~15KB) reactive framework. Add `x-data`, `x-show`, `x-bind` directly in HTML. Think jQuery-level simplicity with Vue-like reactivity. Tailwind = utility CSS.

### Why it fits perfectly
| Factor | Assessment |
|--------|------------|
| Fits current stack | ✅ **Zero migration.** Drop Alpine.js into existing HTML, keep FastAPI, keep JSON |
| Mobile-first | ✅ Tailwind responsive utilities are best-in-class for 390px |
| Learning curve | ✅ Minimal — 14 directives, can learn in an afternoon |
| Bundle size | ✅ ~15KB — faster than any React/Vue/Next.js site |
| Provenance cards | ✅ Easy: `x-data="{provenance: {source:'...', maker:'...'}}"` directly on cards |
| Destination browse | ✅ Alpine handles tabs/filters/maps without page reload |
| Cart | ✅ Alpine Persist plugin for localStorage carts, sync to API |
| SEO | ⚠️ Client-rendered. But FastAPI can serve pre-rendered pages for crawlers |
| Dark factory fit | ✅ A single agent can modify HTML in one file without build chain |

### Example migration path
```
Current:  <button onclick="addToCart('xyz')">
Alpine:   <button @click="addToCart('xyz')" x-show="!inCart('xyz')">
```

### Open-source storefronts to clone
- **Tailwind UI Ecommerce** (paid, $299) — premium components, not open source
- **Laravel's free Tailwind components** — https://tailwindcomponents.com — free community components
- **Alpine.js examples** — https://alpinejs.dev/start-here

### Verdict
Best option for v1. Keep everything, add reactivity, look pro, move fast. No rebuild required.

---

## OPTION B: shadcn/ui + Next.js (🥈 RUNNER-UP)

### What it is
shadcn/ui = copy-paste React components (not a dependency). Beautiful, accessible, customizable. Paired with Next.js for SSR/routing. 113K GitHub stars.

### Why it's excellent (but heavier lift)

| Factor | Assessment |
|--------|------------|
| UX quality | ✅ **Gorgeous.** Cards, dialogs, sheets, tabs — all beautiful out of the box |
| Mobile-first | ✅ Components are responsive by default |
| Cart/checkout | ✅ Server actions, React state — smooth flows |
| Product pages | ✅ Cards with image, badges, quick view — all built-in patterns |
| Customization | ✅ You own the code (it copies into your repo, not a dependency) |
| Migration cost | ❌ Full rewrite. FastAPI → Next.js API routes or keep FastAPI as backend API |
| Build step | ❌ Requires Node toolchain, build step |
| Learning curve | ❌ Moderate — React + Next.js + Tailwind knowledge needed |

### Open-source storefronts to clone
- **Next.js Commerce** (Vercel) — 14K stars, clean headless storefront. Cloneable starting point
- **Medusa Next.js Starter** — Full Medusa + Next.js storefront, open source
- **shadcn/ui blocks** — https://ui.shadcn.com/blocks — ready-made page sections (hero, features, pricing)

### Verdict
Best if you want production polish fast and are willing to migrate to Next.js. The shadcn blocks alone would give you 80% of the storefront for free.

---

## OPTION C: HTMX (🥉 LIGHTWEIGHT ALTERNATIVE)

### What it is
Hypermedia-driven: any HTML element can trigger an AJAX request, and the server returns HTML fragments. 47K GitHub stars. Works beautifully with server-rendered apps (FastAPI + Jinja2).

### Why it's interesting

| Factor | Assessment |
|--------|------------|
| Philosophy match | ✅ Matches your existing server-rendered approach |
| No JS framework | ✅ Just HTML attributes: `hx-get`, `hx-post`, `hx-swap` |
| Works with FastAPI | ✅ FastAPI + Jinja2 templates returning HTML fragments |
| Bundle size | ✅ ~14KB |
| Mobile | ✅ Works fine, but no built-in mobile animations/transitions |
| Cart | ✅ Server-side cart, HTMX swaps cart fragment |
| SEO | ✅ Server-rendered by default |
| UI polish | ⚠️ No animations, transitions. Feels "web 1.0" without extra effort |

### Verdict
Philosophically aligned (server-rendered, lightweight) but UI won't feel as polished as Alpine+Tailwind or shadcn.

---

## OPTION D: Medusa.js (🏗️ OVERKILL FOR NOW)

### What it is
Full open-source headless commerce platform. 32K stars. Backend in Node.js, storefront in Next.js. Order management, multi-region, product management, cart, checkout, plugins.

| Factor | Assessment |
|--------|------------|
| Complete | ✅ Everything you need — products, orders, carts, regions, payments, shipping |
| API | ✅ REST + JS client, could call from any frontend |
| Plugins | ✅ Stripe, PayPal, SendGrid, MeiliSearch |
| Migration cost | ❌ Replaces FastAPI entirely with Node.js backend |
| Hosting | ❌ Needs Postgres + Redis, heavier infra |
| Overkill | ❌ Built for multi-tenant, multi-region, multi-currency ops |

### Verdict
Great if you're building Amazon for Catholic goods. Wrong for v1. Revisit at 1,000+ orders/day.

---

## OPTION E: Saleor (🐍 PYTHON BUT HEAVY)

### What it is
Django + GraphQL commerce backend. 22K stars. Python-native (good for you), but Django monolith. React storefront separate.

| Factor | Assessment |
|--------|------------|
| Python | ✅ Python! But Django, not FastAPI |
| Heavy | ❌ Django ORM, Postgres, Redis, Celery, GraphQL |
| Storefront | ✅ Saleor React Storefront — nice PWA, cloneable |
| Overkill | ❌ More infrastructure than Medusa |

### Verdict
If you're going to go heavy, Medusa is more modern. Saleor is for Django shops.

---

## COMPARISON MATRIX

| | Alpine+Tailwind | shadcn/Next.js | HTMX | Medusa | Saleor |
|---|---|---|---|---|---|
| **Migration effort** | ⭐ Minimal | ⭐⭐⭐ Medium | ⭐ Minimal | ⭐⭐⭐⭐ High | ⭐⭐⭐⭐ High |
| **Mobile UX quality** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Provenance cards** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Keeps FastAPI** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No | ❌ Kinda |
| **Bundle/performance** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Cloneable storefront** | ❌ | ✅ Yes | ❌ | ✅ Yes | ✅ Yes |
| **Learning curve** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐ |
| **Dark-factory friendly** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ |

---

## RECOMMENDATION

### Go Alpine.js + Tailwind for v1, plan Next.js + shadcn for v2.

**Why:**
1. **Zero migration.** Your existing `index.html` gets Alpine directives added. Backend stays untouched.
2. **This week.** You can have destination cards, provenance badges, gift finder wizard, cart drawer all working in days.
3. **Feels pro.** Tailwind makes it look like a $50K design. Alpine adds app-like interactivity.
4. **Dark factory loves it.** Single HTML file, no build step, agents can modify without toolchain hell.
5. **V2 upgrade path clear.** When you hit 500+ products and need SSR/SEO, migrate to Next.js + shadcn using the same Tailwind styles.

### What to clone/modify:
- **Tailwind component gallery** for cards, modals, tabs, drawers — grab and customize
- **Alpine.js cart example** for the cart drawer + checkout flow
- Can pull inspiration from shadcn/ui blocks layout patterns (even though you won't use React)

---

## BONUS: Specific UI Patterns Worth Stealing

| Pattern | Steal From | Why |
|---|---|---|
| Destination cards (horizontal scroll) | Airbnb mobile app | Location-first browsing is their core |
| Product provenance badge | Etsy "Star Seller" / "handmade" badges | Trust signals on cards |
| Gift finder wizard | Uncommon Goods / The Grommet | Occasion→recipient→budget flow |
| Monastery/shop profile | Airbnb host profiles | Shop = host, each has story + location |
| Cart slide-over | shadcn/ui Sheet component | Slide from bottom on mobile, from right on desktop |
| "Blessed at" stamp | Certificate/authenticity patterns | Visual provenance marker |

---

## QUICK START: Alpine + Tailwind in 5 minutes

```html
<!-- Add to existing index.html -->
<script src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
<link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">

<!-- Destination card with Alpine -->
<div x-data="{ open: false }" class="rounded-2xl shadow-md overflow-hidden">
  <img src="/img/lourdes-hero.jpg" alt="Lourdes" class="w-full h-48 object-cover">
  <div class="p-4">
    <span class="text-xs font-bold text-blue-600 bg-blue-100 px-2 py-1 rounded-full">🇫🇷 France</span>
    <h3 class="text-lg font-bold mt-2">Lourdes</h3>
    <p class="text-gray-600 text-sm">8 shops · 47 items</p>
    <button @click="open = !open" 
            class="mt-3 w-full bg-amber-600 text-white py-2 rounded-xl font-medium">
      Browse Items →
    </button>
    <div x-show="open" class="mt-3 border-t pt-3">
      <!-- Lourdes products loaded here -->
      <p class="text-sm">Loading Lourdes items...</p>
    </div>
  </div>
</div>
```
