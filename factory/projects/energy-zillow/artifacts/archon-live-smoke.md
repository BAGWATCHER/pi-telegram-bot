# DemandGrid live smoke

- timestamp_utc: 2026-04-21T20:35:31.748454+00:00
- base_url: http://127.0.0.1:8099
- site_id: site_5dbcd14616d9
- all_ok: True

## checks
- health: ok=True status=200 url=http://127.0.0.1:8099/health
- signals_coverage: ok=True status=200 url=http://127.0.0.1:8099/api/v1/signals/coverage
- outcomes_summary: ok=True status=200 url=http://127.0.0.1:8099/api/v1/outcomes/summary
- governance_policies: ok=True status=200 url=http://127.0.0.1:8099/api/v1/governance/policies
- site_detail: ok=True status=200 url=http://127.0.0.1:8099/api/v1/site/site_5dbcd14616d9
