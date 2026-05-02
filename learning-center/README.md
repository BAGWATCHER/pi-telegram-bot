# Learning Center

Shared learning and research workspace for:
- Mr Chow (agent memory + operational context)
- Adam (human operator)
- Future agents and learners

This project is designed to prevent context loss while researching and training.

## Goals

1. Keep research persistent and searchable.
2. Convert raw links into structured training assets.
3. Make onboarding easy for new agents/people.
4. Build reusable curricula and lesson plans.

## Structure

- `index.md` — top-level map and active tracks
- `data/sources.ndjson` — structured source registry
- `data/notes.ndjson` — distilled insights, drills, and decisions
- `tracks/<track>/` — track-specific curriculum and generated context
- `shared/` — templates and standards

## Core Workflow

1. Add source
   - `npm run learn:add-source -- --track gauntlet-ai --type article --title "..." --url "..."`
2. Add distilled note
   - `npm run learn:add-note -- --track gauntlet-ai --type insight --text "..."`
3. Rebuild context bundle
   - `npm run learn:build-context -- --track gauntlet-ai`
4. Check status
   - `npm run learn:status`

## Design Rules

- Source first, opinion second.
- Every note should map to a source or direct experiment.
- Keep notes concise and operational.
- Prefer repeatable drills over generic theory.

## Current active track

- `gauntlet-ai` — AI-first engineering training path and curriculum mirror.
