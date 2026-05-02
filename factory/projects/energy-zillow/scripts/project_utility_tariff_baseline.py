#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.scoring.solar import ScoringAssumptions
from scripts.score_sites import (
    build_state_utility_rate_medians,
    load_manual_utility_mappings,
    load_official_utility_rate_overrides,
    load_state_rate_overrides,
    resolve_site_rate_context,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _parse_float(v: str) -> float | None:
    try:
        if v in ("", "None", None):
            return None
        return float(v)
    except Exception:
        return None


def _fmt_usd(v: float) -> str:
    return f"${v:,.0f}"


def _pct(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    xs = sorted(values)
    idx = (len(xs) - 1) * max(0.0, min(1.0, p))
    lo = int(idx)
    hi = min(lo + 1, len(xs) - 1)
    w = idx - lo
    return float(xs[lo] * (1.0 - w) + xs[hi] * w)


def _safe_div(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    return a / b


def _build_site_utility_map(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, object]]:
    out: Dict[str, Dict[str, object]] = {}
    for r in rows:
        sid = str(r.get("site_id") or "").strip()
        if not sid:
            continue
        out[sid] = {
            "utility_id": str(r.get("utility_id") or "").strip(),
            "utility_name": str(r.get("utility_name") or "").strip(),
            "rate_plan": str(r.get("rate_plan") or "").strip(),
            "energy_rate_kwh": _parse_float(str(r.get("energy_rate_kwh") or "")),
            "fixed_monthly_usd": _parse_float(str(r.get("fixed_monthly_usd") or "")),
            "demand_charge_kw": _parse_float(str(r.get("demand_charge_kw") or "")),
            "source": str(r.get("source") or "").strip(),
            "as_of": str(r.get("as_of") or "").strip(),
        }
    return out


def _load_solar_kwh_map(path: Path) -> Dict[str, float]:
    rows = _load_csv(path)
    out: Dict[str, float] = {}
    for r in rows:
        sid = str(r.get("site_id") or "").strip()
        if not sid:
            continue
        kwh = _parse_float(str(r.get("annual_kwh_solar") or ""))
        if kwh is None:
            continue
        out[sid] = float(kwh)
    return out


def main() -> int:
    p = argparse.ArgumentParser(description="Build utility/tariff baseline mapping coverage artifact")
    p.add_argument("--sites-csv", default="data/processed/sites.csv")
    p.add_argument("--scores-csv", default="data/processed/site_scores.csv")
    p.add_argument("--tariff-feed", default="data/raw/utility_tariff_feed.csv")
    p.add_argument("--output", default="data/processed/site_utility_tariff.csv")
    p.add_argument("--summary-md", default="artifacts/utility-tariff-summary.md")
    p.add_argument("--summary-json", default="artifacts/utility-tariff-summary.json")
    p.add_argument("--delta-md", default="artifacts/tariff-impact-delta.md")
    p.add_argument("--delta-json", default="artifacts/tariff-impact-delta.json")
    p.add_argument("--state-rate-csv", default="data/raw/eia_state_residential_rates.csv")
    p.add_argument("--official-utility-rate-csv", default="data/raw/official_utility_residential_rates.csv")
    p.add_argument("--manual-utility-map-csv", default="data/raw/manual_utility_map.csv")
    args = p.parse_args()

    sites = _load_csv(ROOT / args.sites_csv)
    feed = _load_csv(ROOT / args.tariff_feed)
    solar_kwh_by_site = _load_solar_kwh_map(ROOT / args.scores_csv)
    now = _now_iso()

    feed_by_site: Dict[str, Dict[str, str]] = {}
    for row in feed:
        sid = str(row.get("site_id") or "").strip()
        if sid:
            feed_by_site[sid] = row

    out_rows: List[Dict[str, str]] = []
    zip_cov = defaultdict(lambda: {"sites": 0, "mapped": 0, "with_rate": 0})

    for s in sites:
        sid = str(s.get("site_id") or "").strip()
        if not sid:
            continue
        z = str(s.get("zip") or "").strip()
        rec = feed_by_site.get(sid, {})

        utility_id = str(rec.get("utility_id") or "").strip()
        utility_name = str(rec.get("utility_name") or "").strip()
        rate_plan = str(rec.get("rate_plan") or "").strip()
        energy_rate = _parse_float(str(rec.get("energy_rate_kwh") or ""))
        fixed_monthly = _parse_float(str(rec.get("fixed_monthly_usd") or ""))
        demand_charge = _parse_float(str(rec.get("demand_charge_kw") or ""))

        out_rows.append(
            {
                "site_id": sid,
                "zip": z,
                "utility_id": utility_id,
                "utility_name": utility_name,
                "rate_plan": rate_plan,
                "energy_rate_kwh": "" if energy_rate is None else f"{energy_rate:.5f}",
                "fixed_monthly_usd": "" if fixed_monthly is None else f"{fixed_monthly:.2f}",
                "demand_charge_kw": "" if demand_charge is None else f"{demand_charge:.2f}",
                "source": str(rec.get("source") or "").strip(),
                "as_of": str(rec.get("effective_date") or "").strip() or now,
            }
        )

        zip_cov[z]["sites"] += 1
        if utility_id or utility_name:
            zip_cov[z]["mapped"] += 1
        if energy_rate is not None:
            zip_cov[z]["with_rate"] += 1

    out_path = ROOT / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "site_id",
                "zip",
                "utility_id",
                "utility_name",
                "rate_plan",
                "energy_rate_kwh",
                "fixed_monthly_usd",
                "demand_charge_kw",
                "source",
                "as_of",
            ],
        )
        w.writeheader()
        w.writerows(out_rows)

    mapped = sum(1 for r in out_rows if r["utility_id"] or r["utility_name"])
    with_rate = sum(1 for r in out_rows if r["energy_rate_kwh"] not in ("", None))

    summary = {
        "generated_at": now,
        "sites": len(out_rows),
        "tariff_feed_rows": len(feed),
        "utility_mapped": mapped,
        "utility_mapped_ratio": (mapped / len(out_rows)) if out_rows else 0.0,
        "rate_filled": with_rate,
        "rate_filled_ratio": (with_rate / len(out_rows)) if out_rows else 0.0,
        "zip_coverage": {k: dict(v) for k, v in sorted(zip_cov.items())},
        "output": str(out_path),
    }

    summary_json = ROOT / args.summary_json
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# Utility Tariff Summary",
        "",
        f"- generated_at: `{now}`",
        f"- sites: **{len(out_rows)}**",
        f"- tariff feed rows: **{len(feed)}**",
        f"- utility mapped: **{mapped}/{len(out_rows)} ({(mapped/len(out_rows) if out_rows else 0):.1%})**",
        f"- rate filled: **{with_rate}/{len(out_rows)} ({(with_rate/len(out_rows) if out_rows else 0):.1%})**",
        f"- output: `{out_path}`",
        "",
        "## Coverage by ZIP",
        "",
    ]
    for z, c in sorted(zip_cov.items()):
        n = c["sites"]
        md_lines.append(
            f"- `{z}`: mapped={c['mapped']}/{n} ({(c['mapped']/n if n else 0):.1%}), with_rate={c['with_rate']}/{n} ({(c['with_rate']/n if n else 0):.1%})"
        )

    (ROOT / args.summary_md).write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    # --- Economics delta vs pre-tariff baseline (no site utility feed) ---
    base_assumptions = ScoringAssumptions()
    state_rate_overrides = load_state_rate_overrides(ROOT / args.state_rate_csv)
    official_utility_overrides = load_official_utility_rate_overrides(ROOT / args.official_utility_rate_csv)
    manual_utility_mappings = load_manual_utility_mappings(ROOT / args.manual_utility_map_csv)

    site_utility_rates = _build_site_utility_map(out_rows)
    state_utility_rate_medians = build_state_utility_rate_medians(sites, site_utility_rates)

    delta_rows: List[Dict[str, object]] = []
    for site in sites:
        sid = str(site.get("site_id") or "").strip()
        if not sid:
            continue

        current_assumptions, current_meta = resolve_site_rate_context(
            site,
            base_assumptions,
            state_rate_overrides,
            site_utility_rates,
            state_utility_rate_medians,
            official_utility_overrides,
            manual_utility_mappings,
        )
        baseline_assumptions, baseline_meta = resolve_site_rate_context(
            site,
            base_assumptions,
            state_rate_overrides,
            {},
            {},
            official_utility_overrides,
            manual_utility_mappings,
        )

        current_rate = float(current_assumptions.utility_rate_usd_per_kwh)
        baseline_rate = float(baseline_assumptions.utility_rate_usd_per_kwh)
        rate_delta = round(current_rate - baseline_rate, 5)

        annual_kwh = float(solar_kwh_by_site.get(sid, 0.0))
        annual_savings_delta = round(annual_kwh * rate_delta, 2)

        delta_rows.append(
            {
                "site_id": sid,
                "zip": str(site.get("zip") or "").strip(),
                "state": str(site.get("state") or "").strip().upper(),
                "utility_name": str(current_meta.get("utility_name") or baseline_meta.get("utility_name") or "").strip(),
                "current_rate": current_rate,
                "baseline_rate": baseline_rate,
                "rate_delta": rate_delta,
                "annual_kwh_solar": annual_kwh,
                "annual_savings_delta_usd": annual_savings_delta,
                "current_method": str(current_meta.get("utility_rate_method") or ""),
                "baseline_method": str(baseline_meta.get("utility_rate_method") or ""),
            }
        )

    rate_deltas = [float(r["rate_delta"]) for r in delta_rows]
    annual_deltas = [float(r["annual_savings_delta_usd"]) for r in delta_rows]
    non_zero_rate = [d for d in rate_deltas if abs(d) > 1e-9]

    by_zip: Dict[str, Dict[str, float]] = defaultdict(lambda: {"sites": 0.0, "total_annual_delta": 0.0, "avg_rate_delta": 0.0, "non_zero": 0.0})
    for r in delta_rows:
        z = str(r["zip"])
        by_zip[z]["sites"] += 1
        by_zip[z]["total_annual_delta"] += float(r["annual_savings_delta_usd"])
        by_zip[z]["avg_rate_delta"] += float(r["rate_delta"])
        if abs(float(r["rate_delta"])) > 1e-9:
            by_zip[z]["non_zero"] += 1

    zip_rank: List[Tuple[str, Dict[str, float]]] = []
    for z, agg in by_zip.items():
        n = max(1.0, agg["sites"])
        agg["avg_rate_delta"] = agg["avg_rate_delta"] / n
        agg["non_zero_ratio"] = _safe_div(agg["non_zero"], n)
        zip_rank.append((z, agg))

    zip_rank = sorted(zip_rank, key=lambda x: abs(float(x[1]["total_annual_delta"])), reverse=True)

    transition_counts = Counter(f"{r['baseline_method']} -> {r['current_method']}" for r in delta_rows)

    top_sites = sorted(delta_rows, key=lambda r: abs(float(r["annual_savings_delta_usd"])), reverse=True)[:12]
    top_zips = zip_rank[:12]

    delta_summary = {
        "generated_at": now,
        "comparison": {
            "current": "state + official utility overrides + manual utility map + site utility/tariff feed",
            "baseline": "state + official utility overrides + manual utility map (site utility/tariff feed disabled)",
        },
        "sites_compared": len(delta_rows),
        "non_zero_rate_delta_sites": len(non_zero_rate),
        "non_zero_rate_delta_ratio": _safe_div(len(non_zero_rate), len(delta_rows)),
        "rate_delta_stats": {
            "mean": _safe_div(sum(rate_deltas), len(rate_deltas)),
            "median": median(rate_deltas) if rate_deltas else 0.0,
            "p10": _pct(rate_deltas, 0.10),
            "p90": _pct(rate_deltas, 0.90),
            "min": min(rate_deltas) if rate_deltas else 0.0,
            "max": max(rate_deltas) if rate_deltas else 0.0,
        },
        "annual_savings_delta_usd": {
            "total": round(sum(annual_deltas), 2),
            "mean": round(_safe_div(sum(annual_deltas), len(annual_deltas)), 2),
            "median": round(median(annual_deltas), 2) if annual_deltas else 0.0,
            "p10": round(_pct(annual_deltas, 0.10), 2),
            "p90": round(_pct(annual_deltas, 0.90), 2),
            "min": round(min(annual_deltas), 2) if annual_deltas else 0.0,
            "max": round(max(annual_deltas), 2) if annual_deltas else 0.0,
        },
        "rate_method_transitions": dict(transition_counts.most_common(10)),
        "top_zip_deltas": [
            {
                "zip": z,
                "sites": int(agg["sites"]),
                "non_zero_ratio": round(float(agg["non_zero_ratio"]), 4),
                "avg_rate_delta": round(float(agg["avg_rate_delta"]), 5),
                "total_annual_delta_usd": round(float(agg["total_annual_delta"]), 2),
            }
            for z, agg in top_zips
        ],
        "top_site_deltas": [
            {
                "site_id": str(r["site_id"]),
                "zip": str(r["zip"]),
                "state": str(r["state"]),
                "utility_name": str(r["utility_name"]),
                "current_rate": round(float(r["current_rate"]), 5),
                "baseline_rate": round(float(r["baseline_rate"]), 5),
                "rate_delta": round(float(r["rate_delta"]), 5),
                "annual_kwh_solar": round(float(r["annual_kwh_solar"]), 2),
                "annual_savings_delta_usd": round(float(r["annual_savings_delta_usd"]), 2),
                "method_transition": f"{r['baseline_method']} -> {r['current_method']}",
            }
            for r in top_sites
        ],
    }

    delta_json_path = ROOT / args.delta_json
    delta_json_path.parent.mkdir(parents=True, exist_ok=True)
    delta_json_path.write_text(json.dumps(delta_summary, indent=2) + "\n", encoding="utf-8")

    delta_lines = [
        "# Tariff Impact Delta (vs pre-tariff baseline)",
        "",
        f"- generated_at: `{now}`",
        "- baseline: state + official + manual utility mapping, **without** site-level utility/tariff feed",
        "- current: baseline + site-level utility/tariff feed (`data/processed/site_utility_tariff.csv`)",
        f"- sites compared: **{len(delta_rows):,}**",
        f"- non-zero rate delta: **{len(non_zero_rate):,}/{len(delta_rows):,} ({_safe_div(len(non_zero_rate), len(delta_rows)):.1%})**",
        f"- total annual savings delta: **{_fmt_usd(float(delta_summary['annual_savings_delta_usd']['total']))}**",
        f"- median annual savings delta per site: **{_fmt_usd(float(delta_summary['annual_savings_delta_usd']['median']))}**",
        "",
        "## Rate delta distribution (USD/kWh)",
        "",
        f"- mean: `{delta_summary['rate_delta_stats']['mean']:.5f}`",
        f"- median: `{delta_summary['rate_delta_stats']['median']:.5f}`",
        f"- p10 / p90: `{delta_summary['rate_delta_stats']['p10']:.5f}` / `{delta_summary['rate_delta_stats']['p90']:.5f}`",
        f"- min / max: `{delta_summary['rate_delta_stats']['min']:.5f}` / `{delta_summary['rate_delta_stats']['max']:.5f}`",
        "",
        "## Dominant rate-method transitions",
        "",
    ]

    for transition, count in transition_counts.most_common(8):
        delta_lines.append(f"- `{transition}`: {count:,} sites")

    delta_lines += ["", "## Top ZIP annual savings deltas", ""]
    for z, agg in top_zips[:8]:
        delta_lines.append(
            f"- `{z}`: total_delta={_fmt_usd(float(agg['total_annual_delta']))}, avg_rate_delta={float(agg['avg_rate_delta']):.5f}, non_zero={float(agg['non_zero_ratio']):.1%}"
        )

    delta_lines += ["", "## Top site annual savings deltas (absolute)", ""]
    for r in top_sites[:8]:
        delta_lines.append(
            f"- `{r['site_id']}` ({r['zip']}, {r['state']}): delta={_fmt_usd(float(r['annual_savings_delta_usd']))}, rate={float(r['baseline_rate']):.5f} -> {float(r['current_rate']):.5f}, utility=`{r['utility_name'] or 'n/a'}`"
        )

    delta_lines += ["", f"- machine-readable summary: `{delta_json_path}`"]
    (ROOT / args.delta_md).write_text("\n".join(delta_lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                "sites": len(out_rows),
                "feed_rows": len(feed),
                "mapped": mapped,
                "with_rate": with_rate,
                "non_zero_delta_sites": len(non_zero_rate),
                "annual_savings_delta_total": delta_summary["annual_savings_delta_usd"]["total"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
