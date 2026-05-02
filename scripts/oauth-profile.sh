#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="${PI_AUTH_PROFILES_DIR:-$HOME/.pi/agent/auth-profiles}"
INDEX_JSON="$BASE_DIR/index.json"
ACTIVE_LINK="$BASE_DIR/active"
DEFAULT_AUTH="${PI_AUTH_PATH:-$HOME/.pi/agent/auth.json}"

mkdir -p "$BASE_DIR"

init_index() {
  if [[ ! -f "$INDEX_JSON" ]]; then
    cat > "$INDEX_JSON" <<'JSON'
{
  "profiles": {},
  "lastUsed": null
}
JSON
  fi
}

usage() {
  cat <<'TXT'
Usage:
  oauth-profile.sh save <name> [authPath]
  oauth-profile.sh use <name> [authPath] [--restart "chow jose"]
  oauth-profile.sh list
  oauth-profile.sh status [name]
  oauth-profile.sh active
  oauth-profile.sh remove <name>

Examples:
  scripts/oauth-profile.sh save codex-main
  scripts/oauth-profile.sh save codex-backup ~/.pi/agent/auth.json
  scripts/oauth-profile.sh use codex-main ~/.pi/agent/auth.json --restart "chow jose"
  scripts/oauth-profile.sh status codex-main
TXT
}

require_file() {
  local p="$1"
  [[ -f "$p" ]] || { echo "Missing file: $p" >&2; exit 1; }
}

sha256_file() {
  sha256sum "$1" | awk '{print $1}'
}

json_get_profile_path() {
  python3 - "$INDEX_JSON" "$1" <<'PY'
import json,sys
idx,name=sys.argv[1],sys.argv[2]
data=json.load(open(idx))
prof=data.get('profiles',{}).get(name)
print(prof.get('path') if prof else '')
PY
}

json_upsert_profile() {
  python3 - "$INDEX_JSON" "$1" "$2" "$3" "$4" <<'PY'
import json,sys,time
idx,name,path,sha,src=sys.argv[1:6]
data=json.load(open(idx))
profiles=data.setdefault('profiles',{})
profiles[name]={
  'path': path,
  'sha256': sha,
  'source': src,
  'savedAt': int(time.time())
}
json.dump(data,open(idx,'w'),indent=2)
print('ok')
PY
}

json_set_last_used() {
  python3 - "$INDEX_JSON" "$1" <<'PY'
import json,sys,time
idx,name=sys.argv[1],sys.argv[2]
data=json.load(open(idx))
data['lastUsed']={'name':name,'at':int(time.time())}
json.dump(data,open(idx,'w'),indent=2)
print('ok')
PY
}

json_remove_profile() {
  python3 - "$INDEX_JSON" "$1" <<'PY'
import json,sys
idx,name=sys.argv[1],sys.argv[2]
data=json.load(open(idx))
profiles=data.setdefault('profiles',{})
profiles.pop(name,None)
json.dump(data,open(idx,'w'),indent=2)
print('ok')
PY
}

cmd_save() {
  local name="$1"; shift || true
  local src="${1:-$DEFAULT_AUTH}"
  require_file "$src"
  init_index

  local out="$BASE_DIR/${name}.json"
  cp "$src" "$out"
  chmod 600 "$out"
  local sha
  sha="$(sha256_file "$out")"
  json_upsert_profile "$name" "$out" "$sha" "$src" >/dev/null
  echo "Saved profile '$name' -> $out"
}

cmd_use() {
  local name="$1"; shift || true
  local target="$DEFAULT_AUTH"
  local restart_apps=""

  if [[ $# -gt 0 && "$1" != "--restart" ]]; then
    target="$1"
    shift || true
  fi
  if [[ $# -gt 0 && "$1" == "--restart" ]]; then
    shift || true
    restart_apps="${1:-}"
  fi

  init_index
  local profile_path
  profile_path="$(json_get_profile_path "$name")"
  [[ -n "$profile_path" ]] || { echo "Unknown profile: $name" >&2; exit 1; }
  require_file "$profile_path"

  mkdir -p "$(dirname "$target")"
  cp "$profile_path" "$target"
  chmod 600 "$target"
  ln -sfn "$profile_path" "$ACTIVE_LINK"
  json_set_last_used "$name" >/dev/null

  echo "Activated profile '$name' -> $target"
  if [[ -n "$restart_apps" ]]; then
    echo "Restarting PM2 apps: $restart_apps"
    pm2 restart $restart_apps --update-env
  fi
}

cmd_list() {
  init_index
  python3 - "$INDEX_JSON" <<'PY'
import json,sys,os,datetime
idx=sys.argv[1]
data=json.load(open(idx))
profiles=data.get('profiles',{})
if not profiles:
    print('No saved auth profiles.')
    raise SystemExit
for name,p in sorted(profiles.items()):
    ts=p.get('savedAt')
    when=datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S UTC') if ts else 'unknown'
    print(f"- {name}: {p.get('path')} (saved {when})")
lu=data.get('lastUsed') or {}
if lu.get('name'):
    ts=lu.get('at')
    when=datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S UTC') if ts else 'unknown'
    print(f"lastUsed: {lu.get('name')} @ {when}")
PY
}

cmd_status() {
  init_index
  local name="${1:-}"
  local target=""

  if [[ -n "$name" ]]; then
    target="$(json_get_profile_path "$name")"
    [[ -n "$target" ]] || { echo "Unknown profile: $name" >&2; exit 1; }
  elif [[ -L "$ACTIVE_LINK" ]]; then
    target="$(readlink -f "$ACTIVE_LINK")"
  else
    target="$DEFAULT_AUTH"
  fi

  require_file "$target"
  python3 - "$target" <<'PY'
import json,sys,time,datetime
p=sys.argv[1]
d=json.load(open(p))
providers=['openai-codex','anthropic','github-copilot','google-antigravity','google-gemini-cli']
print(f'file: {p}')
now=time.time()*1000
for k in providers:
    t=d.get(k)
    if not isinstance(t,dict):
        continue
    exp=t.get('expires')
    left='n/a'
    if isinstance(exp,(int,float)):
        mins=int((exp-now)/60000)
        left=f'{mins}m'
    print(f'- {k}: type={t.get("type")}, expiresIn={left}')
PY
}

cmd_active() {
  if [[ -L "$ACTIVE_LINK" ]]; then
    echo "$(readlink -f "$ACTIVE_LINK")"
  else
    echo "(none)"
  fi
}

cmd_remove() {
  local name="$1"
  init_index
  local path
  path="$(json_get_profile_path "$name")"
  [[ -n "$path" ]] || { echo "Unknown profile: $name" >&2; exit 1; }
  rm -f "$path"
  json_remove_profile "$name" >/dev/null
  echo "Removed profile '$name'"
}

main() {
  local cmd="${1:-}"
  [[ -n "$cmd" ]] || { usage; exit 1; }
  shift || true

  case "$cmd" in
    save) [[ $# -ge 1 ]] || { usage; exit 1; }; cmd_save "$@" ;;
    use) [[ $# -ge 1 ]] || { usage; exit 1; }; cmd_use "$@" ;;
    list) cmd_list ;;
    status) cmd_status "$@" ;;
    active) cmd_active ;;
    remove) [[ $# -ge 1 ]] || { usage; exit 1; }; cmd_remove "$1" ;;
    *) usage; exit 1 ;;
  esac
}

main "$@"
