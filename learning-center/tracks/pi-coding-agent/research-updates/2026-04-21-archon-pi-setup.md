# Archon + Pi setup (local VM)

- Date: 2026-04-21
- Scope: `/home/ubuntu/pi-telegram-bot`
- Goal: enable Pi + plannotator + Archon workflow wiring from shared links

## Completed

1. Installed Archon CLI binary
   - Command used: `curl -fsSL https://archon.diy/install | bash`
   - Version: `0.3.6`
   - Note: released binary build (`git commit 59cda08e`) still rejects `provider: pi` in workflow validation.

2. Installed Bun + Archon source runner for Pi-capable workflow parsing
   - Bun installed: `~/.bun/bin/bun` (`1.3.13`)
   - Archon source cloned at: `/home/ubuntu/Archon` (`git commit 5ed38dc7`)
   - Dependencies installed with: `bun install`
   - Wrapper added: `/home/ubuntu/pi-telegram-bot/scripts/archon-pi.sh`
   - Wrapper calls source CLI (`bun run cli ...`) which validates `provider: pi` correctly

3. Installed plannotator Pi extension (project-local)
   - Command used: `npx pi install npm:@plannotator/pi-extension -l`
   - Installed under: `.pi/npm/node_modules/@plannotator/pi-extension`
   - Registered in: `.pi/settings.json`

4. Added repo-level Archon config
   - File: `.archon/config.yaml`
   - Includes:
     - `assistant: pi`
     - `assistants.pi.extensionFlags.plan: true`
     - `assistants.pi.env.PLANNOTATOR_REMOTE: "1"`
     - Claude/Codex defaults retained for mixed-provider workflows

5. Added plannotator PIV workflow from link
   - Source: `coleam00/GitHubIssueTriager/.archon/workflows/archon-plannotator-piv.yaml`
   - Destination: `.archon/workflows/archon-plannotator-piv.yaml`

## Important runtime note

Archon CLI requires running inside a git repository.
This repo currently is **not** initialized as git, so Archon commands here will fail until either:

- `git init` is run in this repo, or
- Archon is run with `--cwd` pointing at a git repo.

## Smoke commands (after git repo is available)

```bash
# Pi-capable source runner
/home/ubuntu/pi-telegram-bot/scripts/archon-pi.sh workflow list --cwd /path/to/git/repo
/home/ubuntu/pi-telegram-bot/scripts/archon-pi.sh validate workflows archon-plannotator-piv --cwd /path/to/git/repo
/home/ubuntu/pi-telegram-bot/scripts/archon-pi.sh workflow run archon-plannotator-piv "Add X feature" --cwd /path/to/git/repo
```
