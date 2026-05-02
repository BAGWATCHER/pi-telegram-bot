# Chow-only Second Brain (Cole-style adaptation)

This is an additive scaffold inspired by Cole's second-brain architecture, adapted for **Mr Chow only**.

## Scope boundaries
- ✅ Chow memory and workflow only
- ❌ No Jose repointing, renaming, or prompt coupling

## File layout
For a chat id (default `-1003665370879`):

- `memory/<chatId>/second-brain/SOUL.md`
- `memory/<chatId>/second-brain/USER.md`
- `memory/<chatId>/second-brain/MEMORY.md`
- `memory/<chatId>/second-brain/daily/YYYY-MM-DD.md`
- `memory/<chatId>/second-brain/context.md` (generated)

Protected system-of-record still remains:
- `memory/<chatId>/identity.md`
- `memory/<chatId>/summaries.md`

## Commands

```bash
# 1) Create scaffold files if missing
npm run brain:bootstrap

# 2) Sync SOUL/USER/MEMORY from identity+summaries and append daily log
npm run brain:reflect

# 3) Build combined context bundle (SOUL+USER+MEMORY+recent daily)
npm run brain:context
```

Optional with explicit chat id:

```bash
npm run brain:bootstrap -- --chat -1003665370879
npm run brain:reflect -- --chat -1003665370879 --note "Post-deploy sync"
npm run brain:context -- --chat -1003665370879 --days 5
```

## Runtime behavior (Phase 2)
- For the Chow primary chat (`-1003665370879`), `buildSystemPrompt()` now injects `second-brain/context.md` (token-capped).
- On session auto-rotation, memory summarization now triggers a Chow second-brain sync (`SOUL/USER/MEMORY/context + daily log`).

## Suggested cadence
- Run `brain:reflect` after meaningful architecture/deploy decisions.
- Run `brain:context` before major planning sessions.

## Why this helps
- Preserves Cole-style structure (SOUL/USER/MEMORY/daily)
- Keeps existing Chow memory system untouched and safe
- Gives readable operational logs and quick context bundle generation
