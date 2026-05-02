#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import requests

ROOT = Path(__file__).resolve().parents[1]
BOSTON_RESOURCE_ID = "6ddcd912-32a0-43df-9908-63574f8c7e77"
BOSTON_DATASTORE_URL = "https://data.boston.gov/api/3/action/datastore_search"

DIR_MAP = {"NORTH": "N", "SOUTH": "S", "EAST": "E", "WEST": "W"}
STREET_MAP = {
    "STREET": "ST",
    "ST": "ST",
    "ROAD": "RD",
    "RD": "RD",
    "AVENUE": "AVE",
    "AVE": "AVE",
    "BOULEVARD": "BLVD",
    "BLVD": "BLVD",
    "PLACE": "PL",
    "PL": "PL",
    "LANE": "LN",
    "LN": "LN",
    "DRIVE": "DR",
    "DR": "DR",
    "COURT": "CT",
    "CT": "CT",
    "TERRACE": "TER",
    "TER": "TER",
    "PARKWAY": "PKWY",
    "PKWY": "PKWY",
    "SQUARE": "SQ",
    "SQ": "SQ",
}
STOP_TOKENS = {"APT", "UNIT", "FL", "FLOOR", "STE", "SUITE", "#"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _clean_token(tok: str) -> str:
    t = re.sub(r"[^A-Z0-9]", "", tok.upper())
    if not t:
        return ""
    if t in DIR_MAP:
        return DIR_MAP[t]
    if t in STREET_MAP:
        return STREET_MAP[t]
    return t


def _extract_house_numbers(token: str) -> Tuple[str, ...]:
    raw = str(token or "").upper()
    if not raw:
        return tuple()

    nums: List[str] = []

    # include endpoint handling for ranges and multi-number tokens (e.g. 180-186, 77;79)
    for piece in re.split(r"[;/&]", raw):
        p = piece.strip()
        if not p:
            continue

        m_range = re.match(r"(\d+)\s*[-]\s*(\d+)", p)
        if m_range:
            a = int(m_range.group(1))
            b = int(m_range.group(2))
            nums.extend([str(a), str(b)])
            if abs(b - a) <= 20:
                step = 2 if (a % 2) == (b % 2) else 1
                lo, hi = (a, b) if a <= b else (b, a)
                for n in range(lo, hi + 1, step):
                    nums.append(str(n))
            continue

        m = re.match(r"(\d+)", p)
        if m:
            nums.append(m.group(1))

    out: List[str] = []
    seen = set()
    for n in nums:
        if n and n not in seen:
            seen.add(n)
            out.append(n)
    return tuple(out)


def _normalize_address(addr: str) -> Tuple[Tuple[str, ...], Tuple[str, ...], Tuple[str, ...]]:
    if not addr:
        return tuple(), tuple(), tuple()

    text = addr.upper().split(",")[0]
    raw_tokens = re.split(r"\s+", text)
    tokens = []
    for rt in raw_tokens:
        t = _clean_token(rt)
        if not t:
            continue
        tokens.append(t)

    if not tokens:
        return tuple(), tuple(), tuple()

    house_nums = _extract_house_numbers(tokens[0])
    street_tokens = tokens[1:] if house_nums else tokens

    clipped = []
    for t in street_tokens:
        if t in STOP_TOKENS:
            break
        clipped.append(t)

    street_tokens = clipped

    alt_tokens = tuple(street_tokens)
    if len(alt_tokens) >= 2 and alt_tokens[0] in {"N", "S", "E", "W"}:
        alt_tokens = tuple(alt_tokens[1:])

    return house_nums, tuple(street_tokens), alt_tokens


def _site_keys(zip_code: str, address: str) -> List[str]:
    nums, tokens, alt = _normalize_address(address)
    if not nums or not tokens:
        return []
    z = str(zip_code or "").strip()
    keys: List[str] = []
    for num in nums:
        keys.append(f"{z}|{num}|{' '.join(tokens)}")
        if alt and alt != tokens:
            keys.append(f"{z}|{num}|{' '.join(alt)}")
    return keys


def _build_street_number_index(sites: List[Dict[str, str]]) -> Dict[str, List[Tuple[int, str]]]:
    idx: Dict[str, List[Tuple[int, str]]] = defaultdict(list)
    for s in sites:
        sid = str(s.get("site_id") or "").strip()
        z = str(s.get("zip") or "").strip()
        if not sid or not z:
            continue
        nums, tokens, alt = _normalize_address(str(s.get("address") or ""))
        streets = [tokens]
        if alt and alt != tokens:
            streets.append(alt)
        for st in streets:
            if not st:
                continue
            sk = f"{z}|{' '.join(st)}"
            for num in nums:
                try:
                    idx[sk].append((int(num), sid))
                except Exception:
                    continue
    return idx


def _fallback_match_by_street(zip_code: str, address: str, street_idx: Dict[str, List[Tuple[int, str]]], max_gap: int = 20) -> List[str]:
    nums, tokens, alt = _normalize_address(address)
    if not nums or not tokens:
        return []

    out: List[str] = []
    seen = set()
    streets = [tokens]
    if alt and alt != tokens:
        streets.append(alt)

    for st in streets:
        sk = f"{zip_code}|{' '.join(st)}"
        bucket = street_idx.get(sk) or []
        if not bucket:
            continue

        for num in nums:
            try:
                target = int(num)
            except Exception:
                continue

            parity_candidates = [(n, sid) for (n, sid) in bucket if abs(n - target) <= max_gap and (n % 2) == (target % 2)]
            candidates = parity_candidates or [(n, sid) for (n, sid) in bucket if abs(n - target) <= max_gap]
            if not candidates:
                continue

            best_gap = min(abs(n - target) for (n, _sid) in candidates)
            for n, sid in candidates:
                if abs(n - target) == best_gap and sid not in seen:
                    seen.add(sid)
                    out.append(sid)

    return out


def _classify_permit(record: Dict[str, str]) -> str | None:
    text = " ".join(
        [
            str(record.get("worktype") or ""),
            str(record.get("permittypedescr") or ""),
            str(record.get("description") or ""),
            str(record.get("comments") or ""),
        ]
    ).lower()

    if any(k in text for k in ["solar", "photovolta", "pv ", " pv", "battery"]):
        return "solar"
    if any(k in text for k in ["roof", "re-roof", "reroof", "shingle"]):
        return "roof"
    if any(k in text for k in ["hvac", "furnace", "boiler", "heat pump", "air condition", "mechanical"]):
        return "hvac"
    return None


def _fetch_zip_records(zip_code: str, limit: int = 1000, max_records: int = 50000) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    offset = 0
    while True:
        params = {
            "resource_id": BOSTON_RESOURCE_ID,
            "limit": limit,
            "offset": offset,
            "filters": json.dumps({"zip": zip_code}),
        }
        r = requests.get(BOSTON_DATASTORE_URL, params=params, timeout=35)
        r.raise_for_status()
        body = r.json()
        if not body.get("success"):
            break

        result = body.get("result") or {}
        rows = result.get("records") or []
        if not rows:
            break

        out.extend(rows)
        offset += len(rows)
        if len(rows) < limit:
            break
        if len(out) >= max_records:
            break

    return out


def main() -> int:
    p = argparse.ArgumentParser(description="Fetch Boston approved permits and map to EZ site_ids")
    p.add_argument("--sites-csv", default="data/processed/sites.csv")
    p.add_argument("--output", default="data/raw/parcel_permit_feed.csv")
    p.add_argument("--summary-md", default="artifacts/boston-permit-fetch-summary.md")
    p.add_argument("--summary-json", default="artifacts/boston-permit-fetch-summary.json")
    p.add_argument("--zips", default="02118")
    p.add_argument("--max-permits-per-site", type=int, default=12)
    args = p.parse_args()

    zips = [z.strip() for z in str(args.zips or "").split(",") if z.strip()]
    if not zips:
        raise SystemExit("--zips required")

    sites_path = ROOT / args.sites_csv
    if not sites_path.exists():
        raise SystemExit(f"missing sites csv: {sites_path}")

    sites = []
    with sites_path.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            z = str(row.get("zip") or "").strip()
            if z in zips:
                sites.append(row)

    site_key_map: Dict[str, List[str]] = defaultdict(list)
    for s in sites:
        sid = str(s.get("site_id") or "").strip()
        for key in _site_keys(str(s.get("zip") or ""), str(s.get("address") or "")):
            site_key_map[key].append(sid)
    street_idx = _build_street_number_index(sites)

    fetched: Dict[str, List[Dict[str, str]]] = {}
    for z in zips:
        rows = _fetch_zip_records(z)
        fetched[z] = rows
        print(f"fetched zip {z}: {len(rows)} records")

    permit_rows: List[Dict[str, str]] = []
    seen = set()
    per_site_count = Counter()
    class_counts = Counter()
    fallback_match_rows = 0

    for z, records in fetched.items():
        for rec in records:
            pclass = _classify_permit(rec)
            if not pclass:
                continue

            address = str(rec.get("address") or "").strip()
            keys = _site_keys(z, address)
            if not keys:
                continue

            matched_site_ids: List[str] = []
            for k in keys:
                matched_site_ids.extend(site_key_map.get(k, []))

            if not matched_site_ids:
                matched_site_ids = _fallback_match_by_street(z, address, street_idx)
                if matched_site_ids:
                    fallback_match_rows += 1

            if not matched_site_ids:
                continue

            permit_id = str(rec.get("permitnumber") or rec.get("_id") or "").strip() or "unknown"
            issued = str(rec.get("issued_date") or "").strip()
            status = str(rec.get("status") or "").strip() or "unknown"
            worktype = str(rec.get("worktype") or "").strip()

            for sid in set(matched_site_ids):
                if per_site_count[sid] >= max(1, args.max_permits_per_site):
                    continue
                dedupe_key = (sid, permit_id, pclass)
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)

                permit_rows.append(
                    {
                        "site_id": sid,
                        "permit_type": pclass,
                        "permit_date": issued,
                        "permit_status": status,
                        "permit_source": "boston_approved_building_permits",
                        "permit_id": permit_id,
                        "notes": f"zip={z} worktype={worktype} addr={address}",
                    }
                )
                per_site_count[sid] += 1
                class_counts[pclass] += 1

    out_path = ROOT / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["site_id", "permit_type", "permit_date", "permit_status", "permit_source", "permit_id", "notes"],
        )
        w.writeheader()
        w.writerows(permit_rows)

    matched_sites = len(per_site_count)
    total_sites_scope = len(sites)
    now = _now_iso()

    summary = {
        "generated_at": now,
        "zips": zips,
        "sites_in_scope": total_sites_scope,
        "permits_fetched_raw": {z: len(fetched.get(z, [])) for z in zips},
        "permit_rows_written": len(permit_rows),
        "matched_sites": matched_sites,
        "matched_site_ratio": (matched_sites / total_sites_scope) if total_sites_scope else 0.0,
        "permit_type_counts": dict(class_counts),
        "fallback_match_rows": fallback_match_rows,
        "output": str(out_path),
    }

    summary_json = ROOT / args.summary_json
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Boston Permit Fetch Summary",
        "",
        f"- generated_at: `{now}`",
        f"- zips: `{','.join(zips)}`",
        f"- sites in scope: **{total_sites_scope}**",
        f"- permit rows written: **{len(permit_rows)}**",
        f"- matched sites: **{matched_sites}/{total_sites_scope} ({(matched_sites/total_sites_scope if total_sites_scope else 0):.1%})**",
        f"- fallback matched rows: **{fallback_match_rows}**",
        f"- output: `{out_path}`",
        "",
        "## Raw permit rows fetched by ZIP",
        "",
    ]
    for z in zips:
        lines.append(f"- `{z}`: {len(fetched.get(z, []))}")

    lines += ["", "## Permit type counts (matched rows)", ""]
    for k in sorted(class_counts.keys()):
        lines.append(f"- `{k}`: {class_counts[k]}")

    summary_md = ROOT / args.summary_md
    summary_md.parent.mkdir(parents=True, exist_ok=True)
    summary_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"ok": True, "rows": len(permit_rows), "matched_sites": matched_sites, "scope_sites": total_sites_scope}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
