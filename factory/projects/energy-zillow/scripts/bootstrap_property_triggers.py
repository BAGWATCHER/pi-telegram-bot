#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List


def read_sites(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_triggers(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "site_id",
                "zip",
                "storm_trigger_status",
                "outage_trigger_status",
                "equipment_age_trigger_status",
                "flood_risk_trigger_status",
                "storm_trigger_score",
                "storm_event_count_12m",
                "storm_event_count_36m",
                "hail_event_count_36m",
                "wind_event_count_36m",
                "recent_storm_days",
                "storm_severity_proxy",
                "outage_trigger_score",
                "equipment_age_trigger_score",
                "flood_risk_trigger_score",
                "trigger_notes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sites-csv", default="data/processed/sites.csv")
    parser.add_argument("--output", default="data/processed/property_triggers.csv")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    sites = read_sites(root / args.sites_csv)

    rows: List[Dict[str, str]] = []
    for site in sites:
        rows.append(
            {
                "site_id": str(site.get("site_id") or ""),
                "zip": str(site.get("zip") or ""),
                "storm_trigger_status": "missing",
                "outage_trigger_status": "missing",
                "equipment_age_trigger_status": "missing",
                "flood_risk_trigger_status": "missing",
                "storm_trigger_score": "",
                "storm_event_count_12m": "",
                "storm_event_count_36m": "",
                "hail_event_count_36m": "",
                "wind_event_count_36m": "",
                "recent_storm_days": "",
                "storm_severity_proxy": "",
                "outage_trigger_score": "",
                "equipment_age_trigger_score": "",
                "flood_risk_trigger_score": "",
                "trigger_notes": "",
            }
        )

    write_triggers(root / args.output, rows)
    print(f"Wrote {root / args.output} with {len(rows)} trigger rows")


if __name__ == "__main__":
    main()
