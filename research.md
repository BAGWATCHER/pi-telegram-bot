# Research: Biggest AI Announcements & Capabilities — January–March 2026

*Research conducted March 1, 2026. Sources: Anthropic Newsroom, OpenAI News, Google DeepMind Blog, llama.meta.com, xAI News, The Verge AI, Perplexity Blog.*

---

## Summary

Early 2026 is defined by three headline themes: **AI agents becoming real enterprise products** (Perplexity Computer, OpenAI Frontier, Claude Cowork), **model families accelerating to a new capability tier** (Gemini 3 Deep Think leads across academic benchmarks, GPT-5.3-Codex rewrites the coding frontier, Claude Sonnet 4.6 brings Opus-class intelligence at Sonnet prices), and **geopolitics slamming into AI** (Trump bans then uses Claude for Iran strikes on the same day, OpenAI signs Pentagon deal, Anthropic fights "supply chain risk" designation in court). Hardware pricing is collapsing at the cheaper end while massive compute deals are being struck at the top.

---

## 1. Claude / Anthropic

### Latest Models

**Claude Opus 4.6** — Released in early February 2026. The current flagship. Used as the "core reasoning engine" in Perplexity Computer. Scored 68.8% on ARC-AGI-2 and 40.0% on Humanity's Last Exam.

**Claude Sonnet 4.6** — Released **February 17, 2026**. Now the **default model for all Claude plans** (including Free). Key upgrades:
- **Computer use score: 72.5% on OSWorld** (was under 15% in late 2024 — a ~5× jump in 16 months)
- Approaching human-level at spreadsheet navigation and multi-tab web form completion
- **1M token context window** (beta)
- Preferred over Opus 4.5 by developers **59% of the time** in head-to-head testing
- Preferred over Sonnet 4.5 **70% of the time** in Claude Code testing
- Specific enterprise wins: 94% on an insurance computer-use benchmark (Pace), 15% improvement over Sonnet 4.5 on Box's enterprise document reasoning, +15% on Harvey's BigLaw Bench for Gemini 3 Flash equivalent tasks
- **Pricing unchanged from Sonnet 4.5: $3/$15 per 1M tokens** (input/output)

### New Capabilities

**Tool use / API (now GA):**
- Code execution, memory, programmatic tool calling, tool search, tool use examples — all **now generally available**
- Web search + fetch tools now auto-write and execute code to filter results (better quality, fewer tokens)
- Adaptive thinking + extended thinking supported
- Context compaction (beta): auto-summarizes old context as conversations approach limits

**Claude in Excel with MCP** — Claude can pull live data from S&P Global, LSEG, Daloopa, PitchBook, Moody's, and FactSet without leaving the spreadsheet. Available on Pro/Max/Team/Enterprise.

**Computer Use** — Sonnet 4.6 shows "human-level capability" on complex spreadsheets and multi-step web forms. Prompt injection resistance significantly improved.

**Claude Code Security** (Feb 20, 2026, limited preview) — Scans codebases for novel security vulnerabilities the way a human researcher would (not pattern-matching). Uses Opus 4.6 to find bugs. In early testing, the team found **500+ vulnerabilities in production open-source codebases** that had gone undetected for decades. Available to Enterprise/Team customers; free for open-source maintainers.

**Claude Cowork** — Collaborative AI workspace product. Now integrates MCP connectors, supported on Pro/Max/Team/Enterprise.

### Enterprise/Partnerships

- **Infosys collaboration** (Feb 17) — Building AI agents for telecom, financial services, manufacturing, software dev. Claude Code integrated with Infosys Topaz.
- **Bengaluru office opened** (Feb 16) — India is Claude's second-largest market; nearly half of Indian Claude usage is app development.
- **Rwanda MOU** (Feb 17) — Anthropic and the Government of Rwanda signed a memorandum of understanding for AI in health and education.
- **Vercept acquisition** (Feb 25, 2026) — Acquired computer vision startup (co-founders: Kiana Ehsani, Luca Weihs, Ross Girshick) to push computer use capabilities further.
- **Bun acquisition** — Previously acquired JavaScript runtime Bun for Claude Code (which reached a $1B milestone).
- **Available on all three major clouds:** AWS Bedrock, Google Cloud Vertex AI, and Microsoft Azure.

### Responsible Scaling Policy v3.0 (Feb 24, 2026)

Key changes: (1) Separates what Anthropic can do alone from what the whole industry needs. (2) New **Frontier Safety Roadmap** — public goals updated regularly (moonshot R&D for security, automated red-teaming, comprehensive AI activity records). (3) **Risk Reports** published every 3–6 months (Feb 2026 Risk Report published). External review required for higher-risk models. ASL-3 safeguards have been active since May 2025.

### Headline Drama: The Pentagon Standoff

- Trump (via Sec. War Pete Hegseth) designated Anthropic a **"supply chain risk"** (Feb 28).
- Trump ordered federal agencies to immediately cease using Claude, then walked it back to a **6-month phaseout** after learning Iran strike planning had already relied on Claude.
- Per WSJ: **US launched air strikes on Iran using Claude** for intelligence assessments and target identification within hours of Trump's ban announcement.
- Anthropic is **challenging the designation in court**. Dario Amodei published a public statement refusing Pentagon terms requiring removal of safeguards against lethal autonomous weapons and mass surveillance.
- Former Trump advisor Dean Ball called it "attempted corporate murder."

---

## 2. OpenAI / GPT

### Latest Models

**GPT-5** — The base model, available to everyone on ChatGPT (rolled out in 2025). The "Summer Update" launch made it widely available.

**GPT-5.2** — Current main API model. Pricing: **$1.75/$14.00 per 1M tokens**. Key benchmarks (with thinking): HLE 34.5%, ARC-AGI-2 52.9% (highest of any model in that benchmark tier), GPQA Diamond 92.4%, AIME 2025 100% with code execution, SWE-bench Verified 80.0%, long-context MRCR 128k: 81.9%.

**GPT-5.3-Codex** — Released early 2026 (exact date in the recent weeks preceding this research). The headline new model:
- "Most capable agentic coding model to date"
- **New state-of-the-art on SWE-Bench Pro** (spans 4 languages, more contamination-resistant than SWE-bench Verified, which OpenAI declared obsolete on Feb 23)
- **New SOTA on Terminal-Bench 2.0** — by a wide margin vs previous models
- **25% faster** than GPT-5.2-Codex
- **Self-improving**: "The first model that was instrumental in creating itself" — the Codex team used early versions to debug its own training, manage deployment, and diagnose eval results
- **Computer use**: Significantly stronger than prior GPT models on OSWorld-Verified (~72% human)
- First model classified as **"High capability" for cybersecurity** under OpenAI's Preparedness Framework
- Cybersecurity safeguards: automated monitoring, trusted access program, "Aardvark" security research agent
- Co-designed for and trained on **NVIDIA GB200 NVL72 systems**
- Available to paid ChatGPT plan users (API coming)

**Note:** OpenAI declared in Feb 23, 2026 that **SWE-bench Verified no longer measures frontier coding capabilities** — models have saturated it. Industry is moving to SWE-bench Pro, Terminal-Bench 2.0, and other harder evals.

### Products & Scale

- **Codex**: 1.6M weekly active users — **more than tripled since the start of 2026**
- **ChatGPT**: 900M weekly active users; **50M consumer subscribers** (accelerating — Jan/Feb on track to be largest months ever for new subscribers)
- **9M+ paying business users**
- **OpenAI Frontier**: Enterprise AI coworker platform. Connects siloed data (CRM, data warehouses, ticketing), gives agents shared context + identity + permissions, deploys across on-prem/cloud/OpenAI-hosted. Real results: manufacturer reduced 6-week work to 1 day; investment firm freed 90% more sales time; energy producer increased output 5% = $1B+ revenue
- **Stateful Runtime Environment for Agents on Amazon Bedrock** (Feb 27): Agents with persistent memory, cross-tool context; launching "in the next few months"

### Funding & Partnerships

**$110B raised at $730B pre-money valuation:**
- $30B from SoftBank
- $30B from **NVIDIA** (also committing 3GW dedicated inference + 2GW training on Vera Rubin systems)
- $50B from **Amazon** (initial $15B, rest contingent)

**Amazon Partnership (Feb 27, 2026):**
- AWS = **exclusive third-party cloud distribution** for OpenAI Frontier
- Amazon invests $50B total
- OpenAI commits to consume **2GW of Amazon Trainium** (Trainium3 + Trainium4, expected 2027) — expanding existing $38B agreement by $100B over 8 years

**Microsoft Partnership** continued (Feb 27, 2026 joint statement).

**DoW Agreement (Feb 28):**
- OpenAI reached Pentagon deal with stronger guardrails than Anthropic's original contract:
  - Cloud-only deployment (prevents edge-device autonomous weapons)
  - Full control of safety stack retained
  - No autonomous weapons, no mass domestic surveillance
  - Cleared OpenAI engineers + safety researchers in the loop
  - Contractual references to laws as they exist today (future law changes can't override)
- Altman: Asking DoW to offer same terms to all AI companies, including Anthropic

**Legal:** OpenAI **defeats xAI's trade secrets lawsuit** (verdict this period).

---

## 3. Google Gemini

### Current Model Family

Google has released the **Gemini 3** family during this period:

**Gemini 3 Flash**
- **Pricing: $0.50/$3.00 per 1M tokens** (input/output) — extremely competitive
- 1M token context window, 64k output
- Knowledge cutoff: January 2025
- Beats Gemini 2.5 Flash across the board; "pro-class depth at flash speed"
- Key benchmarks vs Gemini 2.5 Flash: 15%+ improvement on Box's extraction tasks, 7% on Harvey BigLaw Bench
- Endorsed by Cursor (VP Dev Experience), Figma (CDO Loredana Crisan), Salesforce Agentforce, JetBrains, Replit, Bridgewater ("first to deliver Pro-class depth at the speed and scale our workflows demand")
- Available in: Gemini App, Vertex AI, Google AI Studio, Gemini CLI, Gemini Enterprise, Google AI Mode, Google Antigravity, Android Studio

**Gemini 3.1 Pro** — Most recent Pro-tier model
- Pricing: **$2.00/$12.00 per 1M tokens** (under 200k), $4.00/$18.00 (over 200k)
- Top benchmark scores vs peers: HLE 44.4% (best), ARC-AGI-2 77.1% (best in Pro tier), GPQA Diamond 94.3% (best), Terminal-Bench 2.0 68.5% (best), BrowseComp 85.9% (best)
- 1M context window
- Compared in tables against Claude Sonnet 4.6, Opus 4.6, GPT-5.2, and GPT-5.3-Codex

**Gemini 3 Deep Think** (Feb 2026)
- Described as "pushes the boundaries of intelligence" — extended specialized reasoning mode
- Available to **Google AI Ultra subscribers** only
- **Leads every major academic benchmark:**
  - **ARC-AGI-2: 84.6%** (GPT-5.2 is 52.9%, Opus 4.6 is 68.8%) — best of any model
  - **Humanity's Last Exam: 48.4%** (with search+code: 53.4%) — best of any model
  - **International Math Olympiad 2025: 81.5%** — only model tested
  - **Codeforces Elo: 3455** — extraordinary coding performance
  - International Chemistry Olympiad: 82.8%, International Physics Olympiad: 87.7%
  - Condensed Matter Theory (CMT-Benchmark): 50.5% vs GPT-5.2's 41.0%

**Nano Banana 2** (image generation model)
- "Combining Pro capabilities with lightning-fast speed"
- Free user access to advanced AI image tools
- Used by Perplexity Computer for image generation tasks

**Veo 3.1**
- Video generation: "Veo 3.1 Ingredients to Video: More consistency, creativity and control"
- Used by Perplexity Computer for video generation

### New Products & Features

**Google Antigravity** — New agentic development platform, described as "evolving the IDE into the agent-first era."

**Google Flow** (updated Feb 2026) — Now unifies Whisk (image remixing), ImageFX (image generation), and AI video generation into one workspace: "generate, edit and animate everything in one unified workspace."

**Gemini on Pixel 10 + Samsung Galaxy S26** — Gemini can now **book Uber rides, order food**, and complete real-world task automation on Android devices. This is the capability Apple's Siri could not ship.

**Project Genie** — Experimenting with "infinite, interactive worlds."

**Gemini creates music** — New capability: users can create music with Gemini in the app.

**Google Translate with Gemini** — Alternative translations based on context. New "Understand" and "Ask" buttons.

**Google takes control of "Android of robotics" project** — Physical AI push.

---

## 4. Meta / Llama

### Llama 4 — Current Open-Source Flagship

**Llama 4 Maverick:**
- **Native multimodality** — text + image understanding via "early fusion" (pre-trained on unlabeled text and vision data jointly, not frozen separate weights)
- **10M token context window** — the largest of any available model
- Cost: **$0.19/Mtok (3:1 blended) distributed inference**; single-host: $0.30–$0.49/Mtok
- Use cases: memory, personalization, multi-modal applications

**Llama 4 Scout:**
- Also natively multimodal (text + image)
- **Single H100 GPU efficiency** — can run on one GPU
- 10M token context window
- Optimized for long document analysis

**Real-world deployments:**
- **Shopify**: 76% higher token throughput vs previous model, 97.7% Macro-F1 on intent detection, 33% compute cost savings
- **Stoque**: 50% reduction in repetitive support queries, 30% more admin tasks completed, 11% user satisfaction increase

**Assessment:** Llama 4 is highly competitive on cost and context length. Its 10M context window beats every closed model currently available. The multimodal early-fusion architecture is technically innovative. However, Llama 4 doesn't appear in the frontier benchmark tables for reasoning/coding (Gemini 3.1 Pro, Opus 4.6, GPT-5.2 tier), suggesting it's not yet competitive with the top closed models on pure intelligence benchmarks, but dominates on value and deployability.

---

## 5. Other Notable Labs

### xAI / Grok

**Grok 4.1** (released Nov 19, 2025) — Current main model. Available on grok.com, X, iOS/Android. "Grok 4.1 Fast Reasoning" is the version appearing in competitive benchmark tables.

**Grok 4.1 Fast Reasoning pricing:** **$0.20/$0.50 per 1M tokens** — the cheapest frontier-class reasoning model by far.

**Grok Imagine API** (Feb 2, 2026) — "State-of-the-art video generation across quality, cost, and latency." xAI entering the video generation API market.

**Grok 4 Fast** (Sep 2025) — "Pushing the Frontier of Cost-Efficient Intelligence."

**xAI for Government** (announced Aug 2025) — Suite of frontier AI products for US Government customers. Legal: OpenAI defeated xAI's trade secrets lawsuit this period.

**Benchmark performance (Grok 4.1 Fast Reasoning in Gemini 3 Flash comparison table):**
- HLE: 17.6%, GPQA Diamond: 84.3%, AIME 2025: 91.9%, SWE-bench Verified: 50.6%, Vending-Bench 2: $1,107 net worth (lowest of compared models)
- Shows Grok is competitive on math/science but weaker on agentic tasks

### Perplexity

**Perplexity Computer** (Feb 2026) — Major new product. A "general-purpose digital worker" platform:
- Described as "the next evolution of AI" beyond chat or single-agent tools
- **Multi-model orchestration**: Routes tasks to the best model for each subtask:
  - Opus 4.6 → core reasoning
  - Gemini → deep research (sub-agent creation)
  - Nano Banana → images
  - Veo 3.1 → video
  - Grok → speed for lightweight tasks
  - ChatGPT 5.2 → long-context recall and wide search
- Creates sub-agents that can run in parallel for hours or months
- Each task runs in isolated compute environment with real filesystem + real browser + real tool integrations
- **Model-agnostic**: users can choose specific models for specific subtasks
- Available to Perplexity Max subscribers; Enterprise Max coming
- Also runs: **Comet** (AI-native browser) + **Comet Assistant**
- Perplexity deep research rated **industry-best** by DRACO benchmark

### Microsoft

**Copilot Tasks** — Uses its own computer to complete tasks (announced this period, similar to Claude Cowork / Perplexity Computer category).

**Alexa Plus personality updates** — Amazon's Alexa AI now lets users configure personality (friendly/blunt/chilled out).

### Other

- **DeepSeek** — No major new model announcement found in this research period (Jan–Mar 2026). DeepSeek was a 2025 story.
- **Mistral/Qwen** — No major announcements captured in this period.
- **Adobe Quick Cut** — New AI video editing tool that stitches clips into a first draft.
- **Seedance 2.0** — New video generation model from ByteDance's AI team, being watched as potential competitor.

---

## 6. AI Agents — State of the Market (Early 2026)

**The agent race is real and products are shipping.** This is the dominant theme of early 2026.

| Product | Company | Approach | Access |
|---|---|---|---|
| Perplexity Computer | Perplexity | Multi-model orchestration, sub-agents, async long-running | Max subscribers |
| Claude Cowork | Anthropic | Collaborative workspace, MCP connectors, agent orchestration | Pro/Max/Team/Enterprise |
| OpenAI Frontier | OpenAI | Enterprise AI coworker platform, shared context, identity, permissions | Limited early access |
| Codex (GPT-5.3-Codex) | OpenAI | Agentic coding, computer use, autonomous multi-day task execution | Paid ChatGPT plans |
| Copilot Tasks | Microsoft | Computer-using agent integrated with Microsoft 365 | Rolling out |
| Devin (Cognition) | Cognition | Agentic coding with Gemini 3 Flash powering "latency-sensitive experiences" | Available |
| Google Antigravity | Google | IDE → agent-first development platform | In development |
| Claude Code | Anthropic | Terminal-native agentic coding with Claude Code Security | Claude Code plans |

**Key patterns:**
1. **Multi-agent orchestration** is winning: Perplexity Computer's model-agnostic approach (best model for each subtask) is conceptually the most advanced.
2. **Stateful persistence** is the new frontier: OpenAI's Stateful Runtime Environment on Bedrock keeps agents working across sessions with shared memory.
3. **Computer use is crossing the human threshold**: Multiple systems now approach or match human performance on desktop tasks (Claude Sonnet 4.6 at 72.5% OSWorld, GPT-5.3-Codex showing "far stronger computer use").
4. **Benchmarks are being retired**: SWE-bench Verified was officially declared obsolete by OpenAI (Feb 23, 2026). The field now uses SWE-bench Pro (4 languages, harder), Terminal-Bench 2.0, Toolathlon, MCP Atlas.
5. **Agentic coding weekly users**: Codex at 1.6M (tripled since Jan 2026 start).

---

## 7. AI in Business — Major Real-World Deployments

**Quantified enterprise results (from OpenAI Frontier):**
- Manufacturing company: production optimization from 6 weeks → **1 day**
- Global investment firm: agents deployed end-to-end in sales → **90% more time freed for salespeople**
- Energy producer: AI increased output by **5%, adding $1B+ revenue**

**Sector deployments:**
- **Insurance:** Pace reports 94% accuracy on Claude Sonnet 4.6 computer use benchmark — "mission-critical for submission intake and first notice of loss"
- **Legal:** Harvey uses Claude Sonnet 4.6 for complex document review; Gemini 3 Flash shows 7% improvement on BigLaw Bench
- **Financial services:** Bridgewater uses Gemini 3 Flash for "complex multi-step agents" reasoning over vast multimodal datasets
- **Telecom:** Anthropic-Infosys partnership specifically targeting carrier network modernization
- **Retail:** Burger King deploying AI to monitor whether employees say "please" and "thank you" (Feb 2026)
- **Staffing:** Jack Dorsey's Block company cut **nearly half its staff** in a bet on AI (Feb 2026)
- **Space/Planetary science:** Claude helped NASA Perseverance rover travel **400 meters on Mars** (Jan 30, 2026) — the first AI-assisted drive on another planet
- **Coding tools:** Replit, Cursor, GitHub, Windsurf all citing dramatic performance improvements with Sonnet 4.6

---

## 8. AI Regulation — Key Developments

### US Federal Level (Dramatic Shift)

The dominant story is **geopolitical conflict between the Trump administration and AI labs:**

- **Trump bans Claude** → walks it back → war planners use Claude for Iran strikes the same day (Feb 27–28, 2026)
- Pentagon designated Anthropic a **"supply chain risk"** under Defense Production Act authority
- **Anthropic is challenging the designation in court**
- OpenAI reached a Pentagon deal with explicit contractual protections (cloud-only, no autonomous weapons, no mass surveillance) — and asked DoW to offer same terms to all AI companies
- Former DOJ official warned this could be a "first step toward partial nationalization of the AI industry"
- **Policy environment has shifted** to prioritizing AI competitiveness and economic growth over safety regulation. Federal safety-oriented AI regulation has stalled.
- Trump at State of the Union: negotiated a "ratepayer protection pledge" requiring tech companies to supply their own power for data centers.
- **Take It Down Act** signed into law: Melania Trump championed legislation requiring social platforms to remove nonconsensual intimate imagery (including AI deepfakes).

### EU / International

- **EU AI Act Codes of Practice** — being implemented. Anthropic's RSP v3.0 directly addresses compliance requirements.
- **California SB 53** — requires frontier AI developers to publish risk frameworks (Anthropic's Frontier Compliance Framework addresses this)
- **New York RAISE Act** — similar requirements
- UK AI Security Institute partnerships with both Google DeepMind and Anthropic deepened this period
- Google DeepMind supporting **US Department of Energy's "Genesis"** national mission for scientific discovery

### Safety Research

- Anthropic Feb 2026 **Risk Report** published — first under RSP v3.0 format
- OpenAI new safety protocols post-Canadian school shooting: would now alert police to accounts showing violent intent
- ARC-AGI-2 is the new benchmark that keeps AI honest — even the best model (Gemini 3 Deep Think) scores 84.6%; GPT-5.2 scores 52.9%

---

## 9. AI Hardware

### NVIDIA

- **Vera Rubin systems** — Next generation after Blackwell. OpenAI has secured **3GW dedicated inference + 2GW training** on Vera Rubin systems.
- **NVIDIA GB200 NVL72** — What GPT-5.3-Codex was co-designed for, trained on, and served on.
- **$30B investment in OpenAI** — NVIDIA is now a financial partner as well as hardware supplier.
- Hopper + Blackwell systems already in operation across Microsoft, OCI, and CoreWeave for OpenAI.

### Amazon Trainium

- **Trainium3** — Currently being deployed under OpenAI's 2GW commitment.
- **Trainium4** — "Expected to begin delivery in 2027." Promises significantly higher FP4 compute performance, expanded memory bandwidth, increased HBM capacity.
- Amazon's purpose-built silicon is now a meaningful part of the inference equation alongside NVIDIA.

### Power & Infrastructure

- Trump at State of the Union claimed to have a "ratepayer protection pledge" with tech companies for self-supplied power.
- Amazon AGI lab leader **David Luan** (head of Amazon's SF AGI lab) is departing to start a new company.
- AI data center demand continues to surge; power supply is cited as a key constraint.

---

## 10. Pricing — Key Data Points

Current API pricing (input/output per 1M tokens) as of early 2026:

| Model | Input | Output | Notes |
|---|---|---|---|
| **Grok 4.1 Fast Reasoning** | $0.20 | $0.50 | Cheapest frontier reasoning |
| **Gemini 3 Flash** | $0.50 | $3.00 | Best value flagship-quality |
| **Gemini 2.5 Flash-Lite** | $0.30 | $2.50 | Budget Gemini |
| **Llama 4 Maverick** | $0.19/Mtok blended | — | Cheapest frontier multimodal |
| **GPT-5.2** | $1.75 | $14.00 | OpenAI's workhorse |
| **Gemini 3.1 Pro** | $2.00 | $12.00 | Google's flagship (under 200k) |
| **Claude Sonnet 4.6** | $3.00 | $15.00 | Same price as Sonnet 4.5 |
| **Gemini 3.1 Pro** (>200k) | $4.00 | $18.00 | Extended context |
| **Claude Opus 4.6** | ~higher | — | Exact not published; top tier |

**Pricing trends:**
1. **Massive deflation at the cheap end**: Grok 4.1 Fast at $0.20/$0.50 is extraordinarily cheap for a capable reasoning model. Llama 4 Maverick at $0.19/Mtok blended sets a floor for open-source economics.
2. **Gemini 3 Flash is the aggressive competitor**: $0.50/$3.00 for what Google claims is "pro-class depth at flash speed" puts pressure on Claude Haiku and GPT-4o-mini equivalents.
3. **Premium models holding price**: Claude Sonnet 4.6 launched at the same price as 4.5 despite being dramatically more capable. GPT-5.2 at $1.75/$14.00 is the mid-premium option.
4. **Compute cost plummeting**: OpenAI's Trainium deal is explicitly described as lowering "the cost and efficiency of producing intelligence at scale."

---

## Sources

**Kept:**
- [Anthropic Newsroom](https://www.anthropic.com/news) — Primary source for all Claude/Anthropic dates and announcements
- [Claude Sonnet 4.6 Launch](https://www.anthropic.com/news/claude-sonnet-4-6) — Full capability specs, benchmark data, enterprise testimonials
- [Anthropic Vercept Acquisition](https://www.anthropic.com/news/acquires-vercept) — Computer use strategy
- [Anthropic RSP v3.0](https://www.anthropic.com/news/responsible-scaling-policy-v3) — Safety policy, industry context
- [Claude Code Security](https://www.anthropic.com/news/claude-code-security) — Cybersecurity capability details
- [Anthropic-Infosys Partnership](https://www.anthropic.com/news/anthropic-infosys) — Enterprise deployment details
- [OpenAI News](https://openai.com/news) — All OpenAI announcements index
- [OpenAI Amazon Partnership](https://openai.com/index/amazon-partnership/) — $50B investment, Trainium, Frontier distribution
- [OpenAI DoW Agreement](https://openai.com/index/our-agreement-with-the-department-of-war/) — Safety guardrails, red lines
- [OpenAI Scaling AI for Everyone](https://openai.com/index/scaling-ai-for-everyone/) — $110B raise, product scale metrics
- [OpenAI Frontier](https://openai.com/index/introducing-openai-frontier/) — Enterprise agent platform details + ROI examples
- [GPT-5.3-Codex](https://openai.com/index/introducing-gpt-5-3-codex/) — Full capability brief, self-referential training, benchmarks
- [GPT-5 Overview](https://openai.com/gpt-5/) — Product positioning
- [Google DeepMind Blog](https://deepmind.google/discover/blog/) — Model list, product names
- [Gemini 3 Flash](https://deepmind.google/models/gemini/flash/) — Detailed benchmarks vs all competitors, pricing, customer testimonials
- [Gemini 3 Family Overview](https://deepmind.google/models/gemini/) — 3.1 Pro benchmarks, Deep Think benchmarks, full model hierarchy
- [llama.meta.com](https://llama.meta.com/) — Llama 4 Maverick/Scout specs, pricing, deployments
- [xAI News](https://x.ai/news) — Grok 4.1 timeline, Grok Imagine API
- [Perplexity Computer](https://www.perplexity.ai/hub/blog/introducing-perplexity-computer) — Multi-model orchestration details, model assignments
- [The Verge AI](https://www.theverge.com/ai-artificial-intelligence) — Pentagon drama, Burger King AI, Block layoffs, business news

**Dropped:**
- VentureBeat (HTTP 429 / paywalled) — Could not access
- TechCrunch AI section (incomplete extraction) — Could not access
- Meta AI Blog direct (404 on specific Llama 4 launch post) — Used llama.meta.com instead
- xAI specific Grok 4.1 article (article URL not accessible separately) — Used news index

---

## Gaps

**Unanswered questions / areas for follow-up:**

1. **Exact Llama 4 release date** — The llama.meta.com site lists it as "latest" but no specific Jan–Mar 2026 launch date was found. Llama 4 may have launched in late 2025.
2. **DeepSeek** — No new model announced in this period. Their last major launch (R1, V3) was in late 2024/early 2025. A follow-up may reveal Q1 2026 activity.
3. **Mistral/Cohere/AI21/Qwen** — Not captured in this research pass. These remain significant enterprise players but didn't break into top news.
4. **Sora updates** — OpenAI's Sora is listed in the nav but no specific Jan–Mar 2026 feature updates were captured.
5. **Claude Opus 4.6 exact launch date** — Referenced throughout benchmarks but announcement page not fetched.
6. **EU AI Act enforcement actions** — The Codes of Practice are in development but no specific enforcement actions or fines were captured.
7. **Pricing for GPT-5.3-Codex** — Not publicly disclosed in API pricing tables yet.
8. **Apple Intelligence** — The Verge references Apple's Siri struggles vs Google/Samsung, but no specific Jan–Mar 2026 Apple AI announcements were captured.

**Suggested next steps:**
- Fetch DeepSeek's official blog and Hugging Face leaderboard for any Q1 2026 releases
- Fetch Mistral's blog for Mistral Medium/Large updates
- Fetch the specific Gemini 3 Deep Think announcement article for exact release date
- Fetch Claude Opus 4.6 announcement article
- Check EU AI Act official documentation for Codes of Practice timeline
