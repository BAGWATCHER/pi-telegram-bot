# Question Bank — AI Dark Factory Session

Use these for mock interviews, architecture reviews, and build-postmortems.

## Conceptual questions
1. What is a software “dark factory,” and what lifecycle stages does it automate? ([00:02:15]–[00:02:20])
2. Why does the presenter still recommend level-3 behavior for reliability? ([00:05:56], [00:30:34]–[00:30:46])
3. Where is the boundary between useful autonomy and unsafe autonomy in production systems?

## Architecture questions
4. How would you decompose dark-factory workflows (triage, implementation, validation, review, release)? ([00:10:13]–[00:10:22])
5. Why should validator/reviewer be separate from implementer? ([00:15:26]–[00:15:30], [02:12:24]–[02:12:50])
6. How do you prevent agent self-confirmation/sycophancy in multi-agent loops? ([02:12:24]–[02:12:38])

## Reliability & QA questions
7. What quality gates are mandatory before auto-merge?
8. What should force human-in-the-loop intervention? ([00:33:09]–[00:33:17], [02:04:51])
9. If unattended runs look successful but prod regressions appear, what telemetry do you inspect first?
10. How do you design rollback when autonomous workflows push bad changes?

## Operations questions
11. What logs and traces must every autonomous workflow emit?
12. How do you evaluate end-to-end dark-factory performance weekly (throughput, defect rate, lead time)?
13. What is your failure budget for autonomous PRs before reducing autonomy level?

## BearingBrain-specific application prompts
14. Which BearingBrain endpoints are safe for high autonomy vs mandatory human gate?
15. How would you add a “dark factory mode” without risking checkout/auth reliability?
16. What does “Level 3.5” look like in our stack today, concretely?

## Red-team prompts
17. Your coding agent repeatedly passes its own work. How do you break the loop?
18. A validator agent is too strict and blocks velocity. How do you calibrate?
19. A release agent merged a compliant but harmful change. Which missing gate allowed it?
20. If you had to choose one: more autonomy or less incident risk this quarter, which and why?
