#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_CSV = ROOT / "data/raw/lakes_contact_source_manifest.csv"
DEFAULT_OUTPUT_CSV = ROOT / "data/raw/lakes_contact_candidates.csv"

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?:\+?1[\s.\-]?)?(?:\(?\d{3}\)?[\s.\-]?)\d{3}[\s.\-]?\d{4}")
CONTACT_FORM_RE = re.compile(r"https?://[^\s)>\"]*(?:contact|connect|inquire|about)[^\s)>\"]*", re.I)


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def split_list(value: Any) -> list[str]:
    if value in (None, "", "None"):
        return []
    return [clean_text(part) for part in str(value).split("|") if clean_text(part)]


def dedupe_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


async def fetch_crawl4ai(url: str, timeout_seconds: int) -> dict[str, Any]:
    try:
        from crawl4ai import AsyncWebCrawler
        from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode
    except Exception as exc:
        raise RuntimeError(
            "crawl4ai is not installed. Install it first, then rerun this generator."
        ) from exc

    browser_config = BrowserConfig(headless=True)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, page_timeout=timeout_seconds * 1000)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)
        if not bool(getattr(result, "success", False)):
            error_message = clean_text(getattr(result, "error_message", "")) or "crawl4ai crawl failed"
            raise RuntimeError(error_message)
        markdown = ""
        markdown_obj = getattr(result, "markdown", None)
        if isinstance(markdown_obj, str):
            markdown = markdown_obj
        elif markdown_obj is not None:
            markdown = clean_text(
                getattr(markdown_obj, "fit_markdown", "")
                or getattr(markdown_obj, "raw_markdown", "")
                or str(markdown_obj)
            )
        return {
            "text": markdown,
            "title": clean_text(getattr(result, "title", "")),
            "source_url": clean_text(getattr(result, "url", "")) or url,
        }


def extract_candidate_fields(text: str, source_url: str, homepage_url: str | None = None) -> dict[str, str]:
    emails = dedupe_keep_order([clean_text(v) for v in EMAIL_RE.findall(text)])
    phones = dedupe_keep_order([normalize_phone(v) for v in PHONE_RE.findall(text)])
    forms = dedupe_keep_order([clean_text(v) for v in CONTACT_FORM_RE.findall(text)])
    return {
        "primary_phone": phones[0] if phones else "",
        "phone_numbers": "|".join(phones),
        "primary_email": emails[0] if emails else "",
        "emails": "|".join(emails),
        "contact_form_url": forms[0] if forms else "",
        "website_url": homepage_url or source_url,
    }


def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) == 10:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    return clean_text(value)


def build_candidate_row(seed: dict[str, str], extracted: dict[str, str]) -> dict[str, str]:
    preferred_channel = clean_text(seed.get("preferred_channel"))
    if not preferred_channel:
        if extracted.get("primary_phone"):
            preferred_channel = "phone"
        elif extracted.get("primary_email"):
            preferred_channel = "email"
        elif extracted.get("contact_form_url"):
            preferred_channel = "website_form"
        else:
            preferred_channel = "website"
    return {
        "source_id": clean_text(seed.get("source_id")),
        "business_name": clean_text(seed.get("business_name")),
        "display_name": clean_text(seed.get("display_name") or seed.get("business_name")),
        "organization_name": clean_text(seed.get("organization_name") or seed.get("business_name")),
        "entity_type": clean_text(seed.get("entity_type") or "organization"),
        "role": clean_text(seed.get("role") or "front_desk"),
        "address": clean_text(seed.get("address")),
        "city": clean_text(seed.get("city")),
        "state": clean_text(seed.get("state")),
        "zip": clean_text(seed.get("zip")),
        "site_id": clean_text(seed.get("site_id")),
        "site_ids": clean_text(seed.get("site_ids")),
        "apply_to_all_matches": clean_text(seed.get("apply_to_all_matches")),
        "preferred_channel": preferred_channel,
        "primary_phone": extracted.get("primary_phone", ""),
        "phone_numbers": extracted.get("phone_numbers", ""),
        "primary_email": extracted.get("primary_email", ""),
        "emails": extracted.get("emails", ""),
        "website_url": extracted.get("website_url", ""),
        "contact_form_url": extracted.get("contact_form_url", ""),
        "mailing_address": clean_text(seed.get("mailing_address") or seed.get("address")),
        "contactability_score": clean_text(seed.get("contactability_score")),
        "contactability_label": clean_text(seed.get("contactability_label")),
        "best_contact_window": clean_text(seed.get("best_contact_window")),
        "identity_sources": clean_text(seed.get("identity_sources") or "firecrawl_candidate"),
        "source_record_ids": dedupe_source_ids(
            split_list(seed.get("source_record_ids")) + [clean_text(seed.get("source_url"))]
        ),
        "verified_at": clean_text(seed.get("verified_at")),
        "freshness_days": clean_text(seed.get("freshness_days")),
        "do_not_contact": clean_text(seed.get("do_not_contact") or "false"),
        "notes": clean_text(seed.get("notes") or "Generated from Firecrawl source manifest."),
        "source_url": clean_text(seed.get("source_url")),
        "source_type": clean_text(seed.get("source_type") or "firecrawl"),
        "match_confidence": clean_text(seed.get("match_confidence") or "review"),
        "safe_to_seed": clean_text(seed.get("safe_to_seed") or "false"),
        "crawl_status": "ok",
        "crawl_error": "",
    }


def dedupe_source_ids(values: list[str]) -> str:
    return "|".join(dedupe_keep_order([value for value in values if value]))


def error_candidate_row(seed: dict[str, str], error: str) -> dict[str, str]:
    row = build_candidate_row(seed, {})
    row["crawl_status"] = "error"
    row["crawl_error"] = clean_text(error)
    return row


async def amain() -> int:
    parser = argparse.ArgumentParser(description="Generate Lakes contact candidates via Crawl4AI.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT_CSV))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_CSV))
    parser.add_argument("--timeout-seconds", type=int, default=30)
    args = parser.parse_args()

    input_csv = Path(args.input)
    output_csv = Path(args.output)
    if not input_csv.exists():
        raise SystemExit(f"Input manifest not found: {input_csv}")

    rows_out: list[dict[str, str]] = []
    with input_csv.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for seed in reader:
            source_url = clean_text(seed.get("source_url"))
            homepage_url = clean_text(seed.get("homepage_url"))
            if not source_url:
                rows_out.append(error_candidate_row(seed, "missing source_url"))
                continue
            try:
                payload = await fetch_crawl4ai(source_url, args.timeout_seconds)
                text = clean_text(payload.get("text") or "")
                extracted = extract_candidate_fields(text, source_url, homepage_url or None)
                rows_out.append(build_candidate_row(seed, extracted))
            except (RuntimeError, TimeoutError, json.JSONDecodeError) as exc:
                rows_out.append(error_candidate_row(seed, str(exc)))

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "source_id",
        "business_name",
        "display_name",
        "organization_name",
        "entity_type",
        "role",
        "address",
        "city",
        "state",
        "zip",
        "site_id",
        "site_ids",
        "apply_to_all_matches",
        "preferred_channel",
        "primary_phone",
        "phone_numbers",
        "primary_email",
        "emails",
        "website_url",
        "contact_form_url",
        "mailing_address",
        "contactability_score",
        "contactability_label",
        "best_contact_window",
        "identity_sources",
        "source_record_ids",
        "verified_at",
        "freshness_days",
        "do_not_contact",
        "notes",
        "source_url",
        "source_type",
        "match_confidence",
        "safe_to_seed",
        "crawl_status",
        "crawl_error",
    ]
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_out)

    ok = sum(1 for row in rows_out if row["crawl_status"] == "ok")
    errors = len(rows_out) - ok
    print(json.dumps({"input": str(input_csv), "output": str(output_csv), "rows": len(rows_out), "ok": ok, "errors": errors}, indent=2))
    return 0


def main() -> int:
    return asyncio.run(amain())


if __name__ == "__main__":
    raise SystemExit(main())
