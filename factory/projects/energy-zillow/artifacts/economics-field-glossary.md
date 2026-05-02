# Economics Field Glossary (Screening Mode)

Updated: 2026-04-17

These fields are **screening estimates**, not quote-grade contract pricing.

- `annual_savings_usd`
  - Estimated annual bill savings under current assumptions.
  - This is **not** the project sale price.

- `install_cost_solar_usd`
  - Estimated installed project cost using current model assumptions.
  - Useful for prioritization, not a final quote.

- `payback_years`
  - Simple payback estimate (`install_cost / annual_savings`).

- `npv_15y_usd`
  - 15-year net present value estimate using configured discount/degradation assumptions.

- `utility_rate_override_usd_per_kwh`
  - Screening utility rate used in economics calculations (from official override, OpenEI mapping, or fallback source).

- `utility_rate_method`
  - How the rate was selected (`official_utility_override`, `utility_screening_bounded_to_state`, `state_official_fallback`, etc.).

## Operator guidance
Use these values to rank and route opportunities, then verify on investigation before quoting.
