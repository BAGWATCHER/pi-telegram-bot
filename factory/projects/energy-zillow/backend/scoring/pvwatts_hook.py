from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Optional

import requests


@dataclass
class PVWattsConfig:
    api_key: str = os.environ.get("PVWATTS_API_KEY", "DEMO_KEY")
    azimuth: int = 180
    array_type: int = 1
    module_type: int = 0
    losses: float = 14.0


def estimate_ac_annual_kwh(*, lat: float, lon: float, system_capacity_kw: float, tilt: float, config: PVWattsConfig | None = None) -> Optional[Dict[str, float]]:
    c = config or PVWattsConfig()

    params = {
        "api_key": c.api_key,
        "lat": lat,
        "lon": lon,
        "system_capacity": max(system_capacity_kw, 0.1),
        "azimuth": c.azimuth,
        "tilt": max(min(tilt, 60), 0),
        "array_type": c.array_type,
        "module_type": c.module_type,
        "losses": c.losses,
        "timeframe": "monthly",
    }

    try:
        r = requests.get("https://developer.nrel.gov/api/pvwatts/v8.json", params=params, timeout=25)
        if r.status_code != 200:
            return None
        payload = r.json()
        if payload.get("errors"):
            return None
        outputs = payload.get("outputs", {})
        return {
            "ac_annual_kwh": float(outputs.get("ac_annual", 0.0)),
            "capacity_factor": float(outputs.get("capacity_factor", 0.0)),
            "solrad_annual": float(outputs.get("solrad_annual", 0.0)),
        }
    except Exception:
        return None
