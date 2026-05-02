# Utility Mapping Gaps

Updated: 2026-04-17

## Current scoreboard

- `official_utility_override`: `57,405`
- `state_official_fallback`: `4,429`
- blank `utility_name` rows: `1,885`, all in `01940 Lynnfield`

## Current unresolved fallback pockets

- `01940` `Lynnfield, MA`: split-territory case. Official sources indicate `Reading Municipal Light Department` serves `Lynnfield Center`, while the Town of Lynnfield points residents to `Peabody Municipal Lighting` for the south side. Do not apply a ZIP-wide mapping without a defensible boundary or street-level list.
- `02043` `Hingham, MA`: utility is mapped to `Hingham Municipal Lighting Plant`, and the official residential rate page now gives a current fixed charge plus `Capacity, Transmission & Distribution Charge` effective `January 1, 2025`, but HMLP still does not publicly expose a current monthly `Standard Energy Charge` / `PCA` figure on the public rate pages. That leaves no defensible current all-in residential `$ / kWh` baseline yet.
- `01949` `Middleton, MA`: utility is mapped to `Middleton Electric Light Dept.`, and MELD publicly posts an official residential tariff PDF (`M.D.P.U. #76`, effective `September 1, 2022`) plus bill FAQ language for `PPA`, but it does not publish a current monthly residential `Energy Charge` / `PPA` figure in the public rate materials. That leaves no clean current all-in residential `$ / kWh` baseline yet.

## Resolved or partially resolved

- `02482` `Wellesley, MA`: mapped and promoted to `Wellesley Municipal Light Plant`.
- `01450` `Groton, MA`: mapped and promoted to `Groton Electric Light Dept.`.
- `05486` `South Hero, VT`: mapped and promoted to `Vermont Electric Cooperative`.
- `04006` `Biddeford Pool / Biddeford, ME`: fully resolved to `Central Maine Power Co` after the ZIP-wide fallback row was applied through the widened scorer.

## Best next actions

- Add a conservative `Lynnfield` split mapping rule only if a defensible boundary source or street-level utility list is found.
- Land exact current screening baselines for `Hingham Municipal Lighting Plant` and `Middleton Electric Light Dept.` from official public materials before promoting them out of state fallback.

## Current official references

- RMLD service territory / Lynnfield Center: https://www.rmld.com/about-rmld
- Town of Lynnfield Peabody Municipal Lighting page: https://www.lynnfieldma.gov/195/Peabody-Municipal-Lighting
- Hingham residential rates: https://www.hmlp.com/rates/residential-rates/
- Hingham electric-bill explainer: https://www.hmlp.com/billing-payment/reading-your-electric-bill/
- Middleton rates landing page: https://middletonlight.org/rates.html
- Middleton residential tariff PDF: https://middletonlight.org/docs/rates/MELD-Residential-Rate-A-ACC.pdf
- Middleton bill explainer / PPA note: https://middletonlight.org/billing.html
