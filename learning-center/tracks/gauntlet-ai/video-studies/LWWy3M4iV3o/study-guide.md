# Study Guide — Night School: How to Interview Like an AI-First Engineer

Video: https://www.youtube.com/watch?v=LWWy3M4iV3o

## Purpose of this guide
Translate the session into operational training for:
- candidate preparation
- agent coaching
- interview rubric design

---

## Core thesis from the session

Hiring signal is broken in AI-era hiring; resumes and buzzwords are noisy. The strongest signal is **observable execution quality** under real constraints.

Evidence cues from transcript:
- "signal in a sea of noise" ([07:10], [08:26])
- better signal by observing real work ([09:12])
- projects + under-the-hood articulation as credibility checks ([29:33], [29:48], [37:54])

---

## Interview framework extracted

## 1) Credibility check (early gate)
Interviewers test whether candidate can prove they actually built what they claim.

What to show:
- concrete project evidence (repo, commits, architecture decisions)
- ability to explain implementation tradeoffs, not just outcomes
- reproducible technical narrative

Transcript anchors: [25:15], [29:33], [29:48], [37:54]

## 2) AI engineering primitives check
Session repeatedly calls out 4 primitives as table stakes:
- **RAG/retrieval**
- **graphs**
- **agents**
- **evals**

Transcript anchors: [11:42], [20:32], [20:36]

Sample expected questioning themes (explicitly mentioned):
- agentic RAG / metadata-filtered RAG
- vector DB choice and failure modes
- agent vs graph distinction
- eval design and LLM-as-judge

Transcript anchors: [11:54]–[12:09], [21:01]–[22:18], [23:21]–[23:57]

## 3) Workflow/system check
Beyond features, they probe whether you can run an end-to-end engineering loop:
- scoped planning
- context control
- implementation
- quality control
- iteration

Transcript anchors: [15:20], [16:20], [17:00], [42:51]–[42:59]

## 4) Product sense + communication check
Session emphasizes PM and engineer convergence in AI workflows.

What this means:
- candidate must show taste/priority judgment
- communication quality matters as much as coding speed
- framing and reasoning in interview are critical

Transcript anchors: [27:34], [27:42], [30:52], [41:50]

---

## Technical expectations extracted

## A) Context engineering discipline
- progressive context disclosure
- precise retrieval over context dumping
- tool-connected workflows (e.g., MCP)

Transcript anchors: [16:20], [21:01]–[21:17], [14:40], [21:59]

## B) Agent orchestration competence
- configuring skills/toolchains
- using sub-agents for review/QA/security checks
- controlling handoffs and failure behavior

Transcript anchors: [10:52]–[10:58], [15:58], [17:00], [17:40]

## C) Evaluation rigor
Session repeatedly frames evals as differentiator.

Expected competence:
- design eval sets
- define scoring + regression criteria
- improve systems from eval feedback loops

Transcript anchors: [22:15], [22:37], [23:21], [47:09]

## D) Quality gates over vibe coding
Direct anti-pattern callout: uncontrolled vibe coding leads to loss of control/quality.

Transcript anchors: [18:50], [31:43]

---

## Candidate proof stack (what to prepare)

1. **One flagship project** you can demo deeply
2. **One architecture walkthrough** (diagram + decisions + tradeoffs)
3. **One QA/eval report** (metrics + failures + fixes)
4. **One interview narrative** that links product goal → system design → measurable quality

Session-reinforced evidence style:
- show repo, not just slides ([37:54])
- explain exactly what you built and why ([29:48])

---

## Anti-patterns to avoid (from session)

- Resume-only storytelling without technical receipts
- Buzzword fluency without primitive-level understanding
- Vague “I used AI” answers with no process detail
- No eval or quality strategy
- No ability to explain retrieval, graph, and agent tradeoffs

---

## Training conversion plan (for our Learning Center)

## Module 1 — Interview primitives deep dive
- outcomes: can explain RAG/graph/agent/eval distinctions with examples
- artifact: 10-question oral defense sheet

## Module 2 — Build + evidence sprint
- outcomes: ship one project with architecture + eval + postmortem
- artifact: demo pack + repo review notes

## Module 3 — Quality and reliability
- outcomes: convert vibe coding loop into gated engineering loop
- artifact: eval harness + regression checklist

## Module 4 — Communication and product sense
- outcomes: concise technical storytelling under interview pressure
- artifact: 5-minute technical narrative + Q&A bank

---

## Recommended use

Use this guide alongside:
- `transcript.clean.md`
- `tracks/gauntlet-ai/training-loop.md`
- `tracks/gauntlet-ai/curriculum-map.md`

and convert each section into drills and graded mock interviews.
