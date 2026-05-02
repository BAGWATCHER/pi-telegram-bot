#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: List[str]) -> dict:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return {
        "cmd": " ".join(cmd),
        "returncode": p.returncode,
        "stdout": p.stdout.strip(),
        "stderr": p.stderr.strip(),
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Run multi-ZIP ingest+score+eval regression")
    p.add_argument("--zips", default="01730,02667,05486,06525")
    p.add_argument("--half-span-deg", type=float, default=0.02)
    p.add_argument("--min-records-per-zip", type=int, default=80)
    p.add_argument("--solar-model", choices=["proxy", "pvwatts-cell-blend"], default="pvwatts-cell-blend")
    args = p.parse_args()

    zip_codes = [z.strip() for z in args.zips.split(",") if z.strip()]
    if not zip_codes:
        raise RuntimeError("No ZIPs provided")

    steps = []

    steps.append(
        _run(
            [
                "python3",
                "scripts/ingest_multi_zip_osm.py",
                "--zips",
                ",".join(zip_codes),
                "--half-span-deg",
                str(args.half_span_deg),
                "--min-records-per-zip",
                str(args.min_records_per_zip),
            ]
        )
    )
    if steps[-1]["returncode"] != 0:
        return _finalize(zip_codes, args.solar_model, steps)

    # rebuild trigger layers against freshly ingested site universe
    steps.append(
        _run(
            [
                "python3",
                "scripts/fetch_nws_storm_triggers.py",
                "--sites-csv",
                "data/processed/sites.csv",
                "--output",
                "data/raw/property_triggers_external.csv",
            ]
        )
    )
    if steps[-1]["returncode"] != 0:
        return _finalize(zip_codes, args.solar_model, steps)

    outage_fetch = _run(["python3", "scripts/fetch_eversource_outage_feed.py", "--output", "data/raw/state_outage_feed.csv"])
    outage_fetch_ok = outage_fetch["returncode"] == 0
    if not outage_fetch_ok:
        outage_fetch["stdout"] = (
            (outage_fetch.get("stdout") or "")
            + "\n(optional) outage feed unavailable; continuing with storm+flood trigger lanes"
        ).strip()
        outage_fetch["returncode"] = 0
    steps.append(outage_fetch)

    if outage_fetch_ok:
        steps.append(
            _run(
                [
                    "python3",
                    "scripts/project_state_outage_triggers.py",
                    "--sites-csv",
                    "data/processed/sites.csv",
                    "--external",
                    "data/raw/property_triggers_external.csv",
                    "--state-feed",
                    "data/raw/state_outage_feed.csv",
                    "--output",
                    "data/raw/property_triggers_external.csv",
                ]
            )
        )
        if steps[-1]["returncode"] != 0:
            return _finalize(zip_codes, args.solar_model, steps)

    steps.append(
        _run(
            [
                "python3",
                "scripts/project_nws_flood_triggers.py",
                "--sites-csv",
                "data/processed/sites.csv",
                "--external",
                "data/raw/property_triggers_external.csv",
                "--output",
                "data/raw/property_triggers_external.csv",
            ]
        )
    )
    if steps[-1]["returncode"] != 0:
        return _finalize(zip_codes, args.solar_model, steps)

    steps.append(
        _run(
            [
                "python3",
                "scripts/project_census_equipment_age_triggers.py",
                "--sites-csv",
                "data/processed/sites.csv",
                "--external",
                "data/raw/property_triggers_external.csv",
                "--output",
                "data/raw/property_triggers_external.csv",
            ]
        )
    )
    if steps[-1]["returncode"] != 0:
        return _finalize(zip_codes, args.solar_model, steps)

    steps.append(
        _run(
            [
                "python3",
                "scripts/merge_property_triggers.py",
                "--sites-csv",
                "data/processed/sites.csv",
                "--external",
                "data/raw/property_triggers_external.csv",
                "--output",
                "data/processed/property_triggers.csv",
            ]
        )
    )
    if steps[-1]["returncode"] != 0:
        return _finalize(zip_codes, args.solar_model, steps)

    steps.append(_run(["python3", "scripts/score_sites.py", "--solar-model", args.solar_model]))
    if steps[-1]["returncode"] != 0:
        return _finalize(zip_codes, args.solar_model, steps)

    steps.append(
        _run(
            [
                "python3",
                "eval/run_eval.py",
                "--require-min-zips",
                str(len(zip_codes)),
                "--min-rows-per-zip",
                str(args.min_records_per_zip),
                "--min-zip-stability",
                "0.90",
            ]
        )
    )

    return _finalize(zip_codes, args.solar_model, steps)


def _finalize(zips: List[str], solar_model: str, steps: List[dict]) -> int:
    ok = all(s["returncode"] == 0 for s in steps)

    artifacts = ROOT / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)

    report = {
        "ok": ok,
        "zips": zips,
        "solar_model": solar_model,
        "steps": steps,
        "env": {
            "PVWATTS_API_KEY_set": bool(os.environ.get("PVWATTS_API_KEY")),
            "NSRDB_API_KEY_set": bool(os.environ.get("NSRDB_API_KEY")),
        },
    }
    (artifacts / "multi-zip-regression.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# Multi-ZIP Regression",
        "",
        f"- status: **{'PASS' if ok else 'FAIL'}**",
        f"- zips: `{', '.join(zips)}`",
        f"- solar model: `{solar_model}`",
        "",
        "## Steps",
        "",
    ]
    for s in steps:
        icon = "✅" if s["returncode"] == 0 else "❌"
        md_lines.append(f"- {icon} `{s['cmd']}` (rc={s['returncode']})")

    (artifacts / "multi-zip-regression.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(json.dumps({"ok": ok, "steps": len(steps), "report": str(artifacts / 'multi-zip-regression.json')}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
