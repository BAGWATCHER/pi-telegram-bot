#!/usr/bin/env python3
"""EZ-002 upgrade: ingest real address/footprint candidates from OSM map API.

This replaces synthetic seed data with real OpenStreetMap address-tagged nodes/ways
within a ZIP-centric bounding box.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List, Tuple
import xml.etree.ElementTree as ET

import requests


def fetch_zip_profile(zip_code: str) -> Dict[str, object]:
    url = f"https://api.zippopotam.us/us/{zip_code}"
    resp = requests.get(url, timeout=20)
    if resp.status_code != 200:
        raise RuntimeError(f"ZIP lookup failed ({resp.status_code}) for {zip_code}")
    payload = resp.json()
    place = payload["places"][0]
    return {
        "zip": payload["post code"],
        "city": place["place name"],
        "state": place["state abbreviation"],
        "lat": float(place["latitude"]),
        "lon": float(place["longitude"]),
    }


def fetch_osm_xml(center_lat: float, center_lon: float, half_span_deg: float) -> str:
    bbox = f"{center_lon-half_span_deg},{center_lat-half_span_deg},{center_lon+half_span_deg},{center_lat+half_span_deg}"
    url = f"https://api.openstreetmap.org/api/0.6/map?bbox={bbox}"
    headers = {"User-Agent": "energy-zillow-gauntlet-mvp/0.1 (contact: local-dev)"}
    resp = requests.get(url, headers=headers, timeout=90)
    if resp.status_code != 200:
        raise RuntimeError(f"OSM map fetch failed ({resp.status_code}): {resp.text[:180]}")
    return resp.text


def _tags(elem: ET.Element) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for t in elem.findall("tag"):
        k = t.get("k")
        v = t.get("v")
        if k and v:
            out[k] = v
    return out


def _normalize_zip5(value: str, fallback: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return fallback
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) >= 5:
        return digits[:5]
    return fallback


def _build_address(tags: Dict[str, str], profile: Dict[str, object]) -> str:
    num = tags.get("addr:housenumber", "").strip()
    street = tags.get("addr:street", "").strip()
    city = tags.get("addr:city", str(profile["city"]))
    state = tags.get("addr:state", str(profile["state"]))
    postcode = _normalize_zip5(tags.get("addr:postcode", str(profile["zip"])), str(profile["zip"]))
    parts = [p for p in [f"{num} {street}".strip(), city, state, postcode] if p]
    return ", ".join(parts)


def _site_id(prefix: str, osm_id: str, address: str) -> str:
    digest = hashlib.sha1(f"{prefix}|{osm_id}|{address}".encode("utf-8")).hexdigest()
    return f"site_{digest[:12]}"


def _project_xy(coords: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    if not coords:
        return []
    mean_lat = math.radians(sum(lat for lat, _ in coords) / len(coords))
    out: List[Tuple[float, float]] = []
    for lat, lon in coords:
        x = lon * 111320.0 * math.cos(mean_lat)
        y = lat * 110540.0
        out.append((x, y))
    return out


def _polygon_metrics(coords: List[Tuple[float, float]]) -> Dict[str, float | int | None]:
    if len(coords) < 3:
        return {
            "footprint_area_m2": None,
            "footprint_perimeter_m": None,
            "footprint_compactness": None,
            "footprint_vertex_count": len(coords),
        }

    ring = coords[:]
    if ring[0] != ring[-1]:
        ring.append(ring[0])

    xy = _project_xy(ring)
    area_acc = 0.0
    perimeter = 0.0
    for i in range(len(xy) - 1):
        x1, y1 = xy[i]
        x2, y2 = xy[i + 1]
        area_acc += (x1 * y2) - (x2 * y1)
        perimeter += math.hypot(x2 - x1, y2 - y1)

    area = abs(area_acc) / 2.0
    compactness = None
    if perimeter > 0 and area > 0:
        compactness = max(0.0, min((4.0 * math.pi * area) / (perimeter * perimeter), 1.0))

    return {
        "footprint_area_m2": round(area, 1) if area > 0 else None,
        "footprint_perimeter_m": round(perimeter, 1) if perimeter > 0 else None,
        "footprint_compactness": round(compactness, 3) if compactness is not None else None,
        "footprint_vertex_count": max(0, len(ring) - 1),
    }


def parse_osm_addresses(xml_text: str, profile: Dict[str, object], target_zip: str) -> List[Dict[str, object]]:
    root = ET.fromstring(xml_text)

    node_coords: Dict[str, Tuple[float, float]] = {}
    for node in root.findall("node"):
        nid = node.get("id")
        lat = node.get("lat")
        lon = node.get("lon")
        if nid and lat and lon:
            node_coords[nid] = (float(lat), float(lon))

    rows: "OrderedDict[str, Dict[str, object]]" = OrderedDict()

    # Address points
    for node in root.findall("node"):
        tags = _tags(node)
        if "addr:housenumber" not in tags or "addr:street" not in tags:
            continue

        postcode = tags.get("addr:postcode", target_zip)
        if postcode and not str(postcode).startswith(str(target_zip)):
            continue

        lat = float(node.get("lat"))
        lon = float(node.get("lon"))
        address = _build_address(tags, profile)
        key = f"{address}|{lat:.6f}|{lon:.6f}"
        normalized_zip = _normalize_zip5(tags.get("addr:postcode", target_zip), str(target_zip))
        rows[key] = {
            "site_id": _site_id("node", node.get("id", ""), address),
            "address": address,
            "zip": normalized_zip,
            "city": tags.get("addr:city", str(profile["city"])),
            "state": tags.get("addr:state", str(profile["state"])),
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "data_source": "osm_real_address",
            "source_type": "node",
            "osm_id": node.get("id", ""),
            "footprint_area_m2": None,
            "footprint_perimeter_m": None,
            "footprint_compactness": None,
            "footprint_vertex_count": 0,
        }

    # Addressed building footprints (ways)
    for way in root.findall("way"):
        tags = _tags(way)
        if "addr:housenumber" not in tags or "addr:street" not in tags:
            continue

        postcode = tags.get("addr:postcode", target_zip)
        if postcode and not str(postcode).startswith(str(target_zip)):
            continue

        refs = [nd.get("ref") for nd in way.findall("nd") if nd.get("ref")]
        coords = [node_coords[r] for r in refs if r in node_coords]
        if not coords:
            continue
        lat = sum(c[0] for c in coords) / len(coords)
        lon = sum(c[1] for c in coords) / len(coords)
        metrics = _polygon_metrics(coords)

        address = _build_address(tags, profile)
        key = f"{address}|{lat:.6f}|{lon:.6f}"
        normalized_zip = _normalize_zip5(tags.get("addr:postcode", target_zip), str(target_zip))
        rows[key] = {
            "site_id": _site_id("way", way.get("id", ""), address),
            "address": address,
            "zip": normalized_zip,
            "city": tags.get("addr:city", str(profile["city"])),
            "state": tags.get("addr:state", str(profile["state"])),
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "data_source": "osm_real_footprint",
            "source_type": "way",
            "osm_id": way.get("id", ""),
            "footprint_area_m2": metrics["footprint_area_m2"],
            "footprint_perimeter_m": metrics["footprint_perimeter_m"],
            "footprint_compactness": metrics["footprint_compactness"],
            "footprint_vertex_count": metrics["footprint_vertex_count"],
        }

    return list(rows.values())


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    if not rows:
        raise RuntimeError("No rows to write")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def write_artifacts(root: Path, profile: Dict[str, object], out_csv: Path, rows: List[Dict[str, object]], span: float) -> None:
    artifacts = root / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)

    coverage = {
        "candidate_addresses": len(rows),
        "scored_ready_addresses": len(rows),
        "coverage": 1.0 if rows else 0.0,
    }

    source_breakdown: Dict[str, int] = {}
    for r in rows:
        source_breakdown[r["source_type"]] = source_breakdown.get(r["source_type"], 0) + 1

    prov = {
        "task": "EZ-002",
        "method": "OSM real address/footprint ingest",
        "zip": profile["zip"],
        "city": profile["city"],
        "state": profile["state"],
        "center": {"lat": profile["lat"], "lon": profile["lon"]},
        "half_span_deg": span,
        "output_csv": str(out_csv),
        "coverage": coverage,
        "source_breakdown": source_breakdown,
        "source_api": "https://api.openstreetmap.org/api/0.6/map",
    }
    (artifacts / "data-provenance.json").write_text(json.dumps(prov, indent=2) + "\n", encoding="utf-8")

    md = f"""# EZ-002 Data Coverage

- ZIP: `{profile['zip']}` ({profile['city']}, {profile['state']})
- Candidates: **{coverage['candidate_addresses']}**
- With site_id+lat/lon: **{coverage['scored_ready_addresses']}**
- Coverage: **{coverage['coverage']:.2%}**
- Source mode: **real OSM address/footprint ingest**
- Output: `{out_csv}`

## Source + Method
- Source APIs:
  - `https://api.zippopotam.us/us/{profile['zip']}` (ZIP center)
  - `https://api.openstreetmap.org/api/0.6/map` (address-tagged nodes/ways)
- Spatial query: bounding box around ZIP centroid (`half_span_deg={span}`)
- Post-filter: keep records in/near ZIP by `addr:postcode` prefix or local bounds

## Breakdown
"""
    for k, v in source_breakdown.items():
        md += f"- `{k}`: **{v}**\n"

    md += "\n## Next Upgrade\n- Add true parcel boundaries from county/city GIS where available\n- Attach rooftop geometry/shading features for higher-confidence scoring\n"

    (artifacts / "data-coverage.md").write_text(md, encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser(description="Ingest real OSM address/footprint candidates for a ZIP")
    p.add_argument("--zip", dest="zip_code", required=True)
    p.add_argument("--half-span-deg", type=float, default=0.010, help="Bounding box half span in degrees")
    p.add_argument("--min-records", type=int, default=50)
    p.add_argument("--project-root", default=str(Path(__file__).resolve().parents[1]))
    args = p.parse_args()

    root = Path(args.project_root).resolve()
    data_dir = root / "data" / "processed"

    profile = fetch_zip_profile(args.zip_code)
    xml_text = fetch_osm_xml(float(profile["lat"]), float(profile["lon"]), args.half_span_deg)
    rows = parse_osm_addresses(xml_text, profile, str(profile["zip"]))

    if len(rows) < args.min_records:
        raise RuntimeError(f"Too few OSM records ({len(rows)}) for ZIP {profile['zip']}; increase span or fallback")

    out_csv = data_dir / f"sites_{profile['zip']}_osm.csv"
    write_csv(out_csv, rows)
    write_csv(data_dir / "sites.csv", rows)

    write_artifacts(root, profile, out_csv, rows, args.half_span_deg)

    summary = {
        "status": "ok",
        "zip": profile["zip"],
        "records": len(rows),
        "output": str(out_csv),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
