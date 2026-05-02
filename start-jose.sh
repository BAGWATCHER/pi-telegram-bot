#!/bin/bash
set -euo pipefail

load_env_file() {
  local file="$1"
  [ -f "$file" ] || return 0
  set -a
  # shellcheck disable=SC1090
  source "$file"
  set +a
}

overlay_nonempty_env_file() {
  local file="$1"
  [ -f "$file" ] || return 0
  python3 - "$file" <<'PY2'
import shlex
import sys
from pathlib import Path

path = Path(sys.argv[1])
for raw in path.read_text().splitlines():
    line = raw.strip()
    if not line or line.startswith('#') or '=' not in line:
        continue
    key, value = line.split('=', 1)
    key = key.strip()
    value = value.strip()
    if not value:
        continue
    try:
        parsed = shlex.split(value, comments=False, posix=True)
        value = parsed[0] if parsed else ''
    except Exception:
        value = value.strip('"').strip("'")
    if value == '':
        continue
    print(f'export {key}={shlex.quote(value)}')
PY2
}

ensure_pi_auth() {
  local target="$HOME/.pi/agent/auth.json"
  local source_auth="/home/adamnorm4wd/.pi/agent/auth.json"
  mkdir -p "$(dirname "$target")"

  if [ ! -s "$source_auth" ]; then
    echo "[jose] No source Pi auth found at $source_auth"
    return 0
  fi

  if [ ! -s "$target" ] || grep -Eq '^\{\s*\}$|^\[\s*\]$' "$target" 2>/dev/null; then
    install -m 600 "$source_auth" "$target"
    echo "[jose] Seeded Pi auth from $source_auth"
    return 0
  fi

  if ! cmp -s "$source_auth" "$target"; then
    install -m 600 "$source_auth" "$target"
    echo "[jose] Refreshed Pi auth from $source_auth"
  fi
}

load_env_file /home/ubuntu/pi-telegram-bot/.env
eval "$(overlay_nonempty_env_file /home/ubuntu/pi-telegram-bot/.env.jose)"
ensure_pi_auth

export PATH=/home/ubuntu/.npm-global/bin:/usr/local/bin:/usr/bin:/bin:$PATH
export NODE_PATH=/home/ubuntu/.npm-global/lib/node_modules

cd /home/ubuntu/pi-telegram-bot
exec npx tsx src/bot.ts
