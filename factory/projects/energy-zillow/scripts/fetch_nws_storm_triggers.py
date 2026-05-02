#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import time
from collections import Counter
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


def _clip(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _event_score(event: str, severity: str) -> float:
    e = (event or "").lower()
    s = (severity or "unknown").lower()
    score = SEVERITY_BASE.get(s, 30.0)

    if "warning" in e:
        score += 15
    elif "watch" in e:
        score += 8
    elif "advisory" in e:
        score += 4
    elif "statement" in e:
        score += 2

    high_impact_keywords = [
        "tornado",
        "hurricane",
        "tropical storm",
        "severe thunderstorm",
        "high wind",
        "blizzard",
        "ice storm",
        "flash flood",
        "flood warning",
        "winter storm",
    ]
    if any(k in e for k in high_impact_keywords):
        score += 10

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
            alerts.append(
                {
                    "event": str(p.get("event") or "").strip(),
                    "severity": str(p.get("severity") or "unknown").strip(),
                    "urgency": str(p.get("urgency") or "unknown").strip(),
                    "headline": str(p.get("headline") or "").strip(),
                }
            )
        return True, alerts, ""
    except Exception as e:
        return False, [], str(e)


def main() -> int:
    p = argparse.ArgumentParser(description="Fetch NWS active alerts and project storm trigger scores by site state")
    p.add_argument("--sites-csv", default="data/processed/sites.csv")
    p.add_argument("--output", default="data/raw/property_triggers_external.csv")
    p.add_argument("--summary-json", default="artifacts/nws-trigger-fetch-summary.json")
    p.add_argument("--summary-md", default="artifacts/nws-trigger-fetch-summary.md")
    args = p.parse_args()

    sites_path = ROOT / args.sites_csv
    output_path = ROOT / args.output
    summary_json_path = ROOT / args.summary_json
    summary_md_path = ROOT / args.summary_md

    if not sites_path.exists():
        raise SystemExit(f"missing sites csv: {sites_path}")

    with sites_path.open("r", encoding="utf-8") as f:
        sites = list(csv.DictReader(f))

    states = sorted({str(r.get("state") or "").strip().upper() for r in sites if str(r.get("state") or "").strip()})

    state_rollup: Dict[str, Dict[str, object]] = {}
    for st in states:
        ok, alerts, err = _fetch_state_alerts(st)
        if not ok:
            state_rollup[st] = {
                "feed_ok": False,
                "storm_trigger_status": "missing",
                "storm_trigger_score": None,
                "alert_count": 0,
                "top_events": [],
                "error": err,
            }
            continue

        if not alerts:
            state_rollup[st] = {
                "feed_ok": True,
                "storm_trigger_status": "low",
                "storm_trigger_score": 0.0,
                "alert_count": 0,
                "top_events": [],
                "error": "",
            }
            continue

        scored = []
        for a in alerts:
            sc = _event_score(a.get("event", ""), a.get("severity", "unknown"))
            scored.append((sc, a))
        scored.sort(key=lambda x: x[0], reverse=True)
        top_score = scored[0][0]
        top_events = [x[1].get("event", "") for x in scored[:3]]

        state_rollup[st] = {
            "feed_ok": True,
            "storm_trigger_status": _status_from_score(top_score, True),
            "storm_trigger_score": round(top_score, 1),
            "alert_count": len(alerts),
            "top_events": top_events,
            "error": "",
        }
        time.sleep(0.2)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    output_rows = []
    for s in sites:
        site_id = str(s.get("site_id") or "").strip()
        if not site_id:
            continue
        st = str(s.get("state") or "").strip().upper()
        roll = state_rollup.get(st)

        if not roll:
            row = {
                "site_id": site_id,
                "storm_trigger_status": "missing",
                "outage_trigger_status": "missing",
                "equipment_age_trigger_status": "missing",
                "flood_risk_trigger_status": "missing",
                "storm_trigger_score": "",
                "outage_trigger_score": "",
                "equipment_age_trigger_score": "",
                "flood_risk_trigger_score": "",
                "trigger_notes": f"No state mapping found for `{st}` ({now})",
            }
        else:
            notes = []
            if roll.get("feed_ok"):
                notes.append(f"NWS active alerts checked for {st}")
                notes.append(f"alerts={roll.get('alert_count', 0)}")
                top_events = roll.get("top_events") or []
                if top_events:
                    notes.append("top=" + " | ".join(top_events))
                else:
                    notes.append("top=none")
            else:
                notes.append(f"NWS fetch failed for {st}: {roll.get('error')}")
            notes.append(f"asof={now}")

            row = {
                "site_id": site_id,
                "storm_trigger_status": roll.get("storm_trigger_status", "missing"),
                "outage_trigger_status": "missing",
                "equipment_age_trigger_status": "missing",
                "flood_risk_trigger_status": "missing",
                "storm_trigger_score": "" if roll.get("storm_trigger_score") is None else roll.get("storm_trigger_score"),
                "outage_trigger_score": "",
                "equipment_age_trigger_score": "",
                "flood_risk_trigger_score": "",
                "trigger_notes": "; ".join(notes),
            }
        output_rows.append(row)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
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
        w.writerows(output_rows)

    status_counts = Counter(str(r.get("storm_trigger_status") or "missing") for r in output_rows)
    summary = {
        "generated_at": now,
        "sites": len(output_rows),
        "states": states,
        "state_rollup": state_rollup,
        "storm_status_counts": dict(status_counts),
        "output": str(output_path),
    }

    summary_json_path.parent.mkdir(parents=True, exist_ok=True)
    summary_json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# NWS Trigger Fetch Summary",
        "",
        f"- generated_at: `{now}`",
        f"- sites: **{len(output_rows)}**",
        f"- output: `{output_path}`",
        "",
        "## Storm status counts",
        "",
    ]
    for k in sorted(status_counts.keys()):
        md_lines.append(f"- `{k}`: {status_counts[k]}")

    md_lines += ["", "## State rollup", ""]
    for st in states:
        roll = state_rollup.get(st, {})
        md_lines.append(
            f"- `{st}`: status={roll.get('storm_trigger_status')} score={roll.get('storm_trigger_score')} alerts={roll.get('alert_count')} feed_ok={roll.get('feed_ok')}"
        )

    summary_md_path.parent.mkdir(parents=True, exist_ok=True)
    summary_md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(json.dumps({"ok": True, "sites": len(output_rows), "output": str(output_path), "summary": str(summary_json_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
