# Agent Onboarding (Learning Center)

## Mission
Preserve research context and convert it into reusable training modules.

## Required behavior

1. Never add unverified claims without source tagging.
2. Add source entries before writing major conclusions.
3. Add distilled notes after every meaningful research pass.
4. Rebuild context bundle before handoff.
5. When a new external tool is identified, add it to `learning-center/shared/agent-build-materials-library.md` (+ structured entry in `learning-center/data/agent-build-materials.json`).

## Minimal handoff checklist

- [ ] `npm run learn:status`
- [ ] `npm run learn:build-context -- --track <track>`
- [ ] Updated `tracks/<track>/curriculum-map.md` if scope changed
- [ ] New tools/resources added to agent materials library (if discovered)
- [ ] At least 1 drill note and 1 open-question note captured
