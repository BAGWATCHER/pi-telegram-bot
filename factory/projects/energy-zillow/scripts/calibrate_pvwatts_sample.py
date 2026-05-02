#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.scoring.pvwatts_hook import estimate_ac_annual_kwh  # noqa: E402


def stable_pick(rows: List[Dict[str, str]], sample_size: int) -> List[Dict[str, str]]:
    ranked = sorted(rows, key=lambda r: hashlib.sha1(r["site_id"].encode()).hexdigest())
    return ranked[: min(sample_size, len(ranked))]


def main() -> int:
    p = argparse.ArgumentParser(description="Calibrate proxy annual_kwh against PVWatts sample")
    p.add_argument("--sample-size", type=int, default=40)
    p.add_argument("--input", default="data/processed/site_scores.csv")
    args = p.parse_args()

    in_path = ROOT / args.input
    if not in_path.exists():
        raise RuntimeError(f"missing input {in_path}")

    with in_path.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    sample = stable_pick(rows, args.sample_size)
    results = []
    for r in sample:
        lat = float(r["lat"])
        lon = float(r["lon"])
        model_kwh = float(r["annual_kwh_solar"])
        install_cost = float(r["install_cost_solar_usd"])
        system_kw = install_cost / 2200.0
        tilt = min(max(abs(lat) * 0.76, 5), 35)

        pv = estimate_ac_annual_kwh(lat=lat, lon=lon, system_capacity_kw=system_kw, tilt=tilt)
        if not pv:
            continue

        pv_kwh = float(pv["ac_annual_kwh"])
        diff = model_kwh - pv_kwh
        ape = abs(diff) / max(pv_kwh, 1e-6)
        results.append(
            {
                "site_id": r["site_id"],
                "model_kwh": model_kwh,
                "pvwatts_kwh": pv_kwh,
                "diff_kwh": diff,
                "ape": ape,
                "pvwatts_capacity_factor": pv["capacity_factor"],
                "pvwatts_solrad_annual": pv["solrad_annual"],
            }
        )

    if not results:
        raise RuntimeError("No PVWatts results; check network/API key")

    diffs = [x["diff_kwh"] for x in results]
    apes = [x["ape"] for x in results]
    factors = [x["model_kwh"] / max(x["pvwatts_kwh"], 1e-6) for x in results]

    summary = {
        "sample_requested": len(sample),
        "sample_scored": len(results),
        "mae_kwh": round(sum(abs(d) for d in diffs) / len(diffs), 2),
        "median_abs_pct_error": round(statistics.median(apes) * 100, 2),
        "mean_signed_diff_kwh": round(sum(diffs) / len(diffs), 2),
        "median_model_to_pvwatts_factor": round(statistics.median(factors), 3),
        "p90_abs_pct_error": round(sorted(apes)[int(0.9 * (len(apes) - 1))] * 100, 2),
    }

    artifacts = ROOT / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / "pvwatts-calibration.json").write_text(json.dumps({"summary": summary, "sample": results[:20]}, indent=2) + "\n")

    md = [
        "# PVWatts Calibration (Sample Hook)",
        "",
        f"- sample requested: **{summary['sample_requested']}**",
        f"- sample scored: **{summary['sample_scored']}**",
        f"- MAE (kWh): **{summary['mae_kwh']}**",
        f"- Median abs % error: **{summary['median_abs_pct_error']}%**",
        f"- Mean signed diff (model - PVWatts): **{summary['mean_signed_diff_kwh']} kWh**",
        f"- Median model/PVWatts factor: **{summary['median_model_to_pvwatts_factor']}x**",
        f"- P90 abs % error: **{summary['p90_abs_pct_error']}%**",
        "",
        "## Interpretation",
        "- This is a calibration hook, not full production calibration.",
        "- Use this output to tune proxy production assumptions and later replace with direct PVWatts/NSRDB-driven scoring.",
    ]
    (artifacts / "pvwatts-calibration.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
