from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class WindPolicy:
    min_confidence: float = 0.70
    synthetic_confidence_cap: float = 0.65
    non_synthetic_confidence_cap: float = 0.90


def _hash_unit(value: str) -> float:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def evaluate_wind_flag(
    *,
    site_id: str,
    data_source: str,
    annual_kwh_solar: float,
    policy: WindPolicy | None = None,
) -> Dict[str, object]:
    """Wind/hybrid gate for MVP.

    Design principle: only emit wind add-on when confidence clears threshold.
    """

    p = policy or WindPolicy()

    exposure = 0.25 + (_hash_unit(site_id + "|wind-exposure") * 0.75)  # 0.25..1.0
    terrain = 0.85 + (_hash_unit(site_id + "|terrain") * 0.25)  # 0.85..1.10

    raw_confidence = min(1.0, (0.45 + 0.45 * exposure) * terrain)
    cap = p.synthetic_confidence_cap if "synthetic" in data_source else p.non_synthetic_confidence_cap
    wind_confidence = round(min(raw_confidence, cap), 3)

    reasons: List[str] = []
    wind_viability = "low"
    annual_kwh_wind = None
    annual_kwh_hybrid = None

    if wind_confidence < p.min_confidence:
        reasons.append(
            f"Wind add-on withheld: confidence {wind_confidence:.2f} below threshold {p.min_confidence:.2f}"
        )
    else:
        if exposure >= 0.78:
            wind_viability = "high"
        elif exposure >= 0.62:
            wind_viability = "medium"
        else:
            wind_viability = "low"

        if wind_viability in ("medium", "high"):
            wind_gain = 0.10 + 0.30 * exposure
            annual_kwh_wind = round(annual_kwh_solar * wind_gain, 1)
            annual_kwh_hybrid = round(annual_kwh_solar + annual_kwh_wind, 1)
            reasons.append("Wind add-on enabled: exposure and confidence meet policy")
        else:
            reasons.append("Wind add-on withheld: low site-level exposure signal")

    return {
        "wind_confidence": wind_confidence,
        "wind_viability": wind_viability,
        "annual_kwh_wind": annual_kwh_wind,
        "annual_kwh_hybrid": annual_kwh_hybrid,
        "reasons": reasons,
    }
