# DemandGrid / Chow — Craigslist research architecture notes

_Date: 2026-04-24_

## Executive summary

The best design is **not** "scrape Craigslist harder from the Azure VM."

The best design is:

1. **Craigslist as a signal source**
2. **Rules + heuristics to qualify posts**
3. **Search + Crawl4AI to resolve the real company and role context**
4. **Structured enrichment to find contact paths and pain hypotheses**
5. **Supervised Chow outreach from inside DemandGrid**
6. **Reply ingestion + learning loop**

This fits what is already true in the repo:
- Craigslist RSS/search fetches from Azure are brittle / currently blocked with `403`
- supervised manual import already works
- Chow can already send real supervised email
- the weak point is now **research, ranking, and enrichment quality**

## Bottom-line recommendation

### Use Craigslist for signal discovery, not as the only data source
Craigslist gives us:
- a fresh hiring signal
- role title / posting text
- some market context
- occasional email / phone hints

Craigslist does **not** reliably give us:
- a clean company identity
- a trustworthy buyer contact
- enough context for strong outreach

So the right pipeline is:

`Craigslist post -> qualify -> resolve company -> enrich site/contact/pain -> draft -> supervised send -> ingest replies`

### Use Crawl4AI for enrichment, not as the first answer to Craigslist anti-bot
Crawl4AI is well suited to:
- loading real company sites
- generating clean markdown
- selecting only relevant page regions
- extracting structured JSON with CSS/XPath
- using LLM extraction only when reasoning is actually needed
- adding browser/session/proxy controls when sites are dynamic or protected

It is **not** the best first move for:
- repeatedly scraping Craigslist directly from a cloud VM that already gets `403`

## What online research suggests

## 1) Crawl4AI is a strong fit for the enrichment layer

### Relevant findings
From the Crawl4AI README and docs:
- it is built to turn pages into **clean markdown** for agent/data pipelines
- it supports **schema-based extraction** without an LLM
- it supports **LLM extraction** when the page requires interpretation
- it supports **content selection** so we can focus on contact/about/service sections
- it supports **session management**, **stealth**, **undetected browser**, and **proxy rotation** for harder targets
- docs explicitly recommend **LLM-free extraction first** when pages are structured

### Why that matters for Chow
For company enrichment, most targets are small business sites with pages like:
- homepage
- about
- services
- contact
- careers

Those pages are usually much better Crawl4AI targets than Craigslist itself.

That means Chow can use Crawl4AI to extract:
- business name
- contact page URL
- phone numbers
- public emails
- service summary
- city/service area
- form availability
- likely workflow pain clues

## 2) Craigslist from Azure is still the brittle layer

### Current reality in our system
The current repo already documents:
- active policy: `manual_first`
- note: avoid direct HTML scraping
- Azure requests to Craigslist RSS/search are returning `403`

We also re-confirmed during this research that a direct request like:
- `https://boston.craigslist.org/search/jjj?query=bookkeeper&format=rss`

still returns `403` from this environment.

### Practical implication
Do **not** make Craigslist scraping the foundation of the system.

Instead:
- keep the current **manual-first / supervised** path as a stable fallback
- treat Craigslist access as a thin signal-adapter layer
- move most engineering effort into enrichment, ranking, and contact research

## 3) The best extraction pattern is hybrid: rules first, LLM second

### Best practice from Crawl4AI docs
The docs are clear:
- use **CSS/XPath / regex extraction** for repeatable structured fields
- use **LLM extraction** only when pages are unstructured or need semantic judgment

### Recommended split for Chow

#### Use rules / selectors for:
- phones
- emails
- contact links
- address / service area
- social/profile links
- schema.org / JSON-LD metadata
- title / H1 / page labels

#### Use LLM reasoning for:
- likely business type
- likely owner/operator workflow pain
- likely first automation win
- whether a page looks like a fit for outreach
- how to summarize the role/company in a sentence or two

This will keep the pipeline cheaper, faster, and more stable.

## 4) Open-source components worth borrowing from

## A. Crawl4AI
**Use for:** browser-based crawl + markdown + structured extraction + optional LLM interpretation

Why it fits:
- markdown generation
- target element selection
- JSON extraction strategies
- anti-bot fallback options if needed for non-Craigslist targets

## B. Trafilatura
**Use for:** cleanup / text extraction from company pages when we only need the main readable content

Why it fits:
- designed to gather text from the web and reduce boilerplate noise
- good for main text, metadata, comments, feeds, and crawl/discovery workflows

Best use here:
- fallback text extractor for company pages
- compare against Crawl4AI markdown quality on SMB sites

## C. Extruct
**Use for:** extracting embedded metadata from HTML

Why it fits:
- supports JSON-LD, microdata, Open Graph, RDFa, microformats, Dublin Core

Best use here:
- pull `Organization`, `LocalBusiness`, address, logo, sameAs, phone, contact metadata
- use as a cheap metadata step before any LLM reasoning

## D. Crawlee
**Use for:** large-scale crawl orchestration, retries, sessions, proxies, queue management

Why it fits:
- strong browser automation / anti-bot ecosystem
- useful if this lane becomes more volume-heavy later

Best use here:
- only if Chow outgrows a lighter Crawl4AI-first setup
- not necessary for initial NH/New England pilot

## E. SearXNG / DDGS
**Use for:** company resolution search step

Why it fits:
- we need a way to go from a fuzzy Craigslist company hint to the real homepage
- metasearch is often enough for low-volume supervised research

Best use here:
- query like `"{company}" {city} official site`
- then crawl top candidate pages and score the best match

## F. JobSpy
**Use for:** future diversification beyond Craigslist

Why it fits:
- open-source job aggregation from multiple boards
- supports proxies and multi-source job collection

Best use here:
- later, if we expand beyond Craigslist into Indeed / LinkedIn / Google / ZipRecruiter
- not the core answer for the current CL pilot

## Recommended system design

## Stage 1 — signal ingest
**Goal:** get raw opportunities into a stable store.

Inputs:
- Craigslist manual import
- Craigslist RSS when reachable
- later: JobSpy-powered non-Craigslist boards

Stored fields:
- opportunity_id
- source
- market_id
- title
- posting_url
- posting_description
- company_name_guess
- role_family
- automation_hypotheses
- contact_hint_emails
- contact_hint_phones
- fetched_at

### Recommendation
Keep the current manual-first path.
Add more NH / New England markets, but do **not** block on perfect Craigslist automation.

## Stage 2 — qualification / scoring
**Goal:** decide what is worth research time.

Score dimensions:
- role fit
- operational pain clarity
- SMB fit
- likely buyer proximity
- contactability potential
- posting freshness
- geographic relevance

### Recommendation
Use deterministic scoring first.
Reserve LLM scoring for tie-breaks or nuanced summaries.

## Stage 3 — company resolution
**Goal:** turn a vague company hint into the right business website.

Suggested process:
1. build a search query from title + company hint + market/city
2. fetch top candidates using DDGS or SearXNG
3. reject obvious directory/listing spam when possible
4. crawl top 3-5 candidates
5. score best match based on:
   - business name similarity
   - city/service area match
   - role/industry consistency
   - presence of contact/about/services pages

### Recommendation
This is the first place to invest after signal ingest.
Without good company resolution, copy quality will always be mediocre.

## Stage 4 — company enrichment
**Goal:** build a structured research packet Chow can use.

Suggested sources:
- homepage
- contact page
- about page
- services page
- careers page
- structured metadata from HTML

Suggested tools:
- Crawl4AI for page load + markdown + page targeting
- Extruct for metadata
- Trafilatura as fallback text cleaner

Output store idea:
- `data/processed/craigslist_company_research.json`

Suggested fields:
- opportunity_id
- resolved_company_name
- website_url
- contact_page_url
- about_page_url
- services_page_urls
- phones
- emails
- contact_forms
- address
- service_area
- business_summary
- role_context_summary
- likely_operational_pain
- likely_first_automation_win
- contactability_score
- research_confidence
- source_refs

## Stage 5 — outreach package generation
**Goal:** give Chow a usable supervised package.

For each qualified opportunity, produce:
- one-line company summary
- one-line role summary
- likely pain signal
- best first automation win
- best contact path
- draft subject line
- draft email body
- confidence / caveats

### Recommendation
Do not let Chow draft from Craigslist text alone once enrichment exists.
Draft from the research packet.

## Stage 6 — supervised send + reply loop
**Goal:** keep execution safe and improve over time.

Already working:
- supervised queue
- Chow-branded live email dispatch

Next after enrichment:
- inbound mailbox polling
- thread persistence
- reply classification
- feedback into scoring and draft quality

## NH / New England starting footprint

Official Craigslist sites we confirmed for the region:
- `https://nh.craigslist.org/`
- `https://maine.craigslist.org/`
- `https://vermont.craigslist.org/`
- `https://boston.craigslist.org/`
- `https://worcester.craigslist.org/`
- `https://westernmass.craigslist.org/`
- `https://capecod.craigslist.org/`
- `https://providence.craigslist.org/`
- `https://hartford.craigslist.org/`
- `https://newhaven.craigslist.org/`

### Recommended phase-1 geographic scope
Start with:
- New Hampshire
- Boston
- Worcester / Central MA
- Southern Maine
- Providence
- Vermont

### Why this subset
- close to home base in NH
- still enough volume for a pilot
- easier to review manually
- enough regional diversity without turning it into a national scrape project

## Suggested implementation order

## Phase A — research lane first
Build:
- `scripts/enrich_craigslist_opportunities.py`
- `data/processed/craigslist_company_research.json`

Behavior:
- take imported opportunities
- resolve likely company website
- crawl homepage/contact/about/services
- extract structured research packet

## Phase B — better ranking
Add prioritization based on:
- role fit
- company confidence
- contactability
- likely first-win clarity
- market relevance

## Phase C — research-backed drafts
Generate copy from:
- role + company summary
- pain hypothesis
- first automation win
- best CTA

## Phase D — inbox loop
Connect Zoho inbox access so Chow can:
- verify replies
- read threads
- draft supervised follow-ups

## Architectural recommendation for this repo

### What to do now
- keep existing supervised/manual CL lane
- add NH + New England market definitions
- build a research/enrichment store
- use Crawl4AI mainly on resolved company websites
- use rules + metadata extraction first
- use LLMs only for reasoning-heavy summaries

### What not to do now
- do not make Azure Craigslist scraping the critical path
- do not rely only on LLM extraction for everything
- do not draft outreach off raw post text alone
- do not build national-scale crawling before NH/New England pilot quality is proven

## Open-source resources reviewed

- Crawl4AI GitHub README: https://github.com/unclecode/crawl4ai
- Crawl4AI docs home: https://docs.crawl4ai.com/
- Crawl4AI markdown generation docs: https://docs.crawl4ai.com/core/markdown-generation/
- Crawl4AI browser/crawler config docs: https://docs.crawl4ai.com/core/browser-crawler-config/
- Crawl4AI content selection docs: https://docs.crawl4ai.com/core/content-selection/
- Crawl4AI LLM-free strategies: https://docs.crawl4ai.com/extraction/no-llm-strategies/
- Crawl4AI LLM strategies: https://docs.crawl4ai.com/extraction/llm-strategies/
- Crawl4AI anti-bot docs (raw): https://raw.githubusercontent.com/unclecode/crawl4ai/main/docs/md_v2/advanced/anti-bot-and-fallback.md
- Crawl4AI undetected browser docs (raw): https://raw.githubusercontent.com/unclecode/crawl4ai/main/docs/md_v2/advanced/undetected-browser.md
- Crawl4AI session docs (raw): https://raw.githubusercontent.com/unclecode/crawl4ai/main/docs/md_v2/advanced/session-management.md
- Crawl4AI proxy docs (raw): https://raw.githubusercontent.com/unclecode/crawl4ai/main/docs/md_v2/advanced/proxy-security.md
- Trafilatura: https://github.com/adbar/trafilatura
- Extruct: https://github.com/scrapinghub/extruct
- Crawlee Python: https://github.com/apify/crawlee-python
- JobSpy: https://github.com/speedyapply/JobSpy
- SearXNG: https://github.com/searxng/searxng
- DDGS: https://github.com/deedy5/ddgs
- Craigslist sites list: https://www.craigslist.org/about/sites
- Craigslist RSS/help page: https://www.craigslist.org/about/rss

## Decision

For the Chow pilot, the best next build is:

**Craigslist company enrichment + ranking for NH/New England, using Crawl4AI as the company research engine.**
