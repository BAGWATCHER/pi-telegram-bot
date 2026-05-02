# One-Command Demo Recording Runbook

## Start demo-ready environment (single command)

```bash
cd /home/ubuntu/pi-telegram-bot/factory/projects/energy-zillow
./scripts/demo_recording_runbook.sh
```

What it does:
1. Loads `.env`
2. Checks PVWatts/NSRDB key health (falls back to proxy if unavailable)
3. Runs multi-ZIP regression (`78701,78702`) with chosen solar model
4. Regenerates OpenAPI
5. Starts API at `http://127.0.0.1:8099/` for recording

## Auto-record a demo video (no manual clicks)

```bash
cd /home/ubuntu/pi-telegram-bot/factory/projects/energy-zillow
python3 scripts/record_demo.py --output artifacts/demo-recording-auto.mp4
```

- Produces:
  - `artifacts/demo-recording-auto.mp4`
  - `artifacts/demo-recording-auto.webm`
- Script runs key checks + regression prep by default, then records with Playwright.

## Dry run (prep only, no server start)

```bash
./scripts/demo_recording_runbook.sh --dry-run
```

## After recording: close EZ-009

Save your recording as `artifacts/demo-recording-v1.mp4`, then run:

```bash
python3 scripts/close_ez009.py --recording artifacts/demo-recording-v1.mp4
```

This will:
- set `EZ-009` status to `done-local` in `queue.yaml`
- update queue timestamp
- append close note to `decision-log.md`
