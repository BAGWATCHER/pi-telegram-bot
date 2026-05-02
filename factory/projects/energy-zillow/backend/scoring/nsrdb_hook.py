from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Optional

import requests


@dataclass
class NSRDBConfig:
    api_key: str = os.environ.get("NSRDB_API_KEY", os.environ.get("PVWATTS_API_KEY", "DEMO_KEY"))


def estimate_solar_resource(*, lat: float, lon: float, config: NSRDBConfig | None = None) -> Optional[Dict[str, float]]:
    """Fetch annual-average solar resource proxy from NREL solar resource endpoint.

    This endpoint is backed by NSRDB-style resource layers and is lightweight enough
    for bounded per-cell enrichment during MVP scoring.
    """

    c = config or NSRDBConfig()
    params = {
        "api_key": c.api_key,
        "lat": lat,
        "lon": lon,
    }

    try:
        r = requests.get("https://developer.nrel.gov/api/solar/solar_resource/v1.json", params=params, timeout=25)
        if r.status_code != 200:
            return None
        payload = r.json()
        if payload.get("errors"):
            return None

        outputs = payload.get("outputs", {})
        avg_dni = outputs.get("avg_dni", {}) or {}
        avg_ghi = outputs.get("avg_ghi", {}) or {}

        # Prefer annual values if available, else monthly average fallback.
        ghi = avg_ghi.get("annual")
        if ghi is None and avg_ghi:
            vals = [float(v) for v in avg_ghi.values() if isinstance(v, (int, float, str))]
            ghi = sum(vals) / len(vals) if vals else None

        dni = avg_dni.get("annual")
        if dni is None and avg_dni:
            vals = [float(v) for v in avg_dni.values() if isinstance(v, (int, float, str))]
            dni = sum(vals) / len(vals) if vals else None

        if ghi is None and dni is None:
            return None

        out: Dict[str, float] = {}
        if ghi is not None:
            out["ghi_annual"] = float(ghi)
        if dni is not None:
            out["dni_annual"] = float(dni)
        return out
    except Exception:
        return None
