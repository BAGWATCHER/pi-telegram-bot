#!/usr/bin/env python3
import base64
import json
import sys
from pathlib import Path


def decode_payload(jwt: str) -> dict:
    parts = jwt.split(".")
    if len(parts) < 2:
        raise ValueError("invalid jwt")
    payload = parts[1] + "=" * (-len(parts[1]) % 4)
    return json.loads(base64.urlsafe_b64decode(payload.encode()).decode())


def main() -> int:
    codex_path = Path(sys.argv[1] if len(sys.argv) > 1 else str(Path.home() / ".codex" / "auth.json"))
    pi_path = Path(sys.argv[2] if len(sys.argv) > 2 else str(Path.home() / ".pi" / "agent" / "auth.json"))

    if not codex_path.exists():
      print(f"missing codex auth: {codex_path}", file=sys.stderr)
      return 1

    raw = json.loads(codex_path.read_text())
    tokens = raw.get("tokens") or {}
    access = tokens.get("access_token")
    refresh = tokens.get("refresh_token")
    account_id = tokens.get("account_id")
    if not access or not refresh:
        print("missing codex access/refresh token", file=sys.stderr)
        return 1

    payload = decode_payload(access)
    if not account_id:
        account_id = (payload.get("https://api.openai.com/auth") or {}).get("chatgpt_account_id")
    expires = int(payload.get("exp", 0)) * 1000

    wrapped = {
        "openai-codex": {
            "type": "oauth",
            "access": access,
            "refresh": refresh,
            "expires": expires,
            "accountId": account_id,
        }
    }

    pi_path.parent.mkdir(parents=True, exist_ok=True)
    pi_path.write_text(json.dumps(wrapped, indent=2) + "\n")
    print(
        json.dumps(
            {
                "email": (payload.get("https://api.openai.com/profile") or {}).get("email"),
                "accountId": account_id,
                "target": str(pi_path),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
