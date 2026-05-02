# DemandGrid — Contact Intelligence Roadmap

## Purpose

This file captures the next data layer needed to turn DemandGrid from a smart ranked board into an AI-driven sales system.

The current stack is already reasonably strong on:
- property scoring
- lane recommendation
- route planning
- workflow state
- outcome logging

The next bottleneck is not more site scoring. It is contact intelligence.

DemandGrid needs to know:
- who the lead actually is
- how to reach them
- what already happened
- what the AI should do next

## Core Product Shift

Split the system into three layers:

1. Property truth
- parcel, address, building, permit, trigger, economics

2. Contact intelligence
- owner identity
- business identity
- mailing address
- registered agent
- phone/email when available
- contactability confidence

3. Sales memory
- touches
- objections
- follow-up timing
- won/lost reasons
- realized revenue and profit

Property truth tells the model what the site is.

Contact intelligence tells the model who to work.

Sales memory tells the model what to do next.

## What To Build First

### P0: Free/public residential and property stack

Best immediate New England sources:

1. Massachusetts parcel and address base
- MassGIS Property Tax Parcels: https://www.mass.gov/info-details/massgis-data-property-tax-parcels
- MassGIS Master Address Data: https://www.mass.gov/info-details/massgis-data-master-address-data
- Best fields:
  - owner name
  - owner mailing address
  - site address
  - assessed values
  - land use / zoning
  - year built
  - parcel geometry

2. Connecticut statewide parcel/CAMA
- CT Parcel and CAMA: https://portal.ct.gov/datapolicy/gis-office/parcel-and-cama
- Best fields:
  - ownership
  - boundaries
  - usage / land use
  - sales
  - valuations
  - parcel join keys

3. New Hampshire parcel mosaic
- NH GRANIT parcels: https://granitweb.sr.unh.edu/MetadataForViewers/CommonViewers/lite/Parcels.html
- Best fields:
  - owner
  - mailing address
  - E911 address
  - parcel identifiers
  - valuation
  - homestead / non-residential indicators

4. Boston property + permit layer
- Property data: https://www.boston.gov/departments/assessing/property-data-and-information
- Historical permit records: https://www.boston.gov/departments/inspectional-services/how-find-historical-permit-records
- Best fields:
  - ownership
  - assessed value
  - abutter mailing list
  - property record cards
  - permit history

5. Cambridge parcel + permit layer
- City data sources: https://www.cambridgema.gov/CDD/factsandmaps/othercitydatasources
- Permit Finder dataset: https://www.cambridgema.gov/Departments/opendata/News/2026/04/cambridgepermitfinderdatasetandinteractivedashboardnowavailable
- Best fields:
  - owner / parcel facts
  - assessed value
  - address-based permit history

6. Universal trigger layers
- FEMA flood maps: https://msc.fema.gov/portal
- FEMA flood map overview: https://www.fema.gov/flood-maps
- NOAA Storm Events: https://www.ncei.noaa.gov/stormevents/
- Best fields:
  - flood exposure
  - storm / hail / wind / flood history
  - date and severity context

Practical output from this stack:
- owner name
- mailing address
- site address
- parcel ID
- occupancy proxy
- permit trigger context
- storm/flood context

That is enough to materially improve routing, suppression, and homeowner targeting before buying any paid contact vendor.

### P0: Free/public commercial identity stack

Best first commercial sources:

1. State business registries
- Massachusetts Corporations Search: https://corp.sec.state.ma.us/CorpWeb/CorpSearch/CorpSearch.aspx
- New Hampshire online business services: https://sos.nh.gov/corporation-ucc-securities/corporation/online-business-services
- Rhode Island Business Data Hub: https://www.sos.ri.gov/divisions/business-services/business-data-hub
- Best fields:
  - legal entity name
  - formation / status
  - principal office
  - registered agent
  - mailing address
  - officer / manager names when exposed

2. SEC EDGAR
- Search and access: https://www.sec.gov/edgar/search-and-access
- API docs: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- Best fields:
  - company name
  - address
  - phone
  - SIC / industry
  - filing history

3. Census business geography
- County Business Patterns overview: https://www.census.gov/programs-surveys/cbp.html
- CBP API: https://www.census.gov/programs-surveys/cbp/data/api.html
- Best fields:
  - establishment counts
  - employment
  - payroll
  - NAICS by ZIP/county

4. SBA Dynamic Small Business Search
- Search help: https://dsbs.sba.gov/search/dsp_search-help.cfm
- Best fields:
  - small-business profile
  - NAICS
  - ownership / certification
  - capability context

5. Local permit / licensing / registration portals
- Boston permits and licenses: https://www.boston.gov/boston-permits-and-licenses
- Boston business certificate process: https://www.boston.gov/departments/city-clerk/how-apply-business-certificate
- Best fields:
  - operating address
  - business certificate data
  - permit / license status
  - application timing

Practical output from this stack:
- business identity
- site occupancy confirmation
- legal contact path
- registered agent path
- industry / lane fit
- permit-triggered timing

### P1: Paid enrichment later

Use paid vendors only after the free/public layer is flowing.

Recommended first paid options:

1. Property-heavy owner/contact resolution
- ATTOM ownership data: https://www.attomdata.com/data/property-ownership-data/
- Regrid parcel API: https://regrid.com/api
- BatchData contact enrichment: https://batchdata.io/contact-enrichment

2. B2B person/company enrichment
- Apollo people enrichment: https://docs.apollo.io/reference/people-enrichment
- Apollo organization enrichment: https://docs.apollo.io/reference/organization-enrichment
- People Data Labs person enrichment: https://docs.peopledatalabs.com/docs/person-enrichment-api
- People Data Labs company enrichment: https://docs.peopledatalabs.com/docs/company-enrichment-api

3. Higher-end commercial identity
- Dun & Bradstreet Direct+: https://directplus.documentation.dnb.com/html/guides/Enrich/Enrich.html

Rule:
- do not buy multiple vendors at once
- start with one property-focused vendor and one B2B/contact vendor only if the public layer is already producing useful targets

## Data Model Changes

The current schemas are still too thin on lead identity.

`schema/sales-core.schema.json` and `schema/revenue-graph.schema.json` treat contact as a shallow proxy.

That is not enough for an AI sales system.

### Add `lead_contact`

New normalized contact record:

- `contact_id`
- `account_id`
- `site_id`
- `entity_type`
- `role`
- `display_name`
- `first_name`
- `last_name`
- `organization_name`
- `owner_occupancy`
- `residency_confidence`
- `preferred_channel`
- `contactability_score`
- `contactability_label`
- `do_not_contact`
- `primary_phone`
- `phone_numbers[]`
- `primary_email`
- `emails[]`
- `mailing_address`
- `best_contact_window`
- `dedupe_key`
- `identity_sources[]`
- `source_record_ids[]`
- `verified_at`
- `freshness_days`

### Add `lead_interaction`

Unified interaction history:

- `interaction_id`
- `site_id`
- `contact_id`
- `account_id`
- `channel`
- `direction`
- `interaction_type`
- `started_at`
- `ended_at`
- `result_status`
- `objection`
- `reason`
- `transcript_excerpt`
- `note`
- `script_id`
- `playbook_id`
- `orchestrator_run_id`
- `outreach_job_id`
- `calling_session_id`
- `outcome_id`
- `next_follow_up_at`
- `next_best_action`
- `rep_id`
- `agent_id`
- `attribution_signal_keys[]`

### Add `lead_next_action`

Explicit AI operator contract:

- `site_id`
- `contact_id`
- `account_id`
- `action_type`
- `action_rank`
- `reason`
- `confidence`
- `recommended_channel`
- `recommended_script_angle`
- `recommended_timing`
- `recommended_sequence_step`
- `expected_value_usd`
- `risk_flags[]`
- `review_required`
- `policy_decision`
- `source_refs[]`
- `generated_at`
- `expires_at`

## API / UI Implications

Priority API additions:
- `GET /api/v1/contacts/{contact_id}`
- `PUT /api/v1/contacts/{contact_id}`
- `GET /api/v1/contacts/{contact_id}/timeline`
- `POST /api/v1/interactions`
- `GET /api/v1/interactions?site_id=...`
- `GET /api/v1/lead/{site_id}/next-action`
- `GET /api/v1/lead/{site_id}/contactability`
- `POST /api/v1/lead/{site_id}/resolve-identity`

Priority UI additions:
- contact card before economics
- interaction timeline before long-form analysis
- explicit next-best-action block
- one recommended channel
- one recommended script angle
- one follow-up deadline

Manager mode should evolve from:
- best site

to:
- best site
- best contact on that site
- exact action to take
- exact channel to use
- exact follow-up timing

## Recommended Build Order

1. Add persistent `lead_contact` storage and real identity-resolution fields.
2. Add persistent `lead_interaction` storage and write every touch into it.
3. Expand `sales-core` and `revenue-graph` contracts to include real contactability and next-best-action state.
4. Build one unified `GET /api/v1/lead/{site_id}/next-action` endpoint for manager mode and the detail card.
5. Add public-record adapters for:
   - MassGIS
   - CT parcel/CAMA
   - NH GRANIT parcels
   - Boston property + permits
   - Cambridge parcel + permits
   - state SOS business registries
6. Add one property/contact paid enrichment vendor only after the public-record layer is stable.
7. Use interactions and outcomes to re-rank by actual close behavior, not just property proxies.

## Blunt Read

DemandGrid already has enough property intelligence to be useful.

The next multiplier is:
- better lead identity
- better contactability
- better sales memory

If only one thing gets built next, it should be:
- `lead_contact`
- `lead_interaction`

That is the minimum data layer required for AI to stop acting like an assistant and start acting like the operator brain.
