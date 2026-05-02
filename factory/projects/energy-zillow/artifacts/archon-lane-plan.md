# DemandGrid optimized lane plan - EZ-022

## Objective
Add parcel permit-history lane (roof/HVAC/solar timing signals)

## Sequence
- [ ] Confirm touched files and existing artifacts
- [ ] Apply minimum changes to satisfy done_when
- [ ] Write implementation report artifact
- [ ] Run eval gate
- [ ] Run live smoke gate

## done_when
- permit feed normalizes to site_id or deterministic parcel/address key
- roofing/HVAC recency triggers populate non-trivial share of active sites
- trigger notes include permit recency fields and source provenance
- merge + score + eval pass with permit lane enabled

## expected artifacts
- scripts/fetch_boston_permit_feed.py
- scripts/fetch_providence_permit_feed.py
- scripts/fetch_cambridge_permit_feed.py
- scripts/project_parcel_permit_triggers.py
- data/raw/parcel_permit_feed.template.csv
- data/raw/parcel_permit_feed.csv
- data/raw/property_triggers_external.csv
- artifacts/boston-permit-fetch-summary.md
- artifacts/boston-permit-fetch-summary.json
- artifacts/providence-permit-fetch-summary.md
- artifacts/providence-permit-fetch-summary.json
- artifacts/cambridge-permit-fetch-summary.md
- artifacts/cambridge-permit-fetch-summary.json
- artifacts/permit-trigger-summary.md
- artifacts/permit-trigger-summary.json
- artifacts/permit-trigger-coverage.md
- artifacts/eval-summary.md

## constraints
- Low-collision edits only
- Keep API contracts stable unless lane contract requires change
