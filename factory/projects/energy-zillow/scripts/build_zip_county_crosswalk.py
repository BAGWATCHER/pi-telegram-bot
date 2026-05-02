#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Dict, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
CENSUS_REVERSE_URL = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
STATE_FIPS_TO_ABBR = {
    "09": "CT",
    "23": "ME",
    "25": "MA",
    "33": "NH",
    "44": "RI",
    "50": "VT",
}


def parse_zip(value: str) -> str:
    digits = "".join(ch for ch in (value or "") if ch.isdigit())
    return digits[:5]


def load_zip_centroids(sites_csv: Path) -> Dict[Tuple[str, str], Tuple[float, float]]:
    centroids: Dict[Tuple[str, str], Tuple[float, float]] = {}
    with sites_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            zip_code = parse_zip(str(row.get("zip") or ""))
            state = str(row.get("state") or "").strip().upper()
            lat_raw = str(row.get("lat") or "").strip()
            lon_raw = str(row.get("lon") or "").strip()
            if not zip_code or not state or not lat_raw or not lon_raw:
                continue
            key = (zip_code, state)
            if key in centroids:
                continue
            try:
                centroids[key] = (float(lat_raw), float(lon_raw))
            except ValueError:
                continue
    return centroids


def fetch_county_for_point(lat: float, lon: float, benchmark: str = "Public_AR_Current") -> Dict[str, str]:
    query = urlencode(
        {
            "x": f"{lon:.6f}",
            "y": f"{lat:.6f}",
            "benchmark": benchmark,
            "vintage": "Current_Current",
            "layers": "Counties",
            "format": "json",
        }
    )
    url = f"{CENSUS_REVERSE_URL}?{query}"
    req = Request(url, headers={"User-Agent": "energy-zillow/zip-county-builder"})
    with urlopen(req, timeout=20) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    counties = (
        payload.get("result", {})
        .get("geographies", {})
        .get("Counties", [])
    )
    if not counties:
        raise RuntimeError(f"no county result for {lat},{lon}")

    county = counties[0]
    county_fips = str(county.get("COUNTY") or "").strip().zfill(3)
    county_name = str(county.get("BASENAME") or county.get("NAME") or "").strip().lower()
    state_abbr = str(county.get("STUSAB") or "").strip().upper() or STATE_FIPS_TO_ABBR.get(str(county.get("STATE") or "").zfill(2), "")
    if not county_fips or not county_name or not state_abbr:
        raise RuntimeError(f"incomplete county result for {lat},{lon}")

    return {
        "county_fips": county_fips,
        "county_name": county_name,
        "state": state_abbr,
    }


def load_existing(path: Path) -> Dict[Tuple[str, str], Dict[str, str]]:
    if not path.exists():
        return {}
    out: Dict[Tuple[str, str], Dict[str, str]] = {}
    with path.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            zip_code = parse_zip(str(row.get("zip") or row.get("zip_code") or row.get("zipcode") or ""))
            state = str(row.get("state") or row.get("state_abbr") or "").strip().upper()
            county_fips = str(row.get("county_fips") or "").strip()
            county_name = str(row.get("county_name") or "").strip().lower()
            if not zip_code or not state or not county_fips or not county_name:
                continue
            out[(zip_code, state)] = {
                "zip": zip_code,
                "state": state,
                "county_fips": county_fips,
                "county_name": county_name,
            }
    return out


def write_rows(path: Path, rows: Dict[Tuple[str, str], Dict[str, str]]) -> None:
    ordered = [rows[key] for key in sorted(rows)]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["zip", "state", "county_fips", "county_name"])
        writer.writeheader()
        writer.writerows(ordered)


def main() -> int:
    p = argparse.ArgumentParser(description="Build ZIP->county crosswalk from site lat/lon using Census reverse geocoder")
    p.add_argument("--sites-csv", default="data/processed/sites.csv")
    p.add_argument("--output", default="data/raw/zip_county_crosswalk.csv")
    p.add_argument("--sleep-ms", type=int, default=150)
    args = p.parse_args()

    sites_csv = ROOT / args.sites_csv
    output = ROOT / args.output
    if not sites_csv.exists():
        raise SystemExit(f"missing sites csv: {sites_csv}")

    existing = load_existing(output)
    centroids = load_zip_centroids(sites_csv)
    total = len(centroids)
    fetched = 0

    for key, (lat, lon) in sorted(centroids.items()):
        if key in existing:
            continue
        try:
            county = fetch_county_for_point(lat, lon)
        except (HTTPError, URLError, TimeoutError, RuntimeError) as err:
            raise SystemExit(f"failed to resolve {key[0]},{key[1]} at {lat},{lon}: {err}")
        existing[key] = {
            "zip": key[0],
            "state": county["state"],
            "county_fips": county["county_fips"],
            "county_name": county["county_name"],
        }
        fetched += 1
        time.sleep(max(args.sleep_ms, 0) / 1000)

    write_rows(output, existing)
    print(
        json.dumps(
            {
                "sites_zip_keys": total,
                "crosswalk_rows": len(existing),
                "fetched_new": fetched,
                "output": str(output),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
