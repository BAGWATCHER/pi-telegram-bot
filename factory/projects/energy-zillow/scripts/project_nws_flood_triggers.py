#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import requests

ROOT = Path(__file__).resolve().parents[1]
NWS_BASE = "https://api.weather.gov/alerts/active"

SEVERITY_BASE = {
    "extreme": 90.0,
    "severe": 80.0,
    "moderate": 65.0,
    "minor": 45.0,
    "unknown": 30.0,
}

FLOOD_KEYWORDS = (
    "flood",
    "flash flood",
    "coastal flood",
    "lakeshore flood",
)


def _clip(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _is_flood_event(event: str) -> bool:
    e = (event or "").strip().lower()
    if not e:
        return False
    return any(k in e for k in FLOOD_KEYWORDS)


def _event_score(event: str, severity: str) -> float:
    e = (event or "").lower()
    s = (severity or "unknown").lower()
    score = SEVERITY_BASE.get(s, 30.0)

    if "warning" in e:
        score += 16
    elif "watch" in e:
        score += 9
    elif "advisory" in e:
        score += 4
    elif "statement" in e:
        score += 2

    if "flash flood" in e:
        score += 14
    elif "coastal flood" in e:
        score += 9
    elif "flood" in e:
        score += 6

    return _clip(score)


def _status_from_score(score: float, has_feed: bool) -> str:
    if not has_feed:
        return "missing"
    if score >= 88:
        return "event_detected"
    if score >= 72:
        return "high"
    if score >= 48:
        return "medium"
    return "low"


def _fetch_state_alerts(state: str, timeout_s: int = 12) -> Tuple[bool, List[Dict[str, str]], str]:
    url = f"{NWS_BASE}?area={state}"
    headers = {
        "User-Agent": "EnergyZillow/0.1 (mrchow@local)",
        "Accept": "application/geo+json",
    }

    try:
        r = requests.get(url, headers=headers, timeout=timeout_s)
        r.raise_for_status()
        body = r.json()
        features = body.get("features") or []
        alerts: List[Dict[str, str]] = []
        for f in features:
            p = (f or {}).get("properties") or {}
            event = str(p.get("event") or "").strip()
            if not _is_flood_event(event):
                continue
            alerts.append(
                {
                    "event": event,
                    "severity": str(p.get("severity") or "unknown").strip(),
                    "urgency": str(p.get("urgency") or "unknown").strip(),
                    "headline": str(p.get("headline") or "").strip(),
                }
            )
        return True, alerts, ""
    except Exception as e:
        return False, [], str(e)


def load_sites(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_external(path: Path) -> Dict[str, Dict[str, str]]:
    if not path.exists():
        return {}
    rows: Dict[str, Dict[str, str]] = {}
    with path.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            sid = str(r.get("site_id") or "").strip()
            if sid:
                rows[sid] = dict(r)
    return rows


def _default_row(site_id: str) -> Dict[str, str]:
    return {
        "site_id": site_id,
        "storm_trigger_status": "missing",
        "outage_trigger_status": "missing",
        "equipment_age_trigger_status": "missing",
        "flood_risk_trigger_status": "missing",
        "storm_trigger_score": "",
        "outage_trigger_score": "",
        "equipment_age_trigger_score": "",
        "flood_risk_trigger_score": "",
        "trigger_notes": "",
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Overlay NWS flood-specific triggers onto property trigger rows")
    p.add_argument("--sites-csv", default="data/processed/sites.csv")
    p.add_argument("--external", default="data/raw/property_triggers_external.csv")
    p.add_argument("--output", default="data/raw/property_triggers_external.csv")
    p.add_argument("--summary-json", default="artifacts/nws-flood-trigger-summary.json")
    p.add_argument("--summary-md", default="artifacts/nws-flood-trigger-summary.md")
    p.add_argument("--coverage-md", default="artifacts/flood-trigger-coverage.md")
    args = p.parse_args()

    sites = load_sites(ROOT / args.sites_csv)
    existing = load_external(ROOT / args.external)

    states = sorted({str(s.get("state") or "").strip().upper() for s in sites if str(s.get("state") or "").strip()})

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    state_rollup: Dict[str, Dict[str, object]] = {}
    for st in states:
        ok, alerts, err = _fetch_state_alerts(st)
        if not ok:
            state_rollup[st] = {
                "feed_ok": False,
                "flood_risk_trigger_status": "missing",
                "flood_risk_trigger_score": None,
                "alert_count": 0,
                "top_events": [],
                "error": err,
            }
            continue

        if not alerts:
            state_rollup[st] = {
                "feed_ok": True,
                "flood_risk_trigger_status": "low",
                "flood_risk_trigger_score": 0.0,
                "alert_count": 0,
                "top_events": [],
                "error": "",
            }
            continue

        scored = sorted(((_event_score(a.get("event", ""), a.get("severity", "unknown")), a) for a in alerts), key=lambda x: x[0], reverse=True)
        top_score = scored[0][0]
        top_events = [x[1].get("event", "") for x in scored[:3]]

        state_rollup[st] = {
            "feed_ok": True,
            "flood_risk_trigger_status": _status_from_score(top_score, True),
            "flood_risk_trigger_score": round(top_score, 1),
            "alert_count": len(alerts),
            "top_events": top_events,
            "error": "",
        }
        time.sleep(0.2)

    out_rows = []
    zip_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: {"sites": 0, "flood_non_missing": 0, "flood_missing": 0})

    for s in sites:
        site_id = str(s.get("site_id") or "").strip()
        if not site_id:
            continue

        base = existing.get(site_id, _default_row(site_id)).copy()
        st = str(s.get("state") or "").strip().upper()
        z = str(s.get("zip") or "").strip()
        roll = state_rollup.get(st)

        if roll:
            base["flood_risk_trigger_status"] = str(roll.get("flood_risk_trigger_status") or "missing")
            score = roll.get("flood_risk_trigger_score")
            base["flood_risk_trigger_score"] = "" if score is None else str(score)

            note_bits = []
            if roll.get("feed_ok"):
                note_bits.append(f"flood_nws={st}")
                note_bits.append(f"flood_alerts={roll.get('alert_count', 0)}")
                top_events = roll.get("top_events") or []
                note_bits.append("flood_top=" + (" | ".join(top_events) if top_events else "none"))
            else:
                note_bits.append(f"flood_nws_error={st}:{roll.get('error')}")
            note_bits.append(f"flood_asof={now}")

            prior = str(base.get("trigger_notes") or "").strip()
            flood_note = " ".join(note_bits)
            base["trigger_notes"] = (prior + "; " + flood_note).strip("; ") if prior else flood_note

        out_rows.append(base)

        zip_counts[z]["sites"] += 1
        if str(base.get("flood_risk_trigger_status") or "missing") == "missing":
            zip_counts[z]["flood_missing"] += 1
        else:
            zip_counts[z]["flood_non_missing"] += 1

    out_path = ROOT / args.output
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
        w.writerows(out_rows)

    status_counts = Counter(str(r.get("flood_risk_trigger_status") or "missing") for r in out_rows)
    summary = {
        "generated_at": now,
        "sites": len(out_rows),
        "states": states,
        "state_rollup": state_rollup,
        "flood_status_counts": dict(status_counts),
        "zip_coverage": {k: dict(v) for k, v in sorted(zip_counts.items())},
        "output": str(out_path),
    }

    summary_json_path = ROOT / args.summary_json
    summary_json_path.parent.mkdir(parents=True, exist_ok=True)
    summary_json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    summary_md_lines = [
        "# NWS Flood Trigger Summary",
        "",
        f"- generated_at: `{now}`",
        f"- sites: **{len(out_rows)}**",
        f"- output: `{out_path}`",
        "",
        "## Flood status counts",
        "",
    ]
    for k in sorted(status_counts.keys()):
        summary_md_lines.append(f"- `{k}`: {status_counts[k]}")

    summary_md_lines += ["", "## State rollup", ""]
    for st in states:
        roll = state_rollup.get(st, {})
        summary_md_lines.append(
            f"- `{st}`: status={roll.get('flood_risk_trigger_status')} score={roll.get('flood_risk_trigger_score')} alerts={roll.get('alert_count')} feed_ok={roll.get('feed_ok')}"
        )

    summary_md_path = ROOT / args.summary_md
    summary_md_path.parent.mkdir(parents=True, exist_ok=True)
    summary_md_path.write_text("\n".join(summary_md_lines) + "\n", encoding="utf-8")

    coverage_lines = [
        "# Flood Trigger Coverage",
        "",
        "Flood trigger lane overlays NWS flood-focused alerts per state and projects to site rows.",
        "",
        "## Coverage by ZIP",
        "",
    ]
    for z, stats in sorted(zip_counts.items()):
        sites_n = stats["sites"]
        nn = stats["flood_non_missing"]
        ratio = (nn / sites_n) if sites_n else 0.0
        coverage_lines.append(f"- `{z}`: non-missing={nn}/{sites_n} ({ratio:.1%}), missing={stats['flood_missing']}")

    coverage_lines += [
        "",
        "## Notes",
        "- `low` with score `0.0` means feed loaded and no active flood alerts at fetch time.",
        "- This lane is event-triggered, not parcel-level FEMA floodplain risk.",
    ]
    coverage_md_path = ROOT / args.coverage_md
    coverage_md_path.parent.mkdir(parents=True, exist_ok=True)
    coverage_md_path.write_text("\n".join(coverage_lines) + "\n", encoding="utf-8")

    print(json.dumps({"ok": True, "sites": len(out_rows), "status_counts": dict(status_counts), "output": str(out_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
