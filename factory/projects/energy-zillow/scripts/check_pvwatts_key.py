#!/usr/bin/env python3
from __future__ import annotations

import json
import os

import requests


def _check_pvwatts(key: str) -> dict:
    params = {
        "api_key": key,
        "lat": 30.2672,
        "lon": -97.7431,
        "system_capacity": 1.0,
        "azimuth": 180,
        "tilt": 20,
        "array_type": 1,
        "module_type": 0,
        "losses": 14,
        "timeframe": "monthly",
    }
    try:
        r = requests.get("https://developer.nrel.gov/api/pvwatts/v8.json", params=params, timeout=25)
        payload = r.json()
        errors = payload.get("errors") if isinstance(payload, dict) else None
        ok = r.status_code == 200 and not errors
        return {
            "ok": ok,
            "status_code": r.status_code,
            "errors": errors,
            "warnings": payload.get("warnings") if isinstance(payload, dict) else None,
            "version": payload.get("version") if isinstance(payload, dict) else None,
        }
    except Exception as e:
        return {"ok": False, "reason": "network_error", "error": str(e)}


def _check_nsrdb_resource(key: str) -> dict:
    params = {
        "api_key": key,
        "lat": 30.2672,
        "lon": -97.7431,
    }
    try:
        r = requests.get("https://developer.nrel.gov/api/solar/solar_resource/v1.json", params=params, timeout=25)
        payload = r.json()
        errors = payload.get("errors") if isinstance(payload, dict) else None
        outputs = payload.get("outputs", {}) if isinstance(payload, dict) else {}
        ok = r.status_code == 200 and not errors
        avg_ghi = outputs.get("avg_ghi", {}) if isinstance(outputs, dict) else {}
        avg_dni = outputs.get("avg_dni", {}) if isinstance(outputs, dict) else {}
        return {
            "ok": ok,
            "status_code": r.status_code,
            "errors": errors,
            "sample_ghi_annual": avg_ghi.get("annual") if isinstance(avg_ghi, dict) else None,
            "sample_dni_annual": avg_dni.get("annual") if isinstance(avg_dni, dict) else None,
        }
    except Exception as e:
        return {"ok": False, "reason": "network_error", "error": str(e)}


def main() -> int:
    pv_key = os.environ.get("PVWATTS_API_KEY", "DEMO_KEY")
    ns_key = os.environ.get("NSRDB_API_KEY", pv_key)

    if pv_key == "DEMO_KEY":
        print(json.dumps({"ok": False, "reason": "PVWATTS_API_KEY not set (using DEMO_KEY)"}, indent=2))
        return 2

    pv = _check_pvwatts(pv_key)
    ns = _check_nsrdb_resource(ns_key)

    ok = bool(pv.get("ok")) and bool(ns.get("ok"))
    out = {
        "ok": ok,
        "pvwatts": pv,
        "nsrdb_resource": ns,
    }
    print(json.dumps(out, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
