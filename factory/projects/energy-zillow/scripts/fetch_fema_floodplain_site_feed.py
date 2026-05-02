#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import requests

ROOT = Path(__file__).resolve().parents[1]
FEMA_QUERY_URL = "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _clip(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _zone_to_score_status(zone: str) -> Tuple[float, str]:
    z = (zone or "").strip().upper()
    if z.startswith("VE") or z.startswith("V"):
        return 93.0, "verified"
    if z.startswith("AE") or z.startswith("AH") or z.startswith("AO") or z.startswith("AR") or z.startswith("A"):
        return 86.0, "verified"
    if "0.2" in z or z in {"X500", "SHADED X", "0.2 PCT ANNUAL CHANCE FLOOD HAZARD"}:
        return 58.0, "medium"
    if z.startswith("X"):
        return 22.0, "low"
    if z.startswith("D"):
        return 30.0, "low"
    if z:
        return 40.0, "low"
    return 0.0, "low"


def _load_sites(path: Path, zips: set[str] | None, limit: int | None) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    out: List[Dict[str, str]] = []
    for r in rows:
        sid = str(r.get("site_id") or "").strip()
        if not sid:
            continue
        z = str(r.get("zip") or "").strip()
        if zips and z not in zips:
            continue
        lat = r.get("lat")
        lon = r.get("lon")
        if lat in ("", None) or lon in ("", None):
            continue
        out.append(
            {
                "site_id": sid,
                "zip": z,
                "lat": str(lat),
                "lon": str(lon),
            }
        )
        if limit and len(out) >= limit:
            break
    return out


def _load_existing(path: Path) -> Dict[str, Dict[str, str]]:
    if not path.exists():
        return {}
    out: Dict[str, Dict[str, str]] = {}
    with path.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sid = str(row.get("site_id") or "").strip()
            if sid:
                out[sid] = dict(row)
    return out


def _query_point(site: Dict[str, str], timeout_s: int = 20, retries: int = 2) -> Dict[str, str]:
    sid = site["site_id"]
    lat = site["lat"]
    lon = site["lon"]

    params = {
        "f": "json",
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "FLD_ZONE,ZONE_SUBTY,SFHA_TF,STATIC_BFE,SOURCE_CIT",
        "returnGeometry": "false",
        "resultRecordCount": "1",
    }

    last_err = ""
    for attempt in range(retries + 1):
        try:
            r = requests.get(FEMA_QUERY_URL, params=params, timeout=timeout_s)
            r.raise_for_status()
            body = r.json()
            feats = body.get("features") or []
            if feats:
                attrs = (feats[0] or {}).get("attributes") or {}
                zone = str(attrs.get("FLD_ZONE") or "").strip()
                subtype = str(attrs.get("ZONE_SUBTY") or "").strip()
                sfha = str(attrs.get("SFHA_TF") or "").strip()
                bfe = attrs.get("STATIC_BFE")
                src = str(attrs.get("SOURCE_CIT") or "fema_nfhl").strip() or "fema_nfhl"

                score, status = _zone_to_score_status(zone)
                if sfha.upper() in {"T", "TRUE", "Y", "YES", "1"}:
                    status = "verified"
                    score = max(score, 82.0)

                row = {
                    "site_id": sid,
                    "flood_zone": f"{zone}{('/' + subtype) if subtype else ''}".strip("/"),
                    "risk_status": status,
                    "risk_score": f"{_clip(score):.1f}",
                    "bfe_ft": "" if bfe in (None, "", "None") else str(bfe),
                    "source": src,
                    "as_of": _now_iso(),
                }
                return row

            # successful response, no intersecting flood polygon returned
            return {
                "site_id": sid,
                "flood_zone": "",
                "risk_status": "low",
                "risk_score": "0.0",
                "bfe_ft": "",
                "source": "fema_nfhl_point_query",
                "as_of": _now_iso(),
            }
        except Exception as e:
            last_err = str(e)
            if attempt < retries:
                time.sleep(0.4 * (attempt + 1))

    return {
        "site_id": sid,
        "flood_zone": "",
        "risk_status": "missing",
        "risk_score": "",
        "bfe_ft": "",
        "source": f"fema_nfhl_error:{last_err[:120]}",
        "as_of": _now_iso(),
    }


def _write_rows(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["site_id", "flood_zone", "risk_status", "risk_score", "bfe_ft", "source", "as_of"],
        )
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    p = argparse.ArgumentParser(description="Fetch FEMA/NFHL floodplain status for sites via point-intersect queries")
    p.add_argument("--sites-csv", default="data/processed/sites.csv")
    p.add_argument("--output", default="data/raw/fema_floodplain_site_feed.csv")
    p.add_argument("--summary-json", default="artifacts/fema-floodplain-fetch-summary.json")
    p.add_argument("--summary-md", default="artifacts/fema-floodplain-fetch-summary.md")
    p.add_argument("--zips", default="", help="comma-separated ZIP filter")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--workers", type=int, default=14)
    p.add_argument("--timeout", type=int, default=20)
    p.add_argument("--retries", type=int, default=2)
    p.add_argument("--resume", action="store_true")
    args = p.parse_args()

    sites_path = ROOT / args.sites_csv
    out_path = ROOT / args.output
    if not sites_path.exists():
        raise SystemExit(f"missing sites csv: {sites_path}")

    zips = {z.strip() for z in str(args.zips or "").split(",") if z.strip()}
    limit = args.limit if args.limit and args.limit > 0 else None

    sites = _load_sites(sites_path, zips=zips if zips else None, limit=limit)
    existing = _load_existing(out_path) if args.resume else {}

    pending = [s for s in sites if s["site_id"] not in existing]

    started = time.time()
    results: Dict[str, Dict[str, str]] = dict(existing)

    if pending:
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
            futures = {
                ex.submit(_query_point, site, args.timeout, args.retries): site
                for site in pending
            }
            done_count = 0
            for fut in as_completed(futures):
                row = fut.result()
                sid = row["site_id"]
                results[sid] = row
                done_count += 1
                if done_count % 250 == 0:
                    print(f"progress: {done_count}/{len(pending)} fetched")

    ordered = [results[s["site_id"]] for s in sites if s["site_id"] in results]
    _write_rows(out_path, ordered)

    status_counts = Counter(r.get("risk_status") or "missing" for r in ordered)
    zip_counts: Dict[str, Dict[str, int]] = {}
    by_site_zip = {s["site_id"]: s["zip"] for s in sites}
    for row in ordered:
        z = by_site_zip.get(row["site_id"], "")
        if z not in zip_counts:
            zip_counts[z] = {"sites": 0, "non_missing": 0, "verified": 0}
        zip_counts[z]["sites"] += 1
        if (row.get("risk_status") or "missing") != "missing":
            zip_counts[z]["non_missing"] += 1
        if (row.get("risk_status") or "") == "verified":
            zip_counts[z]["verified"] += 1

    elapsed = round(time.time() - started, 2)
    summary = {
        "generated_at": _now_iso(),
        "sites_targeted": len(sites),
        "sites_fetched_new": len(pending),
        "sites_total_written": len(ordered),
        "status_counts": dict(status_counts),
        "zip_coverage": zip_counts,
        "output": str(out_path),
        "elapsed_seconds": elapsed,
        "zips_filter": sorted(zips),
    }

    summary_json = ROOT / args.summary_json
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# FEMA Floodplain Fetch Summary",
        "",
        f"- generated_at: `{summary['generated_at']}`",
        f"- sites targeted: **{len(sites)}**",
        f"- fetched new: **{len(pending)}**",
        f"- rows written: **{len(ordered)}**",
        f"- elapsed: **{elapsed}s**",
        f"- output: `{out_path}`",
        "",
        "## Status counts",
        "",
    ]
    for k in sorted(status_counts.keys()):
        lines.append(f"- `{k}`: {status_counts[k]}")

    lines += ["", "## ZIP coverage", ""]
    for z in sorted(zip_counts.keys()):
        s = zip_counts[z]
        lines.append(
            f"- `{z}`: non-missing={s['non_missing']}/{s['sites']} ({(s['non_missing']/s['sites'] if s['sites'] else 0):.1%}), verified={s['verified']}"
        )

    summary_md = ROOT / args.summary_md
    summary_md.parent.mkdir(parents=True, exist_ok=True)
    summary_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"ok": True, "sites": len(ordered), "new": len(pending), "status_counts": dict(status_counts), "elapsed_s": elapsed}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
