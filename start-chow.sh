#!/bin/bash
set -a
source /home/ubuntu/pi-telegram-bot/.env
set +a

export PATH=/home/ubuntu/.npm-global/bin:/usr/local/bin:/usr/bin:/bin:$PATH
export NODE_PATH=/home/ubuntu/.npm-global/lib/node_modules
export CHOW_PI_PROVIDER="${CHOW_PI_PROVIDER:-openai-codex}"
export CHOW_PI_MODEL="${CHOW_PI_MODEL:-gpt-5.5}"
export CHOW_PI_FALLBACK_MODELS="${CHOW_PI_FALLBACK_MODELS:-openai-codex/gpt-5.3-codex,openai-codex/gpt-5.4-mini,google/gemma-4-31b-it,google/gemini-2.5-flash-lite}"

PINNED_DIR="${CHOW_PINNED_AUTH_PROFILE_DIR:-}"
if [ -n "$PINNED_DIR" ] && [ -f "$PINNED_DIR/codex-auth.json" ] && [ -f "$PINNED_DIR/pi-auth.json" ]; then
  cp "$PINNED_DIR/codex-auth.json" /home/ubuntu/.codex/auth.json
  cp "$PINNED_DIR/pi-auth.json" /home/ubuntu/.pi/agent/auth.json
else
  python3 /home/ubuntu/pi-telegram-bot/scripts/rebuild_pi_auth_from_codex.py >/dev/null 2>&1 || true
fi

cd /home/ubuntu/pi-telegram-bot
exec npx tsx src/bot.ts
