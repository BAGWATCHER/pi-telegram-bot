# DemandGrid - Utility Rollout Matrix

Updated: 2026-04-17

## Current Interim Stack

- `data/processed/site_utility_tariff.csv` supplies site-level utility screening rows where available.
- `data/raw/eia_state_residential_rates.csv` supplies official current state residential rate anchors.
- `data/raw/official_utility_residential_rates.csv` now covers `NSTAR Electric Company`, `Massachusetts Electric Co`, `United Illuminating Co`, `Connecticut Light & Power Co`, `Central Maine Power Co`, `Public Service Co of NH`, `The Narragansett Electric Co`, `Wellesley Municipal Light Plant`, `Groton Electric Light Dept.`, and `Vermont Electric Cooperative`.
- `data/raw/manual_utility_map.csv` supplies ZIP/city fallback utility normalization for muni/co-op territories missing from the OpenEI utility feed.
- Scoring currently uses:
  - exact-match official utility override when present
  - utility screening rate when present
  - bounded relative adjustment against current EIA state rates
  - official state fallback when utility mapping is missing

This is an interim screening stack, not the final source of truth.

## First Official Utility Rollout Order

Ranked by:
- current board coverage
- ease of official tariff access
- expected economics impact

1. Eversource Massachusetts
2. National Grid Massachusetts
3. United Illuminating
4. Eversource Connecticut
5. Central Maine Power
6. Versant Power
7. Eversource New Hampshire
8. Unitil
9. Green Mountain Power
10. Burlington Electric Department
11. National Grid Rhode Island

## Why This Order

- Massachusetts is the dominant board geography and should be improved first.
- Connecticut is the second-largest live geography and has clean official utility pages.
- Maine matters because battery and resiliency economics are sensitive there.
- NH, VT, and RI are lower current volume and can follow after MA/CT/ME.
- CMP is now promoted from the screening layer using the Maine PUC residential table.
- CL&P / Eversource CT is now promoted using the official `Rate 1` tariff PDF plus the PURA-managed residential generation board, which exposes the missing CT public-benefit and FMCC components cleanly enough for an all-in baseline.
- Eversource New Hampshire / `Public Service Co of NH` is now promoted from the screening layer using the official February 1, 2026 summary PDF plus current delivery and supply pages.
- Rhode Island / `The Narragansett Electric Co` is now promoted using the RIPUC April 2, 2026 compliance filing and Rhode Island Energy last-resort-service baseline instead of the stale consumer summary page.
- Manual utility normalization now covers Wellesley, Hingham, Middleton, Groton, South Hero, and Biddeford Pool so blank-utility fallback rows can resolve to the right muni/co-op/IOU even when OpenEI returns no utility item.
- Wellesley, Groton, and Vermont Electric Cooperative are promoted with official or officially posted municipal/co-op residential baselines; Hingham and Middleton are mapped but remain on state fallback until cleaner current all-in rows are sourced.
- Fresh 2026 web research tightened the municipal blocker definition:
  - `Hingham Municipal Lighting Plant` now has an official live residential rate page with current fixed + CTD charges effective `2025-01-01`, plus a bill explainer confirming PASNY and PCA semantics, but no public current Standard Energy Charge / PCA number.
  - `Middleton Electric Light Dept.` now has an official residential tariff PDF (`M.D.P.U. #76`, effective `2022-09-01`) plus a bill explainer confirming prompt-pay discount and PPA semantics, but no public current monthly Energy Charge / PPA number.
  - `Lynnfield` still cannot be ZIP-mapped safely because the official evidence remains a territory split between `RMLD` (`Lynnfield Center`) and `Peabody Municipal Lighting` (`South Lynnfield`).

## First-Ship Fields

For each official utility tariff lane, capture:

- `utility_id`
- `utility_name`
- `state`
- `customer_class`
- `rate_code`
- `effective_start`
- `effective_end`
- `customer_charge_monthly`
- `delivery_charge_kwh`
- `supply_charge_kwh`
- `demand_charge_kw`
- `tou_on_peak_kwh`
- `tou_off_peak_kwh`
- `seasonal_flag`
- `source_url`
- `retrieved_at`
- `confidence`
- `notes`

## Current Mapping Artifact

The current practical mapping layer is:

- `data/processed/site_utility_tariff.csv`

If a cleaner split is needed later, add:

- `data/processed/site_utility_map.csv`

with:

- `site_id`
- `zip`
- `state`
- `utility_id`
- `utility_name`
- `mapping_method`
- `confidence`
- `source`
- `as_of`

## Official Sources

- EIA-861: https://www.eia.gov/electricity/data/eia861/
- Eversource MA: https://www.eversource.com/residential/account-billing/manage-bill/about-your-bill/rates-tariffs/electric-delivery-rates/wma
- Eversource CT: https://www.eversource.com/residential/account-billing/manage-bill/about-your-bill/rates-tariffs/electric-delivery-rates/ct
- Eversource NH: https://www.eversource.com/residential/account-billing/manage-bill/about-your-bill/rates-tariffs/electric-delivery-rates/nh
- National Grid MA: https://www.nationalgridus.com/MA-Home/Rates/Service-Rates
- United Illuminating: https://www.uinet.com/w/pricing_custom
- United Illuminating TOU: https://www.uinet.com/w/time-of-day-rate-rt
- CMP: https://www.cmpco.com/account/understandyourbill/pricing
- CMP TOU: https://www.cmpco.com/time-of-use-delivery-rate
- Versant Power: https://www.versantpower.com/energy-solutions/eco-rates
- Unitil: https://unitil.com/electric-gas-service/pricing-rates/rates
- Unitil MA Residential: https://unitil.com/rates/massachusetts-residential-electric-rates
- Green Mountain Power: https://greenmountainpower.com/rates/
- Burlington Electric: https://www.burlingtonelectric.com/rates/
