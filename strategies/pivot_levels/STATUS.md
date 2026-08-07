# Pivot Level Research Status

Date: 2026-08-07  
Work package: `PIV-WP-20260807-01`  
State: `COMPLETE_INTERNAL_GATE_FAIL`

## Binding decision

`NO_PIVOT_MECHANISM_PASSES_INTERNAL_GATE`

Classic floor pivots were tested as fresh targets, independent trend-leg endpoints, containment/stall zones and reversal zones across daily, weekly, monthly, quarterly and yearly horizons.

## Data

- registered Dukascopy FX Cache only;
- ten FX pairs;
- M1 separate BID/ASK source, deterministic H1 trend and M15 first-passage layers;
- development 2015–2019;
- validation 2020–2021;
- 2022–2025 remained unopened;
- no historic reacquisition.

## Main evidence

- PP fresh-touch likelihood is ~79–82% across daily/weekly/monthly/quarterly samples.
- R1/S1 are ~41–47%; R2/S2 ~15–19%; R3/S3 ~4–7%.
- Monthly/quarterly inner midlevels PP↔R1/S1 are ~72–74%.
- None of 20 real-pivot-minus-nearby-placebo primary tests passed the frozen internal gate.
- Weekly/monthly containment and monthly target completion were descriptively positive but statistically uncertain.
- Exact daily and weekly pivot coordinates showed slight negative endpoint clustering; neither passed familywise correction.

## Independent assurance

`PASS`

- 140 compressed source members independently rehashed;
- formula and DST-safe NY17 boundary checks passed;
- exact primary point estimates independently recomputed;
- independent 2,000-draw clustered bootstrap with a different seed confirmed no qualifying positive mechanism;
- holdout absence confirmed.

## Authorization boundary

Do not open 2022–2025, tune pivot formulas/tolerance/barriers, select favorable pairs, build execution P&L, or proceed to Pine/alerts/sizing/deployment from this study.

Pivots may be retained as a descriptive probabilistic reach ladder, not as proven privileged target or reversal coordinates.