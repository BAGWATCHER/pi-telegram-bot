# H3 Aggregation Notes (EZ-004 bootstrap)

- Library: `h3` python package
- Resolution: `8`
- Input: `data/processed/site_scores.csv`
- Output: `data/processed/h3_scores.csv`

## Aggregates per H3 cell
- `site_count`
- `avg_annual_savings_usd`
- `avg_payback_years`
- `avg_confidence`

## Current status
- H3 materialization is running from local scored dataset.
- API exposure of heatmap metrics is pending EZ-005.
