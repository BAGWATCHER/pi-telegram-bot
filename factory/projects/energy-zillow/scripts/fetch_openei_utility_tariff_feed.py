#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import requests

ROOT = Path(__file__).resolve().parents[1]
OPENEI_URL = "https://api.openei.org/utility_rates"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _epoch_to_date(epoch_val) -> str:
    try:
        if epoch_val in (None, "", "None"):
            return ""
        ts = int(float(epoch_val))
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
    except Exception:
        return ""


def _first_energy_rate(item: Dict[str, object]) -> float | None:
    ers = item.get("energyratestructure")
    if not isinstance(ers, list):
        return None
    for tier_list in ers:
        if not isinstance(tier_list, list):
            continue
        for tier in tier_list:
            if not isinstance(tier, dict):
                continue
            rate = tier.get("rate")
            adj = tier.get("adj")
            if rate in (None, "", "None"):
                continue
            try:
                r = float(rate)
                a = float(adj) if adj not in (None, "", "None") else 0.0
                return r + a
            except Exception:
                continue
    return None


def _first_demand_rate(item: Dict[str, object]) -> float | None:
    fds = item.get("flatdemandstructure")
    if not isinstance(fds, list):
        return None
    for tier_list in fds:
        if not isinstance(tier_list, list):
            continue
        for tier in tier_list:
            if not isinstance(tier, dict):
                continue
            rate = tier.get("rate")
            if rate in (None, "", "None"):
                continue
            try:
                return float(rate)
            except Exception:
                continue
    return None


def _choose_item(items: List[Dict[str, object]]) -> Dict[str, object] | None:
    if not items:
        return None

    residential = [it for it in items if str(it.get("sector") or "").lower() == "residential"]
    if residential:
        return residential[0]

    return items[0]


def _load_sites(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> int:
    p = argparse.ArgumentParser(description="Fetch OpenEI utility/tariff defaults by ZIP centroid and map to site rows")
    p.add_argument("--sites-csv", default="data/processed/sites.csv")
    p.add_argument("--output", default="data/raw/utility_tariff_feed.csv")
    p.add_argument("--summary-md", default="artifacts/openei-utility-fetch-summary.md")
    p.add_argument("--summary-json", default="artifacts/openei-utility-fetch-summary.json")
    p.add_argument("--zips", default="", help="comma-separated ZIPs (default: all in sites.csv)")
    p.add_argument("--api-key", default="")
    p.add_argument("--sleep-ms", type=int, default=120)
    args = p.parse_args()

    api_key = str(args.api_key or "").strip() or os.getenv("OPENEI_API_KEY") or "DEMO_KEY"

    sites_path = ROOT / args.sites_csv
    if not sites_path.exists():
        raise SystemExit(f"missing sites csv: {sites_path}")

    all_sites = _load_sites(sites_path)

    requested_zips = {z.strip() for z in str(args.zips or "").split(",") if z.strip()}
    if requested_zips:
        sites = [s for s in all_sites if str(s.get("zip") or "").strip() in requested_zips]
    else:
        sites = [s for s in all_sites if str(s.get("zip") or "").strip()]

    by_zip: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for s in sites:
        by_zip[str(s.get("zip") or "").strip()].append(s)

    zip_items: Dict[str, Dict[str, object]] = {}
    zip_status: Dict[str, str] = {}

    for z, rows in sorted(by_zip.items()):
        # centroid proxy for zip call
        lat_sum = 0.0
        lon_sum = 0.0
        n = 0
        for r in rows:
            try:
                lat_sum += float(r.get("lat") or 0.0)
                lon_sum += float(r.get("lon") or 0.0)
                n += 1
            except Exception:
                continue
        if n == 0:
            zip_status[z] = "no_coords"
            continue

        lat = lat_sum / n
        lon = lon_sum / n

        params = {
            "version": "8",
            "api_key": api_key,
            "format": "json",
            "is_default": "true",
            "detail": "full",
            "lat": f"{lat:.6f}",
            "lon": f"{lon:.6f}",
        }

        try:
            resp = requests.get(OPENEI_URL, params=params, timeout=35)
            resp.raise_for_status()
            body = resp.json()
            items = body.get("items") or []
            chosen = _choose_item(items)
            if not chosen:
                zip_status[z] = "no_items"
            else:
                zip_items[z] = chosen
                zip_status[z] = "mapped"
        except Exception:
            zip_status[z] = "error"

        if args.sleep_ms > 0:
            time.sleep(args.sleep_ms / 1000.0)

    out_rows: List[Dict[str, str]] = []
    for z, rows in sorted(by_zip.items()):
        item = zip_items.get(z)
        if not item:
            continue

        utility_id = str(item.get("eiaid") or "").strip()
        utility_name = str(item.get("utility") or "").strip()
        rate_plan = str(item.get("name") or "").strip()
        effective_date = _epoch_to_date(item.get("startdate"))
        energy_rate = _first_energy_rate(item)
        fixed_monthly = item.get("fixedchargefirstmeter")
        demand_rate = _first_demand_rate(item)
        source = str(item.get("uri") or item.get("source") or "openei_utility_rates").strip()

        for s in rows:
            sid = str(s.get("site_id") or "").strip()
            if not sid:
                continue
            out_rows.append(
                {
                    "site_id": sid,
                    "utility_id": utility_id,
                    "utility_name": utility_name,
                    "rate_plan": rate_plan,
                    "effective_date": effective_date,
                    "energy_rate_kwh": "" if energy_rate is None else f"{float(energy_rate):.5f}",
                    "fixed_monthly_usd": "" if fixed_monthly in (None, "", "None") else f"{float(fixed_monthly):.2f}",
                    "demand_charge_kw": "" if demand_rate is None else f"{float(demand_rate):.2f}",
                    "source": source,
                }
            )

    out_path = ROOT / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "site_id",
                "utility_id",
                "utility_name",
                "rate_plan",
                "effective_date",
                "energy_rate_kwh",
                "fixed_monthly_usd",
                "demand_charge_kw",
                "source",
            ],
        )
        w.writeheader()
        w.writerows(out_rows)

    status_counts = Counter(zip_status.values())
    zip_cov = {}
    out_by_site = {r["site_id"]: r for r in out_rows}
    for z, rows in sorted(by_zip.items()):
        total = len(rows)
        mapped = sum(1 for s in rows if str(s.get("site_id") or "") in out_by_site)
        with_rate = sum(1 for s in rows if (out_by_site.get(str(s.get("site_id") or ""), {}).get("energy_rate_kwh") not in ("", None)))
        zip_cov[z] = {
            "sites": total,
            "mapped": mapped,
            "mapped_ratio": (mapped / total) if total else 0.0,
            "with_rate": with_rate,
            "with_rate_ratio": (with_rate / total) if total else 0.0,
            "zip_status": zip_status.get(z, "missing"),
        }

    now = _now_iso()
    summary = {
        "generated_at": now,
        "api_key_mode": "env_or_demo" if not args.api_key else "explicit",
        "sites_scope": len(sites),
        "zips_scope": len(by_zip),
        "status_counts": dict(status_counts),
        "rows_written": len(out_rows),
        "zip_coverage": zip_cov,
        "output": str(out_path),
    }

    summary_json = ROOT / args.summary_json
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# OpenEI Utility/Tariff Fetch Summary",
        "",
        f"- generated_at: `{now}`",
        f"- sites in scope: **{len(sites)}**",
        f"- zips in scope: **{len(by_zip)}**",
        f"- rows written: **{len(out_rows)}**",
        f"- output: `{out_path}`",
        "",
        "## ZIP fetch status",
        "",
    ]
    for k in sorted(status_counts.keys()):
        lines.append(f"- `{k}`: {status_counts[k]}")

    lines += ["", "## Coverage by ZIP", ""]
    for z, c in sorted(zip_cov.items()):
        lines.append(
            f"- `{z}`: mapped={c['mapped']}/{c['sites']} ({c['mapped_ratio']:.1%}), with_rate={c['with_rate']}/{c['sites']} ({c['with_rate_ratio']:.1%}), status={c['zip_status']}"
        )

    summary_md = ROOT / args.summary_md
    summary_md.parent.mkdir(parents=True, exist_ok=True)
    summary_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"ok": True, "rows": len(out_rows), "zips": len(by_zip), "status_counts": dict(status_counts)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
