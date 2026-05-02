# DemandGrid - Outage / Battery Upgrade Note

Updated: 2026-04-17

## Goal
Turn the current outage lane from a coarse state snapshot into a useful battery trigger and preserve it as a stable part of `property_triggers.csv`.

## Source Options

### Option A: State / utility outage snapshot feeds
- Best for: live outage urgency
- Pros: free, fast, easy to project to sites
- Cons: coarse, utility-territory dependent, not true premise history
- Current fit: good enough to keep shipping

### Option B: Utility reliability history
- Best for: battery prioritization
- Sources to normalize: EIA-861, utility annual reports, SAIDI / SAIFI disclosures
- Pros: better battery signal than a one-time outage map
- Cons: usually utility-level, not address-level

### Option C: Address-level outage history
- Best for: ideal long-term battery targeting
- Pros: strongest signal
- Cons: hardest to obtain free; should not block the lane

## Recommendation
Ship a two-layer outage/battery lane:
- keep the current state / utility outage snapshot as the live `outage_trigger_*` layer
- add utility reliability history as the battery-specific prior
- do not wait for address-level outage history before shipping the next version

## Fields to Add

### To `data/raw/state_outage_feed.csv`
- `utility_name`
- `utility_id`
- `state`
- `outage_pct`
- `customers_out`
- `customers_served`
- `captured_at`
- `source_type`
- `source_url`

### To `data/processed/property_triggers.csv`
- `outage_trigger_status`
- `outage_trigger_score`
- `outage_event_count_12m`
- `outage_event_count_36m`
- `recent_outage_days`
- `utility_name`
- `utility_reliability_tier`
- `saidi_minutes`
- `saifi_events`
- `battery_trigger_status`
- `battery_trigger_score`
- `battery_reason`

## Ingestion Order

1. Load utility territory and source inventory first.
2. Fetch the outage snapshot or reliability feed.
3. Project the feed to ZIP / site rows.
4. Merge into `property_triggers.csv` without overwriting stronger storm, flood, or equipment fields.
5. Rescore and run eval.

## Done Means
- `outage_trigger_status` is non-missing on the widened board.
- `battery_trigger_score` has a real utility-reliability signal.
- Merge order preserves stronger existing trigger layers.
- The scorer can rank battery as a real lane instead of a placeholder.
