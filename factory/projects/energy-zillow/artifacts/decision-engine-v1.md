# DG-003 Decision Engine v1

Updated: 2026-04-17

## Endpoints
- `GET /api/v1/decision/site/{site_id}`
- `POST /api/v1/decision/batch`

## Output contract (site)
- `opportunity_score`
- `confidence`
- `win_probability_proxy`
- `next_best_action`
- `recommended_offer` (product + channel + confidence band + auto-outreach eligibility)
- `decision_factors` (lead temp, operator status, signal quality counts, suppression reasons)

## Initial proxy formula
`win_probability_proxy = clamp(0.02, 0.99, 0.25*confidence + 0.45*(opportunity_score/100) + 0.06*verified_signals + 0.02*proxy_signals)`

This is a deterministic bootstrap pending closed-loop calibration.
