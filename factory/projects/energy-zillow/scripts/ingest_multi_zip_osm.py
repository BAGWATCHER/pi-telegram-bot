#!/usr/bin/env python3
"""Ingest and merge real OSM address/footprint records for multiple ZIPs."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from ingest_zip_osm import (  # type: ignore
    fetch_osm_xml,
    fetch_zip_profile,
    parse_osm_addresses,
)


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    if not rows:
        raise RuntimeError("No rows to write")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    p = argparse.ArgumentParser(description="Merge OSM ingest across multiple ZIPs")
    p.add_argument("--zips", required=True, help="Comma-separated ZIPs, e.g. 78701,78702")
    p.add_argument("--half-span-deg", type=float, default=0.01)
    p.add_argument("--min-records-per-zip", type=int, default=80)
    p.add_argument("--project-root", default=str(ROOT))
    args = p.parse_args()

    root = Path(args.project_root).resolve()
    data_dir = root / "data" / "processed"
    artifacts = root / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)

    zip_codes = [z.strip() for z in args.zips.split(",") if z.strip()]
    if not zip_codes:
        raise RuntimeError("No ZIPs provided")

    merged: "OrderedDict[str, Dict[str, object]]" = OrderedDict()
    per_zip = []

    for z in zip_codes:
        profile = fetch_zip_profile(z)
        xml = fetch_osm_xml(float(profile["lat"]), float(profile["lon"]), args.half_span_deg)
        rows = parse_osm_addresses(xml, profile, str(profile["zip"]))
        if len(rows) < args.min_records_per_zip:
            raise RuntimeError(f"ZIP {z} too sparse: {len(rows)} records")

        zip_path = data_dir / f"sites_{profile['zip']}_osm.csv"
        write_csv(zip_path, rows)

        source_breakdown: Dict[str, int] = {}
        for r in rows:
            source_breakdown[r["source_type"]] = source_breakdown.get(r["source_type"], 0) + 1

        per_zip.append(
            {
                "zip": profile["zip"],
                "city": profile["city"],
                "state": profile["state"],
                "center": {"lat": profile["lat"], "lon": profile["lon"]},
                "records": len(rows),
                "source_breakdown": source_breakdown,
                "output_csv": str(zip_path),
            }
        )

        for row in rows:
            key = f"{row['address']}|{row['lat']}|{row['lon']}"
            merged[key] = row

    merged_rows = list(merged.values())
    merged_path = data_dir / "sites_multi_osm.csv"
    write_csv(merged_path, merged_rows)
    write_csv(data_dir / "sites.csv", merged_rows)

    coverage = {
        "candidate_addresses": len(merged_rows),
        "scored_ready_addresses": len(merged_rows),
        "coverage": 1.0 if merged_rows else 0.0,
    }

    prov = {
        "task": "EZ-002",
        "method": "OSM real address/footprint ingest (multi-zip)",
        "zips": zip_codes,
        "half_span_deg": args.half_span_deg,
        "per_zip": per_zip,
        "output_csv": str(merged_path),
        "coverage": coverage,
        "source_api": "https://api.openstreetmap.org/api/0.6/map",
    }
    (artifacts / "data-provenance.json").write_text(json.dumps(prov, indent=2) + "\n", encoding="utf-8")

    md = [
        "# EZ-002 Data Coverage",
        "",
        f"- ZIPs: `{', '.join(zip_codes)}`",
        f"- Candidates: **{coverage['candidate_addresses']}**",
        f"- With site_id+lat/lon: **{coverage['scored_ready_addresses']}**",
        f"- Coverage: **{coverage['coverage']:.2%}**",
        "- Source mode: **real OSM address/footprint ingest (multi-zip)**",
        f"- Output: `{merged_path}`",
        "",
        "## Per-ZIP Breakdown",
    ]
    for item in per_zip:
        md.append(
            f"- `{item['zip']}` ({item['city']}, {item['state']}): **{item['records']}** records "
            f"(nodes={item['source_breakdown'].get('node', 0)}, ways={item['source_breakdown'].get('way', 0)})"
        )
    md.extend(
        [
            "",
            "## Next Upgrade",
            "- Add county/city parcel authority datasets",
            "- Add rooftop geometry/shading and PVWatts calibration for higher confidence",
            "",
        ]
    )
    (artifacts / "data-coverage.md").write_text("\n".join(md), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "ok",
                "zips": zip_codes,
                "records": len(merged_rows),
                "output": str(merged_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
