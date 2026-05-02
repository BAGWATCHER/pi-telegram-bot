# Study Guide — Building an AI Dark Factory (Live)

Video: https://www.youtube.com/watch?v=Xg0tNz9pICI
Provided link: https://www.youtube.com/live/Xg0tNz9pICI?si=WYR0YFpZmGTBMqzC

## Purpose of this guide
Convert the live build session into practical engineering patterns we can apply to BearingBrain and Gauntlet prep.

---

## Core thesis
A “dark factory” for software is a high-autonomy coding system where AI handles issue triage, implementation, validation, PR flow, and release operations, with human oversight intentionally reduced.

Transcript anchors:
- definition + origin analogy ([00:01:44]–[00:02:20])
- end-to-end automation scope ([00:02:15]–[00:02:19])

---

## 5 levels of AI coding maturity (as presented)

1. **Level 0 — spicy autocomplete**
   - AI as advisor/search; human writes code.
2. **Level 1 — coding intern**
   - AI handles boilerplate; human leads.
3. **Level 2 — junior/pair mode**
   - alternating control on real tasks.
4. **Level 3 — AI engineer mode**
   - AI writes majority; human reviews plans/PRs and is bottleneck for verification.
   - presenter frames this as best reliability/speed balance currently.
5. **Level 4 — harnessed long-run autonomy**
   - unattended long tasks via harnesses; human verifies outcomes.
6. **Level 5 — dark factory**
   - no steering wheel; high autonomy over full codebase lifecycle.

Transcript anchors:
- levels walkthrough ([00:03:00]–[00:07:40])
- level-3 reliability emphasis ([00:05:56], [00:30:34]–[00:30:46])

---

## Important reliability insight
The stream repeatedly stresses that **maximum autonomy ≠ maximum reliability**. 

Key practical stance:
- If you optimize for production reliability now, stay near **Level 3** (human review gates).
- Push toward Level 4/5 only with strong harnessing and validation loops.

Transcript anchors:
- reliability caveat on dark factory ([00:01:21]–[00:01:27])
- level-3 recommended for reliability ([00:05:56]–[00:06:03], [00:30:34]–[00:30:46])
- explicit human-in-loop risk control ([00:33:09]–[00:33:17], [02:04:51])

---

## Architecture pattern shown in the live build

The presenter builds a multi-workflow harness around Archon:
- issue triage workflow
- implementation workflow
- validation workflow
- PR review/merge flow
- release/operational handling

Guardrail pattern highlighted:
- separate validator/reviewer workflow checks coder output
- avoid single-agent self-approval loops (sycophancy risk)

Transcript anchors:
- workflow-building intent ([00:10:13]–[00:10:22])
- validation-before-merge framing ([00:15:26]–[00:15:30])
- sycophancy/peer-review mitigation ([02:12:24]–[02:12:50])

---

## Anti-patterns called out implicitly
- trusting unattended runs without robust validation
- collapsing reviewer and implementer into one unchallenged agent
- over-optimizing for “hands-off” before reliability and standards are ready

---

## Practical translation for us (BearingBrain)

Recommended target mode now: **Level 3.5**
- AI handles most implementation and repetitive flows.
- Human gate remains for:
  - API/auth changes
  - payment and webhook flows
  - production merges and deploys

Required guardrails:
1. eval harness with pass/fail + latency thresholds
2. validator agent/workflow separate from coder
3. merge conditions tied to objective checks
4. failure logs + postmortems on every incident

---

## One-sprint drill from this video

**Drill:** implement a “triage -> code -> validate -> PR-ready” loop for one narrow BearingBrain issue type.

Done criteria:
- issue is auto-classified and scoped
- implementation proposal generated
- validator catches at least one deliberate defect
- PR summary includes rationale + risk + test evidence

This converts dark-factory theory into measurable engineering signal.
