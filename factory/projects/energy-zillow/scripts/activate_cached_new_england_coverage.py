#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, OrderedDict
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[1]
NE_STATES = {"CT", "MA", "ME", "NH", "RI", "VT"}
STATE_ABBR = {
    "CONNECTICUT": "CT",
    "MASSACHUSETTS": "MA",
    "MAINE": "ME",
    "NEW HAMPSHIRE": "NH",
    "RHODE ISLAND": "RI",
    "VERMONT": "VT",
}


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    if not rows:
        raise RuntimeError(f"No rows to write for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def normalize_state(value: str) -> str:
    raw = str(value or "").strip()
    upper = raw.upper()
    if upper in NE_STATES:
        return upper
    return STATE_ABBR.get(upper, raw)


def main() -> int:
    p = argparse.ArgumentParser(description="Activate wider New England coverage from cached per-ZIP OSM files")
    p.add_argument("--data-dir", default="data/processed")
    p.add_argument("--sites-glob", default="sites_*_osm.csv")
    p.add_argument("--output-sites", default="data/processed/sites.csv")
    p.add_argument("--output-merged", default="data/processed/sites_multi_osm.csv")
    p.add_argument("--summary-json", default="artifacts/new-england-cached-coverage.json")
    p.add_argument("--summary-md", default="artifacts/new-england-cached-coverage.md")
    args = p.parse_args()

    data_dir = ROOT / args.data_dir
    files = sorted(data_dir.glob(args.sites_glob))
    if not files:
        raise RuntimeError(f"No files matched {data_dir / args.sites_glob}")

    merged: "OrderedDict[str, Dict[str, str]]" = OrderedDict()
    included = []
    skipped = []
    state_counts: Counter[str] = Counter()

    for path in files:
        rows = read_csv(path)
        if not rows:
            skipped.append({"file": path.name, "reason": "empty"})
            continue

        state = normalize_state(rows[0].get("state") or "")
        zip_code = str(rows[0].get("zip") or path.stem.split("_")[1]).strip()
        city = str(rows[0].get("city") or "").strip()
        if state not in NE_STATES:
            skipped.append({"file": path.name, "zip": zip_code, "state": state, "reason": "non_new_england"})
            continue

        source_breakdown: Counter[str] = Counter(str(r.get("source_type") or "unknown") for r in rows)
        included.append(
            {
                "zip": zip_code,
                "city": city,
                "state": state,
                "records": len(rows),
                "file": path.name,
                "source_breakdown": dict(source_breakdown),
            }
        )
        state_counts[state] += len(rows)

        for row in rows:
            row = dict(row)
            row["state"] = normalize_state(row.get("state") or state)
            key = f"{row.get('address','')}|{row.get('lat','')}|{row.get('lon','')}"
            merged[key] = row

    merged_rows = list(merged.values())
    if not merged_rows:
        raise RuntimeError("No New England rows were found in cached OSM files")

    write_csv(ROOT / args.output_merged, merged_rows)
    write_csv(ROOT / args.output_sites, merged_rows)

    included.sort(key=lambda x: (x["state"], x["zip"]))
    summary = {
        "status": "ok",
        "included_zip_count": len(included),
        "included_site_count": len(merged_rows),
        "state_site_counts": dict(sorted(state_counts.items())),
        "included": included,
        "skipped": skipped,
        "outputs": {
            "sites_csv": str(ROOT / args.output_sites),
            "sites_multi_osm_csv": str(ROOT / args.output_merged),
        },
    }

    summary_json_path = ROOT / args.summary_json
    summary_json_path.parent.mkdir(parents=True, exist_ok=True)
    summary_json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# New England Cached Coverage",
        "",
        f"- included ZIPs: **{summary['included_zip_count']}**",
        f"- included sites: **{summary['included_site_count']:,}**",
        "",
        "## State Totals",
    ]
    for state, count in sorted(state_counts.items()):
        md_lines.append(f"- `{state}`: **{count:,}**")

    md_lines.extend(["", "## Included ZIPs"])
    for item in included:
        md_lines.append(f"- `{item['zip']}` {item['city']}, {item['state']}: **{item['records']:,}**")

    if skipped:
        md_lines.extend(["", "## Skipped"])
        for item in skipped[:20]:
            md_lines.append(f"- `{item.get('file')}`: {item.get('reason')}")

    (ROOT / args.summary_md).write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "ok",
                "included_zip_count": len(included),
                "included_site_count": len(merged_rows),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
