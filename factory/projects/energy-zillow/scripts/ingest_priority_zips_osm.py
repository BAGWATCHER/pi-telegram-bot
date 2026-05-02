#!/usr/bin/env python3
"""Ingest OSM candidates for prioritized ZIP list with skip-on-failure behavior."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from ingest_zip_osm import fetch_osm_xml, fetch_zip_profile, parse_osm_addresses  # type: ignore


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    if not rows:
        raise RuntimeError(f"No rows to write for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def fetch_osm_with_retry(lat: float, lon: float, half_span_deg: float, max_retries: int) -> str:
    attempt = 0
    while True:
        attempt += 1
        try:
            return fetch_osm_xml(lat, lon, half_span_deg)
        except Exception as e:
            msg = str(e)
            if "OSM map fetch failed (509)" in msg and attempt <= max_retries:
                m = re.search(r"try again in\s+(\d+)\s+seconds", msg)
                wait_sec = int(m.group(1)) + 1 if m else min(30, attempt * 4)
                time.sleep(wait_sec)
                continue
            raise


def main() -> None:
    p = argparse.ArgumentParser(description="Ingest priority ZIPs with graceful skips")
    p.add_argument("--priority-csv", default="artifacts/new-england-zip-priority.csv")
    p.add_argument("--top", type=int, default=100, help="How many priority ZIPs to attempt")
    p.add_argument("--half-span-deg", type=float, default=0.015)
    p.add_argument("--min-records-per-zip", type=int, default=40)
    p.add_argument("--max-fetch-retries", type=int, default=5)
    p.add_argument("--per-zip-delay-sec", type=float, default=1.0)
    p.add_argument("--project-root", default=str(ROOT))
    args = p.parse_args()

    root = Path(args.project_root).resolve()
    data_dir = root / "data" / "processed"
    artifacts = root / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)

    priority_path = root / args.priority_csv
    if not priority_path.exists():
        raise RuntimeError(f"Priority CSV missing: {priority_path}")

    priority_rows = list(csv.DictReader(priority_path.open("r", encoding="utf-8")))
    selected = priority_rows[: args.top]
    zips = [str(r["zip"]).zfill(5) for r in selected]

    merged: "OrderedDict[str, Dict[str, object]]" = OrderedDict()
    successes = []
    failures = []

    for i, z in enumerate(zips, start=1):
        try:
            profile = fetch_zip_profile(z)
            xml = fetch_osm_with_retry(
                float(profile["lat"]),
                float(profile["lon"]),
                args.half_span_deg,
                max_retries=args.max_fetch_retries,
            )
            rows = parse_osm_addresses(xml, profile, str(profile["zip"]))
            if len(rows) < args.min_records_per_zip:
                failures.append(
                    {
                        "zip": z,
                        "state": profile.get("state"),
                        "reason": f"sparse ({len(rows)} < {args.min_records_per_zip})",
                    }
                )
                continue

            zip_path = data_dir / f"sites_{profile['zip']}_osm.csv"
            write_csv(zip_path, rows)

            source_breakdown: Dict[str, int] = {}
            for r in rows:
                source_breakdown[str(r.get("source_type", "unknown"))] = source_breakdown.get(
                    str(r.get("source_type", "unknown")), 0
                ) + 1

            successes.append(
                {
                    "zip": profile["zip"],
                    "city": profile["city"],
                    "state": profile["state"],
                    "records": len(rows),
                    "source_breakdown": source_breakdown,
                    "output_csv": str(zip_path),
                    "rank": i,
                }
            )

            for row in rows:
                key = f"{row['address']}|{row['lat']}|{row['lon']}"
                merged[key] = row

        except Exception as e:
            failures.append({"zip": z, "reason": str(e)[:300]})
        finally:
            if args.per_zip_delay_sec > 0:
                time.sleep(args.per_zip_delay_sec)

    merged_rows = list(merged.values())
    if merged_rows:
        merged_path = data_dir / "sites_multi_osm.csv"
        write_csv(merged_path, merged_rows)
        write_csv(data_dir / "sites.csv", merged_rows)
    else:
        raise RuntimeError("No merged rows produced; all selected ZIPs failed")

    output = {
        "status": "ok",
        "attempted_zips": len(zips),
        "succeeded_zips": len(successes),
        "failed_zips": len(failures),
        "half_span_deg": args.half_span_deg,
        "min_records_per_zip": args.min_records_per_zip,
        "max_fetch_retries": args.max_fetch_retries,
        "per_zip_delay_sec": args.per_zip_delay_sec,
        "merged_records": len(merged_rows),
        "successes": successes,
        "failures": failures,
        "outputs": {
            "sites_csv": str(data_dir / "sites.csv"),
            "sites_multi_osm_csv": str(data_dir / "sites_multi_osm.csv"),
        },
    }

    (artifacts / "new-england-priority-ingest.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")

    md = [
        "# New England Priority Ingest",
        "",
        f"- attempted ZIPs: **{output['attempted_zips']}**",
        f"- succeeded ZIPs: **{output['succeeded_zips']}**",
        f"- failed ZIPs: **{output['failed_zips']}**",
        f"- merged addresses: **{output['merged_records']:,}**",
        f"- half-span: `{args.half_span_deg}`",
        f"- min records per ZIP: `{args.min_records_per_zip}`",
        "",
        "## Top successful ZIPs",
    ]
    for s in successes[:30]:
        md.append(f"- #{s['rank']} `{s['zip']}` {s['city']}, {s['state']}: **{s['records']}**")

    if failures:
        md.extend(["", "## Failures (sample)"])
        for f in failures[:30]:
            md.append(f"- `{f.get('zip')}`: {f.get('reason')}")

    (artifacts / "new-england-priority-ingest.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(json.dumps({k: output[k] for k in ["status", "attempted_zips", "succeeded_zips", "failed_zips", "merged_records"]}, indent=2))


if __name__ == "__main__":
    main()
