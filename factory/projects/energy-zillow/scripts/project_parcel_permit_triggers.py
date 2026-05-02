#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _default_ext_row(site_id: str) -> Dict[str, str]:
    # keep full trigger contract shape to avoid dropping fields from other lanes
    return {
        "site_id": site_id,
        "zip": "",
        "storm_trigger_status": "missing",
        "outage_trigger_status": "missing",
        "equipment_age_trigger_status": "missing",
        "flood_risk_trigger_status": "missing",
        "permit_trigger_status": "missing",
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
        "permit_trigger_score": "",
        "permit_recent_count": "",
        "permit_recent_types": "",
        "permit_last_date": "",
        "permit_last_type": "",
        "trigger_notes": "",
    }


def _load_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _load_external(path: Path) -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for row in _load_csv(path):
        sid = str(row.get("site_id") or "").strip()
        if sid:
            out[sid] = dict(row)
    return out


def _parse_year(value: str) -> int | None:
    txt = str(value or "").strip()
    if len(txt) >= 4 and txt[:4].isdigit():
        try:
            return int(txt[:4])
        except Exception:
            return None
    return None


def _classify_equipment_age(last_hvac_year: int | None, now_year: int) -> tuple[str, float | None]:
    if not last_hvac_year:
        return "missing", None
    age = max(0, now_year - last_hvac_year)
    if age >= 18:
        return "high", 88.0
    if age >= 12:
        return "medium", 68.0
    return "low", 34.0


def _classify_roof_signal(last_roof_year: int | None, now_year: int) -> tuple[str, float | None]:
    if not last_roof_year:
        return "missing", None
    age = max(0, now_year - last_roof_year)
    if age >= 22:
        return "high", 82.0
    if age >= 14:
        return "medium", 62.0
    return "low", 30.0


def _classify_permit_activity(last_permit_year: int | None, now_year: int) -> tuple[str, float | None]:
    if not last_permit_year:
        return "missing", None
    age = max(0, now_year - last_permit_year)
    if age <= 2:
        return "event_detected", 92.0
    if age <= 5:
        return "high", 78.0
    if age <= 10:
        return "medium", 58.0
    return "low", 34.0


def main() -> int:
    p = argparse.ArgumentParser(description="Overlay parcel permit-history signals onto trigger rows")
    p.add_argument("--sites-csv", default="data/processed/sites.csv")
    p.add_argument("--external", default="data/raw/property_triggers_external.csv")
    p.add_argument("--permit-feed", default="data/raw/parcel_permit_feed.csv")
    p.add_argument("--output", default="data/raw/property_triggers_external.csv")
    p.add_argument("--summary-json", default="artifacts/permit-trigger-summary.json")
    p.add_argument("--summary-md", default="artifacts/permit-trigger-summary.md")
    p.add_argument("--coverage-md", default="artifacts/permit-trigger-coverage.md")
    args = p.parse_args()

    sites_path = ROOT / args.sites_csv
    external_path = ROOT / args.external
    permit_feed_path = ROOT / args.permit_feed
    output_path = ROOT / args.output

    if not sites_path.exists():
        raise SystemExit(f"missing sites csv: {sites_path}")

    now_iso = _now_iso()
    now_year = datetime.now(timezone.utc).year

    sites = _load_csv(sites_path)
    external = _load_external(external_path)
    permits = _load_csv(permit_feed_path)

    by_site_permits: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in permits:
        sid = str(row.get("site_id") or "").strip()
        if not sid:
            continue
        by_site_permits[sid].append(row)

    output_rows: List[Dict[str, str]] = []
    zip_stats = defaultdict(lambda: {"sites": 0, "permit_matched": 0, "equipment_non_missing": 0, "roof_non_missing": 0})

    for site in sites:
        sid = str(site.get("site_id") or "").strip()
        if not sid:
            continue
        z = str(site.get("zip") or "").strip()

        row = dict(external.get(sid) or _default_ext_row(sid))
        row.setdefault("site_id", sid)
        for k, v in _default_ext_row(sid).items():
            row.setdefault(k, v)
        row["zip"] = z

        site_permits = by_site_permits.get(sid, [])
        roof_years: List[int] = []
        hvac_years: List[int] = []
        permit_years: List[int] = []
        permit_type_dates: List[tuple[str, str]] = []
        recent_types: List[str] = []

        for perm in site_permits:
            ptype = str(perm.get("permit_type") or "").strip().lower()
            pdate = str(perm.get("permit_date") or "").strip()
            pyear = _parse_year(str(perm.get("permit_date") or ""))
            if not pyear:
                continue
            permit_years.append(pyear)
            permit_type_dates.append((pdate, ptype))
            if any(k in ptype for k in ["roof", "re-roof", "reroof"]):
                roof_years.append(pyear)
            if any(k in ptype for k in ["hvac", "heat", "furnace", "boiler", "air", "mechanical"]):
                hvac_years.append(pyear)
            if pyear >= (now_year - 5) and ptype:
                recent_types.append(ptype)

        last_roof = max(roof_years) if roof_years else None
        last_hvac = max(hvac_years) if hvac_years else None
        last_permit_year = max(permit_years) if permit_years else None

        eq_status, eq_score = _classify_equipment_age(last_hvac, now_year)
        roof_status, roof_score = _classify_roof_signal(last_roof, now_year)
        permit_status, permit_score = _classify_permit_activity(last_permit_year, now_year)

        if eq_status != "missing":
            row["equipment_age_trigger_status"] = eq_status
            row["equipment_age_trigger_score"] = f"{eq_score:.1f}" if eq_score is not None else row.get("equipment_age_trigger_score", "")
        if roof_status != "missing":
            row["storm_trigger_status"] = roof_status
            row["storm_trigger_score"] = f"{roof_score:.1f}" if roof_score is not None else row.get("storm_trigger_score", "")
        if permit_status != "missing":
            row["permit_trigger_status"] = permit_status
            row["permit_trigger_score"] = f"{permit_score:.1f}" if permit_score is not None else row.get("permit_trigger_score", "")
            row["permit_recent_count"] = str(sum(1 for year in permit_years if year >= (now_year - 5)))
            row["permit_recent_types"] = "|".join(sorted(set(recent_types)))
            if permit_type_dates:
                last_date, last_type = max(permit_type_dates, key=lambda item: item[0] or "")
                row["permit_last_date"] = last_date
                row["permit_last_type"] = last_type

        if site_permits:
            prior = str(row.get("trigger_notes") or "").strip()
            note = f"permit_rows={len(site_permits)} permit_asof={now_iso}"
            if last_roof:
                note += f" roof_last={last_roof}"
            if last_hvac:
                note += f" hvac_last={last_hvac}"
            if row.get("permit_last_date"):
                note += f" permit_last={row.get('permit_last_date')}"
            if row.get("permit_recent_types"):
                note += f" permit_types={row.get('permit_recent_types')}"
            row["trigger_notes"] = f"{prior}; {note}".strip("; ") if prior else note

        zip_stats[z]["sites"] += 1
        if site_permits:
            zip_stats[z]["permit_matched"] += 1
        if str(row.get("equipment_age_trigger_status") or "missing") != "missing":
            zip_stats[z]["equipment_non_missing"] += 1
        if str(row.get("storm_trigger_status") or "missing") != "missing":
            zip_stats[z]["roof_non_missing"] += 1

        output_rows.append(row)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=list(_default_ext_row("sample").keys()),
        )
        w.writeheader()
        w.writerows(output_rows)

    equipment_counts = Counter(str(r.get("equipment_age_trigger_status") or "missing") for r in output_rows)
    storm_counts = Counter(str(r.get("storm_trigger_status") or "missing") for r in output_rows)

    summary = {
        "generated_at": now_iso,
        "sites": len(output_rows),
        "permit_rows": len(permits),
        "permit_sites_matched": sum(1 for r in zip_stats.values() if r["permit_matched"] > 0),
        "equipment_status_counts": dict(equipment_counts),
        "storm_status_counts": dict(storm_counts),
        "permit_status_counts": dict(Counter(str(r.get("permit_trigger_status") or "missing") for r in output_rows)),
        "zip_coverage": {k: dict(v) for k, v in sorted(zip_stats.items())},
        "output": str(output_path),
    }

    summary_json = ROOT / args.summary_json
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# Permit Trigger Summary",
        "",
        f"- generated_at: `{now_iso}`",
        f"- sites: **{len(output_rows)}**",
        f"- permit rows loaded: **{len(permits)}**",
        f"- output: `{output_path}`",
        "",
        "## Equipment status counts",
        "",
    ]
    for k in sorted(equipment_counts.keys()):
        md_lines.append(f"- `{k}`: {equipment_counts[k]}")

    md_lines += ["", "## Roofing/storm status counts", ""]
    for k in sorted(storm_counts.keys()):
        md_lines.append(f"- `{k}`: {storm_counts[k]}")

    permit_counts = Counter(str(r.get("permit_trigger_status") or "missing") for r in output_rows)
    md_lines += ["", "## Permit activity status counts", ""]
    for k in sorted(permit_counts.keys()):
        md_lines.append(f"- `{k}`: {permit_counts[k]}")

    (ROOT / args.summary_md).write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    cov_lines = [
        "# Permit Trigger Coverage",
        "",
        "Coverage by ZIP for permit-linked rows and resulting non-missing trigger fields.",
        "",
    ]
    for z, s in sorted(zip_stats.items()):
        n = s["sites"]
        cov_lines.append(
            f"- `{z}`: permit_matched={s['permit_matched']}/{n} ({(s['permit_matched']/n if n else 0):.1%}), equipment_non_missing={s['equipment_non_missing']}/{n} ({(s['equipment_non_missing']/n if n else 0):.1%}), roof_non_missing={s['roof_non_missing']}/{n} ({(s['roof_non_missing']/n if n else 0):.1%})"
        )

    (ROOT / args.coverage_md).write_text("\n".join(cov_lines) + "\n", encoding="utf-8")

    print(json.dumps({"ok": True, "sites": len(output_rows), "permit_rows": len(permits)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
