# Operations Log — Gauntlet AI Track

## 2026-04-15

- Bootstrapped Learning Center project scaffolding.
- Added structured source registry (`25` entries).
- Added distilled notes (`9` entries) with decisions/drills/questions.
- Generated first context bundle (`context.md`).
- Published curriculum map and training loop for agent/human reuse.
- Ingested and parsed full ASR transcript for Night School video `LWWy3M4iV3o` via Piped streams endpoint.
- Added video study artifacts: metadata, raw transcript, cleaned transcript, study guide, and question bank.
- Added source/note updates and regenerated context bundle.
- Performed additional source-backed deep-dive on Gauntlet teachings using core site pages (`/apply`, `/catalyst`, `/hire`, challenger-content), apply portal course bundle, and admissions API.
- Saved synthesis artifact: `research-updates/2026-04-15-gauntlet-teachings-deep-dive.md`.
- Initialized Day 01 Gauntlet sprint pack for BearingBrain reliability execution:
  - `sprints/day-01-bearingbrain-gauntlet-sprint.md`
  - `sprints/ARTIFACT-01-baseline-metrics.md`
  - `sprints/ARTIFACT-02-failure-log.md`
  - `sprints/ARTIFACT-03-patch-plan.md`
  - `sprints/ARTIFACT-04-post-patch-results.md`.
- Executed Day 01 baseline evals:
  - local passed (`http://127.0.0.1:3001`)
  - prod failed at `GET /api/v1/capabilities` with `522`.
- Shipped Day 01 patch: timing instrumentation for eval harness (`scripts/eval-agentic-v1.ts`) with median/p95/worst summary on success + failure paths.
- Added new video-study artifacts for `Xg0tNz9pICI` ("Building an AI Dark Factory"):
  - `video-studies/Xg0tNz9pICI/metadata.json`
  - `video-studies/Xg0tNz9pICI/transcript.raw.ttml`
  - `video-studies/Xg0tNz9pICI/transcript.clean.md`
  - `video-studies/Xg0tNz9pICI/study-guide.md`
  - `video-studies/Xg0tNz9pICI/question-bank.md`.
