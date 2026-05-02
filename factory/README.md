# Multi-Project Dark Factory (Chow)

Purpose: one shared factory control plane for projects we actively operate, with per-project safety gates.

## Design
- **Factory core (shared)**
  - task intake
  - run queue
  - observability artifacts
  - common policy checks
- **Project adapters (per project)**
  - repo path
  - build/eval/test commands
  - deploy command
  - risk gates (human approval required/not)

## Why this structure
- avoids context bleed
- avoids secrets/policy mistakes across repos
- keeps one operator workflow while preserving project-specific standards

## Current managed projects
See `projects.manifest.json`.

## Files
- `projects.manifest.json` — project adapters + commands + risk profile
- `policies.json` — shared safety and merge/deploy policy
- `queues/pending.ndjson` — intake queue
- `templates/task.md` — standard task artifact

## Next implementation steps
1. Add queue runner (`factory:run`) with per-project command execution.
2. Add artifact writer (`factory/runs/YYYY-MM-DD/...`).
3. Add approval gate for high-risk deploys.
4. Add eval pass thresholds per project.
