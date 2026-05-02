# Gauntlet Teachings Deep-Dive (2026-04-15)

## Scope
Additional source-backed extraction from:
- gauntletai.com core pages (`/apply`, `/catalyst`, `/hire`, challenger-content)
- apply portal course bundle (`https://apply.gauntletai.com/assets/index-B4xGckjh.js`)
- admissions office-hours API (`/api/qa-webinar-sessions`)
- Claude Code Mastery PDF (`apply.gauntletai.com/pdfs/Claude%20Code%20Mastery%20Guide.pdf`)

---

## What Gauntlet teaches (converging signal)

## 1) Program philosophy
- AI-first is framed as operating-model transformation, not tool adoption.
- Repeated emphasis on immersion, pressure, deadlines, and observable output.
- Positioning language consistently stresses: weekly shipping, proof over résumé, and execution under constraints.

Source pages:
- `https://gauntletai.com/apply`
- `https://gauntletai.com/challenger-content/xatij9iw/how-the-fellowship-works`
- `https://gauntletai.com/challenger-content/jeexct5g/what-you-become-as-an-ai-first-engineer`

## 2) Flagship fellowship structure (Apply page)
- 10-week format, full-time
- 3 weeks remote + 7 weeks in Austin
- Travel/housing/food/compute/model access described as funded by hiring partners
- Weekly builds with escalating complexity and deadline pressure

Source:
- `https://gauntletai.com/apply`

## 3) Enterprise/Catalyst structure
- 6-week upskilling format for existing engineering teams
- 4 weeks remote/part-time + 2 weeks Austin immersion
- Curriculum modules explicitly listed:
  - Weeks 1–2: RAG + graph orchestration
  - Weeks 3–4: agent architectures + evals (+ MCP mentions)
  - Week 5: AI-first coding methodology immersion (80–100 hrs/week claim)
  - Week 6: focused production build sprint on company capstone

Source:
- `https://gauntletai.com/catalyst`

## 4) Core curriculum surfaces visible in Apply portal
From the public JS course bundle:
- Course lanes:
  - Context Engineering — Cursor
  - Context Engineering — Claude
  - Codex (marked coming soon)
- Cursor lesson sequence (6): planning setup, PRD, context management, tasking + architecture diagrams, context feeding, first coding task + checkpoints
- Claude lesson sequence (6):
  1. What Is Claude Code & Why It Matters
  2. Config hierarchy + project/global files + PRDs
  3. Hooks, Skills, MCP
  4. Community methodologies (BMAD, Ralph Wiggum, Claude Flow)
  5. Prompting + security + power-user habits
  6. Research-driven development + future of AI engineering

Source:
- `https://apply.gauntletai.com/assets/index-B4xGckjh.js`

## 5) Candidate profile and eligibility framing
- Challenger-content emphasizes intensity tolerance, high-agency behavior, and shipping pace as fit signals
- Eligibility page explicitly mentions hard-line CCAT threshold + authorization/availability requirements (no exceptions language)

Source pages:
- `https://gauntletai.com/challenger-content/8jmlfkr3/anatomy-of-a-challenger`
- `https://gauntletai.com/challenger-content/128re836/eligibility-criteria-for-gauntlet`

## 6) Admissions cadence / live touchpoint
- Public API currently exposes recurring office-hours sessions (with timestamps and join metadata)

Source:
- `https://apply.gauntletai.com/api/qa-webinar-sessions`

---

## Practical interpretation for our prep
1. Prioritize weekly shippable artifacts over passive study.
2. Practice curriculum primitives explicitly: PRD -> architecture -> context control -> build -> evals.
3. Prepare to defend RAG/graph/agent/eval tradeoffs in interview language.
4. Train for observable execution: measurable output, real constraints, reproducible quality checks.
