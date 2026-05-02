#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.api.app import app  # noqa: E402


def main() -> None:
    schema = app.openapi()
    out_yaml = ROOT / "backend" / "openapi.yaml"
    out_json = ROOT / "backend" / "openapi.json"

    out_yaml.parent.mkdir(parents=True, exist_ok=True)
    out_yaml.write_text(yaml.safe_dump(schema, sort_keys=False), encoding="utf-8")
    out_json.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_yaml}")
    print(f"wrote {out_json}")


if __name__ == "__main__":
    main()
