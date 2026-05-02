# Task for crew-planner

Create a task breakdown for implementing this request.

## Request

Stabilize rico-v3 immediately: diagnose PM2 rapid restart loop, find root cause from logs/config/env, apply minimal safe fix, restart process, and verify stable uptime with no crash loop. Prioritize getting trading bot running in paper mode; do not change strategy logic beyond startup stability.

You must follow this sequence strictly:
1) Understand the request
2) Review relevant code/docs/reference resources
3) Produce sequential implementation steps
4) Produce a parallel task graph

Return output in this exact section order and headings:
## 1. PRD Understanding Summary
## 2. Relevant Code/Docs/Resources Reviewed
## 3. Sequential Implementation Steps
## 4. Parallelized Task Graph

In section 4, include both:
- markdown task breakdown
- a `tasks-json` fenced block with task objects containing title, description, and dependsOn.