#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


BASE_TRIGGER_FIELDS = [
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
]

HIGH_VALUE_EVENTS = {
    "hail": 1.0,
    "thunderstorm wind": 0.8,
    "tornado": 1.2,
    "strong wind": 0.45,
    "high wind": 0.55,
    "flash flood": 0.35,
    "flood": 0.25,
    "hurricane": 0.9,
    "tropical storm": 0.7,
}

STATE_ABBR = {
    "MASSACHUSETTS": "MA",
    "CONNECTICUT": "CT",
    "VERMONT": "VT",
    "RHODE ISLAND": "RI",
    "NEW HAMPSHIRE": "NH",
    "MAINE": "ME",
}


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, str]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def normalize_text(value: str) -> str:
    return " ".join((value or "").strip().lower().replace(".", " ").replace(",", " ").split())


def normalize_state(value: str) -> str:
    raw = (value or "").strip().upper()
    if len(raw) == 2:
        return raw
    return STATE_ABBR.get(raw, raw)


def parse_zip(value: str) -> str:
    digits = "".join(ch for ch in (value or "") if ch.isdigit())
    return digits[:5]


def parse_date(value: str) -> datetime | None:
    raw = (value or "").strip()
    if not raw:
        return None
    patterns = [
        "%d-%b-%y %H:%M:%S",
        "%d-%b-%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    ]
    for pattern in patterns:
        try:
            return datetime.strptime(raw, pattern).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def read_existing_triggers(path: Path) -> Dict[str, Dict[str, str]]:
    if not path.exists():
        return {}
    return {str(row.get("site_id") or ""): row for row in read_csv(path)}


def read_zip_county_crosswalk(path: Path) -> Dict[Tuple[str, str], Dict[str, str]]:
    if not path.exists():
        return {}
    rows = read_csv(path)
    out: Dict[Tuple[str, str], Dict[str, str]] = {}
    for row in rows:
        zip_code = parse_zip(str(row.get("zip") or row.get("zipcode") or row.get("zip_code") or ""))
        state = normalize_state(str(row.get("state") or row.get("state_abbr") or ""))
        if not zip_code or not state:
            continue
        county_fips = str(row.get("county_fips") or row.get("fips") or "").strip().zfill(3)
        county_name = normalize_text(str(row.get("county_name") or row.get("county") or ""))
        out[(zip_code, state)] = {"county_fips": county_fips, "county_name": county_name}
    return out


def iter_noaa_rows(storm_dir: Path) -> Iterable[Dict[str, str]]:
    if not storm_dir.exists():
        return []
    paths = sorted(storm_dir.glob("*.csv"))
    rows: List[Dict[str, str]] = []
    for path in paths:
        rows.extend(read_csv(path))
    return rows


def aggregate_noaa_events(storm_rows: Iterable[Dict[str, str]], now: datetime) -> Dict[Tuple[str, str, str], Dict[str, float]]:
    out: Dict[Tuple[str, str, str], Dict[str, float]] = {}
    for row in storm_rows:
        state = normalize_state(str(row.get("STATE") or row.get("state") or ""))
        county_fips = str(row.get("CZ_FIPS") or row.get("cz_fips") or "").strip().zfill(3)
        county_name = normalize_text(str(row.get("CZ_NAME") or row.get("cz_name") or row.get("county_name") or ""))
        key = (state, county_fips, county_name)
        if not state or (not county_fips and not county_name):
            continue

        event_type = normalize_text(str(row.get("EVENT_TYPE") or row.get("event_type") or ""))
        if event_type not in HIGH_VALUE_EVENTS:
            continue

        dt = parse_date(str(row.get("BEGIN_DATE_TIME") or row.get("begin_date_time") or row.get("BEGIN_YEARMONTH") or ""))
        if dt is None:
            continue
        age_days = max((now - dt).days, 0)
        if age_days > 365 * 3:
            continue

        bucket = out.setdefault(
            key,
            {
                "storm_event_count_12m": 0.0,
                "storm_event_count_36m": 0.0,
                "hail_event_count_36m": 0.0,
                "wind_event_count_36m": 0.0,
                "recent_storm_days": 99999.0,
                "storm_severity_proxy": 0.0,
            },
        )

        bucket["storm_event_count_36m"] += 1
        if age_days <= 365:
            bucket["storm_event_count_12m"] += 1
        if event_type == "hail":
            bucket["hail_event_count_36m"] += 1
        if event_type in {"thunderstorm wind", "strong wind", "high wind", "tornado"}:
            bucket["wind_event_count_36m"] += 1
        bucket["recent_storm_days"] = min(bucket["recent_storm_days"], float(age_days))

        recency_weight = 1.0
        if age_days <= 90:
            recency_weight = 1.3
        elif age_days <= 365:
            recency_weight = 1.0
        else:
            recency_weight = 0.45
        bucket["storm_severity_proxy"] += HIGH_VALUE_EVENTS[event_type] * recency_weight

    for bucket in out.values():
        if bucket["recent_storm_days"] == 99999.0:
            bucket["recent_storm_days"] = 0.0
    return out


def score_bucket(bucket: Dict[str, float]) -> float:
    raw = (
        min(24.0, bucket.get("hail_event_count_36m", 0.0) * 6.0)
        + min(18.0, bucket.get("wind_event_count_36m", 0.0) * 0.25)
        + min(14.0, bucket.get("storm_event_count_12m", 0.0) * 0.45)
        + min(22.0, bucket.get("storm_severity_proxy", 0.0) * 0.6)
    )
    recent_days = bucket.get("recent_storm_days", 0.0)
    if recent_days and recent_days <= 60:
        raw += 10.0
    elif recent_days and recent_days <= 180:
        raw += 5.0
    return max(0.0, min(100.0, raw))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sites-csv", default="data/processed/sites.csv")
    parser.add_argument("--triggers-csv", default="data/processed/property_triggers.csv")
    parser.add_argument("--storm-dir", default="data/raw/noaa")
    parser.add_argument("--zip-county-csv", default="data/raw/zip_county_crosswalk.csv")
    parser.add_argument("--output", default="data/processed/property_triggers.csv")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    sites = read_csv(root / args.sites_csv)
    existing = read_existing_triggers(root / args.triggers_csv)
    crosswalk = read_zip_county_crosswalk(root / args.zip_county_csv)
    storm_rows = list(iter_noaa_rows(root / args.storm_dir))
    aggregates = aggregate_noaa_events(storm_rows, now=datetime.now(timezone.utc))

    output_rows: List[Dict[str, str]] = []
    matched = 0
    missing_crosswalk = 0

    for site in sites:
        site_id = str(site.get("site_id") or "")
        base = dict(existing.get(site_id) or {})
        for field in BASE_TRIGGER_FIELDS:
            base.setdefault(field, "")
        base["site_id"] = site_id
        base["zip"] = parse_zip(str(site.get("zip") or ""))

        state = str(site.get("state") or "").strip().upper()
        county = crosswalk.get((base["zip"], state))
        if not county:
            missing_crosswalk += 1
            if not base.get("trigger_notes"):
                base["trigger_notes"] = "NOAA storm join pending ZIP-to-county crosswalk."
            output_rows.append(base)
            continue

        key = (state, county.get("county_fips", ""), county.get("county_name", ""))
        bucket = aggregates.get(key)
        if not bucket and county.get("county_name"):
            for candidate_key, candidate_bucket in aggregates.items():
                if candidate_key[0] == state and candidate_key[2] == county.get("county_name"):
                    bucket = candidate_bucket
                    break

        if not bucket:
            if not base.get("storm_trigger_status") or base.get("storm_trigger_status") == "missing":
                base["storm_trigger_status"] = "missing"
            if not base.get("trigger_notes"):
                base["trigger_notes"] = "No matching NOAA storm events found for joined county in current lookback window."
            output_rows.append(base)
            continue

        matched += 1
        base["storm_trigger_status"] = "proxy"
        base["storm_trigger_score"] = f"{score_bucket(bucket):.1f}"
        base["storm_event_count_12m"] = str(int(bucket.get("storm_event_count_12m", 0.0)))
        base["storm_event_count_36m"] = str(int(bucket.get("storm_event_count_36m", 0.0)))
        base["hail_event_count_36m"] = str(int(bucket.get("hail_event_count_36m", 0.0)))
        base["wind_event_count_36m"] = str(int(bucket.get("wind_event_count_36m", 0.0)))
        base["recent_storm_days"] = str(int(bucket.get("recent_storm_days", 0.0)))
        base["storm_severity_proxy"] = f"{bucket.get('storm_severity_proxy', 0.0):.2f}"
        base["trigger_notes"] = (
            f"NOAA county proxy join applied for {county.get('county_name') or county.get('county_fips')}; "
            f"hail {base['hail_event_count_36m']}, wind {base['wind_event_count_36m']}, recent {base['recent_storm_days']}d."
        )
        output_rows.append(base)

    write_csv(root / args.output, output_rows, BASE_TRIGGER_FIELDS)
    print(
        f"Wrote {root / args.output} with {len(output_rows)} rows; "
        f"matched={matched}, missing_crosswalk={missing_crosswalk}, storm_files={len(storm_rows)}"
    )


if __name__ == "__main__":
    main()
