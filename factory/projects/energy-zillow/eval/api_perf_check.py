#!/usr/bin/env python3
from __future__ import annotations

import statistics
import time
from pathlib import Path

import requests

BASE = "http://127.0.0.1:8099"
ROOT = Path(__file__).resolve().parents[1]
ZIP = "78701"


def p95(values):
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    return statistics.quantiles(values, n=100)[94]


def main() -> int:
    heatmap_resp = requests.get(f"{BASE}/api/v1/zip/{ZIP}/heatmap", timeout=5)
    heatmap_resp.raise_for_status()
    cells = heatmap_resp.json().get("cells", [])
    if not cells:
        raise RuntimeError("No heatmap cells available for perf check")
    h3_cell = cells[0]["h3_cell"]

    endpoint = f"{BASE}/api/v1/hex/{h3_cell}/sites?limit=100"
    times = []
    for _ in range(120):
        t0 = time.perf_counter()
        r = requests.get(endpoint, timeout=5)
        dt = (time.perf_counter() - t0) * 1000
        r.raise_for_status()
        times.append(dt)

    summary = {
        "endpoint": endpoint,
        "requests": len(times),
        "median_ms": round(statistics.median(times), 2),
        "p95_ms": round(p95(times), 2),
        "worst_ms": round(max(times), 2),
    }
    out = ROOT / "artifacts/api-perf-summary.json"
    out.write_text(__import__("json").dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
