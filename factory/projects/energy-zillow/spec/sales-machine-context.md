# DemandGrid — Sales Machine Context

## What This Project Is

DemandGrid is not just a consumer-facing solar map.

It is a private operator tool intended to help Adam identify, rank, and work the highest-value sales opportunities faster than normal door-to-door or bought-lead workflows.

Primary framing:
- Use software to identify who to sell what to
- Build a targeting advantage
- Turn map intelligence into a multi-product sales workflow

The map is an interface, not the end product.

## Core Product Goal

The real goal is:

`Where should I spend my next 4 hours selling?`

Every feature should support at least one of these:
- identify better targets
- contact them faster
- avoid wasting time on weak leads
- improve close rate
- increase revenue per territory/day

The unit of value is not a map cell. It is a closed deal.

## Current Operating Model

Current product flow remains:
1. neighborhood heatmap
2. click hex
3. ranked addresses
4. click address
5. recommendation card with primary/secondary offer + economics + confidence + reasons

But the product direction is now explicitly sales-first:
- this is a targeting machine
- not just an energy analysis demo
- not just a solar ranking toy

## What We Actually Care About

Avoid treating "solar potential" as the only output.

The real scoring model should move toward these axes:
- `profit_score`: how much money is realistically on the table
- `close_probability`: how likely the address is to convert
- `fit_score`: technical suitability for the offer
- `effort_score`: how annoying/slow/expensive the lead is to work
- `product_scores`: which offer should be pitched first vs second

Derived operator score:
- `priority_score`: what should be worked first

Derived operator recommendation:
- `primary_product`: what to pitch first
- `secondary_product`: best adjacent lane if first lane is weak or timing is wrong
- `recommended_pitch`: short operator-facing angle to open with

Simple operator labels we want:
- `hot`
- `warm`
- `skip`

Simple difficulty labels we want:
- `easy win`
- `medium effort`
- `hard sell`

## Offer Strategy

Do not think about this as one industry only.

This project should become a property-led AI opportunity engine with many monetization lanes on top of one intelligence substrate.

Core substrate:
- property + location + business intelligence by address/building

Priority implementation lanes should be the products where property/location signals actually help:
- `roofing`
- `solar`
- `hvac / heat pump`
- `battery / backup power`
- later: `waterproofing / foundation / restoration`
- later: `commercial roofing`
- later: `commercial solar`
- later: `commercial hvac`

Priority order:
1. `roofing`
2. `solar`
3. `hvac / heat pump`
4. `battery / backup power`

Near-term rule:
- ship a multi-product recommendation layer immediately
- keep the initial live scoring focused on products we can infer honestly from current data
- do not pretend to have quote-grade certainty on products where we only have proxy evidence

Do not build ten disconnected verticals.
Build one engine that can recommend multiple products per property.

## Product Philosophy

Do not optimize for a polished general-purpose platform before the targeting engine is strong.

Prefer:
- better lead ranking
- better product recommendation ordering
- better operator workflow
- better sales prioritization

Over:
- generic dashboards
- marketplace features
- abstract platform fantasies detached from real lead quality

## Workflow Direction

This tool should evolve into an operator console.

Useful workflow layers:
- save targets
- tag `hot / warm / skip`
- mark `visited / contacted / follow-up / closed`
- add notes per address
- build route plans for field days

This is what makes it a sales machine instead of just a map.

For every property/building, the operator should be able to answer:
- what should I sell here first?
- what should I sell here second?
- why this product first?
- how much money is on the table?
- how hard is this deal likely to be?

## Data Honesty

Even when the product becomes more sales-driven, maintain honesty:
- do not present quote-grade certainty when data is screening-grade
- keep confidence and survey requirements visible
- degrade gracefully when data is weak

The right behavior is:
- strong targeting confidence when evidence is good
- obvious warnings when inputs are incomplete

## Near-Term Build Priority

Near-term priority order for implementation:
1. strengthen address-level ranking signals
2. add multi-product recommendation output per address
3. add operator workflow fields/state
4. add route planning / territory workflow

## Guidance For Future Work

When choosing between tasks, prefer work that answers:
- does this improve target ranking?
- does this improve primary/secondary product selection?
- does this improve expected profit per lead?
- does this improve close probability estimation?
- does this reduce time wasted on low-value houses?

If a proposed feature does not improve operator efficiency or deal quality, it is probably not the right next step.
