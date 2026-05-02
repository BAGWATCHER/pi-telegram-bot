# DemandGrid — Targeting Matrix

## Purpose

This file exists to keep implementation aligned on what the engine should target first.

The project is not a single-product solar tool.
It is a property-led AI opportunity engine that should recommend the best first offer and best adjacent offer for each property/building.

## Core Build Rule

Prefer product lanes where property/location/building signals create a real targeting edge.

Good map-native lanes:
- `roofing`
- `solar`
- `hvac / heat pump`
- `battery / backup power`
- `waterproofing / foundation / restoration`
- `commercial roofing`
- `commercial solar`
- `commercial hvac`

Less map-native lanes:
- merchant services
- payroll / HR
- staffing
- software retainers
- generic B2B service sales

Those may still pay well, but they need a different intelligence model than the current property engine.

## Initial Active Lanes

### 1. Roofing

- Why it pays: large contracts, urgency, storm/event triggers, strong visual/property cues
- Best trigger: hail/wind/storm exposure, roof age/size proxies, neighborhood replacement clusters
- Best signals: roof area proxy, storm-history layers, visible replacement clusters, building size
- Ease of close: high when damage/urgency is real
- Seasonality: storm-driven and regional
- Recommendation status: `core`

### 2. Solar

- Why it pays: high contract value, long-term savings story, strong fit with property data
- Best trigger: good roof geometry, good solar access, high utility economics, owner-occupied affluent areas
- Best signals: roof usable area, roof complexity, solar access proxy, ZIP economics, confidence
- Ease of close: medium
- Seasonality: less seasonal, incentive/policy sensitive
- Recommendation status: `core`

### 3. HVAC / Heat Pump

- Why it pays: high homeowner pain, urgent failures, strong replacement economics
- Best trigger: older housing stock, larger homes, electrification fit, high-income owner-occupied homes
- Best signals: home/building age when available, home size proxy, neighborhood age proxy, ZIP fit
- Ease of close: high when urgency exists
- Seasonality: hot/cold weather spikes
- Recommendation status: `core`

### 4. Battery / Backup Power

- Why it pays: good ticket size, strong solar adjacencies, outage-driven urgency
- Best trigger: outage-prone zones, high-value homes, solar-fit properties, resiliency angle
- Best signals: solar fit, owner profile, outage history, home size/value proxies
- Ease of close: medium
- Seasonality: storm/outage sensitive
- Recommendation status: `core-adjacent`

## Expansion Lanes

### Waterproofing / Foundation / Restoration

- Why it pays: underexploited, high pain, prevent-damage framing
- Best trigger: flood-prone zones, slope/drainage issues, older housing stock, basement-heavy areas
- Best signals: flood risk, drainage/slope, lot/building elevation context, age
- Ease of close: medium to high when water issues are active
- Recommendation status: `expansion`

### Commercial Roofing

- Why it pays: very large ticket sizes, repeatable building-level targeting
- Best trigger: flat roof age, storm exposure, coating/replacement cycles
- Best signals: building size, roof type, storm history, parcel/building footprint
- Ease of close: medium; fewer prospects but much larger value
- Recommendation status: `expansion`

### Commercial Solar

- Why it pays: very high contract sizes, strong ROI framing for energy-intensive facilities
- Best trigger: large roofs, high daytime load, owner-occupied commercial property, high rates
- Best signals: building footprint, land use, likely business type, rate environment, solar exposure
- Ease of close: medium to low; bigger deal cycles
- Recommendation status: `expansion`

### Commercial HVAC

- Why it pays: meaningful ticket size, real operating pain, recurring maintenance adjacency
- Best trigger: aging facilities, rooftop units, occupancy-intensive uses
- Best signals: building size, business type, age, heat/cooling load proxies
- Ease of close: medium
- Recommendation status: `expansion`

## Operator Output We Want Per Property

For each property/building, the scoring engine should eventually emit:
- `primary_product`
- `secondary_product`
- `priority_score`
- `profit_score`
- `close_probability`
- `fit_score`
- `effort_score`
- `recommended_pitch`
- `evidence_summary`

## Immediate Build Guidance

Current recommendation engine should start simple:
- score shared opportunity factors first
- derive product ordering second
- stay explicit when a recommendation is proxy-based rather than quote-grade

Do not wait for perfect multi-vertical data before shipping a useful primary/secondary recommendation layer.
