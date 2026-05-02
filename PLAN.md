# EZ-022 — Add parcel permit-history lane (roof/HVAC/solar timing signals)

## Explicit files to change

Code / contract:
- `factory/projects/energy-zillow/scripts/fetch_boston_permit_feed.py`
- `factory/projects/energy-zillow/scripts/fetch_cambridge_permit_feed.py`
- `factory/projects/energy-zillow/scripts/fetch_providence_permit_feed.py`
- `factory/projects/energy-zillow/scripts/project_parcel_permit_triggers.py`
- `factory/projects/energy-zillow/scripts/merge_property_triggers.py`
- `factory/projects/energy-zillow/data/raw/parcel_permit_feed.template.csv`
- `factory/projects/energy-zillow/spec/trigger-feed-contract.md`
- `factory/projects/energy-zillow/README.md`

Regenerated artifacts / data outputs:
- `factory/projects/energy-zillow/data/raw/parcel_permit_feed.csv`
- `factory/projects/energy-zillow/data/raw/property_triggers_external.csv`
- `factory/projects/energy-zillow/data/processed/property_triggers.csv`
- `factory/projects/energy-zillow/artifacts/boston-permit-fetch-summary.md`
- `factory/projects/energy-zillow/artifacts/boston-permit-fetch-summary.json`
- `factory/projects/energy-zillow/artifacts/cambridge-permit-fetch-summary.md`
- `factory/projects/energy-zillow/artifacts/cambridge-permit-fetch-summary.json`
- `factory/projects/energy-zillow/artifacts/providence-permit-fetch-summary.md`
- `factory/projects/energy-zillow/artifacts/providence-permit-fetch-summary.json`
- `factory/projects/energy-zillow/artifacts/permit-trigger-summary.md`
- `factory/projects/energy-zillow/artifacts/permit-trigger-summary.json`
- `factory/projects/energy-zillow/artifacts/permit-trigger-coverage.md`
- `factory/projects/energy-zillow/artifacts/eval-summary.md`

## Step-by-step patch sequence

1. **Tighten the permit feed contract first**
   - Extend `data/raw/parcel_permit_feed.template.csv` with low-collision provenance fields only: `match_method`, `match_key`, `source_city`, and `source_dataset`.
   - Update `spec/trigger-feed-contract.md` to document these as optional permit-lane fields and to define the canonical build order for the combined feed.
   - Keep the existing required columns unchanged so downstream readers do not break.

2. **Normalize fetcher behavior across Boston/Cambridge/Providence**
   - In `scripts/fetch_boston_permit_feed.py`, add the same append/replace semantics already used by the other city scripts so the full lane can be rebuilt deterministically without manual file juggling.
   - In all 3 fetch scripts, emit the same provenance columns (`match_method`, `match_key`, `source_city`, `source_dataset`) for every written permit row.
   - Preserve current address-matching logic; do not broaden matching heuristics unless needed for a specific false-negative fix.
   - Keep dedupe keyed on `site_id + permit_id + permit_type` to minimize ranking churn.

3. **Make the permit projection emit structured provenance, not just free-text notes**
   - In `scripts/project_parcel_permit_triggers.py`, aggregate permit rows by `site_id` and carry forward:
     - recent permit counts
     - recent permit types
     - last permit date/type
     - compact source provenance summary derived from the new feed columns
   - Keep existing trigger columns stable; only enrich `trigger_notes` with concise provenance text rather than introducing broad new site-score schema changes in this pass.
   - Preserve non-permit trigger values already present in `data/raw/property_triggers_external.csv`.

4. **Harden merge preservation for permit metadata**
   - In `scripts/merge_property_triggers.py`, make sure incoming permit metadata wins only for permit-related fields and never clears existing storm/outage/flood values.
   - Keep full trigger contract output shape unchanged.
   - Verify merge still produces a contract-complete row for every site even when permit feed coverage is sparse.

5. **Refresh docs/runbook with deterministic lane order**
   - Update `README.md` to show the intended permit rebuild sequence:
     1. Boston with replace/fresh output
     2. Cambridge append
     3. Providence append
     4. permit projection
     5. trigger merge
     6. scoring + eval
   - Keep this limited to the permit-lane commands already used by EZ-022.

6. **Regenerate lane artifacts only after code/contract changes land**
   - Rebuild `data/raw/parcel_permit_feed.csv` from the 3 municipal fetchers.
   - Re-run `scripts/project_parcel_permit_triggers.py` and `scripts/merge_property_triggers.py`.
   - Regenerate the permit fetch summaries, trigger summary/coverage artifacts, and `artifacts/eval-summary.md`.

## Validation checklist

- Data contract:
  - `data/raw/parcel_permit_feed.csv` contains the original permit fields plus `match_method`, `match_key`, `source_city`, `source_dataset`.
  - `data/raw/property_triggers_external.csv` still has one row per site and preserves all non-permit trigger columns.

- Lane rebuild:
  - `python3 scripts/fetch_boston_permit_feed.py --zips 02118 --output data/raw/parcel_permit_feed.csv --replace`
  - `python3 scripts/fetch_cambridge_permit_feed.py --zips 02139 --output data/raw/parcel_permit_feed.csv`
  - `python3 scripts/fetch_providence_permit_feed.py --zips 02903 --output data/raw/parcel_permit_feed.csv`
  - `python3 scripts/project_parcel_permit_triggers.py --permit-feed data/raw/parcel_permit_feed.csv`
  - `python3 scripts/merge_property_triggers.py --external data/raw/property_triggers_external.csv`
  - `python3 scripts/score_sites.py --solar-model proxy`

- Eval:
  - `python3 eval/run_eval.py`
  - Confirm `permit_evidence_contract` remains PASS.
  - Confirm coverage/ranking/perf gates do not regress.

- API smoke checks against `http://127.0.0.1:8099`:
  - `GET /health`
  - `GET /api/v1/site/{permit_backed_site_id}` returns non-empty permit fields (`permit_trigger_status`, `permit_recent_count`, `permit_last_date`, `permit_last_type`).
  - `GET /api/v1/investigation/site/{permit_backed_site_id}` includes permit evidence and trigger notes with source provenance.
  - `GET /api/v1/site/{control_site_id}` still returns contract-complete permit fields with safe defaults.

- Artifact sanity:
  - Boston/Cambridge/Providence fetch summaries show non-zero matched rows for their target ZIPs.
  - `artifacts/permit-trigger-coverage.md` shows non-trivial non-missing coverage in `02118`, `02139`, and `02903`.

## Rollback notes

- Fast rollback scope: revert only the 8 code/contract/doc files listed above.
- Restore prior generated data/artifacts by checking out the previous versions of:
  - `data/raw/parcel_permit_feed.csv`
  - `data/raw/property_triggers_external.csv`
  - `data/processed/property_triggers.csv`
  - permit summary artifacts
  - `artifacts/eval-summary.md`
- If merge behavior regresses, back out `scripts/merge_property_triggers.py` first and regenerate `data/processed/property_triggers.csv` from the last known-good external feed.
- If fetcher normalization causes unexpected row churn, keep the prior fetchers and re-run only the previous known-good sequence to restore the baseline permit feed.
