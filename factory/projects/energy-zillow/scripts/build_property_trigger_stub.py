#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    p = argparse.ArgumentParser(description="Build screening-grade property trigger contract file")
    p.add_argument("--sites-csv", default="data/processed/sites.csv")
    p.add_argument("--output", default="data/processed/property_triggers.csv")
    args = p.parse_args()

    sites_path = ROOT / args.sites_csv
    out_path = ROOT / args.output

    if not sites_path.exists():
        raise SystemExit(f"missing sites csv: {sites_path}")

    with sites_path.open("r", encoding="utf-8") as f:
        sites = list(csv.DictReader(f))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "site_id",
                "storm_trigger_status",
                "outage_trigger_status",
                "equipment_age_trigger_status",
                "flood_risk_trigger_status",
                "storm_trigger_score",
                "outage_trigger_score",
                "equipment_age_trigger_score",
                "flood_risk_trigger_score",
                "trigger_notes",
            ],
        )
        w.writeheader()
        for row in sites:
            site_id = str(row.get("site_id") or "").strip()
            if not site_id:
                continue
            w.writerow(
                {
                    "site_id": site_id,
                    "storm_trigger_status": "missing",
                    "outage_trigger_status": "missing",
                    "equipment_age_trigger_status": "missing",
                    "flood_risk_trigger_status": "missing",
                    "storm_trigger_score": "",
                    "outage_trigger_score": "",
                    "equipment_age_trigger_score": "",
                    "flood_risk_trigger_score": "",
                    "trigger_notes": "screening contract stub; external trigger layers not loaded",
                }
            )

    print(f"wrote {out_path} rows={len(sites)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
