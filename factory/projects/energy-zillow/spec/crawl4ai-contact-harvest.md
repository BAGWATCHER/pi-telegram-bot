# DemandGrid — Crawl4AI Contact Harvest

## Purpose

This connects Chow's Crawl4AI fetch stack to DemandGrid's existing safe import path.

The flow is:

1. `data/raw/lakes_contact_source_manifest.csv`
2. `scripts/generate_lakes_contact_candidates.py`
3. review `data/raw/lakes_contact_candidates.csv`
4. move safe rows into `data/raw/lakes_commercial_contacts_seed.csv`
5. run `scripts/import_lakes_commercial_contacts.py --write`

## Why This Exists

DemandGrid already has:
- exact-address `site_id` matching
- safe import into `lead_contacts.json`
- UI and voice paths that consume contact records

What it was missing was a bulk discovery layer.

Chow's side already has crawler infrastructure. This script gives DemandGrid a repo-local Crawl4AI harvest path so it can produce candidate rows in batches without hand-copying every contact.

## Inputs

Source manifest columns:
- `source_id`
- `business_name`
- `address`
- `city`
- `state`
- `zip`
- `site_id`
- `source_url`
- `homepage_url`
- optional match/confidence metadata

## Output

`data/raw/lakes_contact_candidates.csv`

Important columns:
- `site_id`
- `display_name`
- `primary_phone`
- `primary_email`
- `website_url`
- `contact_form_url`
- `source_url`
- `match_confidence`
- `safe_to_seed`
- `crawl_status`
- `crawl_error`

## Usage

```bash
python3 scripts/generate_lakes_contact_candidates.py \
  --input data/raw/lakes_contact_source_manifest.csv \
  --output data/raw/lakes_contact_candidates.csv
```

## Guardrails

- Do not auto-import `match_confidence=review` rows.
- Do not auto-seed duplicate-address rows unless the manifest pins a single `site_id`.
- Prefer official business, municipal, chamber, or direct organization pages over listing aggregators.
- Use Crawl4AI discovery for candidate generation, not blind production writes.
