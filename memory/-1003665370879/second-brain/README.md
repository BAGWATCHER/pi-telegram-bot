# Chow Second Brain (Cole-style, adapted)

This is an additive, Chow-only memory layer inspired by Cole's setup.

## Files
- SOUL.md: operating identity and guardrails
- USER.md: user preferences and collaboration constraints
- MEMORY.md: long-lived distilled state
- daily/YYYY-MM-DD.md: rolling operational logs
- events.ndjson: structured event memory (phase 3)
- consolidated/YYYY-MM-DD.md: daily memory consolidation snapshots

## Commands
- Bootstrap: `npm run brain:bootstrap`
- Reflect sync: `npm run brain:reflect`
- Build context: `npm run brain:context`
- Consolidate: `npm run brain:consolidate -- --force`

## Chat ops (Chow primary chat only)
- `/brain peek [n]`
- `/brain search <query>`
- `/brain add <note>`
- `/brain status`
- `/brain consolidate`

## Safety
- Does not modify Jose settings
- Does not replace protected identity.md; it derives/syncs from it
