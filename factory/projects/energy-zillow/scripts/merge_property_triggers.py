#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALID_STATUS = {"missing", "low", "medium", "high", "event_detected", "proxy", "verified"}
TRIGGER_FIELDS = [
    "site_id",
    "zip",
    "storm_trigger_status",
    "outage_trigger_status",
    "equipment_age_trigger_status",
    "flood_risk_trigger_status",
    "permit_trigger_status",
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
    "permit_trigger_score",
    "permit_recent_count",
    "permit_recent_types",
    "permit_last_date",
    "permit_last_type",
    "trigger_notes",
]


def _as_int_text(value):
    try:
        if value in ("", "None", None):
            return ""
        return str(int(float(value)))
    except Exception:
        return ""


def _as_float(value: str):
    try:
        if value in ("", "None", None):
            return None
        return float(value)
    except Exception:
        return None


def _norm_status(value: str) -> str:
    s = str(value or "missing").strip().lower()
    return s if s in VALID_STATUS else "missing"


def load_existing(path: Path):
    if not path.exists():
        return {}
    out = {}
    with path.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            site_id = str(row.get("site_id") or "").strip()
            if not site_id:
                continue
            out[site_id] = {
                "zip": str(row.get("zip") or "").strip(),
                "storm_trigger_status": _norm_status(row.get("storm_trigger_status") or "missing"),
                "outage_trigger_status": _norm_status(row.get("outage_trigger_status") or "missing"),
                "equipment_age_trigger_status": _norm_status(row.get("equipment_age_trigger_status") or "missing"),
                "flood_risk_trigger_status": _norm_status(row.get("flood_risk_trigger_status") or "missing"),
                "permit_trigger_status": _norm_status(row.get("permit_trigger_status") or "missing"),
                "storm_trigger_score": _as_float(row.get("storm_trigger_score")),
                "storm_event_count_12m": _as_int_text(row.get("storm_event_count_12m")),
                "storm_event_count_36m": _as_int_text(row.get("storm_event_count_36m")),
                "hail_event_count_36m": _as_int_text(row.get("hail_event_count_36m")),
                "wind_event_count_36m": _as_int_text(row.get("wind_event_count_36m")),
                "recent_storm_days": _as_int_text(row.get("recent_storm_days")),
                "storm_severity_proxy": _as_float(row.get("storm_severity_proxy")),
                "outage_trigger_score": _as_float(row.get("outage_trigger_score")),
                "equipment_age_trigger_score": _as_float(row.get("equipment_age_trigger_score")),
                "flood_risk_trigger_score": _as_float(row.get("flood_risk_trigger_score")),
                "permit_trigger_score": _as_float(row.get("permit_trigger_score")),
                "permit_recent_count": _as_int_text(row.get("permit_recent_count")),
                "permit_recent_types": str(row.get("permit_recent_types") or "").strip(),
                "permit_last_date": str(row.get("permit_last_date") or "").strip(),
                "permit_last_type": str(row.get("permit_last_type") or "").strip(),
                "trigger_notes": str(row.get("trigger_notes") or "").strip(),
            }
    return out


def load_external(path: Path):
    if not path.exists():
        return {}
    out = {}
    with path.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            site_id = str(row.get("site_id") or "").strip()
            if not site_id:
                continue
            out[site_id] = {
                "storm_trigger_status": _norm_status(row.get("storm_trigger_status") or "missing"),
                "outage_trigger_status": _norm_status(row.get("outage_trigger_status") or "missing"),
                "equipment_age_trigger_status": _norm_status(row.get("equipment_age_trigger_status") or "missing"),
                "flood_risk_trigger_status": _norm_status(row.get("flood_risk_trigger_status") or "missing"),
                "permit_trigger_status": _norm_status(row.get("permit_trigger_status") or "missing"),
                "storm_trigger_score": _as_float(row.get("storm_trigger_score")),
                "outage_trigger_score": _as_float(row.get("outage_trigger_score")),
                "equipment_age_trigger_score": _as_float(row.get("equipment_age_trigger_score")),
                "flood_risk_trigger_score": _as_float(row.get("flood_risk_trigger_score")),
                "permit_trigger_score": _as_float(row.get("permit_trigger_score")),
                "permit_recent_count": _as_int_text(row.get("permit_recent_count")),
                "permit_recent_types": str(row.get("permit_recent_types") or "").strip(),
                "permit_last_date": str(row.get("permit_last_date") or "").strip(),
                "permit_last_type": str(row.get("permit_last_type") or "").strip(),
                "trigger_notes": str(row.get("trigger_notes") or "").strip(),
            }
    return out


def _prefer_status(existing: str, incoming: str) -> str:
    inc = _norm_status(incoming)
    cur = _norm_status(existing)
    return cur if inc == "missing" and cur != "missing" else inc


def _prefer_numeric(existing, incoming):
    return existing if incoming is None and existing not in ("", None) else incoming


def _prefer_text(existing: str, incoming: str) -> str:
    inc = str(incoming or "").strip()
    cur = str(existing or "").strip()
    return cur if not inc else inc


def main() -> int:
    p = argparse.ArgumentParser(description="Merge external trigger signals onto site universe")
    p.add_argument("--sites-csv", default="data/processed/sites.csv")
    p.add_argument("--external", default="data/raw/property_triggers_external.csv")
    p.add_argument("--output", default="data/processed/property_triggers.csv")
    args = p.parse_args()

    sites_path = ROOT / args.sites_csv
    ext_path = ROOT / args.external
    out_path = ROOT / args.output

    if not sites_path.exists():
        raise SystemExit(f"missing sites csv: {sites_path}")

    with sites_path.open("r", encoding="utf-8") as f:
        sites = list(csv.DictReader(f))

    existing = load_existing(out_path)
    ext = load_external(ext_path)

    rows = []
    for site in sites:
        site_id = str(site.get("site_id") or "").strip()
        if not site_id:
            continue

        payload = dict(existing.get(site_id) or {})
        payload.setdefault("zip", str(site.get("zip") or "").strip())
        if site_id in ext:
            incoming = ext[site_id]
            payload["storm_trigger_status"] = _prefer_status(payload.get("storm_trigger_status"), incoming.get("storm_trigger_status"))
            payload["outage_trigger_status"] = _prefer_status(payload.get("outage_trigger_status"), incoming.get("outage_trigger_status"))
            payload["equipment_age_trigger_status"] = _prefer_status(payload.get("equipment_age_trigger_status"), incoming.get("equipment_age_trigger_status"))
            payload["flood_risk_trigger_status"] = _prefer_status(payload.get("flood_risk_trigger_status"), incoming.get("flood_risk_trigger_status"))
            payload["permit_trigger_status"] = _prefer_status(payload.get("permit_trigger_status"), incoming.get("permit_trigger_status"))
            payload["storm_trigger_score"] = _prefer_numeric(payload.get("storm_trigger_score"), incoming.get("storm_trigger_score"))
            payload["outage_trigger_score"] = _prefer_numeric(payload.get("outage_trigger_score"), incoming.get("outage_trigger_score"))
            payload["equipment_age_trigger_score"] = _prefer_numeric(payload.get("equipment_age_trigger_score"), incoming.get("equipment_age_trigger_score"))
            payload["flood_risk_trigger_score"] = _prefer_numeric(payload.get("flood_risk_trigger_score"), incoming.get("flood_risk_trigger_score"))
            payload["permit_trigger_score"] = _prefer_numeric(payload.get("permit_trigger_score"), incoming.get("permit_trigger_score"))
            payload["permit_recent_count"] = _prefer_text(payload.get("permit_recent_count"), incoming.get("permit_recent_count"))
            payload["permit_recent_types"] = _prefer_text(payload.get("permit_recent_types"), incoming.get("permit_recent_types"))
            payload["permit_last_date"] = _prefer_text(payload.get("permit_last_date"), incoming.get("permit_last_date"))
            payload["permit_last_type"] = _prefer_text(payload.get("permit_last_type"), incoming.get("permit_last_type"))
            payload["trigger_notes"] = _prefer_text(payload.get("trigger_notes"), incoming.get("trigger_notes"))
        elif not payload:
            payload = {
                "zip": str(site.get("zip") or "").strip(),
                "storm_trigger_status": "missing",
                "outage_trigger_status": "missing",
                "equipment_age_trigger_status": "missing",
                "flood_risk_trigger_status": "missing",
                "permit_trigger_status": "missing",
                "storm_trigger_score": None,
                "storm_event_count_12m": "",
                "storm_event_count_36m": "",
                "hail_event_count_36m": "",
                "wind_event_count_36m": "",
                "recent_storm_days": "",
                "storm_severity_proxy": None,
                "outage_trigger_score": None,
                "equipment_age_trigger_score": None,
                "flood_risk_trigger_score": None,
                "permit_trigger_score": None,
                "permit_recent_count": "",
                "permit_recent_types": "",
                "permit_last_date": "",
                "permit_last_type": "",
                "trigger_notes": "screening contract stub; external trigger layers not loaded",
            }

        for field in TRIGGER_FIELDS:
            payload.setdefault(field, "" if field not in {
                "storm_trigger_score",
                "storm_severity_proxy",
                "outage_trigger_score",
                "equipment_age_trigger_score",
                "flood_risk_trigger_score",
                "permit_trigger_score",
            } else None)

        rows.append({**payload, "site_id": site_id})

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=TRIGGER_FIELDS,
        )
        w.writeheader()
        w.writerows(rows)

    matched = sum(1 for r in rows if r["trigger_notes"] != "screening contract stub; external trigger layers not loaded")
    print(f"wrote {out_path} rows={len(rows)} matched_external={matched} external_path={ext_path if ext_path.exists() else 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
