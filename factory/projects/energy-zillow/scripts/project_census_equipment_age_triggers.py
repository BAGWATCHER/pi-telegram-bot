#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import requests
import subprocess
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
CENSUS_YEAR = "2023"
CENSUS_DATASET = "acs/acs5"
CENSUS_VAR = "B25035_001E"  # Median year structure built
CENSUS_BASE = f"https://api.census.gov/data/{CENSUS_YEAR}/{CENSUS_DATASET}"


def _clip(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _status_from_age(age_years: float) -> str:
    if age_years >= 55:
        return "event_detected"
    if age_years >= 45:
        return "high"
    if age_years >= 30:
        return "medium"
    return "low"


def _score_from_age(age_years: float) -> float:
    # conservative linear proxy; 30y -> 40, 45y -> 70, 60y -> 100
    return round(_clip((age_years - 10.0) * 2.0, 0.0, 100.0), 1)


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


def _parse_census_rows(body: object) -> Tuple[bool, Dict[str, int], str]:
    if not isinstance(body, list) or len(body) < 2:
        return False, {}, "unexpected census response shape"

    header = body[0]
    try:
        idx_var = header.index(CENSUS_VAR)
        idx_zip = header.index("zip code tabulation area")
    except ValueError:
        return False, {}, "missing expected columns in census response"

    out: Dict[str, int] = {}
    for row in body[1:]:
        if not isinstance(row, list):
            continue
        z = str(row[idx_zip]).strip()
        raw = str(row[idx_var]).strip()
        if not z or raw in ("", "-666666666", "-999999999"):
            continue
        try:
            year_built = int(float(raw))
        except Exception:
            continue
        if 1700 <= year_built <= 2026:
            out[z] = year_built
    return True, out, ""


def _fetch_zip_median_year_built(zips: List[str], timeout_s: int = 45) -> Tuple[bool, Dict[str, int], str]:
    if not zips:
        return True, {}, ""

    get_value = quote(f"NAME,{CENSUS_VAR}", safe=",")
    for_value = quote(f"zip code tabulation area:{','.join(zips)}", safe=":,")
    url = f"{CENSUS_BASE}?get={get_value}&for={for_value}"

    # path A: requests
    try:
        r = requests.get(url, timeout=(10, timeout_s))
        r.raise_for_status()
        ok, rows, err = _parse_census_rows(r.json())
        if ok:
            return True, rows, ""
        req_err = err
    except Exception as e:
        req_err = str(e)

    # path B: curl fallback (often more resilient on this VM)
    try:
        p = subprocess.run(["curl", "-m", str(timeout_s), "-sS", url], capture_output=True, text=True, check=False)
        if p.returncode != 0:
            return False, {}, f"requests_error={req_err}; curl_error={p.stderr.strip() or p.stdout.strip()}"
        payload = json.loads(p.stdout)
        ok, rows, err = _parse_census_rows(payload)
        if ok:
            return True, rows, ""
        return False, {}, f"requests_error={req_err}; curl_parse_error={err}"
    except Exception as e:
        return False, {}, f"requests_error={req_err}; curl_exception={e}"


def load_zip_feed(path: Path) -> Dict[str, Dict[str, str]]:
    if not path.exists():
        return {}
    out: Dict[str, Dict[str, str]] = {}
    with path.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            z = str(r.get("zip") or "").strip()
            if z:
                out[z] = dict(r)
    return out


def save_zip_feed(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "zip",
                "median_year_built",
                "median_structure_age_years",
                "equipment_age_trigger_status",
                "equipment_age_trigger_score",
                "source",
                "asof",
            ],
        )
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    p = argparse.ArgumentParser(description="Overlay Census ZIP-level equipment-age triggers onto property trigger rows")
    p.add_argument("--sites-csv", default="data/processed/sites.csv")
    p.add_argument("--external", default="data/raw/property_triggers_external.csv")
    p.add_argument("--output", default="data/raw/property_triggers_external.csv")
    p.add_argument("--zip-feed", default="data/raw/zip_equipment_age_feed.csv")
    p.add_argument("--summary-json", default="artifacts/equipment-age-trigger-summary.json")
    p.add_argument("--summary-md", default="artifacts/equipment-age-trigger-summary.md")
    p.add_argument("--coverage-md", default="artifacts/equipment-age-trigger-coverage.md")
    args = p.parse_args()

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    current_year = datetime.now(timezone.utc).year

    sites = load_sites(ROOT / args.sites_csv)
    existing = load_external(ROOT / args.external)

    site_zips = sorted({str(s.get("zip") or "").strip() for s in sites if str(s.get("zip") or "").strip()})

    ok, census_map, census_error = _fetch_zip_median_year_built(site_zips)
    feed_rows: List[Dict[str, str]] = []

    if ok and census_map:
        for z in site_zips:
            year_built = census_map.get(z)
            if year_built is None:
                continue
            age_years = float(current_year - year_built)
            feed_rows.append(
                {
                    "zip": z,
                    "median_year_built": str(year_built),
                    "median_structure_age_years": f"{age_years:.1f}",
                    "equipment_age_trigger_status": _status_from_age(age_years),
                    "equipment_age_trigger_score": f"{_score_from_age(age_years):.1f}",
                    "source": f"census_{CENSUS_YEAR}_{CENSUS_DATASET}_{CENSUS_VAR}",
                    "asof": now,
                }
            )
        save_zip_feed(ROOT / args.zip_feed, feed_rows)
        feed_source = "live-census"
    else:
        cached = load_zip_feed(ROOT / args.zip_feed)
        if cached:
            for z in site_zips:
                row = cached.get(z)
                if row:
                    feed_rows.append(row)
            feed_source = "cached-zip-feed"
        else:
            feed_source = "none"

    feed_by_zip = {str(r.get("zip") or "").strip(): r for r in feed_rows}

    out_rows = []
    zip_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: {"sites": 0, "equipment_non_missing": 0, "equipment_missing": 0})

    for s in sites:
        site_id = str(s.get("site_id") or "").strip()
        if not site_id:
            continue

        z = str(s.get("zip") or "").strip()
        base = existing.get(site_id, _default_row(site_id)).copy()
        zr = feed_by_zip.get(z)
        if zr:
            status = str(zr.get("equipment_age_trigger_status") or "missing")
            score = str(zr.get("equipment_age_trigger_score") or "")
            year_built = str(zr.get("median_year_built") or "")
            age = str(zr.get("median_structure_age_years") or "")
            source = str(zr.get("source") or "zip_feed")

            base["equipment_age_trigger_status"] = status
            base["equipment_age_trigger_score"] = score

            note = f"equipment_zip={z} median_year_built={year_built} age={age}y source={source} asof={now}"
            prior = str(base.get("trigger_notes") or "").strip()
            base["trigger_notes"] = (prior + "; " + note).strip("; ") if prior else note

        out_rows.append(base)

        zip_counts[z]["sites"] += 1
        if str(base.get("equipment_age_trigger_status") or "missing") == "missing":
            zip_counts[z]["equipment_missing"] += 1
        else:
            zip_counts[z]["equipment_non_missing"] += 1

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

    status_counts = Counter(str(r.get("equipment_age_trigger_status") or "missing") for r in out_rows)

    summary = {
        "generated_at": now,
        "sites": len(out_rows),
        "zip_count": len(site_zips),
        "feed_source": feed_source,
        "census_fetch_ok": ok,
        "census_error": census_error,
        "zip_feed_rows": len(feed_rows),
        "equipment_status_counts": dict(status_counts),
        "zip_coverage": {k: dict(v) for k, v in sorted(zip_counts.items())},
        "output": str(out_path),
    }

    summary_json_path = ROOT / args.summary_json
    summary_json_path.parent.mkdir(parents=True, exist_ok=True)
    summary_json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# Equipment-Age Trigger Summary",
        "",
        f"- generated_at: `{now}`",
        f"- sites: **{len(out_rows)}**",
        f"- feed_source: **{feed_source}**",
        f"- census_fetch_ok: `{ok}`",
        f"- output: `{out_path}`",
        "",
        "## Equipment status counts",
        "",
    ]
    for k in sorted(status_counts.keys()):
        md_lines.append(f"- `{k}`: {status_counts[k]}")

    if census_error:
        md_lines += ["", "## Fetch error", "", f"- `{census_error}`"]

    summary_md_path = ROOT / args.summary_md
    summary_md_path.parent.mkdir(parents=True, exist_ok=True)
    summary_md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    coverage_lines = [
        "# Equipment-Age Trigger Coverage",
        "",
        "Equipment-age lane uses Census ACS ZIP-level median year built as a screening proxy.",
        "",
        "## Coverage by ZIP",
        "",
    ]
    for z, stats in sorted(zip_counts.items()):
        s_n = stats["sites"]
        n = stats["equipment_non_missing"]
        ratio = (n / s_n) if s_n else 0.0
        coverage_lines.append(f"- `{z}`: non-missing={n}/{s_n} ({ratio:.1%}), missing={stats['equipment_missing']}")

    coverage_lines += [
        "",
        "## Notes",
        "- Status is a ZIP-level proxy derived from median year built (`B25035_001E`), not parcel-level equipment age.",
        "- Treat this lane as prospecting guidance until equipment-specific records are integrated.",
    ]

    coverage_md_path = ROOT / args.coverage_md
    coverage_md_path.parent.mkdir(parents=True, exist_ok=True)
    coverage_md_path.write_text("\n".join(coverage_lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                "sites": len(out_rows),
                "feed_source": feed_source,
                "status_counts": dict(status_counts),
                "output": str(out_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
