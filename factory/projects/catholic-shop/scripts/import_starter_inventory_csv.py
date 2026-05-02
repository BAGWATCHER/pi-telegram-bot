#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-") or "na"


def _split_pipe(value: str) -> List[str]:
    return [v.strip() for v in str(value or "").split("|") if v.strip()]


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value).strip()))
    except Exception:
        return default


def _safe_price_to_cents(value: Any) -> int:
    try:
        return int(round(float(str(value).strip()) * 100))
    except Exception:
        return 0


def _derive_inventory_status(qty: int, explicit_mode: str) -> str:
    mode = _slug(explicit_mode).replace("-", "_")
    if mode in {"in_stock", "low_stock", "out_of_stock", "made_to_order", "preorder"}:
        return mode
    if qty <= 0:
        return "out_of_stock"
    if qty <= 2:
        return "low_stock"
    return "in_stock"


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / f".{path.name}.{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}.tmp"
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Import starter inventory CSV into products.json")
    parser.add_argument("--input", default="data/raw/starter_inventory_intake.csv")
    parser.add_argument("--products", default="data/processed/products.json")
    parser.add_argument("--summary-json", default="artifacts/inventory-import-summary.json")
    parser.add_argument("--summary-md", default="artifacts/inventory-import-summary.md")
    args = parser.parse_args()

    input_path = ROOT / args.input
    products_path = ROOT / args.products
    if not input_path.exists():
        raise SystemExit(f"missing input csv: {input_path}")

    existing = _load_json(products_path, [])
    if not isinstance(existing, list):
        existing = []

    by_product_id: Dict[str, Dict[str, Any]] = {}
    by_sku: Dict[str, str] = {}
    by_shop_title: Dict[str, str] = {}

    for item in existing:
        if not isinstance(item, dict):
            continue
        pid = str(item.get("product_id") or "").strip()
        if not pid:
            continue
        by_product_id[pid] = dict(item)
        sku = str(item.get("sku") or "").strip().upper()
        if sku:
            by_sku[sku] = pid
        shop_title_key = f"{_slug(str(item.get('shop_id') or ''))}::{_slug(str(item.get('title') or ''))}"
        if shop_title_key not in by_shop_title:
            by_shop_title[shop_title_key] = pid

    created = 0
    updated = 0
    rows_total = 0

    with input_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows_total += 1
            sku = str(row.get("sku") or "").strip().upper()
            shop_id = str(row.get("shop_id") or "").strip()
            title = str(row.get("title") or "").strip()
            if not shop_id or not title:
                continue

            product_id = by_sku.get(sku) if sku else None
            if not product_id:
                shop_title_key = f"{_slug(shop_id)}::{_slug(title)}"
                product_id = by_shop_title.get(shop_title_key)
            if not product_id:
                sku_slug = _slug(sku) if sku else _slug(title)
                product_id = f"prod_{_slug(shop_id)}_{sku_slug}"

            qty = _safe_int(row.get("quantity_on_hand"), 0)
            status = _derive_inventory_status(qty, str(row.get("inventory_mode") or ""))

            payload = {
                "product_id": product_id,
                "sku": sku or None,
                "title": title,
                "shop_id": shop_id,
                "price_cents": _safe_price_to_cents(row.get("price_usd")),
                "currency": str(row.get("currency") or "USD").strip() or "USD",
                "country": str(row.get("country") or "").strip(),
                "city": str(row.get("city") or "").strip(),
                "materials": _split_pipe(row.get("materials") or ""),
                "tags": _split_pipe(row.get("tags") or ""),
                "sacrament_tags": _split_pipe(row.get("sacrament_tags") or ""),
                "story": str(row.get("story") or "").strip(),
                "image_url": str(row.get("image_url") or "").strip(),
                "quantity_on_hand": qty,
                "lead_time_days": _safe_int(row.get("lead_time_days"), 0),
                "inventory_status": status,
                "inventory_updated_at": _now_iso(),
            }

            if product_id in by_product_id:
                previous = by_product_id[product_id]
                previous.update(payload)
                by_product_id[product_id] = previous
                updated += 1
            else:
                by_product_id[product_id] = payload
                created += 1

            if sku:
                by_sku[sku] = product_id
            shop_title_key = f"{_slug(shop_id)}::{_slug(title)}"
            if shop_title_key not in by_shop_title:
                by_shop_title[shop_title_key] = product_id

    merged = list(by_product_id.values())

    # Deduplicate by shop/title if legacy rows exist.
    deduped: Dict[str, Dict[str, Any]] = {}
    for item in merged:
        key = f"{_slug(str(item.get('shop_id') or ''))}::{_slug(str(item.get('title') or ''))}"
        current = deduped.get(key)
        if current is None:
            deduped[key] = dict(item)
            continue

        def score(row: Dict[str, Any]) -> int:
            s = 0
            if str(row.get("sku") or "").strip():
                s += 3
            if row.get("quantity_on_hand") not in (None, ""):
                s += 2
            if str(row.get("inventory_updated_at") or "").strip():
                s += 1
            return s

        winner = current if score(current) >= score(item) else dict(item)
        loser = item if winner is current else current

        for field, value in loser.items():
            if winner.get(field) in (None, "", [], {}):
                winner[field] = value

        deduped[key] = winner

    merged = list(deduped.values())
    merged.sort(key=lambda item: str(item.get("product_id") or ""))
    _write_json(products_path, merged)

    status_counts: Dict[str, int] = {}
    for item in merged:
        key = str(item.get("inventory_status") or "unknown")
        status_counts[key] = status_counts.get(key, 0) + 1

    summary = {
        "generated_at": _now_iso(),
        "input": str(input_path),
        "products_path": str(products_path),
        "rows_total": rows_total,
        "created": created,
        "updated": updated,
        "products_total": len(merged),
        "inventory_status_counts": status_counts,
    }

    summary_json = ROOT / args.summary_json
    _write_json(summary_json, summary)

    lines = [
        "# Inventory Import Summary",
        "",
        f"- generated_at: `{summary['generated_at']}`",
        f"- input: `{summary['input']}`",
        f"- rows_total: **{rows_total}**",
        f"- created: **{created}**",
        f"- updated: **{updated}**",
        f"- products_total: **{len(merged)}**",
        "",
        "## Inventory status counts",
        "",
    ]
    for key in sorted(status_counts.keys()):
        lines.append(f"- `{key}`: {status_counts[key]}")

    summary_md = ROOT / args.summary_md
    summary_md.parent.mkdir(parents=True, exist_ok=True)
    summary_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"ok": True, **summary}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
