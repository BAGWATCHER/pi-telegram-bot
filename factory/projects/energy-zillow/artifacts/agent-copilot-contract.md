# Agent Copilot Contract (EZ-020A)

## Framework
- `pi-tool-router-v1`
- Mode: tool-routed, grounded to in-process DemandGrid APIs/data cache.

## Endpoints
- `GET /api/v1/agent/capabilities`
- `POST /api/v1/agent/chat`

## Chat request
```json
{
  "message": "top hot solar leads in 01730 with outage trigger",
  "zip": "01730",
  "h3_cell": null,
  "site_id": null,
  "max_results": 8
}
```

## Chat response (shape)
```json
{
  "framework": "pi-tool-router-v1",
  "intent": "top_leads",
  "reply": "Top 8 leads in scope...",
  "tool_calls": [
    {"tool": "scope_rows", "args": {"zip": "01730", "h3_cell": null}, "result_count": 2173},
    {"tool": "top_leads", "args": {"zip": "01730"}, "result_count": 8}
  ],
  "cards": [
    {
      "site_id": "site_...",
      "address": "...",
      "primary_product": "solar",
      "lead_temperature": "hot",
      "sales_route_score": 98.2
    }
  ],
  "scope": {"zip": "01730", "h3_cell": null, "site_id": null},
  "suggested_actions": ["Why this site", "Plan route", "Mark site contacted"]
}
```

## Supported intents
- help/capabilities
- top leads (with scope/product/trigger keywords)
- site explain (`why this site`)
- route planning
- heatmap summary
- workflow status update (`mark site_x contacted`)

## Guardrails
- Grounded to local scored dataset and operator status store.
- No external LLM call in default path.
- Returns explicit `tool_calls` for traceability.
