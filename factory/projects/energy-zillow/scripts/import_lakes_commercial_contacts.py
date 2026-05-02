#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITE_SCORES_CSV = ROOT / "data/processed/site_scores.csv"
LEAD_CONTACTS_JSON = ROOT / "data/processed/lead_contacts.json"
DEFAULT_INPUT_CSV = ROOT / "data/raw/lakes_commercial_contacts_seed.csv"


def slug_token(value: Any) -> str:
    token = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    return token or "unknown"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def normalize_address(value: Any) -> str:
    text = clean_text(value).lower()
    replacements = {
        " highway": " hwy",
        " road": " rd",
        " street": " st",
        " avenue": " ave",
        " drive": " dr",
        " lane": " ln",
        " boulevard": " blvd",
        " route ": " rte ",
        " north": " n",
        " south": " s",
        " east": " e",
        " west": " w",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def split_list(value: Any) -> list[str]:
    if value in (None, "", "None"):
        return []
    if isinstance(value, list):
        return [clean_text(v) for v in value if clean_text(v)]
    raw = str(value)
    return [clean_text(part) for part in raw.split("|") if clean_text(part)]


def contact_id_for_row(row: dict[str, Any]) -> str:
    site_id = str(row.get("site_id") or "")
    stem = site_id[-10:] if len(site_id) >= 10 else slug_token(site_id)
    return f"contact_{stem}"


def account_id_for_row(row: dict[str, Any]) -> str:
    site_id = str(row.get("site_id") or "")
    zip_code = slug_token(row.get("zip"))
    stem = site_id[-8:] if len(site_id) >= 8 else slug_token(site_id)
    return f"acct_{zip_code}_{stem}"


def load_site_rows() -> list[dict[str, Any]]:
    with SITE_SCORES_CSV.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_contact_store() -> dict[str, dict[str, Any]]:
    if not LEAD_CONTACTS_JSON.exists():
        return {}
    try:
        raw = json.loads(LEAD_CONTACTS_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def write_contact_store(store: dict[str, dict[str, Any]]) -> None:
    LEAD_CONTACTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    tmp = LEAD_CONTACTS_JSON.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(store, indent=2) + "\n", encoding="utf-8")
    tmp.replace(LEAD_CONTACTS_JSON)


def preferred_channel_for(seed: dict[str, str]) -> str:
    explicit = clean_text(seed.get("preferred_channel"))
    if explicit:
        return explicit
    if clean_text(seed.get("primary_phone")):
        return "phone"
    if clean_text(seed.get("primary_email")):
        return "email"
    if clean_text(seed.get("contact_form_url")):
        return "website_form"
    if clean_text(seed.get("website_url")):
        return "website"
    return "mail"


def contactability_score_for(seed: dict[str, str], preferred_channel: str) -> float:
    explicit = clean_text(seed.get("contactability_score"))
    if explicit:
        try:
            return round(max(0.0, min(0.99, float(explicit))), 3)
        except Exception:
            pass
    score = 0.35
    if clean_text(seed.get("primary_phone")):
        score += 0.33
    if clean_text(seed.get("primary_email")):
        score += 0.12
    if clean_text(seed.get("contact_form_url")):
        score += 0.10
    if clean_text(seed.get("website_url")):
        score += 0.05
    if clean_text(seed.get("mailing_address")):
        score += 0.06
    if preferred_channel == "phone":
        score += 0.06
    return round(min(score, 0.95), 3)


def contactability_label_for(score: float, explicit: str) -> str:
    if explicit:
        return explicit
    if score >= 0.8:
        return "high"
    if score >= 0.55:
        return "medium"
    return "low"


def sort_rows_for_match(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(row: dict[str, Any]) -> tuple[int, float, float]:
        source_type = clean_text(row.get("source_type")).lower()
        try:
            footprint = float(row.get("footprint_area_m2") or 0.0)
        except Exception:
            footprint = 0.0
        try:
            priority = float(row.get("priority_score") or 0.0)
        except Exception:
            priority = 0.0
        return (0 if source_type == "way" else 1, -footprint, -priority)

    return sorted(rows, key=key)


def build_address_key(address: str, city: str, state: str, zip_code: str) -> tuple[str, str, str, str]:
    return (
        normalize_address(address),
        clean_text(city).lower(),
        clean_text(state).lower(),
        clean_text(zip_code),
    )


def resolve_target_rows(seed: dict[str, str], by_site: dict[str, dict[str, Any]], by_address: dict[tuple[str, str, str, str], list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], str | None]:
    explicit_site_ids = split_list(seed.get("site_ids"))
    if clean_text(seed.get("site_id")):
        explicit_site_ids.insert(0, clean_text(seed.get("site_id")))
    if explicit_site_ids:
        rows = [by_site[site_id] for site_id in explicit_site_ids if site_id in by_site]
        if rows:
            return rows, None
        return [], f"explicit site_id not found: {'|'.join(explicit_site_ids)}"

    address = clean_text(seed.get("address"))
    city = clean_text(seed.get("city"))
    state = clean_text(seed.get("state"))
    zip_code = clean_text(seed.get("zip"))
    key = build_address_key(address, city, state, zip_code)
    matches = list(by_address.get(key, []))
    if not matches:
        return [], f"no site match for {address}, {city}, {state} {zip_code}"
    if clean_text(seed.get("apply_to_all_matches")).lower() in {"1", "true", "yes", "y"}:
        return sort_rows_for_match(matches), None
    return sort_rows_for_match(matches)[:1], None


def build_contact_paths(seed: dict[str, str], preferred_channel: str) -> list[dict[str, Any]]:
    paths: list[dict[str, Any]] = []
    phones = split_list(seed.get("phone_numbers"))
    primary_phone = clean_text(seed.get("primary_phone"))
    if primary_phone and primary_phone not in phones:
        phones.insert(0, primary_phone)
    emails = split_list(seed.get("emails"))
    primary_email = clean_text(seed.get("primary_email"))
    if primary_email and primary_email not in emails:
        emails.insert(0, primary_email)

    priority = 1
    for phone in phones:
        paths.append({"type": "phone", "value": phone, "label": "Phone", "priority": priority})
        priority += 1
    for email in emails:
        paths.append({"type": "email", "value": email, "label": "Email", "priority": priority})
        priority += 1
    if clean_text(seed.get("contact_form_url")):
        paths.append({"type": "website_form", "value": clean_text(seed.get("contact_form_url")), "label": "Contact form", "priority": priority})
        priority += 1
    if clean_text(seed.get("website_url")):
        paths.append({"type": "website", "value": clean_text(seed.get("website_url")), "label": "Website", "priority": priority})
        priority += 1
    if clean_text(seed.get("mailing_address")):
        paths.append({"type": "mailing_address", "value": clean_text(seed.get("mailing_address")), "label": "Mailing address", "priority": priority})
    if preferred_channel == "phone":
        paths.sort(key=lambda item: (0 if item["type"] == "phone" else 1, item.get("priority") or 99))
    elif preferred_channel == "email":
        paths.sort(key=lambda item: (0 if item["type"] == "email" else 1, item.get("priority") or 99))
    elif preferred_channel == "website_form":
        paths.sort(key=lambda item: (0 if item["type"] == "website_form" else 1, item.get("priority") or 99))
    return paths


def build_contact_record(seed: dict[str, str], site_row: dict[str, Any]) -> dict[str, Any]:
    now = utc_now_iso()
    preferred_channel = preferred_channel_for(seed)
    score = contactability_score_for(seed, preferred_channel)
    label = contactability_label_for(score, clean_text(seed.get("contactability_label")))
    display_name = clean_text(seed.get("display_name") or seed.get("business_name") or seed.get("organization_name")) or clean_text(site_row.get("address"))
    organization_name = clean_text(seed.get("organization_name") or seed.get("business_name")) or display_name
    primary_phone = clean_text(seed.get("primary_phone")) or None
    phone_numbers = split_list(seed.get("phone_numbers"))
    if primary_phone and primary_phone not in phone_numbers:
        phone_numbers.insert(0, primary_phone)
    primary_email = clean_text(seed.get("primary_email")) or None
    emails = split_list(seed.get("emails"))
    if primary_email and primary_email not in emails:
        emails.insert(0, primary_email)
    mailing_address = clean_text(seed.get("mailing_address") or site_row.get("address")) or None
    identity_sources = split_list(seed.get("identity_sources"))
    if "lakes_contact_seed" not in identity_sources:
        identity_sources.append("lakes_contact_seed")
    source_record_ids = split_list(seed.get("source_record_ids"))
    source_id = clean_text(seed.get("source_id"))
    if source_id:
        source_record_ids.insert(0, source_id)
    site_id = str(site_row.get("site_id") or "")
    dedupe_basis = display_name or organization_name or site_id
    return {
        "contact_id": contact_id_for_row(site_row),
        "account_id": account_id_for_row(site_row),
        "site_id": site_id,
        "entity_type": clean_text(seed.get("entity_type")) or "organization",
        "role": clean_text(seed.get("role")) or "business_contact",
        "display_name": display_name,
        "first_name": None,
        "last_name": None,
        "organization_name": organization_name or None,
        "owner_occupancy": None,
        "residency_confidence": None,
        "preferred_channel": preferred_channel,
        "contactability_score": score,
        "contactability_label": label,
        "do_not_contact": clean_text(seed.get("do_not_contact")).lower() in {"1", "true", "yes", "y"},
        "primary_phone": primary_phone,
        "phone_numbers": phone_numbers,
        "primary_email": primary_email,
        "emails": emails,
        "website_url": clean_text(seed.get("website_url")) or None,
        "contact_form_url": clean_text(seed.get("contact_form_url")) or None,
        "contact_paths": build_contact_paths(seed, preferred_channel),
        "mailing_address": mailing_address,
        "best_contact_window": clean_text(seed.get("best_contact_window")) or None,
        "dedupe_key": f"{site_id}:{slug_token(dedupe_basis)}",
        "identity_sources": identity_sources,
        "source_record_ids": source_record_ids,
        "verified_at": clean_text(seed.get("verified_at")) or now,
        "freshness_days": int(clean_text(seed.get("freshness_days"))) if clean_text(seed.get("freshness_days")).isdigit() else None,
        "notes": clean_text(seed.get("notes")) or "Imported from Lakes commercial contact seed.",
        "created_at": now,
        "updated_at": now,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Lakes Region commercial contacts into lead_contacts.json")
    parser.add_argument("--input", default=str(DEFAULT_INPUT_CSV))
    parser.add_argument("--write", action="store_true", help="Persist changes to lead_contacts.json")
    args = parser.parse_args()

    input_csv = Path(args.input)
    if not input_csv.exists():
        raise SystemExit(f"Input CSV not found: {input_csv}")

    site_rows = load_site_rows()
    by_site = {str(row.get("site_id") or ""): row for row in site_rows}
    by_address: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    for row in site_rows:
        key = build_address_key(row.get("address"), row.get("city"), row.get("state"), row.get("zip"))
        by_address.setdefault(key, []).append(row)

    store = load_contact_store()
    created = 0
    updated = 0
    unmatched: list[dict[str, Any]] = []
    imported_contacts: list[dict[str, Any]] = []

    with input_csv.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for seed in reader:
            target_rows, error = resolve_target_rows(seed, by_site, by_address)
            if error or not target_rows:
                unmatched.append({"source_id": clean_text(seed.get("source_id")), "business_name": clean_text(seed.get("business_name")), "error": error or "no targets"})
                continue
            for row in target_rows:
                record = build_contact_record(seed, row)
                contact_id = record["contact_id"]
                if contact_id in store:
                    record["created_at"] = store[contact_id].get("created_at") or record["created_at"]
                    updated += 1
                else:
                    created += 1
                store[contact_id] = record
                imported_contacts.append({
                    "contact_id": contact_id,
                    "site_id": record["site_id"],
                    "display_name": record["display_name"],
                    "address": row.get("address"),
                })

    if args.write:
        write_contact_store(store)

    summary = {
        "input_csv": str(input_csv),
        "write": bool(args.write),
        "created": created,
        "updated": updated,
        "unmatched": unmatched,
        "imported_contacts": imported_contacts,
        "contact_store_size": len(store),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
