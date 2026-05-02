# DemandGrid — Product Contract (EZ-001, sales-machine revision)

## One-liner
Neighborhood heatmap -> ranked addresses -> per-address primary/secondary product recommendation with confidence + economics + operator workflow guidance.

## User flow (must remain true)
1. Operator opens map and sees H3 opportunity heatmap.
2. Operator clicks a hex and sees ranked addresses.
3. Operator clicks an address and gets recommendation card:
   - primary / secondary product
   - priority + lead bucket (`hot|warm|skip`)
   - next step (`work_now|follow_up|deprioritize`)
   - annual kWh / savings / payback / NPV
   - confidence + reasons + trigger gaps
4. Operator updates workflow status (`unworked|visited|contacted|follow_up|closed|skip`).
5. Operator can generate route plan for field-day execution.

## In scope (current MVP+)
- Solar-first economics with multi-product ranking (roofing, solar, hvac/heat-pump, battery).
- H3 aggregate map layer and ranked address API.
- Per-site recommendation endpoint with confidence/reasons.
- Operator workflow status persistence endpoints.
- Route-day planning endpoint with stop ordering.
- Trigger-layer contract (screening-grade stubs until external layers are loaded).

## Out of scope (MVP)
- Permit/interconnection automation.
- High-precision rooftop wind CFD.
- Financing/loan marketplace integrations.
- Perfect parcel normalization across all municipalities.

## Data honesty constraints
- Wind/hybrid only when confidence evidence is explicit.
- Non-solar lanes stay proxy-labeled until real trigger layers are present.
- Trigger gaps and survey requirements must remain visible.
- Assumptions must be documented for tariff/install/incentive values.

## Done criteria for EZ-001
- [x] Product contract documented.
- [x] Site recommendation schema created (`schema/site-score.schema.json`).
- [x] No-scope list documented.
