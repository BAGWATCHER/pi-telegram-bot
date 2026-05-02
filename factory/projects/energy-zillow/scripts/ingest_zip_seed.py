#!/usr/bin/env python3
"""EZ-002 bootstrap ingest.

Creates a deterministic starter dataset for one ZIP so downstream scoring/API/UI
can be built immediately. Uses Zippopotam.us for ZIP centroid + city/state and
then generates synthetic address candidates around that centroid.

This is intentionally a bootstrap path; replace with true parcel/footprint
sources in a later task.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Dict, List

import requests

STREET_NAMES = [
    "Oak St",
    "Maple Ave",
    "Pine St",
    "Cedar Ln",
    "Elm St",
    "Sunset Blvd",
    "Hillcrest Dr",
    "Ridge Rd",
    "Park Ave",
    "Willow Way",
    "Lakeview Dr",
    "1st St",
    "2nd St",
    "3rd St",
    "Main St",
]


def fetch_zip_profile(zip_code: str) -> Dict[str, str]:
    url = f"https://api.zippopotam.us/us/{zip_code}"
    resp = requests.get(url, timeout=20)
    if resp.status_code != 200:
        raise RuntimeError(f"ZIP lookup failed ({resp.status_code}) for {zip_code}")
    payload = resp.json()
    place = payload["places"][0]
    return {
        "zip": payload["post code"],
        "city": place["place name"],
        "state": place["state abbreviation"],
        "lat": float(place["latitude"]),
        "lon": float(place["longitude"]),
    }


def make_site_id(address: str, zip_code: str, idx: int) -> str:
    digest = hashlib.sha1(f"{zip_code}|{idx}|{address}".encode("utf-8")).hexdigest()
    return f"site_{digest[:12]}"


def generate_sites(profile: Dict[str, str], count: int) -> List[Dict[str, object]]:
    lat0 = profile["lat"]
    lon0 = profile["lon"]
    sites: List[Dict[str, object]] = []

    # deterministic spiral so output is stable run-to-run
    for i in range(count):
        angle = (i * 137.508) % 360  # golden angle
        radius = 0.002 + (i / max(count, 1)) * 0.03
        lat = lat0 + radius * math.cos(math.radians(angle))
        lon = lon0 + radius * math.sin(math.radians(angle))

        number = 100 + (i * 3)
        street = STREET_NAMES[i % len(STREET_NAMES)]
        address = f"{number} {street}, {profile['city']}, {profile['state']} {profile['zip']}"

        sites.append(
            {
                "site_id": make_site_id(address, profile["zip"], i),
                "address": address,
                "zip": profile["zip"],
                "city": profile["city"],
                "state": profile["state"],
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "data_source": "synthetic_seed_from_zip_centroid",
            }
        )

    return sites


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise RuntimeError("No rows to write")
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def compute_coverage(rows: List[Dict[str, object]]) -> Dict[str, object]:
    total = len(rows)
    with_core = 0
    for r in rows:
        if r.get("site_id") and r.get("lat") is not None and r.get("lon") is not None:
            with_core += 1
    coverage = (with_core / total) if total else 0.0
    return {
        "candidate_addresses": total,
        "scored_ready_addresses": with_core,
        "coverage": coverage,
    }


def write_artifacts(root: Path, profile: Dict[str, str], coverage: Dict[str, object], out_csv: Path, count: int) -> None:
    artifacts = root / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)

    provenance = {
        "task": "EZ-002",
        "method": "zip-centroid synthetic bootstrap",
        "zip": profile["zip"],
        "city": profile["city"],
        "state": profile["state"],
        "centroid": {"lat": profile["lat"], "lon": profile["lon"]},
        "candidate_count": count,
        "output_csv": str(out_csv),
        "notes": [
            "Bootstrap dataset for pipeline bring-up only.",
            "Replace with real parcel/building footprint ingest in next iteration.",
        ],
    }
    (artifacts / "data-provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")

    coverage_md = f"""# EZ-002 Data Coverage\n\n- ZIP: `{profile['zip']}` ({profile['city']}, {profile['state']})\n- Candidates: **{coverage['candidate_addresses']}**\n- With site_id+lat/lon: **{coverage['scored_ready_addresses']}**\n- Coverage: **{coverage['coverage']:.2%}**\n- Output: `{out_csv}`\n\n## Source + Method\n- Source API: `https://api.zippopotam.us/us/{profile['zip']}`\n- Method: deterministic synthetic candidate generation around ZIP centroid\n- Purpose: unblock scoring/API/UI while real parcel ingest is implemented\n\n## Next Upgrade\n- Replace synthetic addresses with real parcel/building footprint records\n- Attach rooftop geometry metadata and shading proxies\n"""
    (artifacts / "data-coverage.md").write_text(coverage_md, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap ZIP dataset for Energy Zillow")
    parser.add_argument("--zip", dest="zip_code", required=True, help="US ZIP code, e.g. 78701")
    parser.add_argument("--count", type=int, default=250, help="Number of candidate sites")
    parser.add_argument(
        "--project-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Project root path",
    )
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    data_dir = root / "data" / "processed"

    profile = fetch_zip_profile(args.zip_code)
    rows = generate_sites(profile, args.count)

    out_csv = data_dir / f"sites_{profile['zip']}.csv"
    write_csv(out_csv, rows)
    # canonical latest pointer
    write_csv(data_dir / "sites.csv", rows)

    coverage = compute_coverage(rows)
    write_artifacts(root, profile, coverage, out_csv, args.count)

    print(json.dumps({"status": "ok", "zip": profile["zip"], **coverage, "output": str(out_csv)}, indent=2))


if __name__ == "__main__":
    main()
