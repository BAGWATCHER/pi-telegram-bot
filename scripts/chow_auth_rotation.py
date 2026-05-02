#!/usr/bin/env python3
import argparse
import hashlib
import json
import time
from pathlib import Path

HOME = Path.home()
PROFILE_ROOT = HOME / ".auth-profiles" / "chow"
STATE_PATH = PROFILE_ROOT / "rotation-state.json"
CODEX_AUTH = HOME / ".codex" / "auth.json"
PI_AUTH = HOME / ".pi" / "agent" / "auth.json"
FAILURE_COOLDOWN_SECS = 6 * 60 * 60


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def save_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def profile_dirs():
    if not PROFILE_ROOT.exists():
        return []
    dirs = [p for p in PROFILE_ROOT.iterdir() if p.is_dir() and p.name != "latest"]
    return sorted(dirs)


def decode_jwt_email(token: str) -> str:
    import base64

    if not token:
        return ""
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return ""
        payload = parts[1] + "=" * (-len(parts[1]) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload.encode()).decode())
        profile = data.get("https://api.openai.com/profile") or {}
        return str(profile.get("email") or data.get("email") or "").strip()
    except Exception:
        return ""


def codex_email(path: Path) -> str:
    raw = load_json(path, {})
    return decode_jwt_email(str(((raw.get("tokens") or {}).get("id_token")) or ""))


def read_profiles():
    out = []
    for d in profile_dirs():
        codex = d / "codex-auth.json"
        pi = d / "pi-auth.json"
        meta = load_json(d / "meta.json", {})
        if not codex.exists() or not pi.exists():
            continue
        codex_email_value = str(meta.get("codex_email") or codex_email(codex)).strip()
        pi_email_value = str(meta.get("pi_email") or "").strip()
        if not pi_email_value:
            pi_raw = load_json(pi, {})
            wrapped = pi_raw.get("openai-codex") or {}
            pi_email_value = decode_jwt_email(str(wrapped.get("access") or ""))
        out.append(
            {
                "name": d.name,
                "dir": d,
                "codex_path": codex,
                "pi_path": pi,
                "codex_sha": sha256_path(codex),
                "pi_sha": sha256_path(pi),
                "email": codex_email_value or pi_email_value,
                "codex_email": codex_email_value,
                "pi_email": pi_email_value,
                "paired": bool(codex_email_value and pi_email_value and codex_email_value == pi_email_value),
            }
        )
    return out


def slugify(text: str) -> str:
    import re

    text = re.sub(r"[^a-z0-9._-]+", "-", text.strip().lower())
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "profile"


def save_current_profile_snapshot(label: str | None = None):
    if not CODEX_AUTH.exists() or not PI_AUTH.exists():
        return None
    timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    email = codex_email(CODEX_AUTH) or "current"
    name = f"{timestamp}-{slugify(label or f'auto-{email}')}"
    dest = PROFILE_ROOT / name
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "codex-auth.json").write_bytes(CODEX_AUTH.read_bytes())
    (dest / "pi-auth.json").write_bytes(PI_AUTH.read_bytes())
    meta = {
        "saved_at_utc": timestamp,
        "label": label or "auto-current-snapshot",
        "codex_email": email,
        "pi_email": email,
        "codex_path": "codex-auth.json",
        "pi_path": "pi-auth.json",
    }
    save_json(dest / "meta.json", meta)
    return name


def load_state():
    return load_json(STATE_PATH, {"profiles": {}, "last_rotated_to": None})


def save_state(state):
    save_json(STATE_PATH, state)


def current_profile(profiles):
    if not CODEX_AUTH.exists():
        return None
    current_sha = sha256_path(CODEX_AUTH)
    for profile in profiles:
        if profile["codex_sha"] == current_sha:
            return profile
    return None


def ensure_current_profile_saved(profiles):
    if not CODEX_AUTH.exists():
        return profiles, None
    current = current_profile(profiles)
    if current:
        return profiles, current
    saved_name = save_current_profile_snapshot()
    profiles = read_profiles()
    current = current_profile(profiles)
    return profiles, current or {"name": saved_name, "email": codex_email(CODEX_AUTH)}


def activate_profile(profile):
    CODEX_AUTH.write_bytes(profile["codex_path"].read_bytes())
    PI_AUTH.parent.mkdir(parents=True, exist_ok=True)
    PI_AUTH.write_bytes(profile["pi_path"].read_bytes())


def choose_next_profile(profiles, state, current_name: str | None):
    if not profiles:
        return None
    eligible = [p for p in profiles if p.get("paired")]
    if not eligible:
        return None
    names = [p["name"] for p in eligible]
    start_idx = names.index(current_name) if current_name in names else -1
    now = time.time()
    current = None
    for p in eligible:
        if p["name"] == current_name:
            current = p
            break
    current_email = str((current or {}).get("email") or "").strip().lower()
    seen_emails = {current_email} if current_email else set()
    for offset in range(1, len(eligible) + 1):
        candidate = eligible[(start_idx + offset) % len(eligible)]
        status = (state.get("profiles") or {}).get(candidate["name"], {})
        cooldown_until = float(status.get("cooldown_until") or 0)
        if candidate["name"] == current_name:
            continue
        candidate_email = str(candidate.get("email") or "").strip().lower()
        if candidate_email and candidate_email in seen_emails:
            continue
        if cooldown_until > now:
            continue
        return candidate
    return None


def cmd_status():
    profiles = read_profiles()
    current = current_profile(profiles)
    state = load_state()
    payload = {
        "profile_count": len(profiles),
        "current": current["name"] if current else None,
        "current_email": current["email"] if current else (codex_email(CODEX_AUTH) if CODEX_AUTH.exists() else ""),
        "last_rotated_to": state.get("last_rotated_to"),
    }
    print(json.dumps(payload))


def cmd_rotate_next():
    profiles = read_profiles()
    profiles, current = ensure_current_profile_saved(profiles)
    state = load_state()
    candidate = choose_next_profile(profiles, state, current["name"] if current else None)
    if not candidate:
        print(json.dumps({"rotated": False, "reason": "no_alternate_profile_available"}))
        return
    activate_profile(candidate)
    state["last_rotated_to"] = {"name": candidate["name"], "at": int(time.time())}
    save_state(state)
    print(
        json.dumps(
            {
                "rotated": True,
                "from": current["name"] if current else None,
                "to": candidate["name"],
                "email": candidate["email"],
            }
        )
    )


def cmd_mark_current(result: str, reason: str):
    profiles = read_profiles()
    profiles, current = ensure_current_profile_saved(profiles)
    state = load_state()
    if not current:
        print(json.dumps({"ok": False, "reason": "current_profile_not_saved"}))
        return
    profile_state = (state.setdefault("profiles", {})).setdefault(current["name"], {})
    profile_state["last_result"] = result
    profile_state["last_reason"] = reason
    profile_state["last_at"] = int(time.time())
    if result == "failure":
        profile_state["failure_count"] = int(profile_state.get("failure_count") or 0) + 1
        profile_state["cooldown_until"] = int(time.time() + FAILURE_COOLDOWN_SECS)
    else:
        profile_state["success_count"] = int(profile_state.get("success_count") or 0) + 1
        profile_state["cooldown_until"] = 0
    save_state(state)
    print(json.dumps({"ok": True, "profile": current["name"], "result": result}))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    sub.add_parser("rotate-next")
    mark = sub.add_parser("mark-current")
    mark.add_argument("--result", choices=["success", "failure"], required=True)
    mark.add_argument("--reason", default="")
    args = parser.parse_args()

    if args.cmd == "status":
        cmd_status()
    elif args.cmd == "rotate-next":
        cmd_rotate_next()
    elif args.cmd == "mark-current":
        cmd_mark_current(args.result, args.reason)


if __name__ == "__main__":
    main()
