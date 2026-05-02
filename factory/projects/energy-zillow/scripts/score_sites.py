#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Dict, List, Tuple

import h3

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.scoring.nsrdb_hook import estimate_solar_resource
from backend.scoring.pvwatts_hook import estimate_ac_annual_kwh
from backend.scoring.solar import ScoringAssumptions, apply_spatial_context, score_site


def read_sites(path: Path) -> List[Dict[str, object]]:
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _npv_15y(annual_savings: float, install_cost: float, discount_rate: float, degradation: float) -> float:
    npv = -install_cost
    yearly = annual_savings
    for y in range(1, 16):
        npv += yearly / ((1 + discount_rate) ** y)
        yearly *= (1 - degradation)
    return round(npv, 2)


def _as_float(v: object) -> float | None:
    if v in (None, "", "None"):
        return None
    try:
        return float(v)
    except Exception:
        return None


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _zip_key(value: object) -> str:
    if value in (None, "", "None"):
        return "unknown"
    zs = str(value).strip()
    match = re.match(r"^(\d{5})", zs)
    if match:
        return match.group(1)
    return zs


def _as_bool(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _nsrdb_confidence_adjustment(ghi_annual: float | None) -> float:
    if ghi_annual is None:
        return 0.0
    # Conservative confidence nudge around an MVP baseline annual GHI.
    # Typical US annual average GHI often falls near ~5.0 kWh/m2/day.
    return _clamp((ghi_annual - 5.0) * 0.02, -0.04, 0.04)


def load_zip_priority(path: Path) -> Dict[str, Dict[str, float]]:
    if not path.exists():
        return {}

    priors: Dict[str, Dict[str, float]] = {}
    with path.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            zip_code = _zip_key(row.get("zip"))
            priors[zip_code] = {
                "priority_score": _as_float(row.get("priority_score")) or 0.50,
                "income_pct": _as_float(row.get("income_pct")) or 0.50,
                "home_value_pct": _as_float(row.get("home_value_pct")) or 0.50,
                "owner_occ_pct": _as_float(row.get("owner_occ_pct")) or 0.50,
                "occupied_units_pct": _as_float(row.get("occupied_units_pct")) or 0.50,
            }
    return priors


def load_property_triggers(path: Path) -> Dict[str, Dict[str, object]]:
    if not path.exists():
        return {}

    triggers: Dict[str, Dict[str, object]] = {}
    with path.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            site_id = str(row.get("site_id") or "").strip()
            if not site_id:
                continue
            triggers[site_id] = {
                "storm_trigger_status": str(row.get("storm_trigger_status") or "missing").strip() or "missing",
                "outage_trigger_status": str(row.get("outage_trigger_status") or "missing").strip() or "missing",
                "equipment_age_trigger_status": str(row.get("equipment_age_trigger_status") or "missing").strip() or "missing",
                "flood_risk_trigger_status": str(row.get("flood_risk_trigger_status") or "missing").strip() or "missing",
                "permit_trigger_status": str(row.get("permit_trigger_status") or "missing").strip() or "missing",
                "storm_trigger_score": _as_float(row.get("storm_trigger_score")),
                "outage_trigger_score": _as_float(row.get("outage_trigger_score")),
                "equipment_age_trigger_score": _as_float(row.get("equipment_age_trigger_score")),
                "flood_risk_trigger_score": _as_float(row.get("flood_risk_trigger_score")),
                "permit_trigger_score": _as_float(row.get("permit_trigger_score")),
                "permit_recent_count": _as_float(row.get("permit_recent_count")),
                "permit_recent_types": str(row.get("permit_recent_types") or "").strip(),
                "permit_last_date": str(row.get("permit_last_date") or "").strip(),
                "permit_last_type": str(row.get("permit_last_type") or "").strip(),
                "trigger_notes": str(row.get("trigger_notes") or "").strip(),
            }
    return triggers


def load_state_reliability_prior(path: Path) -> Dict[str, Dict[str, object]]:
    if not path.exists():
        return {}

    rows: List[Dict[str, object]] = []
    with path.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            state = str(row.get("state") or "").strip().upper()
            saidi = _as_float(row.get("saidi_with_major"))
            saifi = _as_float(row.get("saifi_with_major"))
            if not state or saidi is None or saifi is None:
                continue
            rows.append(
                {
                    "state": state,
                    "reliability_year": str(row.get("reliability_year") or "").strip(),
                    "source_table": str(row.get("source_table") or "").strip(),
                    "source_url": str(row.get("source_url") or "").strip(),
                    "saidi_with_major": saidi,
                    "saifi_with_major": saifi,
                }
            )

    if not rows:
        return {}

    saidi_bounds = _minmax_bounds([float(r["saidi_with_major"]) for r in rows])
    saifi_bounds = _minmax_bounds([float(r["saifi_with_major"]) for r in rows])
    priors: Dict[str, Dict[str, object]] = {}

    for row in rows:
        saidi_score = _scale_from_bounds(saidi_bounds, float(row["saidi_with_major"]))
        saifi_score = _scale_from_bounds(saifi_bounds, float(row["saifi_with_major"]))
        prior_score = round((saidi_score * 0.7) + (saifi_score * 0.3), 1)
        if prior_score >= 70.0:
            status = "high"
            tier = "fragile"
        elif prior_score >= 40.0:
            status = "medium"
            tier = "elevated"
        else:
            status = "low"
            tier = "stable"

        priors[str(row["state"])] = {
            "battery_reliability_prior_status": status,
            "battery_reliability_prior_score": prior_score,
            "utility_reliability_tier": tier,
            "saidi_minutes": round(float(row["saidi_with_major"]), 1),
            "saifi_events": round(float(row["saifi_with_major"]), 3),
            "battery_reliability_prior_note": (
                f"EIA {row['reliability_year']} reliability prior: SAIDI {float(row['saidi_with_major']):.1f} min, "
                f"SAIFI {float(row['saifi_with_major']):.3f}, tier={tier}"
            ),
        }

    return priors


def load_state_rate_overrides(path: Path) -> Dict[str, Dict[str, object]]:
    if not path.exists():
        return {}

    overrides: Dict[str, Dict[str, object]] = {}
    with path.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            state = str(row.get("state") or "").strip().upper()
            rate = _as_float(row.get("retail_rate_usd_per_kwh"))
            if not state or rate is None:
                continue
            overrides[state] = {
                "utility_rate_override_usd_per_kwh": round(rate, 4),
                "utility_rate_source": str(row.get("source_table") or "").strip(),
                "utility_rate_source_url": str(row.get("source_url") or "").strip(),
                "utility_rate_period": str(row.get("rate_period") or "").strip(),
                "utility_rate_year": str(row.get("rate_year") or "").strip(),
            }
    return overrides


def load_site_utility_rates(path: Path) -> Dict[str, Dict[str, object]]:
    if not path.exists():
        return {}

    rates: Dict[str, Dict[str, object]] = {}
    with path.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            site_id = str(row.get("site_id") or "").strip()
            if not site_id:
                continue
            rates[site_id] = {
                "utility_id": str(row.get("utility_id") or "").strip(),
                "utility_name": str(row.get("utility_name") or "").strip(),
                "rate_plan": str(row.get("rate_plan") or "").strip(),
                "energy_rate_kwh": _as_float(row.get("energy_rate_kwh")),
                "fixed_monthly_usd": _as_float(row.get("fixed_monthly_usd")),
                "demand_charge_kw": _as_float(row.get("demand_charge_kw")),
                "source": str(row.get("source") or "").strip(),
                "as_of": str(row.get("as_of") or "").strip(),
            }
    return rates


def load_manual_utility_mappings(path: Path) -> Dict[Tuple[str, str, str], Dict[str, object]]:
    if not path.exists():
        return {}

    mappings: Dict[Tuple[str, str, str], Dict[str, object]] = {}
    with path.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            zip_code = str(row.get("zip") or "").strip()[:5]
            state = str(row.get("state") or "").strip().upper()
            city = str(row.get("city") or "").strip().lower()
            utility_name = str(row.get("utility_name") or "").strip()
            if not zip_code or not state or not utility_name:
                continue
            mappings[(zip_code, state, city)] = {
                "utility_id": str(row.get("utility_id") or "").strip(),
                "utility_name": utility_name,
                "rate_plan": str(row.get("rate_plan") or "").strip(),
                "source": str(row.get("source_title") or "").strip(),
                "source_url": str(row.get("source_url") or "").strip(),
                "as_of": str(row.get("as_of") or "").strip(),
                "notes": str(row.get("notes") or "").strip(),
                "mapping_method": str(row.get("mapping_method") or "").strip(),
            }
    return mappings


def load_official_utility_rate_overrides(path: Path) -> Dict[str, Dict[str, object]]:
    if not path.exists():
        return {}

    overrides: Dict[str, Dict[str, object]] = {}
    with path.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            utility_name = str(row.get("utility_name") or "").strip()
            total_rate = _as_float(row.get("total_rate_kwh"))
            if not utility_name or total_rate is None:
                continue
            overrides[utility_name] = {
                "utility_rate_override_usd_per_kwh": round(total_rate, 5),
                "utility_rate_source": str(row.get("source_title") or "").strip(),
                "utility_rate_source_url": str(row.get("source_url") or "").strip(),
                "utility_rate_period": (
                    f"{str(row.get('effective_start') or '').strip()} to {str(row.get('effective_end') or '').strip()}"
                ).strip(" to "),
                "utility_rate_year": str(row.get("effective_start") or "").strip()[:4],
                "utility_rate_notes": str(row.get("notes") or "").strip(),
                "rate_plan": str(row.get("rate_code") or "").strip(),
                "fixed_monthly_usd": _as_float(row.get("customer_charge_monthly")),
            }
    return overrides


def build_state_utility_rate_medians(
    sites: List[Dict[str, object]],
    site_utility_rates: Dict[str, Dict[str, object]],
) -> Dict[str, float]:
    values_by_state: Dict[str, List[float]] = defaultdict(list)
    for site in sites:
        site_id = str(site.get("site_id") or "").strip()
        state = str(site.get("state") or "").strip().upper()
        if not site_id or not state:
            continue
        utility_row = site_utility_rates.get(site_id)
        rate = _as_float((utility_row or {}).get("energy_rate_kwh"))
        if rate is None or rate <= 0:
            continue
        values_by_state[state].append(rate)

    medians: Dict[str, float] = {}
    for state, values in values_by_state.items():
        medians[state] = round(median(values), 5)
    return medians


def scoring_assumptions_for_site(
    site: Dict[str, object],
    base_assumptions: ScoringAssumptions,
    state_rate_overrides: Dict[str, Dict[str, object]] | None = None,
) -> ScoringAssumptions:
    state = str(site.get("state") or "").strip().upper()
    override = (state_rate_overrides or {}).get(state)
    if not override:
        return base_assumptions

    return ScoringAssumptions(
        utility_rate_usd_per_kwh=float(override["utility_rate_override_usd_per_kwh"]),
        install_cost_usd_per_kw=base_assumptions.install_cost_usd_per_kw,
        wind_addon_cost_multiplier=base_assumptions.wind_addon_cost_multiplier,
        discount_rate=base_assumptions.discount_rate,
        annual_degradation=base_assumptions.annual_degradation,
        h3_resolution=base_assumptions.h3_resolution,
        wind_min_confidence=base_assumptions.wind_min_confidence,
    )


def resolve_site_rate_context(
    site: Dict[str, object],
    base_assumptions: ScoringAssumptions,
    state_rate_overrides: Dict[str, Dict[str, object]] | None = None,
    site_utility_rates: Dict[str, Dict[str, object]] | None = None,
    state_utility_rate_medians: Dict[str, float] | None = None,
    official_utility_rate_overrides: Dict[str, Dict[str, object]] | None = None,
    manual_utility_mappings: Dict[Tuple[str, str, str], Dict[str, object]] | None = None,
) -> Tuple[ScoringAssumptions, Dict[str, object]]:
    state = str(site.get("state") or "").strip().upper()
    site_id = str(site.get("site_id") or "").strip()
    zip_code = str(site.get("zip") or "").strip()[:5]
    city = str(site.get("city") or "").strip().lower()
    state_override = (state_rate_overrides or {}).get(state)
    utility_row = (site_utility_rates or {}).get(site_id)
    manual_row = (manual_utility_mappings or {}).get((zip_code, state, city)) or (manual_utility_mappings or {}).get((zip_code, state, ""))
    utility_context = dict(utility_row or {})
    if manual_row:
        if not utility_context:
            utility_context = dict(manual_row)
        else:
            for key, value in manual_row.items():
                if utility_context.get(key) in (None, "", "None"):
                    utility_context[key] = value
    utility_rate = _as_float((utility_row or {}).get("energy_rate_kwh"))
    utility_name = str((utility_context or {}).get("utility_name") or "").strip()
    official_override = (official_utility_rate_overrides or {}).get(utility_name)
    state_rate = _as_float((state_override or {}).get("utility_rate_override_usd_per_kwh"))
    state_median = _as_float((state_utility_rate_medians or {}).get(state))

    resolved_rate = base_assumptions.utility_rate_usd_per_kwh
    rate_method = "default_assumption"
    rate_source = "ScoringAssumptions default"
    rate_source_url = ""
    rate_period = "default"
    rate_year = ""

    if official_override:
        resolved_rate = round(float(official_override["utility_rate_override_usd_per_kwh"]), 5)
        rate_method = "official_utility_override"
        rate_source = str(official_override.get("utility_rate_source") or "").strip()
        rate_source_url = str(official_override.get("utility_rate_source_url") or "").strip()
        rate_period = str(official_override.get("utility_rate_period") or "").strip()
        rate_year = str(official_override.get("utility_rate_year") or "").strip()
    elif utility_rate is not None and utility_rate > 0 and state_rate is not None and state_median and state_median > 0:
        relative_ratio = _clamp(utility_rate / state_median, 0.85, 1.15)
        resolved_rate = round(state_rate * relative_ratio, 4)
        rate_method = "utility_screening_bounded_to_state"
        rate_source = str(utility_row.get("source") or "utility screening feed").strip()
        rate_source_url = str(utility_row.get("source") or "").strip()
        rate_period = str((state_override or {}).get("utility_rate_period") or "").strip()
        rate_year = str((state_override or {}).get("utility_rate_year") or "").strip()
    elif utility_rate is not None and utility_rate > 0:
        resolved_rate = round(utility_rate, 4)
        rate_method = "utility_screening_direct"
        rate_source = str(utility_row.get("source") or "utility screening feed").strip()
        rate_source_url = str(utility_row.get("source") or "").strip()
        rate_period = str((utility_row or {}).get("as_of") or "").strip()
    elif state_rate is not None:
        resolved_rate = round(state_rate, 4)
        rate_method = "state_official_fallback"
        rate_source = str((state_override or {}).get("utility_rate_source") or "").strip()
        rate_source_url = str((state_override or {}).get("utility_rate_source_url") or "").strip()
        rate_period = str((state_override or {}).get("utility_rate_period") or "").strip()
        rate_year = str((state_override or {}).get("utility_rate_year") or "").strip()

    assumptions = ScoringAssumptions(
        utility_rate_usd_per_kwh=float(resolved_rate),
        install_cost_usd_per_kw=base_assumptions.install_cost_usd_per_kw,
        wind_addon_cost_multiplier=base_assumptions.wind_addon_cost_multiplier,
        discount_rate=base_assumptions.discount_rate,
        annual_degradation=base_assumptions.annual_degradation,
        h3_resolution=base_assumptions.h3_resolution,
        wind_min_confidence=base_assumptions.wind_min_confidence,
    )

    metadata = {
        "utility_id": str((utility_context or {}).get("utility_id") or "").strip(),
        "utility_name": str((utility_context or {}).get("utility_name") or "").strip(),
        "rate_plan": str((official_override or {}).get("rate_plan") or (utility_context or {}).get("rate_plan") or "").strip(),
        "utility_rate_screening_usd_per_kwh": round(float(utility_rate), 5) if utility_rate is not None else None,
        "utility_rate_override_usd_per_kwh": round(float(resolved_rate), 4),
        "utility_rate_method": rate_method,
        "utility_rate_source": rate_source,
        "utility_rate_source_url": rate_source_url,
        "utility_rate_period": rate_period,
        "utility_rate_year": rate_year,
        "utility_rate_as_of": str((utility_context or {}).get("as_of") or "").strip(),
        "utility_rate_notes": str((official_override or {}).get("utility_rate_notes") or (utility_context or {}).get("notes") or "").strip(),
        "fixed_monthly_usd": _as_float((official_override or {}).get("fixed_monthly_usd"))
        if (official_override or {}).get("fixed_monthly_usd") is not None
        else _as_float((utility_context or {}).get("fixed_monthly_usd")),
    }
    return assumptions, metadata


def _minmax(values: List[float], value: float, lo: float = 0.0, hi: float = 100.0, default: float = 50.0) -> float:
    if not values:
        return default
    vmin = min(values)
    vmax = max(values)
    if abs(vmax - vmin) < 1e-9:
        return default
    ratio = (value - vmin) / (vmax - vmin)
    return _clamp(lo + ((hi - lo) * ratio), lo, hi)


def _minmax_bounds(values: List[float]) -> Tuple[float, float] | None:
    if not values:
        return None
    return (min(values), max(values))


def _scale_from_bounds(
    bounds: Tuple[float, float] | None,
    value: float,
    lo: float = 0.0,
    hi: float = 100.0,
    default: float = 50.0,
) -> float:
    if not bounds:
        return default
    vmin, vmax = bounds
    if abs(vmax - vmin) < 1e-9:
        return default
    ratio = (value - vmin) / (vmax - vmin)
    return _clamp(lo + ((hi - lo) * ratio), lo, hi)


def _product_trigger_metadata(product: str, confidence: float, solar_access: float) -> Dict[str, str]:
    if product == "solar":
        readiness = "geometry-screening"
        gap = "Still screening-grade: upgrade with parcel shading, tariff normalization, and install assumptions before quote-grade solar claims."
        if confidence < 0.75 or solar_access < 0.7:
            gap = "Still screening-grade: verify shading, roof condition, and tariff assumptions on site before pushing a solar-first pitch."
        return {"readiness": readiness, "gap": gap}

    if product == "roofing":
        return {
            "readiness": "proxy-only",
            "gap": "Needs storm or hail history, roof-age evidence, and neighborhood replacement clustering before event-ready roofing targeting.",
        }

    if product == "hvac_heat_pump":
        return {
            "readiness": "proxy-only",
            "gap": "Needs equipment-age, fuel-type, and replacement-timing evidence before HVAC upgrade timing is reliable.",
        }

    if product == "battery_backup":
        return {
            "readiness": "proxy-only",
            "gap": "Needs outage history, tariff structure, and whole-home backup need signals before resiliency targeting is reliable.",
        }

    return {
        "readiness": "proxy-only",
        "gap": "Supporting trigger data is not loaded for this lane yet.",
    }


def _trigger_signal_level(status: object, score: object) -> str:
    normalized = str(status or "").strip().lower()
    numeric = _as_float(score) or 0.0
    if normalized in {"", "missing", "none", "low"} and numeric <= 0.0:
        return "none"
    if normalized in {"event_detected", "high", "verified", "modeled"} or numeric >= 70.0:
        return "strong"
    if normalized in {"medium", "proxy"} or numeric > 0.0:
        return "weak"
    return "none"


def _battery_outage_signal_level(status: object, score: object) -> str:
    normalized = str(status or "").strip().lower()
    numeric = _as_float(score) or 0.0
    if normalized in {"event_detected", "high", "verified"} or numeric >= 20.0:
        return "strong"
    if normalized == "medium" or numeric >= 8.0:
        return "weak"
    return "none"


def _percentile(sorted_values: List[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    q = _clamp(q, 0.0, 1.0)
    idx = q * (len(sorted_values) - 1)
    lo = int(idx)
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = idx - lo
    return sorted_values[lo] + ((sorted_values[hi] - sorted_values[lo]) * frac)


def apply_sales_priority(scored: List[Dict[str, object]], zip_priors: Dict[str, Dict[str, float]]) -> List[Dict[str, object]]:
    npvs = [_as_float(r.get("npv_15y_usd")) or 0.0 for r in scored]
    savings = [_as_float(r.get("annual_savings_usd")) or 0.0 for r in scored]
    systems = [
        (_as_float(r.get("install_cost_solar_usd")) or 0.0) / 2200.0
        for r in scored
    ]
    usable_areas = [kw * 8.5 for kw in systems]
    npv_bounds = _minmax_bounds(npvs)
    savings_bounds = _minmax_bounds(savings)
    system_bounds = _minmax_bounds(systems)
    usable_area_bounds = _minmax_bounds(usable_areas)

    for row, estimated_kw, roof_usable_area_m2 in zip(scored, systems, usable_areas):
        zip_code = _zip_key(row.get("zip"))
        prior = zip_priors.get(
            zip_code,
            {
                "priority_score": 0.50,
                "income_pct": 0.50,
                "home_value_pct": 0.50,
                "owner_occ_pct": 0.50,
                "occupied_units_pct": 0.50,
            },
        )

        compactness = _as_float(row.get("footprint_compactness"))
        vertex_count = _as_float(row.get("footprint_vertex_count"))
        confidence = _as_float(row.get("confidence")) or 0.70
        annual_kwh_solar = _as_float(row.get("annual_kwh_solar")) or 0.0
        local_count = _as_float(row.get("site_context_local_count")) or 0.0
        source_type = str(row.get("source_type") or "unknown")
        requires_site_survey = _as_bool(row.get("requires_site_survey"))

        solar_access_proxy = _clamp(annual_kwh_solar / max(estimated_kw * 8760.0 * 0.22, 1e-6), 0.45, 1.0)

        shape_penalty = 0.0
        if compactness is not None:
            shape_penalty += (1.0 - _clamp(compactness, 0.0, 1.0)) * 38.0
        if vertex_count is not None and vertex_count > 0:
            shape_penalty += _clamp((vertex_count - 8.0) * 1.9, 0.0, 24.0)
        if source_type == "node":
            shape_penalty += 12.0
        roof_complexity_score = round(_clamp(shape_penalty, 5.0, 95.0), 1)

        profit_score = (
            (0.50 * _scale_from_bounds(npv_bounds, _as_float(row.get("npv_15y_usd")) or 0.0))
            + (0.35 * _scale_from_bounds(savings_bounds, _as_float(row.get("annual_savings_usd")) or 0.0))
            + (0.15 * _scale_from_bounds(system_bounds, estimated_kw))
        )
        close_probability = (
            (prior["priority_score"] * 40.0)
            + (prior["owner_occ_pct"] * 24.0)
            + (prior["income_pct"] * 18.0)
            + (prior["home_value_pct"] * 8.0)
            + (confidence * 10.0)
        )
        fit_score = (
            (solar_access_proxy * 42.0)
            + (_scale_from_bounds(usable_area_bounds, roof_usable_area_m2) * 0.28)
            + (confidence * 20.0)
            + (0.0 if requires_site_survey else 10.0)
        )
        effort_score = (
            (30.0 if requires_site_survey else 8.0)
            + (roof_complexity_score * 0.35)
            + (_clamp(local_count, 0.0, 10.0) * 2.2)
            + (12.0 if source_type == "node" else 4.0)
        )
        priority_score = _clamp(
            (0.40 * profit_score)
            + (0.30 * close_probability)
            + (0.20 * fit_score)
            - (0.10 * effort_score),
            0.0,
            100.0,
        )

        if priority_score >= 78 and effort_score <= 42 and close_probability >= 70:
            easy_win_label = "Easy win"
        elif priority_score >= 58:
            easy_win_label = "Medium effort"
        else:
            easy_win_label = "Hard sell"

        row["zip_priority_score"] = round(prior["priority_score"] * 100.0, 1)
        row["roof_usable_area_m2"] = round(roof_usable_area_m2, 1)
        row["estimated_system_kw"] = round(estimated_kw, 2)
        row["roof_complexity_score"] = roof_complexity_score
        row["solar_access_proxy"] = round(solar_access_proxy, 3)
        row["profit_score"] = round(_clamp(profit_score, 0.0, 100.0), 1)
        row["close_probability"] = round(_clamp(close_probability, 0.0, 100.0), 1)
        row["fit_score"] = round(_clamp(fit_score, 0.0, 100.0), 1)
        row["effort_score"] = round(_clamp(effort_score, 0.0, 100.0), 1)
        row["priority_score"] = round(priority_score, 1)
        row["easy_win_label"] = easy_win_label
        reasons = list(row.get("reasons") or [])
        reasons.append(
            f"Sales priority combines profit {row['profit_score']}, close probability {row['close_probability']}, fit {row['fit_score']}, and effort {row['effort_score']}"
        )
        reasons.append(f"ZIP market prior contributed {row['zip_priority_score']:.1f}/100 to close-probability weighting")
        row["reasons"] = reasons

    return scored


def apply_product_recommendations(scored: List[Dict[str, object]]) -> List[Dict[str, object]]:
    usable_roofs = [_as_float(r.get("roof_usable_area_m2")) or 0.0 for r in scored]
    system_sizes = [_as_float(r.get("estimated_system_kw")) or 0.0 for r in scored]
    priorities = [_as_float(r.get("priority_score")) or 0.0 for r in scored]
    usable_roof_bounds = _minmax_bounds(usable_roofs)
    system_size_bounds = _minmax_bounds(system_sizes)
    priority_bounds = _minmax_bounds(priorities)

    for row in scored:
        profit = _as_float(row.get("profit_score")) or 0.0
        close = _as_float(row.get("close_probability")) or 0.0
        fit = _as_float(row.get("fit_score")) or 0.0
        effort = _as_float(row.get("effort_score")) or 0.0
        usable_roof = _as_float(row.get("roof_usable_area_m2")) or 0.0
        solar_access = _as_float(row.get("solar_access_proxy")) or 0.0
        zip_priority = _as_float(row.get("zip_priority_score")) or 50.0
        estimated_kw = _as_float(row.get("estimated_system_kw")) or 0.0
        complexity = _as_float(row.get("roof_complexity_score")) or 50.0
        confidence = _as_float(row.get("confidence")) or 0.70
        survey_required = _as_bool(row.get("requires_site_survey"))
        storm_trigger = _as_float(row.get("storm_trigger_score")) or 0.0
        outage_trigger = _as_float(row.get("outage_trigger_score")) or 0.0
        battery_reliability_prior = _as_float(row.get("battery_reliability_prior_score")) or 0.0
        equipment_trigger = _as_float(row.get("equipment_age_trigger_score")) or 0.0
        flood_trigger = _as_float(row.get("flood_risk_trigger_score")) or 0.0
        permit_trigger = _as_float(row.get("permit_trigger_score")) or 0.0
        storm_signal = _trigger_signal_level(row.get("storm_trigger_status"), storm_trigger)
        outage_signal = _trigger_signal_level(row.get("outage_trigger_status"), outage_trigger)
        battery_outage_signal = _battery_outage_signal_level(row.get("outage_trigger_status"), outage_trigger)
        battery_prior_signal = _trigger_signal_level(
            row.get("battery_reliability_prior_status"),
            battery_reliability_prior,
        )
        equipment_signal = _trigger_signal_level(row.get("equipment_age_trigger_status"), equipment_trigger)
        flood_signal = _trigger_signal_level(row.get("flood_risk_trigger_status"), flood_trigger)
        permit_signal = _trigger_signal_level(row.get("permit_trigger_status"), permit_trigger)
        roof_scale = _scale_from_bounds(usable_roof_bounds, usable_roof)
        home_size_proxy = _scale_from_bounds(system_size_bounds, estimated_kw)
        priority = _scale_from_bounds(priority_bounds, _as_float(row.get("priority_score")) or 0.0)
        survey_bonus = 0.0 if survey_required else 10.0
        low_solar_bonus = (1.0 - solar_access) * 16.0
        resilience_fit = (solar_access * 42.0) + (confidence * 26.0) + (close * 0.24)
        storm_trigger_boost = storm_trigger * (0.26 if storm_signal == "strong" else 0.12 if storm_signal == "weak" else 0.0)
        outage_trigger_boost = outage_trigger * (
            0.32 if battery_outage_signal == "strong" else 0.08 if battery_outage_signal == "weak" else 0.0
        )
        battery_prior_boost = battery_reliability_prior * (
            0.08 if battery_prior_signal == "strong" else 0.03 if battery_prior_signal == "weak" else 0.0
        )
        equipment_trigger_boost = min(equipment_trigger, 75.0) * (
            0.08 if equipment_signal == "strong" else 0.04 if equipment_signal == "weak" else 0.0
        )
        permit_trigger_boost = permit_trigger * (
            0.16 if permit_signal == "strong" else 0.08 if permit_signal == "weak" else 0.0
        )

        product_scores = {
            "roofing": (
                (roof_scale * 0.30)
                + (zip_priority * 0.20)
                + (close * 0.20)
                + ((100.0 - complexity) * 0.14)
                + (low_solar_bonus)
                + survey_bonus
                + storm_trigger_boost
                + permit_trigger_boost
            ),
            "solar": (
                (profit * 0.28)
                + (fit * 0.26)
                + (close * 0.18)
                + (roof_scale * 0.12)
                + (solar_access * 26.0)
                + (confidence * 6.0)
            ),
            "hvac_heat_pump": (
                (close * 0.24)
                + (zip_priority * 0.14)
                + (priority * 0.08)
                + (profit * 0.10)
                + (home_size_proxy * 0.16)
                + ((100.0 - effort) * 0.08)
                + (survey_bonus * 0.4)
                + (low_solar_bonus * 0.4)
                + equipment_trigger_boost
                + (permit_trigger_boost * 0.55)
            ),
            "battery_backup": (
                (resilience_fit * 0.34)
                + (zip_priority * 0.18)
                + (fit * 0.14)
                + (profit * 0.12)
                + (priority * 0.08)
                + (18.0 if battery_outage_signal == "strong" else 5.0 if battery_outage_signal == "weak" else 0.0)
                + (6.0 if battery_prior_signal == "strong" else 2.0 if battery_prior_signal == "weak" else 0.0)
                + survey_bonus
                + outage_trigger_boost
                + battery_prior_boost
            ),
        }

        if equipment_signal == "strong":
            hvac_context_boost = (
                min(5.0, equipment_trigger * 0.05)
                + max(0.0, home_size_proxy - 55.0) * 0.05
                + max(0.0, 82.0 - (solar_access * 100.0)) * 0.08
            )
            product_scores["hvac_heat_pump"] += hvac_context_boost

        ordered = sorted(product_scores.items(), key=lambda item: item[1], reverse=True)
        if (
            equipment_signal == "strong"
            and solar_access < 0.84
            and home_size_proxy >= 58.0
            and (product_scores["solar"] - product_scores["hvac_heat_pump"]) <= 4.0
        ):
            ordered = sorted(
                [
                    ("hvac_heat_pump", product_scores["hvac_heat_pump"]),
                    ("solar", product_scores["solar"]),
                    ("roofing", product_scores["roofing"]),
                    ("battery_backup", product_scores["battery_backup"]),
                ],
                key=lambda item: item[1],
                reverse=True,
            )
        primary_product, primary_score = ordered[0]
        secondary_product, secondary_score = ordered[1]

        product_reasons = {
            "roofing": f"large roof proxy {roof_scale:.0f}/100, close probability {close:.0f}/100, moderate complexity headroom {(100.0 - complexity):.0f}/100",
            "solar": f"solar access {(solar_access * 100):.0f}%, fit {fit:.0f}/100, profit {profit:.0f}/100",
            "hvac_heat_pump": f"close probability {close:.0f}/100, home-size proxy {home_size_proxy:.0f}/100, manageable effort {(100.0 - effort):.0f}/100",
            "battery_backup": f"resilience fit {resilience_fit:.0f}/100, solar access {(solar_access * 100):.0f}%, confidence {(confidence * 100):.0f}%",
        }

        if primary_product == "roofing":
            pitch = "Lead with roof value and replacement economics; use solar as a follow-on if timing is right."
        elif primary_product == "solar":
            pitch = "Lead with energy savings and roof fit; mention battery if resiliency or outage concerns come up."
        elif primary_product == "hvac_heat_pump":
            pitch = "Lead with comfort, replacement timing, and efficiency upgrade economics; keep roofing/solar as secondary."
        else:
            pitch = "Lead with resiliency and backup power value; use solar as the obvious adjacent upgrade."

        row["roofing_score"] = round(_clamp(product_scores["roofing"], 0.0, 100.0), 1)
        row["solar_score"] = round(_clamp(product_scores["solar"], 0.0, 100.0), 1)
        row["hvac_score"] = round(_clamp(product_scores["hvac_heat_pump"], 0.0, 100.0), 1)
        row["battery_score"] = round(_clamp(product_scores["battery_backup"], 0.0, 100.0), 1)
        row["primary_product"] = primary_product
        row["secondary_product"] = secondary_product
        row["primary_product_score"] = round(_clamp(primary_score, 0.0, 100.0), 1)
        row["secondary_product_score"] = round(_clamp(secondary_score, 0.0, 100.0), 1)
        row["primary_product_reason"] = product_reasons[primary_product]
        row["secondary_product_reason"] = product_reasons[secondary_product]
        primary_trigger = _product_trigger_metadata(primary_product, confidence, solar_access)
        secondary_trigger = _product_trigger_metadata(secondary_product, confidence, solar_access)
        row["primary_product_readiness"] = primary_trigger["readiness"]
        row["secondary_product_readiness"] = secondary_trigger["readiness"]
        row["primary_product_trigger_gap"] = primary_trigger["gap"]
        row["secondary_product_trigger_gap"] = secondary_trigger["gap"]
        storm_status = str(row.get("storm_trigger_status") or "missing")
        outage_status = str(row.get("outage_trigger_status") or "missing")
        equipment_status = str(row.get("equipment_age_trigger_status") or "missing")
        flood_status = str(row.get("flood_risk_trigger_status") or "missing")
        row["has_storm_trigger_data"] = storm_signal != "none"
        row["has_outage_trigger_data"] = outage_signal != "none"
        row["has_actionable_outage_data"] = battery_outage_signal != "none"
        row["has_battery_reliability_data"] = str(row.get("battery_reliability_prior_status") or "missing") != "missing"
        row["has_actionable_battery_reliability_data"] = battery_prior_signal != "none"
        row["has_equipment_age_data"] = equipment_signal != "none"
        row["has_flood_risk_data"] = flood_signal != "none"
        row["has_permit_trigger_data"] = permit_signal != "none"
        missing_labels: List[str] = []
        if not row["has_storm_trigger_data"]:
            missing_labels.append("storm/hail events")
        if not row["has_outage_trigger_data"]:
            missing_labels.append("outage reliability")
        if not row["has_battery_reliability_data"]:
            missing_labels.append("historical reliability baseline")
        if not row["has_equipment_age_data"]:
            missing_labels.append("equipment age or fuel type")
        if not row["has_flood_risk_data"]:
            missing_labels.append("flood or drainage risk")
        if not row["has_permit_trigger_data"]:
            missing_labels.append("permit/work history")
        row["trigger_data_gaps"] = (
            f"Missing external trigger layers: {', '.join(missing_labels)}."
            if missing_labels
            else "Core trigger layers are loaded for storm, outage, equipment age, flood risk, permit/work history, and historical reliability."
        )
        row["recommended_pitch"] = pitch
        reasons = list(row.get("reasons") or [])
        reasons.append(
            f"Primary offer `{primary_product}` outranked `{secondary_product}` using current proxy-based multi-product scoring"
        )
        reasons.append(
            f"{primary_product} lane readiness is {row['primary_product_readiness']}: {row['primary_product_trigger_gap']}"
        )
        trigger_notes = str(row.get("trigger_notes") or "").strip()
        permit_last_date = str(row.get("permit_last_date") or "").strip()
        permit_recent_types = str(row.get("permit_recent_types") or "").strip()
        if row["has_permit_trigger_data"]:
            permit_summary = f"Permit history loaded ({str(row.get('permit_trigger_status') or '').strip()}"
            if permit_last_date:
                permit_summary += f", last={permit_last_date}"
            if permit_recent_types:
                permit_summary += f", recent_types={permit_recent_types}"
            permit_summary += ")"
            reasons.append(permit_summary)
        if trigger_notes:
            reasons.append(f"Trigger notes: {trigger_notes}")
        row["reasons"] = reasons

    return scored


def apply_operator_routing(scored: List[Dict[str, object]]) -> List[Dict[str, object]]:
    raw_scores: List[float] = []

    for row in scored:
        priority = _as_float(row.get("priority_score")) or 0.0
        primary_score = _as_float(row.get("primary_product_score")) or 0.0
        secondary_score = _as_float(row.get("secondary_product_score")) or 0.0
        close = _as_float(row.get("close_probability")) or 0.0
        effort = _as_float(row.get("effort_score")) or 0.0
        product = str(row.get("primary_product") or "solar")
        actionable_outage = bool(row.get("has_actionable_outage_data"))

        trigger_count = sum(
            1.0
            for key in (
                "has_storm_trigger_data",
                "has_equipment_age_data",
                "has_flood_risk_data",
                "has_permit_trigger_data",
            )
            if bool(row.get(key))
        )
        if actionable_outage:
            trigger_count += 1.0
        if bool(row.get("has_actionable_battery_reliability_data")):
            trigger_count += 0.5
        product_boost = {
            "roofing": 14.0,
            "hvac_heat_pump": 4.0,
            "battery_backup": 2.0,
            "solar": 0.0,
        }.get(product, 0.0)
        route_score_raw = (
            (priority * 0.56)
            + (primary_score * 0.28)
            + (close * 0.10)
            + (secondary_score * 0.04)
            + (trigger_count * 2.0)
            + product_boost
            - (effort * 0.04)
        )
        row["_route_score_raw"] = route_score_raw
        raw_scores.append(route_score_raw)

    sorted_scores = sorted(raw_scores)
    hot_threshold = _percentile(sorted_scores, 0.97)
    warm_threshold = _percentile(sorted_scores, 0.72)

    for row in scored:
        route_score = _as_float(row.get("_route_score_raw")) or 0.0
        product = str(row.get("primary_product") or "solar")
        readiness = str(row.get("primary_product_readiness") or "proxy-only")
        trigger_gap = str(row.get("primary_product_trigger_gap") or "")
        close = _as_float(row.get("close_probability")) or 0.0
        profit = _as_float(row.get("profit_score")) or 0.0
        fit = _as_float(row.get("fit_score")) or 0.0
        trigger_loaded = {
            "roofing": bool(row.get("has_storm_trigger_data")),
            "hvac_heat_pump": bool(row.get("has_equipment_age_data")),
            "battery_backup": actionable_outage or bool(row.get("has_actionable_battery_reliability_data")),
            "solar": True,
        }.get(product, False)
        permit_loaded = bool(row.get("has_permit_trigger_data"))

        if route_score >= hot_threshold:
            lead_temperature = "hot"
            operator_next_step = "work_now"
        elif route_score >= warm_threshold:
            lead_temperature = "warm"
            operator_next_step = "follow_up"
        else:
            lead_temperature = "skip"
            operator_next_step = "deprioritize"

        if product == "roofing":
            pitch_angle = "Urgency and roof-value framing"
            why_now = "Large roof and closeability make this worth a roof-first conversation even before full storm evidence is loaded."
            if trigger_loaded:
                why_now = "Storm-linked roofing evidence is loaded here, so roof urgency should be tested before solar."
        elif product == "hvac_heat_pump":
            pitch_angle = "Comfort and replacement timing"
            why_now = "This property looks like a strong comfort-and-efficiency sale if replacement timing is favorable."
            if trigger_loaded:
                why_now = "Equipment-age evidence is loaded, so HVAC timing risk is lower than usual."
            elif permit_loaded:
                why_now = "Permit/work-history evidence is loaded here, so HVAC timing can be investigated before generic outreach."
        elif product == "battery_backup":
            pitch_angle = "Resiliency and outage protection"
            why_now = "Backup power is worth testing here if resiliency concerns are active, but outage urgency is still screening-grade."
            if actionable_outage:
                why_now = "Outage evidence is loaded, so backup power urgency is more credible than a generic upsell."
            elif bool(row.get("has_actionable_battery_reliability_data")):
                why_now = "Historical reliability is weak enough here to justify a real backup-power conversation even without a live outage spike."
        else:
            pitch_angle = "Savings and roof fit"
            why_now = "Solar remains the strongest first offer because the economics and roof-fit proxies are better than the alternatives."
            if permit_loaded:
                why_now = "Solar still leads here, and permit/work-history evidence gives a better investigation trail than a pure geometry-only lead."

        action_summary = {
            "work_now": f"Prioritize this stop and lead with {product.replace('_', ' ')}.",
            "follow_up": f"Keep this in the next route batch and validate {product.replace('_', ' ')} timing.",
            "deprioritize": "Park this unless a better trigger or operator note appears.",
        }[operator_next_step]

        if readiness != "geometry-screening" and not trigger_loaded:
            action_summary += f" Current gap: {trigger_gap}"
        elif permit_loaded and product in {"roofing", "hvac_heat_pump", "solar"}:
            action_summary += " Use permit history in the investigation packet before outreach."

        row["sales_route_score"] = round(_clamp(route_score, 0.0, 100.0), 1)
        row["lead_temperature"] = lead_temperature
        row["operator_next_step"] = operator_next_step
        row["operator_lane"] = product
        row["operator_pitch_angle"] = pitch_angle
        row["why_now_summary"] = why_now
        row["operator_action_summary"] = action_summary
        reasons = list(row.get("reasons") or [])
        reasons.append(
            f"Route score {row['sales_route_score']}/100 set lead bucket `{lead_temperature}` with next step `{operator_next_step}`"
        )
        row["reasons"] = reasons
        row.pop("_route_score_raw", None)

    scored.sort(
        key=lambda r: (
            -(_as_float(r.get("sales_route_score")) or 0.0),
            -(_as_float(r.get("priority_score")) or 0.0),
            -(_as_float(r.get("annual_savings_usd")) or 0.0),
            str(r.get("site_id") or ""),
        )
    )
    return scored


def write_scored(path: Path, rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise RuntimeError("no scored rows")
    columns = [
        "site_id",
        "address",
        "zip",
        "city",
        "state",
        "data_source",
        "source_type",
        "data_quality_tier",
        "lat",
        "lon",
        "footprint_area_m2",
        "footprint_perimeter_m",
        "footprint_compactness",
        "footprint_vertex_count",
        "site_context_local_count",
        "site_context_nearest_m",
        "h3_cell",
        "zip_priority_score",
        "roof_usable_area_m2",
        "estimated_system_kw",
        "roof_complexity_score",
        "solar_access_proxy",
        "profit_score",
        "close_probability",
        "fit_score",
        "effort_score",
        "priority_score",
        "sales_route_score",
        "easy_win_label",
        "lead_temperature",
        "operator_next_step",
        "operator_lane",
        "operator_pitch_angle",
        "why_now_summary",
        "operator_action_summary",
        "roofing_score",
        "solar_score",
        "hvac_score",
        "battery_score",
        "primary_product",
        "secondary_product",
        "primary_product_score",
        "secondary_product_score",
        "primary_product_reason",
        "secondary_product_reason",
        "primary_product_readiness",
        "secondary_product_readiness",
        "primary_product_trigger_gap",
        "secondary_product_trigger_gap",
        "storm_trigger_status",
        "outage_trigger_status",
        "equipment_age_trigger_status",
        "flood_risk_trigger_status",
        "permit_trigger_status",
        "battery_reliability_prior_status",
        "storm_trigger_score",
        "outage_trigger_score",
        "equipment_age_trigger_score",
        "flood_risk_trigger_score",
        "permit_trigger_score",
        "permit_recent_count",
        "permit_recent_types",
        "permit_last_date",
        "permit_last_type",
        "battery_reliability_prior_score",
        "utility_reliability_tier",
        "utility_id",
        "utility_name",
        "rate_plan",
        "fixed_monthly_usd",
        "utility_rate_screening_usd_per_kwh",
        "utility_rate_override_usd_per_kwh",
        "utility_rate_method",
        "utility_rate_source",
        "utility_rate_source_url",
        "utility_rate_period",
        "utility_rate_year",
        "utility_rate_as_of",
        "utility_rate_notes",
        "saidi_minutes",
        "saifi_events",
        "battery_reliability_prior_note",
        "has_storm_trigger_data",
        "has_outage_trigger_data",
        "has_actionable_outage_data",
        "has_battery_reliability_data",
        "has_actionable_battery_reliability_data",
        "has_equipment_age_data",
        "has_flood_risk_data",
        "has_permit_trigger_data",
        "trigger_data_gaps",
        "trigger_notes",
        "recommended_pitch",
        "annual_kwh_solar",
        "annual_kwh_wind",
        "annual_kwh_hybrid",
        "wind_confidence",
        "wind_viability",
        "install_cost_solar_usd",
        "install_cost_hybrid_usd",
        "annual_savings_usd",
        "payback_years",
        "npv_15y_usd",
        "best_option",
        "confidence",
        "confidence_label",
        "requires_site_survey",
        "solar_model",
        "pvwatts_ratio",
        "nsrdb_ghi_annual",
        "nsrdb_dni_annual",
        "nsrdb_confidence_adjustment",
        "reasons_json",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        for r in rows:
            out = dict(r)
            out["reasons_json"] = json.dumps(out.pop("reasons"))
            w.writerow(out)


def write_h3_aggregates(path: Path, scored: List[Dict[str, object]]) -> List[Dict[str, object]]:
    agg = defaultdict(list)
    for r in scored:
        agg[r["h3_cell"]].append(r)

    rows = []
    for h3_cell, items in agg.items():
        rows.append(
            {
                "h3_cell": h3_cell,
                "site_count": len(items),
                "avg_priority_score": round(mean(float(i["priority_score"]) for i in items), 2),
                "avg_annual_savings_usd": round(mean(float(i["annual_savings_usd"]) for i in items), 2),
                "avg_payback_years": round(mean(float(i["payback_years"]) for i in items), 2),
                "avg_confidence": round(mean(float(i["confidence"]) for i in items), 3),
            }
        )

    rows.sort(key=lambda r: r["avg_priority_score"], reverse=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return rows


def write_api_samples(path: Path, scored: List[Dict[str, object]], h3_rows: List[Dict[str, object]]) -> None:
    sample_site = scored[0]
    sample_h3 = h3_rows[0]["h3_cell"]
    sample_hex_sites = [s for s in scored if s["h3_cell"] == sample_h3][:10]

    payload = {
        "GET /api/v1/zip/{zip}/heatmap": {
            "zip": "sample",
            "cells": h3_rows[:10],
        },
        "GET /api/v1/hex/{h3}/sites": {
            "h3": sample_h3,
            "sites": sample_hex_sites,
        },
        "GET /api/v1/site/{site_id}": sample_site,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_assumptions(path: Path, assumptions: ScoringAssumptions, solar_model: str) -> None:
    content = f"""# Scoring Assumptions (Bootstrap)\n\n- Solar model: `{solar_model}`\n- Utility rate: `${assumptions.utility_rate_usd_per_kwh:.3f}` per kWh\n- Install cost: `${assumptions.install_cost_usd_per_kw:.0f}` per kW\n- Discount rate: `{assumptions.discount_rate:.1%}`\n- Annual degradation: `{assumptions.annual_degradation:.1%}`\n- H3 resolution: `{assumptions.h3_resolution}`\n- Wind confidence threshold: `{assumptions.wind_min_confidence:.2f}`\n- Wind add-on cost multiplier: `{assumptions.wind_addon_cost_multiplier:.0%}` of solar install\n\n## Notes\n- `proxy` model uses deterministic rooftop-capacity and CF proxies for speed/repeatability.\n- `pvwatts-cell-blend` model calibrates each H3 cell against PVWatts at cell centroid and scales outputs conservatively.\n- NSRDB enrichment uses NREL solar-resource annual GHI/DNI as a bounded confidence signal (small adjustment only).\n- Wind add-on is policy-gated and confidence-constrained by design.\n- Replace with full roof-area, tilt, azimuth, shading, and local wind evidence in production path.\n"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_pvwatts_cell_ratios(
    scored: List[Dict[str, object]], assumptions: ScoringAssumptions
) -> Tuple[Dict[str, float], Dict[str, Dict[str, float]], List[Dict[str, object]]]:
    by_cell: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for r in scored:
        by_cell[str(r["h3_cell"])].append(r)

    ratios: Dict[str, float] = {}
    nsrdb_by_cell: Dict[str, Dict[str, float]] = {}
    details: List[Dict[str, object]] = []

    for h3_cell, items in by_cell.items():
        cell_lat, cell_lon = h3.cell_to_latlng(h3_cell)
        tilt = min(max(abs(cell_lat) * 0.76, 5), 35)

        nsrdb = estimate_solar_resource(lat=cell_lat, lon=cell_lon)
        ghi_annual = float(nsrdb["ghi_annual"]) if nsrdb and nsrdb.get("ghi_annual") is not None else None
        dni_annual = float(nsrdb["dni_annual"]) if nsrdb and nsrdb.get("dni_annual") is not None else None
        conf_adj = _nsrdb_confidence_adjustment(ghi_annual)

        if ghi_annual is not None or dni_annual is not None:
            nsrdb_by_cell[h3_cell] = {
                "ghi_annual": ghi_annual if ghi_annual is not None else float("nan"),
                "dni_annual": dni_annual if dni_annual is not None else float("nan"),
                "confidence_adjustment": conf_adj,
            }

        pv = estimate_ac_annual_kwh(lat=cell_lat, lon=cell_lon, system_capacity_kw=1.0, tilt=tilt)
        if not pv:
            details.append(
                {
                    "h3_cell": h3_cell,
                    "site_count": len(items),
                    "pvwatts_cf": None,
                    "proxy_cf": None,
                    "raw_ratio": None,
                    "applied_ratio": None,
                    "tilt": tilt,
                    "nsrdb_ghi_annual": round(ghi_annual, 4) if ghi_annual is not None else None,
                    "nsrdb_dni_annual": round(dni_annual, 4) if dni_annual is not None else None,
                    "nsrdb_confidence_adjustment": round(conf_adj, 4),
                }
            )
            continue

        pv_cf = float(pv["ac_annual_kwh"]) / 8760.0
        proxy_cfs: List[float] = []
        for r in items:
            install = _as_float(r.get("install_cost_solar_usd"))
            annual_kwh = _as_float(r.get("annual_kwh_solar"))
            if install is None or annual_kwh is None:
                continue
            kw = install / max(assumptions.install_cost_usd_per_kw, 1e-6)
            if kw <= 0:
                continue
            proxy_cfs.append(annual_kwh / (kw * 8760.0))

        if not proxy_cfs:
            continue

        proxy_cf = mean(proxy_cfs)
        raw_ratio = pv_cf / max(proxy_cf, 1e-6)
        # conservative clamp to avoid extreme swings from sparse/outlier calls
        ratio = min(max(raw_ratio, 0.65), 1.35)
        ratios[h3_cell] = ratio
        details.append(
            {
                "h3_cell": h3_cell,
                "site_count": len(items),
                "pvwatts_cf": round(pv_cf, 6),
                "proxy_cf": round(proxy_cf, 6),
                "raw_ratio": round(raw_ratio, 6),
                "applied_ratio": round(ratio, 6),
                "tilt": tilt,
                "nsrdb_ghi_annual": round(ghi_annual, 4) if ghi_annual is not None else None,
                "nsrdb_dni_annual": round(dni_annual, 4) if dni_annual is not None else None,
                "nsrdb_confidence_adjustment": round(conf_adj, 4),
            }
        )

    return ratios, nsrdb_by_cell, details


def _apply_pvwatts_cell_blend(
    scored: List[Dict[str, object]], assumptions: ScoringAssumptions
) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    ratios, nsrdb_by_cell, details = _build_pvwatts_cell_ratios(scored, assumptions)

    applied = 0
    fallback = 0
    ratio_values = []
    nsrdb_adjustments = []

    for r in scored:
        h3_cell = str(r["h3_cell"])
        ratio = ratios.get(h3_cell)
        reasons = r.get("reasons") or []

        ns = nsrdb_by_cell.get(h3_cell)
        if ns:
            ghi = ns.get("ghi_annual")
            dni = ns.get("dni_annual")
            adj = float(ns.get("confidence_adjustment", 0.0))

            r["nsrdb_ghi_annual"] = None if ghi is None or str(ghi) == "nan" else round(float(ghi), 4)
            r["nsrdb_dni_annual"] = None if dni is None or str(dni) == "nan" else round(float(dni), 4)
            r["nsrdb_confidence_adjustment"] = round(adj, 4)
            nsrdb_adjustments.append(adj)

            base_conf = _as_float(r.get("confidence")) or 0.7
            r["confidence"] = round(_clamp(base_conf + adj, 0.55, 0.95), 3)
            reasons.append("NSRDB annual irradiance signal applied as bounded confidence adjustment")
        else:
            r["nsrdb_ghi_annual"] = None
            r["nsrdb_dni_annual"] = None
            r["nsrdb_confidence_adjustment"] = 0.0

        if ratio is None:
            fallback += 1
            r["solar_model"] = "proxy-fallback"
            r["pvwatts_ratio"] = None
            continue

        applied += 1
        ratio_values.append(ratio)

        for key, digits in [
            ("annual_kwh_solar", 1),
            ("annual_kwh_wind", 1),
            ("annual_kwh_hybrid", 1),
            ("annual_savings_usd", 2),
        ]:
            v = _as_float(r.get(key))
            if v is not None:
                r[key] = round(v * ratio, digits)

        selected_install = _as_float(r.get("install_cost_solar_usd")) or 0.0
        if str(r.get("best_option")) == "hybrid":
            selected_install = _as_float(r.get("install_cost_hybrid_usd")) or selected_install

        annual_savings = _as_float(r.get("annual_savings_usd")) or 0.0
        r["payback_years"] = round(selected_install / max(annual_savings, 1e-6), 2)
        r["npv_15y_usd"] = _npv_15y(annual_savings, selected_install, assumptions.discount_rate, assumptions.annual_degradation)

        reasons.append("PVWatts H3-cell calibration applied to production baseline")
        r["reasons"] = reasons
        r["solar_model"] = "pvwatts-cell-blend"
        r["pvwatts_ratio"] = round(ratio, 6)

    summary = {
        "mode": "pvwatts-cell-blend",
        "cells_total": len({str(r['h3_cell']) for r in scored}),
        "cells_with_pvwatts": len(ratios),
        "cells_with_nsrdb": len(nsrdb_by_cell),
        "sites_total": len(scored),
        "sites_calibrated": applied,
        "sites_proxy_fallback": fallback,
        "ratio_median": round(median(ratio_values), 4) if ratio_values else None,
        "ratio_min": round(min(ratio_values), 4) if ratio_values else None,
        "ratio_max": round(max(ratio_values), 4) if ratio_values else None,
        "nsrdb_confidence_adjustment_median": round(median(nsrdb_adjustments), 4) if nsrdb_adjustments else None,
        "nsrdb_confidence_adjustment_min": round(min(nsrdb_adjustments), 4) if nsrdb_adjustments else None,
        "nsrdb_confidence_adjustment_max": round(max(nsrdb_adjustments), 4) if nsrdb_adjustments else None,
        "cell_details": details,
    }

    return scored, summary


def write_pvwatts_artifacts(root: Path, summary: Dict[str, object]) -> None:
    artifacts = root / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)

    (artifacts / "pvwatts-calibration.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# PVWatts Cell Calibration (Scoring Path)",
        "",
        f"- mode: **{summary.get('mode')}**",
        f"- cells total: **{summary.get('cells_total')}**",
        f"- cells with PVWatts result: **{summary.get('cells_with_pvwatts')}**",
        f"- cells with NSRDB resource enrichment: **{summary.get('cells_with_nsrdb')}**",
        f"- sites calibrated: **{summary.get('sites_calibrated')} / {summary.get('sites_total')}**",
        f"- sites fallback proxy: **{summary.get('sites_proxy_fallback')}**",
        f"- ratio median: **{summary.get('ratio_median')}**",
        f"- ratio range: **{summary.get('ratio_min')} .. {summary.get('ratio_max')}**",
        f"- NSRDB confidence adjustment median: **{summary.get('nsrdb_confidence_adjustment_median')}**",
        f"- NSRDB confidence adjustment range: **{summary.get('nsrdb_confidence_adjustment_min')} .. {summary.get('nsrdb_confidence_adjustment_max')}**",
        "",
        "## Notes",
        "- Per-cell PVWatts/NSRDB calls are bounded by number of H3 cells, not number of sites.",
        "- Conservative PVWatts ratio clamp [0.65, 1.35] reduces overcorrection risk.",
        "- NSRDB signal nudges confidence only (bounded), not direct economics multipliers.",
        "- Fallback remains proxy when external APIs are unavailable.",
    ]
    (artifacts / "pvwatts-calibration.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--sites-csv", default="data/processed/sites.csv")
    p.add_argument("--solar-model", choices=["proxy", "pvwatts-cell-blend"], default="proxy")
    p.add_argument("--triggers-csv", default="data/processed/property_triggers.csv")
    p.add_argument("--reliability-prior-csv", default="data/raw/eia_state_reliability_prior.csv")
    p.add_argument("--state-rate-csv", default="data/raw/eia_state_residential_rates.csv")
    p.add_argument("--site-utility-csv", default="data/processed/site_utility_tariff.csv")
    p.add_argument("--official-utility-rate-csv", default="data/raw/official_utility_residential_rates.csv")
    p.add_argument("--manual-utility-map-csv", default="data/raw/manual_utility_map.csv")
    args = p.parse_args()

    root = Path(__file__).resolve().parents[1]
    sites = read_sites(root / args.sites_csv)
    assumptions = ScoringAssumptions()
    zip_priors = load_zip_priority(root / "artifacts" / "new-england-zip-priority.csv")
    property_triggers = load_property_triggers(root / args.triggers_csv)
    reliability_priors = load_state_reliability_prior(root / args.reliability_prior_csv)
    state_rate_overrides = load_state_rate_overrides(root / args.state_rate_csv)
    site_utility_rates = load_site_utility_rates(root / args.site_utility_csv)
    state_utility_rate_medians = build_state_utility_rate_medians(sites, site_utility_rates)
    official_utility_rate_overrides = load_official_utility_rate_overrides(root / args.official_utility_rate_csv)
    manual_utility_mappings = load_manual_utility_mappings(root / args.manual_utility_map_csv)

    scored = []
    for site in sites:
        site_assumptions, rate_context = resolve_site_rate_context(
            site,
            assumptions,
            state_rate_overrides,
            site_utility_rates,
            state_utility_rate_medians,
            official_utility_rate_overrides,
            manual_utility_mappings,
        )
        row = score_site(site, site_assumptions)
        row.update(rate_context)
        scored.append(row)
    apply_spatial_context(scored, assumptions)
    for r in scored:
        r["solar_model"] = "proxy"
        r["pvwatts_ratio"] = None
        r["nsrdb_ghi_annual"] = None
        r["nsrdb_dni_annual"] = None
        r["nsrdb_confidence_adjustment"] = 0.0
        trigger_row = property_triggers.get(str(r.get("site_id") or ""))
        if trigger_row:
            r.update(trigger_row)
        else:
            r["storm_trigger_status"] = "missing"
            r["outage_trigger_status"] = "missing"
            r["equipment_age_trigger_status"] = "missing"
            r["flood_risk_trigger_status"] = "missing"
            r["storm_trigger_score"] = None
            r["outage_trigger_score"] = None
            r["equipment_age_trigger_score"] = None
            r["flood_risk_trigger_score"] = None
            r["trigger_notes"] = ""

        reliability_prior = reliability_priors.get(str(r.get("state") or "").strip().upper())
        if reliability_prior:
            r.update(reliability_prior)
        else:
            r["battery_reliability_prior_status"] = "missing"
            r["battery_reliability_prior_score"] = None
            r["utility_reliability_tier"] = ""
            r["saidi_minutes"] = None
            r["saifi_events"] = None
            r["battery_reliability_prior_note"] = ""

    pv_summary = None
    if args.solar_model == "pvwatts-cell-blend":
        scored, pv_summary = _apply_pvwatts_cell_blend(scored, assumptions)
        write_pvwatts_artifacts(root, pv_summary)

    apply_sales_priority(scored, zip_priors)
    apply_product_recommendations(scored)
    apply_operator_routing(scored)

    scored_path = root / "data" / "processed" / "site_scores.csv"
    h3_path = root / "data" / "processed" / "h3_scores.csv"

    write_scored(scored_path, scored)
    h3_rows = write_h3_aggregates(h3_path, scored)

    write_api_samples(root / "artifacts" / "api-sample-responses.json", scored, h3_rows)
    write_assumptions(root / "artifacts" / "scoring-assumptions.md", assumptions, args.solar_model)

    summary = {
        "status": "ok",
        "solar_model": args.solar_model,
        "sites": len(scored),
        "h3_cells": len(h3_rows),
        "pvwatts": pv_summary,
        "outputs": [str(scored_path), str(h3_path)],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
