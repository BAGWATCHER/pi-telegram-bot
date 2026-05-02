#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -f /home/ubuntu/.chow-secrets/stripe.env ]]; then
  set -a
  # shellcheck source=/dev/null
  source /home/ubuntu/.chow-secrets/stripe.env
  set +a
fi

exec python3 -m uvicorn backend.api.app:app --host 127.0.0.1 --port 8110
