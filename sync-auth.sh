#!/bin/bash
# Sync pi auth from Mac (via reverse tunnel), restart bots only if auth changed or token expiring
set -a
source /home/ubuntu/pi-telegram-bot/.env
set +a

LOG=~/pi-telegram-bot/auth-sync.log
AUTH=~/.pi/agent/auth.json
CODEX_AUTH=~/.codex/auth.json
PINNED_DIR="${CHOW_PINNED_AUTH_PROFILE_DIR:-}"
if [ -n "$PINNED_DIR" ] && [ -f "$PINNED_DIR/codex-auth.json" ] && [ -f "$PINNED_DIR/pi-auth.json" ]; then
  cp "$PINNED_DIR/codex-auth.json" "$CODEX_AUTH"
  cp "$PINNED_DIR/pi-auth.json" "$AUTH"
  echo "[$(date)] applied pinned chow auth profile from $PINNED_DIR" >> "$LOG"
elif python3 ~/pi-telegram-bot/scripts/rebuild_pi_auth_from_codex.py "$CODEX_AUTH" "$AUTH" >/dev/null 2>&1; then
  echo "[$(date)] rebuilt local pi auth from ~/.codex/auth.json" >> "$LOG"
else
  echo "[$(date)] skipped local pi auth rebuild (missing/invalid ~/.codex/auth.json)" >> "$LOG"
fi

if false && ssh -p 2222 -i ~/.ssh/chow_mac_key -o BatchMode=yes -o ConnectTimeout=5 adamn@localhost true 2>/dev/null; then
  OLD_SUM=$(md5sum "$AUTH" 2>/dev/null | cut -d" " -f1)

  if scp -P 2222 -i ~/.ssh/chow_mac_key -o StrictHostKeyChecking=no \
    adamn@localhost:~/.pi/agent/auth.json "$AUTH" 2>/dev/null; then

    NEW_SUM=$(md5sum "$AUTH" 2>/dev/null | cut -d" " -f1)

    # Check if any token expires within 2 hours
    EXPIRING=$(python3 -c "
import json, time
now_ms = time.time() * 1000
data = json.load(open(\"$AUTH\"))
tokens = data if isinstance(data, list) else [data]
soon = any((t.get(\"expires\",0) - now_ms) < 7200000 for t in tokens)
print(\"yes\" if soon else \"no\")
" 2>/dev/null)

    if [ "$OLD_SUM" != "$NEW_SUM" ]; then
      echo "[$(date)] auth updated — restarting bots" >> "$LOG"
      pkill -9 -f "src/bot.ts" 2>/dev/null
      pkill -9 -f "src/web-chat.ts" 2>/dev/null
      sleep 2
      pm2 restart chow chow-web --update-env 2>/dev/null
      echo "[$(date)] bots restarted" >> "$LOG"
    elif [ "$EXPIRING" = "yes" ]; then
      echo "[$(date)] token expiring soon — restarting bots anyway" >> "$LOG"
      pkill -9 -f "src/bot.ts" 2>/dev/null
      pkill -9 -f "src/web-chat.ts" 2>/dev/null
      sleep 2
      pm2 restart chow chow-web --update-env 2>/dev/null
      echo "[$(date)] bots restarted (expiry)" >> "$LOG"
    else
      echo "[$(date)] auth unchanged, no restart" >> "$LOG"
    fi
  else
    echo "[$(date)] scp failed" >> "$LOG"
  fi
else
  echo "[$(date)] Mac tunnel down, skipping" >> "$LOG"
fi

# Push auth to Dad's VM
SCP_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5"
scp $SCP_OPTS -i ~/clawd/ssh/john-assistant \
  ~/.pi/agent/auth.json ubuntu@18.117.162.164:~/.pi/agent/auth.json 2>/dev/null \
  && ssh $SCP_OPTS -i ~/clawd/ssh/john-assistant ubuntu@18.117.162.164 \
     "pm2 restart john tolerance 2>/dev/null || true" \
  || echo "[sync] Dad VM unreachable"

# Push auth to Anna's VM
scp $SCP_OPTS -i ~/.ssh/annasvm.pem \
  ~/.pi/agent/auth.json ec2-user@3.17.57.39:~/.pi/agent/auth.json 2>/dev/null \
  && ssh $SCP_OPTS -i ~/.ssh/annasvm.pem ec2-user@3.17.57.39 \
     "pm2 restart anna 2>/dev/null || true" \
  || echo "[sync] Anna VM unreachable"

# Push auth to AWS Chow VM
scp $SCP_OPTS ~/.pi/agent/auth.json aws-chow:~/.pi/agent/auth.json 2>/dev/null   && ssh $SCP_OPTS aws-chow      "pm2 restart chow chow-web --update-env 2>/dev/null || pm2 restart chow --update-env 2>/dev/null || true"   || echo "[sync] AWS Chow VM unreachable"
