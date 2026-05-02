#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[1]


def _as_float(value: str):
    try:
        if value in ("", "None", None):
            return None
        return float(value)
    except Exception:
        return None


def _clip(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _status_from_outage_pct(outage_pct: float) -> str:
    if outage_pct >= 15.0:
        return "event_detected"
    if outage_pct >= 8.0:
        return "high"
    if outage_pct >= 3.0:
        return "medium"
    return "low"


def _score_from_outage_pct(outage_pct: float) -> float:
    return round(_clip(outage_pct * 6.5, 0.0, 100.0), 1)


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


def load_state_feed(path: Path) -> Dict[str, Dict[str, str]]:
    if not path.exists():
        return {}
    out = {}
    with path.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            st = str(r.get("state") or "").strip().upper()
            if st:
                out[st] = dict(r)
    return out


def main() -> int:
    p = argparse.ArgumentParser(description="Project state-level outage feed to site-level outage trigger columns")
    p.add_argument("--sites-csv", default="data/processed/sites.csv")
    p.add_argument("--external", default="data/raw/property_triggers_external.csv")
    p.add_argument("--state-feed", default="data/raw/state_outage_feed.csv")
    p.add_argument("--output", default="data/raw/property_triggers_external.csv")
    args = p.parse_args()

    sites = load_sites(ROOT / args.sites_csv)
    existing = load_external(ROOT / args.external)
    state_feed = load_state_feed(ROOT / args.state_feed)

    out_rows = []
    matched_states = 0

    for s in sites:
        site_id = str(s.get("site_id") or "").strip()
        if not site_id:
            continue

        base = existing.get(site_id, {
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
        }).copy()

        state = str(s.get("state") or "").strip().upper()
        feed = state_feed.get(state)
        if feed:
            matched_states += 1
            outage_pct = _as_float(feed.get("outage_pct")) or 0.0
            base["outage_trigger_status"] = _status_from_outage_pct(outage_pct)
            base["outage_trigger_score"] = str(_score_from_outage_pct(outage_pct))

            source = str(feed.get("source") or "state-feed")
            asof = str(feed.get("asof") or "")
            note = f"outage_pct={outage_pct:.2f}% source={source}"
            if asof:
                note += f" asof={asof}"
            prior = str(base.get("trigger_notes") or "").strip()
            base["trigger_notes"] = (prior + "; " + note).strip("; ") if prior else note

        out_rows.append(base)

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

    print(f"wrote {out_path} rows={len(out_rows)} matched_state_rows={matched_states} state_feed={'present' if state_feed else 'missing'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
