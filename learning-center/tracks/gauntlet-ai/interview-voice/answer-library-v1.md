# Answer Library v1

## 1) Tell me about yourself (60s)
I’m an AI-first engineer focused on shipping production systems, not demos. My edge is combining rapid build velocity with strict quality controls: clear planning, context discipline, and eval-driven iteration. In recent projects, I’ve built systems using RAG and agent workflows, then hardened them with test/eval gates and failure monitoring. I’m strongest when the problem is ambiguous and the team needs someone who can translate goals into working software quickly and reliably.

## 2) What makes you AI-first?
I treat models as part of the engineering system, not as autocomplete. I design workflows where planning, implementation, and QA are all AI-assisted, but quality is enforced through explicit gates. That includes scoped context, tool orchestration, and eval loops before anything ships.

## 3) Walk me through a project
- Problem: <1 sentence user/business problem>
- Constraints: <latency/cost/data/risk>
- Architecture: <components + why>
- Quality: <tests/evals/monitoring>
- Failure: <what broke>
- Fix: <what changed>
- Outcome: <metric or concrete impact>

## 4) How do you ensure quality with AI-generated code?
I separate speed from acceptance. AI can generate quickly, but acceptance requires passing quality gates: unit/integration tests, eval checks for model behavior, and regression thresholds. I also force explicit review for risky paths and keep rollback paths ready. If a change improves one metric but harms reliability, it doesn’t ship.

## 5) Explain RAG vs agent vs graph (concise)
RAG is retrieval + generation to ground answers in external context. Agents add decision-making and tool use across steps. Graphs formalize multi-step flows with explicit nodes, edges, and control logic. I usually start simple (RAG), then add agent behavior and graph structure when complexity and reliability needs justify it.

## 6) Failure story (high-value format)
In one project, retrieval quality degraded as corpus size grew. Symptoms were subtle: answers looked plausible but citation relevance dropped. Root cause was weak chunking + poor reranking under domain-specific queries. I fixed it by redesigning chunk boundaries, adding reranking, and introducing query-specific eval slices. Precision improved and false-confidence responses dropped.

## 7) Why do you want this role?
Because this role rewards what I actually optimize for: fast execution with engineering rigor. I like environments where I can own delivery end-to-end, defend technical decisions clearly, and improve systems through tight feedback loops.
