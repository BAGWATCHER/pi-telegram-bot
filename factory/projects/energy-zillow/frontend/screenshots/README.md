# Frontend Screenshots

Manual capture pending.

Expected captures for EZ-006:
1. Full map view with H3 heatmap loaded.
2. Hex selected with ranked address list visible.
3. Site detail card with recommendation + confidence + reasons.

Run locally:
```bash
python3 -m uvicorn backend.api.app:app --host 127.0.0.1 --port 8099 --app-dir /home/ubuntu/pi-telegram-bot/factory/projects/energy-zillow
# open http://127.0.0.1:8099
```
