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
VALID_STATUS = {"missing", "low", "medium", "high", "event_detected", "proxy", "verified"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _clip(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _default_ext_row(site_id: str) -> Dict[str, str]:
    # keep full trigger contract shape to avoid dropping columns from prior lanes
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


def _write_template(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "site_id",
                "flood_zone",
                "risk_status",
                "risk_score",
                "bfe_ft",
                "source",
                "as_of",
            ],
        )
        w.writeheader()


def _load_external(path: Path) -> Dict[str, Dict[str, str]]:
    rows = {}
    for row in _load_csv(path):
        sid = str(row.get("site_id") or "").strip()
        if not sid:
            continue
        rows[sid] = dict(row)
    return rows


def _parse_float(v: str) -> float | None:
    try:
        if v in ("", "None", None):
            return None
        return float(v)
    except Exception:
        return None


def _normalize_status(v: str) -> str | None:
    s = str(v or "").strip().lower()
    return s if s in VALID_STATUS else None


def _zone_to_score_status(zone: str) -> tuple[float | None, str | None]:
    z = str(zone or "").strip().upper()
    if not z:
        return None, None

    if z.startswith("VE") or z.startswith("V"):
        return 92.0, "verified"
    if z.startswith("AE") or z.startswith("AH") or z.startswith("AO") or z.startswith("AR") or z.startswith("A"):
        return 84.0, "verified"
    if "0.2" in z or z in {"X500", "SHADED X"}:
        return 56.0, "medium"
    if z.startswith("X"):
        return 24.0, "low"
    if z.startswith("D"):
        return 34.0, "low"

    return None, None


def _score_to_status(score: float) -> str:
    if score >= 82:
        return "high"
    if score >= 55:
        return "medium"
    if score >= 1:
        return "low"
    return "missing"


def _feed_row_to_trigger(feed: Dict[str, str]) -> Dict[str, str]:
    explicit_status = _normalize_status(feed.get("risk_status") or "")
    explicit_score = _parse_float(feed.get("risk_score") or "")
    zone_score, zone_status = _zone_to_score_status(feed.get("flood_zone") or "")

    score = explicit_score if explicit_score is not None else zone_score
    status = explicit_status or zone_status

    if status is None and score is not None:
        status = _score_to_status(score)

    if score is None:
        score = 0.0 if status in {"low", "medium", "high", "verified"} else None

    if status == "verified" and score is not None:
        score = max(score, 80.0)

    if status is None:
        status = "missing"

    return {
        "flood_risk_trigger_status": status,
        "flood_risk_trigger_score": "" if score is None else f"{_clip(score):.1f}",
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Overlay FEMA/NFHL parcel floodplain feed onto property trigger rows")
    p.add_argument("--sites-csv", default="data/processed/sites.csv")
    p.add_argument("--external", default="data/raw/property_triggers_external.csv")
    p.add_argument("--floodplain-feed", default="data/raw/fema_floodplain_site_feed.csv")
    p.add_argument("--output", default="data/raw/property_triggers_external.csv")
    p.add_argument("--summary-json", default="artifacts/fema-floodplain-trigger-summary.json")
    p.add_argument("--summary-md", default="artifacts/fema-floodplain-trigger-summary.md")
    p.add_argument("--coverage-md", default="artifacts/fema-floodplain-coverage.md")
    args = p.parse_args()

    now = _now_iso()
    sites_path = ROOT / args.sites_csv
    external_path = ROOT / args.external
    floodplain_feed_path = ROOT / args.floodplain_feed
    out_path = ROOT / args.output

    if not sites_path.exists():
        raise SystemExit(f"missing sites csv: {sites_path}")

    sites = _load_csv(sites_path)
    existing = _load_external(external_path)

    if not floodplain_feed_path.exists():
        _write_template(ROOT / "data/raw/fema_floodplain_site_feed.template.csv")

    feed_rows = _load_csv(floodplain_feed_path)
    feed_by_site = {}
    for row in feed_rows:
        sid = str(row.get("site_id") or "").strip()
        if not sid:
            continue
        feed_by_site[sid] = row

    output_rows: List[Dict[str, str]] = []
    zip_stats = defaultdict(lambda: {"sites": 0, "flood_non_missing": 0, "flood_missing": 0, "verified": 0, "fema_matched": 0})

    for site in sites:
        sid = str(site.get("site_id") or "").strip()
        if not sid:
            continue

        row = dict(existing.get(sid) or _default_ext_row(sid))
        row.setdefault("site_id", sid)
        for k in _default_ext_row(sid).keys():
            row.setdefault(k, _default_ext_row(sid).get(k, ""))

        feed = feed_by_site.get(sid)
        if feed:
            mapped = _feed_row_to_trigger(feed)
            row["flood_risk_trigger_status"] = mapped["flood_risk_trigger_status"]
            row["flood_risk_trigger_score"] = mapped["flood_risk_trigger_score"]

            zone = str(feed.get("flood_zone") or "").strip() or "unknown"
            bfe = str(feed.get("bfe_ft") or "").strip()
            src = str(feed.get("source") or "fema_nfhl").strip()
            feed_asof = str(feed.get("as_of") or now).strip()
            note = f"fema_zone={zone}"
            if bfe:
                note += f" bfe_ft={bfe}"
            note += f" source={src} asof={feed_asof}"
            prior = str(row.get("trigger_notes") or "").strip()
            row["trigger_notes"] = f"{prior}; {note}".strip("; ") if prior else note

        z = str(site.get("zip") or "").strip()
        row["zip"] = z
        zip_stats[z]["sites"] += 1
        status = str(row.get("flood_risk_trigger_status") or "missing")
        if status == "missing":
            zip_stats[z]["flood_missing"] += 1
        else:
            zip_stats[z]["flood_non_missing"] += 1
        if status == "verified":
            zip_stats[z]["verified"] += 1
        if sid in feed_by_site:
            zip_stats[z]["fema_matched"] += 1

        output_rows.append(row)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(_default_ext_row("sample").keys())
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(output_rows)

    status_counts = Counter(str(r.get("flood_risk_trigger_status") or "missing") for r in output_rows)
    summary = {
        "generated_at": now,
        "sites": len(output_rows),
        "floodplain_feed_exists": floodplain_feed_path.exists(),
        "floodplain_feed_rows": len(feed_rows),
        "matched_sites": sum(1 for r in output_rows if "fema_zone=" in str(r.get("trigger_notes") or "")),
        "status_counts": dict(status_counts),
        "zip_coverage": {k: dict(v) for k, v in sorted(zip_stats.items())},
        "output": str(out_path),
    }

    summary_json = ROOT / args.summary_json
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    summary_md_lines = [
        "# FEMA Floodplain Trigger Summary",
        "",
        f"- generated_at: `{now}`",
        f"- sites: **{len(output_rows)}**",
        f"- floodplain feed: `{floodplain_feed_path}`",
        f"- floodplain feed rows: **{len(feed_rows)}**",
        f"- matched sites: **{summary['matched_sites']}**",
        f"- output: `{out_path}`",
        "",
        "## Flood status counts",
        "",
    ]
    for k in sorted(status_counts.keys()):
        summary_md_lines.append(f"- `{k}`: {status_counts[k]}")

    summary_md_lines += [
        "",
        "## Notes",
        "- This lane upgrades flood triggers using parcel/site-level FEMA feed when provided.",
        "- If feed rows are zero, event-based NWS flood triggers remain the active flood proxy.",
    ]

    summary_md = ROOT / args.summary_md
    summary_md.parent.mkdir(parents=True, exist_ok=True)
    summary_md.write_text("\n".join(summary_md_lines) + "\n", encoding="utf-8")

    coverage_lines = [
        "# FEMA Floodplain Coverage",
        "",
        "Parcel/site-level FEMA floodplain feed coverage by ZIP.",
        "",
        "## Coverage by ZIP",
        "",
    ]
    for z, s in sorted(zip_stats.items()):
        n = s["sites"]
        matched = s["fema_matched"]
        verified = s["verified"]
        nn = s["flood_non_missing"]
        coverage_lines.append(
            f"- `{z}`: fema_matched={matched}/{n} ({(matched / n if n else 0):.1%}), flood_non_missing={nn}/{n} ({(nn / n if n else 0):.1%}), verified={verified}"
        )

    coverage_lines += [
        "",
        "## Interpretation",
        "- `fema_matched` tracks parcels/sites with authoritative floodplain rows loaded.",
        "- `flood_non_missing` can exceed `fema_matched` because event-based flood triggers may already exist.",
    ]

    coverage_md = ROOT / args.coverage_md
    coverage_md.parent.mkdir(parents=True, exist_ok=True)
    coverage_md.write_text("\n".join(coverage_lines) + "\n", encoding="utf-8")

    print(json.dumps({"ok": True, "sites": len(output_rows), "floodplain_feed_rows": len(feed_rows), "status_counts": dict(status_counts)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
