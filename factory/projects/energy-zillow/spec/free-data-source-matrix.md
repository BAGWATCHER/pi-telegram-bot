# DemandGrid — Free Data Source Matrix

## Purpose

This file narrows the research to free/public data sources that can improve the opportunity engine without requiring paid vendors.

Use this as the shared reference for future ingestion work.

## Priority Order

### 1. Building / geometry base layer

Best free sources:
- Microsoft US Building Footprints
- OpenStreetMap building footprints and address points
- Geofabrik OSM extracts

Why it matters:
- base geometry for solar, roofing, HVAC, battery, waterproofing, and commercial siting
- nationwide coverage
- good enough for screening when parcel-grade data is unavailable

What it unlocks:
- building footprint
- building size proxy
- roof area proxy
- commercial building candidate screening

Operational note:
- keep OSM as the active ingest baseline
- use Microsoft footprints as a geometry-upgrade option where OSM coverage is weak

Sources:
- Microsoft US Building Footprints: https://github.com/microsoft/USBuildingFootprints
- Geofabrik North America OSM downloads: https://download.geofabrik.de/north-america.html

### 2. Storm / hazard / flood layer

Best free sources:
- NOAA Storm Events Database
- FEMA National Risk Index
- FEMA National Flood Hazard Layer / Flood Map Service Center

Why it matters:
- first real urgency layer for roofing
- also useful for battery, waterproofing, restoration, and route prioritization after major events

What it unlocks:
- hail / thunderstorm wind / tornado history
- tract/county hazard exposure
- flood zone and flood hazard overlays

Operational note:
- NOAA Storm Events is the highest-priority non-solar source because it can power a roofing trigger quickly
- FEMA NRI is more coarse, but useful as a broad tract/county risk prior across many lanes
- NFHL is important where flood/waterproofing matters, but coverage is not fully uniform

Sources:
- NOAA Storm Events Database: https://www.ncei.noaa.gov/stormevents/
- NOAA Storm Events bulk CSV download: https://www.ncei.noaa.gov/stormevents/ftp.jsp
- FEMA National Risk Index: https://hazards.fema.gov/nri/
- FEMA National Risk Index data resources: https://hazards.fema.gov/nri/data-resources
- FEMA Flood Map Service Center: https://msc.fema.gov/portal
- FEMA NFHL database search: https://hazards.fema.gov/femaportal/NFHL/searchResulthttps%3A/hazards.fema.gov/femaportal/NFHL/searchResult

### 3. Utility territory / rate / outage-adjacent layer

Best free sources:
- OpenEI Utility Rate Database
- EIA Form 861 detailed data

Why it matters:
- improves solar economics
- improves battery economics
- improves electrification targeting
- helps route by energy pain, not just roof fit

What it unlocks:
- utility lookup by geography / EIA ID
- tariff and default-rate screening
- utility-level sales, revenue, customer, dynamic pricing, net metering, reliability, and program context

Operational note:
- OpenEI is the most useful free rate source for direct economics
- EIA-861 is broader and more operational; use it for utility/program/reliability context and utility mapping
- true address-level outage pain is still weak in the free stack

Sources:
- OpenEI utility rates API docs: https://apps.openei.org/services/doc/rest/util_rates/
- OpenEI U.S. Utility Rate Database: https://apps.openei.org/USURDB/
- EIA Form 861 detailed data: https://www.eia.gov/electricity/data/eia861/

### 4. Solar resource layer

Best free sources:
- NREL PVWatts
- NREL NSRDB

Why it matters:
- stronger solar production estimates
- better confidence calibration
- better battery adjacency scoring

What it unlocks:
- annual production estimates
- irradiance and weather resource context
- long-term solar resource downloads

Operational note:
- already aligned with the current scoring architecture
- keep this as the free solar-grade path before any paid roof-model vendors

Sources:
- PVWatts API: https://developer.nrel.gov/docs/solar/pvwatts/
- PVWatts V8 API: https://developer.nrel.gov/docs/solar/pvwatts/v8/
- NSRDB API: https://developer.nrel.gov/docs/solar/nsrdb/

### 5. Housing age / fuel / energy burden proxies

Best free sources:
- Census ACS 5-year API
- ACS table B25034 Year Structure Built
- DOE LEAD Tool
- EIA RECS

Why it matters:
- strongest free HVAC / heat pump signal stack
- helps identify older housing stock, fuel switching opportunities, and high-burden neighborhoods

What it unlocks:
- tract/block-group age profile
- tenure and housing type
- heating fuel type
- energy burden by geography

Operational note:
- this is not address-level equipment age
- still very useful for neighborhood targeting and close-probability proxies
- DOE LEAD is especially useful because it combines ACS + EIA calibration and exposes energy burden, building age, ownership, and heating fuel characteristics

Sources:
- Census ACS 5-year API overview: https://www.census.gov/data/developers/data-sets/acs-5year.2023.html
- Census ACS table B25034 Year Structure Built: https://data.census.gov/table/ACSDT5Y2020.B25034
- DOE LEAD Tool: https://www.energy.gov/scep/low-income-energy-affordability-data-lead-tool
- DOE LEAD FAQ/methodology details: https://www.energy.gov/scep/slsc/low-income-energy-affordability-data-lead-tool-frequently-asked-questions
- EIA RECS: https://www.eia.gov/consumption/residential/

### 6. Commercial territory selection layer

Best free sources:
- County Business Patterns
- BLS QCEW

Why it matters:
- useful for deciding where to hunt commercial roofing / HVAC / solar
- weaker for per-building scoring, stronger for territory selection

What it unlocks:
- business density
- industry mix
- establishment counts
- wages and employment by county / ZIP / industry

Operational note:
- use these for territory scoring and ZIP prioritization, not direct address ranking

Sources:
- County Business Patterns overview: https://www.census.gov/programs-surveys/cbp.html
- CBP downloadable datasets: https://www.census.gov/programs-surveys/cbp/data/datasets.html
- QCEW overview: https://www.bls.gov/cew/overview.htm
- QCEW downloadable/open data guide: https://www.bls.gov/cew/about-data/data-files-guide.htm

## Best Free Stack By Lane

### Roofing
- NOAA Storm Events
- FEMA National Risk Index
- OSM / Microsoft footprints

### Solar
- OSM / Microsoft footprints
- OpenEI utility rates
- NREL PVWatts
- NREL NSRDB

### HVAC / Heat Pump
- ACS building age
- DOE LEAD building age / heating fuel / tenure / burden
- EIA RECS for national priors

### Battery / Backup Power
- OpenEI rates
- EIA-861 reliability / dynamic pricing / net metering context
- FEMA hazard exposure
- later: a better outage source if found

### Waterproofing / Restoration
- FEMA NFHL
- FEMA National Risk Index
- NOAA storm/flood event history

### Commercial Expansion
- OSM / Microsoft footprints
- CBP
- QCEW
- OpenEI rates

## Recommended Ingestion Order

1. NOAA Storm Events
2. OpenEI utility rates
3. ACS + DOE LEAD tract-level age/fuel/burden proxies
4. FEMA NRI
5. FEMA NFHL
6. CBP / QCEW for commercial territory expansion

## Blunt Read

The best free stack is enough to materially improve:
- roofing
- solar
- HVAC / heat pump
- battery
- waterproofing
- commercial territory selection

The biggest free-data weakness remains true address-level:
- roof age
- HVAC equipment age
- owner contact / parcel-grade assessor fields
- precise outage history at the premise level

Those are the places where paid data will eventually matter.
