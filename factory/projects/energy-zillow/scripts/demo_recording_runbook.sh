#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="8099"
ZIPS="01730,02667,05486,06525"
SOLAR_MODEL="pvwatts-cell-blend"
SKIP_REGRESSION="0"
DRY_RUN="0"

usage() {
  cat <<'EOF'
Usage: ./scripts/demo_recording_runbook.sh [options]

Options:
  --port <port>              API port (default: 8099)
  --zips <csv>               ZIP list for regression (default: 01730,02667,05486,06525)
  --solar-model <model>      proxy | pvwatts-cell-blend (default: pvwatts-cell-blend)
  --skip-regression          Skip multi-zip regression; run local score+eval only
  --dry-run                  Run prep only (no uvicorn start)
  -h, --help                 Show help

Examples:
  ./scripts/demo_recording_runbook.sh
  ./scripts/demo_recording_runbook.sh --dry-run
  ./scripts/demo_recording_runbook.sh --port 8100 --zips 01730,02667,05486,06525
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port)
      PORT="$2"; shift 2 ;;
    --zips)
      ZIPS="$2"; shift 2 ;;
    --solar-model)
      SOLAR_MODEL="$2"; shift 2 ;;
    --skip-regression)
      SKIP_REGRESSION="1"; shift ;;
    --dry-run)
      DRY_RUN="1"; shift ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "Unknown arg: $1" >&2
      usage
      exit 2 ;;
  esac
done

cd "$ROOT"

echo "[runbook] root=$ROOT"
if [[ -f .env ]]; then
  echo "[runbook] loading .env"
  set -a
  # shellcheck source=/dev/null
  source .env
  set +a
else
  echo "[runbook] .env not found; continuing with current env"
fi

if [[ "$SOLAR_MODEL" == "pvwatts-cell-blend" ]]; then
  echo "[runbook] checking PVWatts/NSRDB key health"
  if ! python3 scripts/check_pvwatts_key.py; then
    echo "[runbook] key check failed; falling back to proxy model for reliability"
    SOLAR_MODEL="proxy"
  fi
fi

if [[ "$SKIP_REGRESSION" == "0" ]]; then
  echo "[runbook] running multi-zip regression for demo baseline"
  python3 eval/run_multi_zip_regression.py --zips "$ZIPS" --min-records-per-zip 80 --solar-model "$SOLAR_MODEL"
else
  echo "[runbook] skip regression enabled; refreshing trigger layers then running score+eval"
  python3 scripts/fetch_nws_storm_triggers.py --sites-csv data/processed/sites.csv --output data/raw/property_triggers_external.csv
  if python3 scripts/fetch_eversource_outage_feed.py --output data/raw/state_outage_feed.csv; then
    python3 scripts/project_state_outage_triggers.py --sites-csv data/processed/sites.csv --external data/raw/property_triggers_external.csv --state-feed data/raw/state_outage_feed.csv --output data/raw/property_triggers_external.csv
  else
    echo "[runbook] outage feed unavailable; continuing with storm+flood lanes"
  fi
  python3 scripts/project_nws_flood_triggers.py --sites-csv data/processed/sites.csv --external data/raw/property_triggers_external.csv --output data/raw/property_triggers_external.csv
  python3 scripts/project_census_equipment_age_triggers.py --sites-csv data/processed/sites.csv --external data/raw/property_triggers_external.csv --output data/raw/property_triggers_external.csv
  python3 scripts/merge_property_triggers.py --sites-csv data/processed/sites.csv --external data/raw/property_triggers_external.csv --output data/processed/property_triggers.csv
  python3 scripts/score_sites.py --solar-model "$SOLAR_MODEL"
  python3 eval/run_eval.py --require-min-zips 2 --min-rows-per-zip 80 --min-zip-stability 0.90
fi

python3 scripts/export_openapi.py >/dev/null

echo "[runbook] prep complete"
echo "[runbook] model=$SOLAR_MODEL"
echo "[runbook] eval: artifacts/eval-summary.md"
echo "[runbook] recording checklist: artifacts/demo-recording-checklist.md"
echo "[runbook] open: http://127.0.0.1:${PORT}/"

if [[ "$DRY_RUN" == "1" ]]; then
  exit 0
fi

exec python3 -m uvicorn backend.api.app:app --host 127.0.0.1 --port "$PORT"
