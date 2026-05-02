from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Dict, List

import h3

from backend.scoring.wind_flag import WindPolicy, evaluate_wind_flag


@dataclass
class ScoringAssumptions:
    utility_rate_usd_per_kwh: float = 0.14
    install_cost_usd_per_kw: float = 2200.0
    wind_addon_cost_multiplier: float = 0.30
    discount_rate: float = 0.08
    annual_degradation: float = 0.005
    h3_resolution: int = 8
    wind_min_confidence: float = 0.70


def _hash_unit(value: str) -> float:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def _spatial_unit(lat: float, lon: float, salt: str) -> float:
    # Stable site variation should follow location, not arbitrary site ids.
    key = f"{round(lat, 5):.5f}|{round(lon, 5):.5f}|{salt}"
    return _hash_unit(key)


def _estimate_kw(
    lat: float,
    lon: float,
    source_type: str,
    footprint_area_m2: float | None = None,
    footprint_compactness: float | None = None,
) -> float:
    # Bootstrap capacity estimate anchored on source evidence:
    # addressed building footprints tend to support larger rooftop capacity than address points.
    if footprint_area_m2 is not None and footprint_area_m2 > 0:
        compactness = footprint_compactness if footprint_compactness is not None else 0.7
        usable_ratio = 0.38 + (0.22 * max(0.0, min(compactness, 1.0)))
        usable_area_m2 = footprint_area_m2 * usable_ratio
        derived_kw = usable_area_m2 / 8.5
        micro = (_spatial_unit(lat, lon, "roof-capacity") - 0.5) * 0.9
        return round(max(1.6, min(derived_kw + micro, 24.0)), 3)

    base = 4.6 if source_type == "way" else 3.5
    micro = (_spatial_unit(lat, lon, "roof-capacity") - 0.5) * 1.4
    return round(max(1.4, base + micro), 3)


def _capacity_factor(lat: float, lon: float, source_type: str) -> float:
    # Rough latitude + site variability proxy for MVP bootstrap, but tied to location and source type.
    base = 0.208 if source_type == "way" else 0.196
    lat_penalty = min(abs(lat - 35.0) * 0.0012, 0.05)
    shading = 0.76 + (_spatial_unit(lat, lon, "shade") * 0.20)  # 0.76..0.96
    orientation = 0.92 + (_spatial_unit(lat, lon, "az") * 0.12)  # 0.92..1.04
    cf = max(0.11, (base - lat_penalty) * shading * orientation)
    return cf


def _npv_15y(annual_savings: float, install_cost: float, discount_rate: float, degradation: float) -> float:
    npv = -install_cost
    yearly = annual_savings
    for y in range(1, 16):
        npv += yearly / ((1 + discount_rate) ** y)
        yearly *= (1 - degradation)
    return round(npv, 2)


def _distance_m(lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
    mean_lat = math.radians((lat_a + lat_b) / 2.0)
    dx = (lon_b - lon_a) * 111320.0 * math.cos(mean_lat)
    dy = (lat_b - lat_a) * 110540.0
    return math.hypot(dx, dy)


def _as_float(v: object) -> float | None:
    if v in (None, "", "None"):
        return None
    try:
        return float(v)
    except Exception:
        return None


def _neighbor_distance_update(
    nearest_by_site: Dict[str, float],
    left: Dict[str, object] | None,
    right: Dict[str, object] | None,
) -> None:
    if not left or not right:
        return
    if left["site_id"] == right["site_id"]:
        return
    d = _distance_m(float(left["lat"]), float(left["lon"]), float(right["lat"]), float(right["lon"]))
    left_id = str(left["site_id"])
    right_id = str(right["site_id"])
    if d < nearest_by_site.get(left_id, math.inf):
        nearest_by_site[left_id] = d
    if d < nearest_by_site.get(right_id, math.inf):
        nearest_by_site[right_id] = d


def _approximate_block_nearest(neighbors: List[Dict[str, object]]) -> Dict[str, float]:
    nearest_by_site: Dict[str, float] = {str(r["site_id"]): math.inf for r in neighbors}
    if len(neighbors) <= 1:
        return nearest_by_site

    lat_sorted = sorted(neighbors, key=lambda r: (float(r["lat"]), float(r["lon"]), str(r["site_id"])))
    lon_sorted = sorted(neighbors, key=lambda r: (float(r["lon"]), float(r["lat"]), str(r["site_id"])))

    for items in (lat_sorted, lon_sorted):
        for idx, row in enumerate(items):
            if idx > 0:
                _neighbor_distance_update(nearest_by_site, row, items[idx - 1])
            if idx + 1 < len(items):
                _neighbor_distance_update(nearest_by_site, row, items[idx + 1])

    return nearest_by_site


def _data_quality_tier(data_source: str, source_type: str) -> str:
    source = (data_source or "").lower()
    source_kind = (source_type or "").lower()

    if "parcel" in source or "authoritative" in source:
        return "parcel-grade"
    if "synthetic" in source:
        return "synthetic-bootstrap"
    if source.startswith("osm_") and source_kind in {"way", "relation"}:
        return "osm-footprint-screening"
    if source.startswith("osm_"):
        return "osm-address-screening"
    return "unknown-screening"


def _confidence_label(confidence: float) -> str:
    if confidence >= 0.82:
        return "high"
    if confidence >= 0.70:
        return "medium"
    return "low"


def score_site(site: Dict[str, object], assumptions: ScoringAssumptions | None = None) -> Dict[str, object]:
    a = assumptions or ScoringAssumptions()

    site_id = str(site["site_id"])
    lat = float(site["lat"])
    lon = float(site["lon"])
    source_type = str(site.get("source_type", "unknown"))
    footprint_area_m2 = _as_float(site.get("footprint_area_m2"))
    footprint_perimeter_m = _as_float(site.get("footprint_perimeter_m"))
    footprint_compactness = _as_float(site.get("footprint_compactness"))
    footprint_vertex_count = int(float(site.get("footprint_vertex_count", 0) or 0))

    kw = _estimate_kw(lat, lon, source_type, footprint_area_m2, footprint_compactness)
    cf = _capacity_factor(lat, lon, source_type)
    annual_kwh_solar = round(kw * 8760 * cf, 1)

    annual_savings = round(annual_kwh_solar * a.utility_rate_usd_per_kwh, 2)
    install_cost = round(kw * a.install_cost_usd_per_kw, 2)
    payback_years = round(install_cost / max(annual_savings, 1e-6), 2)
    npv_15y = _npv_15y(annual_savings, install_cost, a.discount_rate, a.annual_degradation)

    reasons: List[str] = []
    if payback_years <= 10:
        reasons.append("Payback is within target threshold")
    else:
        reasons.append("Payback exceeds target threshold")

    if annual_kwh_solar >= 7000:
        reasons.append("Strong estimated annual PV production")
    else:
        reasons.append("Moderate estimated annual PV production")

    data_source = str(site.get("data_source", "unknown"))
    if "synthetic" in data_source:
        confidence = 0.62
        reasons.append("Bootstrap synthetic site geometry lowers confidence")
    else:
        confidence = 0.8
        reasons.append("Address and geometry inputs support higher confidence")

    data_quality_tier = _data_quality_tier(data_source, source_type)
    if source_type == "way":
        reasons.append("Addressed building footprint supports stronger rooftop-capacity estimate")
    elif source_type == "node":
        reasons.append("Address-point source increases rooftop-capacity uncertainty")

    if footprint_area_m2 is not None:
        reasons.append(f"Footprint-informed capacity estimate uses ~{round(footprint_area_m2):,} m2 building area")
    if footprint_compactness is not None and footprint_compactness < 0.45:
        reasons.append("Irregular footprint shape reduces likely usable roof packing efficiency")

    wind = evaluate_wind_flag(
        site_id=site_id,
        data_source=data_source,
        annual_kwh_solar=annual_kwh_solar,
        policy=WindPolicy(min_confidence=a.wind_min_confidence),
    )
    wind_confidence = float(wind["wind_confidence"])
    wind_viability = str(wind["wind_viability"])
    annual_kwh_wind = wind["annual_kwh_wind"]
    annual_kwh_hybrid = wind["annual_kwh_hybrid"]
    reasons.extend(list(wind["reasons"]))

    install_cost_hybrid = None
    if annual_kwh_wind is not None:
        install_cost_hybrid = round(install_cost * (1 + a.wind_addon_cost_multiplier), 2)

    # default to solar-first economics
    best_option = "no-go"
    selected_annual_savings = annual_savings
    selected_payback_years = payback_years
    selected_npv_15y = npv_15y

    if payback_years <= 10 and confidence >= a.wind_min_confidence:
        best_option = "solar"
    elif payback_years <= 12:
        best_option = "solar+battery"
        reasons.append("Battery may improve bill-shifting economics under TOU tariffs")

    # only allow hybrid if wind add-on cleared policy and improves economics
    if annual_kwh_hybrid is not None and install_cost_hybrid is not None and confidence >= a.wind_min_confidence:
        hybrid_savings = round(float(annual_kwh_hybrid) * a.utility_rate_usd_per_kwh, 2)
        hybrid_payback = round(install_cost_hybrid / max(hybrid_savings, 1e-6), 2)
        hybrid_npv = _npv_15y(hybrid_savings, install_cost_hybrid, a.discount_rate, a.annual_degradation)
        if hybrid_payback <= (payback_years + 1.0):
            best_option = "hybrid"
            selected_annual_savings = hybrid_savings
            selected_payback_years = hybrid_payback
            selected_npv_15y = hybrid_npv
            reasons.append("Hybrid selected: wind add-on passed confidence gate and economics check")

    score = {
        "site_id": site_id,
        "address": site["address"],
        "zip": site.get("zip"),
        "city": site.get("city"),
        "state": site.get("state"),
        "data_source": data_source,
        "source_type": source_type,
        "data_quality_tier": data_quality_tier,
        "lat": lat,
        "lon": lon,
        "footprint_area_m2": footprint_area_m2,
        "footprint_perimeter_m": footprint_perimeter_m,
        "footprint_compactness": footprint_compactness,
        "footprint_vertex_count": footprint_vertex_count,
        "h3_cell": h3.latlng_to_cell(lat, lon, a.h3_resolution),
        "annual_kwh_solar": annual_kwh_solar,
        "annual_kwh_wind": annual_kwh_wind,
        "annual_kwh_hybrid": annual_kwh_hybrid,
        "wind_confidence": wind_confidence,
        "wind_viability": wind_viability,
        "install_cost_solar_usd": install_cost,
        "install_cost_hybrid_usd": install_cost_hybrid,
        "annual_savings_usd": selected_annual_savings,
        "payback_years": selected_payback_years,
        "npv_15y_usd": selected_npv_15y,
        "best_option": best_option,
        "confidence": confidence,
        "confidence_label": _confidence_label(confidence),
        "requires_site_survey": data_quality_tier != "parcel-grade",
        "reasons": reasons,
    }
    return score


def apply_spatial_context(scored: List[Dict[str, object]], assumptions: ScoringAssumptions | None = None) -> List[Dict[str, object]]:
    a = assumptions or ScoringAssumptions()
    block_resolution = 10
    by_block: Dict[str, List[Dict[str, object]]] = {}
    for row in scored:
        block = str(h3.latlng_to_cell(float(row["lat"]), float(row["lon"]), block_resolution))
        by_block.setdefault(block, []).append(row)

    nearest_by_site: Dict[str, float] = {}
    local_count_by_site: Dict[str, int] = {}
    for neighbors in by_block.values():
        block_nearest = _approximate_block_nearest(neighbors)
        local_count = len(neighbors)
        for row in neighbors:
            site_id = str(row["site_id"])
            nearest_by_site[site_id] = block_nearest.get(site_id, math.inf)
            local_count_by_site[site_id] = local_count

    for row in scored:
        source_type = str(row.get("source_type", "unknown"))
        site_id = str(row["site_id"])
        nearest_raw = nearest_by_site.get(site_id, math.inf)
        nearest_m = None if math.isinf(nearest_raw) else nearest_raw
        local_count = local_count_by_site.get(site_id, 1)
        capacity_mult = 1.0
        confidence_delta = 0.0
        reasons = list(row.get("reasons") or [])

        if source_type == "way":
            capacity_mult *= 1.08
            confidence_delta += 0.03
        elif source_type == "node":
            capacity_mult *= 0.94
            confidence_delta -= 0.02

        if local_count >= 6:
            capacity_mult *= 0.90
            reasons.append("Dense local address clustering reduces likely usable roof area")
        elif local_count <= 2:
            capacity_mult *= 1.05
            reasons.append("Lower local site density supports slightly higher usable roof area")

        if nearest_m is not None and nearest_m < 18:
            capacity_mult *= 0.92
            reasons.append("Very tight nearest-neighbor spacing suggests tighter rooftop constraints")
        elif nearest_m is not None and nearest_m > 45:
            capacity_mult *= 1.04
            reasons.append("Wider nearest-neighbor spacing supports slightly larger rooftop envelope")

        capacity_mult = max(0.78, min(capacity_mult, 1.18))
        confidence = max(0.55, min((_as_float(row.get("confidence")) or 0.7) + confidence_delta, 0.95))

        for key, digits in [
            ("annual_kwh_solar", 1),
            ("annual_kwh_wind", 1),
            ("annual_kwh_hybrid", 1),
            ("annual_savings_usd", 2),
            ("install_cost_solar_usd", 2),
            ("install_cost_hybrid_usd", 2),
        ]:
            value = _as_float(row.get(key))
            if value is not None:
                row[key] = round(value * capacity_mult, digits)

        install_cost = _as_float(row.get("install_cost_solar_usd")) or 0.0
        if str(row.get("best_option")) == "hybrid":
            install_cost = _as_float(row.get("install_cost_hybrid_usd")) or install_cost
        annual_savings = _as_float(row.get("annual_savings_usd")) or 0.0
        row["payback_years"] = round(install_cost / max(annual_savings, 1e-6), 2)
        row["npv_15y_usd"] = _npv_15y(annual_savings, install_cost, a.discount_rate, a.annual_degradation)
        row["confidence"] = round(confidence, 3)
        row["confidence_label"] = _confidence_label(confidence)
        row["reasons"] = reasons
        row["site_context_local_count"] = local_count
        row["site_context_nearest_m"] = round(nearest_m, 1) if nearest_m is not None else None

    return scored
