#!/usr/bin/env python3
"""Build wealth-prioritized New England ZIP target list for ingest planning.

Data sources:
- GeoNames US postal list (zip -> state)
- US Census ACS 5-year ZCTA metrics (income/home value/owner occupancy)
"""

from __future__ import annotations

import csv
import io
import json
import zipfile
from pathlib import Path
from statistics import quantiles
from typing import Dict, List

import requests

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"

NE_STATES = {"CT", "MA", "ME", "NH", "RI", "VT"}
ACS_ENDPOINT = "https://api.census.gov/data/2023/acs/acs5"


def _safe_int(v: str | None) -> int | None:
    if v is None:
        return None
    v = str(v).strip()
    if not v or v.startswith("-"):
        return None
    try:
        return int(float(v))
    except Exception:
        return None


def fetch_geonames_us_zip_states() -> Dict[str, str]:
    url = "https://download.geonames.org/export/zip/US.zip"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()

    out: Dict[str, str] = {}
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    with zf.open("US.txt") as fh:
        for raw in fh:
            row = raw.decode("utf-8", errors="ignore").strip().split("\t")
            if len(row) < 5:
                continue
            zip_code = row[1].zfill(5)
            state = row[4].strip().upper()
            if state:
                out[zip_code] = state
    return out


def fetch_acs_zcta_metrics() -> Dict[str, Dict[str, float]]:
    params = {
        "get": "NAME,B19013_001E,B25077_001E,B25003_001E,B25003_002E",
        "for": "zip code tabulation area:*",
    }
    resp = requests.get(ACS_ENDPOINT, params=params, timeout=120)
    resp.raise_for_status()
    rows = resp.json()
    header = rows[0]
    idx = {k: i for i, k in enumerate(header)}

    metrics: Dict[str, Dict[str, float]] = {}
    for r in rows[1:]:
        zip_code = str(r[idx["zip code tabulation area"]]).zfill(5)
        income = _safe_int(r[idx["B19013_001E"]])
        home_value = _safe_int(r[idx["B25077_001E"]])
        occupied_total = _safe_int(r[idx["B25003_001E"]])
        owner_occ = _safe_int(r[idx["B25003_002E"]])

        if not income or not home_value or not occupied_total or owner_occ is None:
            continue
        if occupied_total <= 0:
            continue

        owner_rate = max(0.0, min(1.0, owner_occ / occupied_total))
        metrics[zip_code] = {
            "median_income": float(income),
            "median_home_value": float(home_value),
            "owner_occ_rate": owner_rate,
            "occupied_units": float(occupied_total),
        }

    return metrics


def pct_rank(values: List[float], v: float) -> float:
    if not values:
        return 0.0
    less_or_equal = sum(1 for x in values if x <= v)
    return less_or_equal / len(values)


def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    zip_to_state = fetch_geonames_us_zip_states()
    acs = fetch_acs_zcta_metrics()

    rows: List[Dict[str, float | str]] = []
    for zip_code, m in acs.items():
        state = zip_to_state.get(zip_code)
        if state not in NE_STATES:
            continue
        rows.append(
            {
                "zip": zip_code,
                "state": state,
                "median_income": m["median_income"],
                "median_home_value": m["median_home_value"],
                "owner_occ_rate": m["owner_occ_rate"],
                "occupied_units": m["occupied_units"],
            }
        )

    incomes = [float(r["median_income"]) for r in rows]
    values = [float(r["median_home_value"]) for r in rows]
    owners = [float(r["owner_occ_rate"]) for r in rows]
    units = [float(r["occupied_units"]) for r in rows]

    for r in rows:
        income_pct = pct_rank(incomes, float(r["median_income"]))
        value_pct = pct_rank(values, float(r["median_home_value"]))
        owner_pct = pct_rank(owners, float(r["owner_occ_rate"]))
        units_pct = pct_rank(units, float(r["occupied_units"]))

        # Wealth-first but still biases toward addressable scale.
        score = 0.40 * income_pct + 0.35 * value_pct + 0.15 * owner_pct + 0.10 * units_pct

        r["income_pct"] = round(income_pct, 4)
        r["home_value_pct"] = round(value_pct, 4)
        r["owner_occ_pct"] = round(owner_pct, 4)
        r["occupied_units_pct"] = round(units_pct, 4)
        r["priority_score"] = round(score, 6)

    rows.sort(key=lambda r: float(r["priority_score"]), reverse=True)

    csv_path = ARTIFACTS / "new-england-zip-priority.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "zip",
                "state",
                "priority_score",
                "median_income",
                "median_home_value",
                "owner_occ_rate",
                "occupied_units",
                "income_pct",
                "home_value_pct",
                "owner_occ_pct",
                "occupied_units_pct",
            ],
        )
        w.writeheader()
        w.writerows(rows)

    top_100 = [str(r["zip"]) for r in rows[:100]]
    top_250 = [str(r["zip"]) for r in rows[:250]]

    summary = {
        "status": "ok",
        "new_england_zip_count": len(rows),
        "top_100_count": len(top_100),
        "top_250_count": len(top_250),
        "top_20": top_100[:20],
        "output_csv": str(csv_path),
        "top_100_zips": top_100,
        "top_250_zips": top_250,
    }
    (ARTIFACTS / "new-england-zip-priority.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
