#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import requests

ROOT = Path(__file__).resolve().parents[1]
CAMBRIDGE_BASE = "https://data.cambridgema.gov/resource"

# dataset_id, source_label, normalized permit_type
CAMBRIDGE_DATASETS: List[Tuple[str, str, str]] = [
    ("79ih-g44d", "cambridge_roof_permits", "roof"),
    ("whpw-w55x", "cambridge_solar_permits", "solar"),
    ("4rb4-q8tj", "cambridge_mechanical_permits", "hvac"),
    ("5cra-jws5", "cambridge_gas_permits", "hvac"),
    ("8793-tet2", "cambridge_plumbing_permits", "hvac"),
]

DIR_MAP = {"NORTH": "N", "SOUTH": "S", "EAST": "E", "WEST": "W"}
STREET_MAP = {
    "STREET": "ST", "ST": "ST", "ROAD": "RD", "RD": "RD", "AVENUE": "AVE", "AVE": "AVE",
    "BOULEVARD": "BLVD", "BLVD": "BLVD", "PLACE": "PL", "PL": "PL", "LANE": "LN", "LN": "LN",
    "DRIVE": "DR", "DR": "DR", "COURT": "CT", "CT": "CT", "TERRACE": "TER", "TER": "TER",
    "PARKWAY": "PKWY", "PKWY": "PKWY", "SQUARE": "SQ", "SQ": "SQ",
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
        if t:
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


def _fetch_zip_rows(dataset_id: str, zip_code: str, limit: int = 5000, max_rows: int = 250000) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    offset = 0
    while True:
        params = {
            "$limit": str(limit),
            "$offset": str(offset),
            "$where": f"full_address like '%{zip_code}%'",
        }
        url = f"{CAMBRIDGE_BASE}/{dataset_id}.json"
        r = requests.get(url, params=params, timeout=45)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        rows.extend(batch)
        offset += len(batch)
        if len(batch) < limit or len(rows) >= max_rows:
            break
    return rows


def _load_existing(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> int:
    p = argparse.ArgumentParser(description="Fetch Cambridge permit datasets and append mapped site-level permit rows")
    p.add_argument("--sites-csv", default="data/processed/sites.csv")
    p.add_argument("--output", default="data/raw/parcel_permit_feed.csv")
    p.add_argument("--summary-md", default="artifacts/cambridge-permit-fetch-summary.md")
    p.add_argument("--summary-json", default="artifacts/cambridge-permit-fetch-summary.json")
    p.add_argument("--zips", default="02139")
    p.add_argument("--max-permits-per-site", type=int, default=20)
    p.add_argument("--replace", action="store_true", help="replace output instead of appending deduped rows")
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
            if str(row.get("zip") or "").strip() in zips:
                sites.append(row)

    site_key_map: Dict[str, List[str]] = defaultdict(list)
    for s in sites:
        sid = str(s.get("site_id") or "").strip()
        if not sid:
            continue
        for key in _site_keys(str(s.get("zip") or ""), str(s.get("address") or "")):
            site_key_map[key].append(sid)
    street_idx = _build_street_number_index(sites)

    existing = [] if args.replace else _load_existing(ROOT / args.output)
    existing_key = {
        (str(r.get("site_id") or ""), str(r.get("permit_id") or ""), str(r.get("permit_type") or ""))
        for r in existing
    }

    fetched_counts = defaultdict(int)
    fetched_by_dataset = defaultdict(int)
    added_rows: List[Dict[str, str]] = []
    per_site_count = Counter()
    type_counts = Counter()
    source_counts = Counter()
    fallback_match_rows = 0

    for dataset_id, source_label, permit_type in CAMBRIDGE_DATASETS:
        for z in zips:
            rows = _fetch_zip_rows(dataset_id, z)
            fetched_counts[z] += len(rows)
            fetched_by_dataset[source_label] += len(rows)
            print(f"fetched {source_label} zip {z}: {len(rows)} rows")

            for rec in rows:
                address = str(rec.get("full_address") or "").strip()
                if not address:
                    continue

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

                permit_id = str(rec.get("id") or "").strip()
                if not permit_id:
                    continue
                permit_id = f"{dataset_id}:{permit_id}"

                permit_date = str(rec.get("issue_date") or rec.get("applicant_submit_date") or "").strip()
                permit_status = str(rec.get("status") or "").strip() or "unknown"

                for sid in set(matched_site_ids):
                    if per_site_count[sid] >= max(1, args.max_permits_per_site):
                        continue
                    key = (sid, permit_id, permit_type)
                    if key in existing_key:
                        continue
                    existing_key.add(key)

                    added_rows.append(
                        {
                            "site_id": sid,
                            "permit_type": permit_type,
                            "permit_date": permit_date,
                            "permit_status": permit_status,
                            "permit_source": source_label,
                            "permit_id": permit_id,
                            "notes": f"zip={z} dataset={dataset_id} addr={address}",
                        }
                    )
                    per_site_count[sid] += 1
                    type_counts[permit_type] += 1
                    source_counts[source_label] += 1

    final_rows = existing + added_rows

    out_path = ROOT / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["site_id", "permit_type", "permit_date", "permit_status", "permit_source", "permit_id", "notes"],
        )
        w.writeheader()
        w.writerows(final_rows)

    scope_sites = len(sites)
    matched_sites = len(per_site_count)
    now = _now_iso()

    summary = {
        "generated_at": now,
        "zips": zips,
        "sites_in_scope": scope_sites,
        "raw_fetched_by_zip": dict(fetched_counts),
        "raw_fetched_by_dataset": dict(fetched_by_dataset),
        "rows_added": len(added_rows),
        "rows_total_output": len(final_rows),
        "matched_sites_added": matched_sites,
        "matched_site_ratio_added": (matched_sites / scope_sites) if scope_sites else 0.0,
        "permit_type_counts_added": dict(type_counts),
        "permit_source_counts_added": dict(source_counts),
        "fallback_match_rows": fallback_match_rows,
        "output": str(out_path),
    }

    summary_json = ROOT / args.summary_json
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Cambridge Permit Fetch Summary",
        "",
        f"- generated_at: `{now}`",
        f"- zips: `{','.join(zips)}`",
        f"- sites in scope: **{scope_sites}**",
        f"- rows added: **{len(added_rows)}**",
        f"- output total rows: **{len(final_rows)}**",
        f"- matched sites (added): **{matched_sites}/{scope_sites} ({(matched_sites/scope_sites if scope_sites else 0):.1%})**",
        f"- fallback matched rows: **{fallback_match_rows}**",
        f"- output: `{out_path}`",
        "",
        "## Raw fetched by dataset",
        "",
    ]
    for src, n in sorted(fetched_by_dataset.items()):
        lines.append(f"- `{src}`: {n}")

    lines += ["", "## Added rows by permit type", ""]
    for k in sorted(type_counts.keys()):
        lines.append(f"- `{k}`: {type_counts[k]}")

    lines += ["", "## Added rows by source", ""]
    for k in sorted(source_counts.keys()):
        lines.append(f"- `{k}`: {source_counts[k]}")

    summary_md = ROOT / args.summary_md
    summary_md.parent.mkdir(parents=True, exist_ok=True)
    summary_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({
        "ok": True,
        "rows_added": len(added_rows),
        "rows_total": len(final_rows),
        "matched_sites_added": matched_sites,
        "scope_sites": scope_sites,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
