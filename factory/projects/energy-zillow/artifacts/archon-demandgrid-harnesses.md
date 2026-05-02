# DemandGrid Archon harnesses (Pi)

Date: 2026-04-21

## Workflows added

These workflows are registered at:
- `/home/ubuntu/pi-telegram-bot/.archon/workflows/demandgrid-eval-gate.yaml`
- `/home/ubuntu/pi-telegram-bot/.archon/workflows/demandgrid-live-smoke.yaml`
- `/home/ubuntu/pi-telegram-bot/.archon/workflows/demandgrid-lane-context.yaml`
- `/home/ubuntu/pi-telegram-bot/.archon/workflows/demandgrid-lane-implement.yaml`

## Purpose

1. `demandgrid-eval-gate`
   - Runs `python3 eval/run_eval.py`
   - Captures logs to `artifacts/archon-eval-gate.log`
   - Writes summary JSON to `artifacts/archon-eval-gate.json`
   - Fails the workflow if final eval status is not `PASS`

2. `demandgrid-live-smoke`
   - Hits key API endpoints on demo stack
   - Writes `artifacts/archon-live-smoke.{json,md}`
   - Fails if any required endpoint check fails

3. `demandgrid-lane-context`
   - Extracts lane details from `queue.yaml` for a lane id (e.g. `EZ-022`)
   - Writes `artifacts/archon-lane-context-{LANE_ID}.{json,md}`

4. `demandgrid-lane-implement` (approval-gated)
   - Builds lane context + targeted patch plan
   - Pauses on approval gate before code changes
   - On approval executes implementation node then eval + live-smoke gates
   - Writes `artifacts/archon-lane-{plan,implementation,eval,live-smoke,final-summary}*`

## Verified runs

- `demandgrid-lane-context "EZ-022"` → PASS
- `demandgrid-eval-gate "nightly"` → PASS
- `demandgrid-live-smoke "http://127.0.0.1:8099"` → PASS
- `demandgrid-lane-implement "EZ-022 http://127.0.0.1:8099"` → reaches approval gate (run `5a8468da3d52931b7fca42c32ad0ca27`)

## Usage

```bash
/home/ubuntu/pi-telegram-bot/scripts/archon-pi.sh workflow run demandgrid-lane-context "EZ-022" --cwd /home/ubuntu/pi-telegram-bot --no-worktree
/home/ubuntu/pi-telegram-bot/scripts/archon-pi.sh workflow run demandgrid-eval-gate "nightly" --cwd /home/ubuntu/pi-telegram-bot --no-worktree
/home/ubuntu/pi-telegram-bot/scripts/archon-pi.sh workflow run demandgrid-live-smoke "http://127.0.0.1:8099" --cwd /home/ubuntu/pi-telegram-bot --no-worktree
/home/ubuntu/pi-telegram-bot/scripts/archon-pi.sh workflow run demandgrid-lane-implement "EZ-022 http://127.0.0.1:8099" --cwd /home/ubuntu/pi-telegram-bot --no-worktree

# approval controls for active lane implement run
/home/ubuntu/pi-telegram-bot/scripts/archon-pi.sh workflow approve 5a8468da3d52931b7fca42c32ad0ca27
/home/ubuntu/pi-telegram-bot/scripts/archon-pi.sh workflow reject 5a8468da3d52931b7fca42c32ad0ca27 "revise plan"
```
