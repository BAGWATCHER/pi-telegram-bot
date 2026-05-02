# Tariff Impact Delta (vs pre-tariff baseline)

- generated_at: `2026-04-17T07:21:02Z`
- baseline: state + official + manual utility mapping, **without** site-level utility/tariff feed
- current: baseline + site-level utility/tariff feed (`data/processed/site_utility_tariff.csv`)
- sites compared: **61,834**
- non-zero rate delta: **53,965/61,834 (87.3%)**
- total annual savings delta: **$20,855,075**
- median annual savings delta per site: **$280**

## Rate delta distribution (USD/kWh)

- mean: `0.02400`
- median: `0.03402`
- p10 / p90: `0.00000` / `0.03402`
- min / max: `-0.07602` / `0.08242`

## Dominant rate-method transitions

- `state_official_fallback -> official_utility_override`: 53,965 sites
- `state_official_fallback -> state_official_fallback`: 4,429 sites
- `official_utility_override -> official_utility_override`: 3,440 sites

## Top ZIP annual savings deltas

- `01890`: total_delta=$1,844,480, avg_rate_delta=0.03402, non_zero=100.0%
- `02492`: total_delta=$1,509,519, avg_rate_delta=0.03402, non_zero=100.0%
- `02420`: total_delta=$1,430,869, avg_rate_delta=0.03402, non_zero=100.0%
- `02186`: total_delta=$1,423,025, avg_rate_delta=0.03402, non_zero=100.0%
- `01730`: total_delta=$1,238,830, avg_rate_delta=0.03402, non_zero=100.0%
- `02090`: total_delta=$897,417, avg_rate_delta=0.03402, non_zero=100.0%
- `02052`: total_delta=$867,072, avg_rate_delta=0.03405, non_zero=100.0%
- `01776`: total_delta=$802,323, avg_rate_delta=0.03402, non_zero=100.0%

## Top site annual savings deltas (absolute)

- `site_89d9104e5699` (06890, CT): delta=$2,404, rate=0.28300 -> 0.33480, utility=`United Illuminating Co`
- `site_dd5d72ba25a5` (06525, CT): delta=$2,363, rate=0.28300 -> 0.33480, utility=`United Illuminating Co`
- `site_2cfcefcb240c` (06824, CT): delta=$2,351, rate=0.28300 -> 0.33480, utility=`United Illuminating Co`
- `site_63e666cd335d` (06525, CT): delta=$2,286, rate=0.28300 -> 0.33480, utility=`United Illuminating Co`
- `site_4e9fefdeae1d` (06890, CT): delta=$2,272, rate=0.28300 -> 0.33480, utility=`United Illuminating Co`
- `site_0a25f523701a` (02052, NH): delta=$2,269, rate=0.26320 -> 0.34562, utility=`NSTAR Electric Company`
- `site_481b2fc6eb4d` (06525, CT): delta=$2,190, rate=0.28300 -> 0.33480, utility=`United Illuminating Co`
- `site_41ac2fecd7c7` (06890, CT): delta=$2,153, rate=0.28300 -> 0.33480, utility=`United Illuminating Co`

- machine-readable summary: `/home/ubuntu/pi-telegram-bot/factory/projects/energy-zillow/artifacts/tariff-impact-delta.json`
