#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import requests

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://outagemap.eversource.com/resources/data/external/interval_generation_data"


def _to_float(value) -> float | None:
    if value in (None, "", "None"):
        return None
    try:
        return float(value)
    except Exception:
        return None


def _pct_to_float(s: str | None) -> float | None:
    if not s:
        return None
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)", str(s))
    if not m:
        return None
    return _to_float(m.group(1))


def _norm_state_from_title(title: str) -> str | None:
    t = (title or "").strip().lower()
    if "connecticut" in t:
        return "CT"
    if "massachusetts" in t or "mass" in t:
        return "MA"
    if "new hampshire" in t or "n.h" in t:
        return "NH"
    return None


def _fetch_json(url: str) -> dict:
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()


def main() -> int:
    p = argparse.ArgumentParser(description="Fetch Eversource outage map data and emit state outage feed CSV")
    p.add_argument("--output", default="data/raw/state_outage_feed.csv")
    p.add_argument("--summary-json", default="artifacts/eversource-outage-fetch-summary.json")
    p.add_argument("--summary-md", default="artifacts/eversource-outage-fetch-summary.md")
    args = p.parse_args()

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    meta = _fetch_json(f"{BASE}/metadata.json")
    directory = str(meta.get("directory") or "").strip()
    if not directory:
        raise RuntimeError("metadata.json missing directory")

    thematic = _fetch_json(f"{BASE}/{directory}/thematic_region/thematic_areas.json")
    file_data = thematic.get("file_data") or []
    if not isinstance(file_data, list):
        raise RuntimeError("thematic_region/thematic_areas.json missing list file_data")

    by_state: Dict[str, Dict[str, object]] = {}
    source_rows = []
    for item in file_data:
        title = str(item.get("title") or item.get("id") or "").strip()
        state = _norm_state_from_title(title)
        if not state:
            continue

        desc = item.get("desc") or {}
        n_out = _to_float(desc.get("n_out")) or 0.0

        cust_s = desc.get("cust_s")
        if isinstance(cust_s, dict):
            cust_s = cust_s.get("val")
        cust_s = _to_float(cust_s) or 0.0

        cust_a = desc.get("cust_a")
        if isinstance(cust_a, dict):
            cust_a = cust_a.get("val")
        cust_a = _to_float(cust_a)
        if cust_a is None and cust_s > 0:
            # fallback estimation if map only gives outage points
            cust_a = n_out

        pct = _pct_to_float(desc.get("percent_out"))
        if pct is None and cust_s > 0 and cust_a is not None:
            pct = (cust_a / cust_s) * 100.0
        pct = pct or 0.0

        source_rows.append(
            {
                "state": state,
                "region": title,
                "outage_pct": round(pct, 4),
                "customers_out": int(round(cust_a or 0.0)),
                "customers_served": int(round(cust_s or 0.0)),
            }
        )

        prev = by_state.get(state)
        if not prev:
            by_state[state] = {
                "outage_pct": pct,
                "customers_out": cust_a or 0.0,
                "customers_served": cust_s,
                "regions": [title],
            }
        else:
            prev["customers_out"] = float(prev["customers_out"]) + (cust_a or 0.0)
            prev["customers_served"] = float(prev["customers_served"]) + cust_s
            prev["regions"] = list(prev["regions"]) + [title]
            served = float(prev["customers_served"])
            out = float(prev["customers_out"])
            prev["outage_pct"] = (out / served * 100.0) if served > 0 else max(float(prev["outage_pct"]), pct)

    out_rows = []
    for st, row in sorted(by_state.items()):
        out_rows.append(
            {
                "state": st,
                "outage_pct": round(float(row["outage_pct"]), 4),
                "customers_out": int(round(float(row["customers_out"]))),
                "asof": now,
                "source": f"eversource_outage_map regions={','.join(row['regions'])} dir={directory}",
            }
        )

    output_path = ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["state", "outage_pct", "customers_out", "asof", "source"])
        w.writeheader()
        w.writerows(out_rows)

    summary = {
        "generated_at": now,
        "directory": directory,
        "regions_seen": source_rows,
        "state_rows": out_rows,
        "output": str(output_path),
    }

    summary_json_path = ROOT / args.summary_json
    summary_json_path.parent.mkdir(parents=True, exist_ok=True)
    summary_json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# Eversource Outage Feed Summary",
        "",
        f"- generated_at: `{now}`",
        f"- directory: `{directory}`",
        f"- output: `{output_path}`",
        "",
        "## State rows",
        "",
    ]
    for row in out_rows:
        md_lines.append(
            f"- `{row['state']}`: outage_pct={row['outage_pct']} customers_out={row['customers_out']} source={row['source']}"
        )

    summary_md_path = ROOT / args.summary_md
    summary_md_path.parent.mkdir(parents=True, exist_ok=True)
    summary_md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(json.dumps({"ok": True, "states": len(out_rows), "output": str(output_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
