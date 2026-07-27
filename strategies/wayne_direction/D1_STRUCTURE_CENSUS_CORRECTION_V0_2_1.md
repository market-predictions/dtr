# Wayne Direction-First D1 Structural Census — Correction v0.2.1

Date: 2026-07-27  
Authoritative corrected run: `30227738020`  
Evaluated head: `5bf382c60537bc2cf592136f6198759206199266`  
Artifact: `wayne-direction-first-census`  
Artifact digest: `sha256:ee1ef45f0f4206dcbe2d3272a9dd3bab4ceeccba48b4cce7c42724dad192cbcf`

## Correction

The original v0.2 census compared the continuation higher high/lower low with the BOS candle extreme. The source-faithful rule requires comparison with the full pre-retest impulse extreme.

The engine now:

- initializes the impulse extreme on the BOS bar;
- extends that extreme on every subsequent completed bar before the first retest;
- freezes the extreme when the retest begins;
- requires the final continuation close to exceed that frozen impulse extreme plus the 0.05 ATR buffer.

A regression test proves that a close above the BOS candle but below the later impulse extreme does not confirm the trend.

## Corrected decision

`FAIL_STRUCTURE_CENSUS_REVIEW_DEFINITION`

The corrected population contains 79 complete D1 trend starts:

| Pair | Bull | Bear | Total |
|---|---:|---:|---:|
| AUDUSD | 7 | 10 | 17 |
| EURUSD | 6 | 8 | 14 |
| GBPUSD | 7 | 5 | 12 |
| USDCAD | 9 | 3 | 12 |
| USDCHF | 10 | 6 | 16 |
| USDJPY | 4 | 4 | 8 |
| **Pooled** | **43** | **36** | **79** |

The original census contained 83 events. Four borderline events were removed by the stricter impulse reference. The preregistered requirement remained 300 pooled events and at least 40 events in four pairs; no pair reached 40.

## Corrected structural funnel

Bullish:

- 196 double bottoms;
- 79 breaks of structure;
- 70 retests;
- 56 confirmed higher lows;
- 43 continuation higher highs.

Bearish:

- 174 double tops;
- 75 breaks of structure;
- 63 retests;
- 51 confirmed lower highs;
- 36 continuation lower lows.

## Temporal breadth

| Year | Bull | Bear | Total |
|---|---:|---:|---:|
| 2015 | 5 | 4 | 9 |
| 2016 | 8 | 5 | 13 |
| 2017 | 6 | 5 | 11 |
| 2018 | 6 | 6 | 12 |
| 2019 | 9 | 5 | 14 |
| 2020 | 5 | 4 | 9 |
| 2021 | 4 | 7 | 11 |

All seven development years remain represented.

## H4 health at corrected D1 confirmation

- aligned expanding: 50 of 79;
- aligned stable: 19 of 79;
- aligned healthy total: 69 of 79, or 87.34%;
- mixed or conflicted: 10 of 79.

The stricter transition definition therefore increases, rather than weakens, the relationship between D1 structural confirmation and healthy H4 moving-average alignment.

## Persistence

- bullish runs: median 22 D1 bars, mean 56.86, maximum 348;
- bearish runs: median 45 D1 bars, mean 94.92, maximum 558.

D1 remains a slow strategic regime state.

## Corrected descriptive monthly reach

| Side | Zone | Target | Opportunities | Reached before D1 invalidation | Rate |
|---|---|---|---:|---:|---:|
| Bull | M2–P | M4 | 42 | 6 | 14.29% |
| Bull | M2–P | R2 | 42 | 3 | 7.14% |
| Bear | P–M3 | M1 | 61 | 14 | 22.95% |
| Bear | P–M3 | S2 | 61 | 10 | 16.39% |

These are descriptive path counts, not executable strategy results.

## Consequence

The original v0.2 artifact remains preserved as an audit record but is superseded for all future work by this corrected v0.2.1 census. The strategic conclusion is unchanged:

- retain D1 structure as long-horizon regime context;
- do not loosen the D1 thresholds to manufacture sample;
- use a faster current-direction layer for monthly opportunity timing;
- keep macro, regime, seasonality and execution outcomes closed until the technical sequencing is coherent.

## Corrected artifact hashes

- `wayne_direction_census_decision.json`: `d3cc54d7c4c4cdf7d462a11c0b7c2a2a4f271d1c97adb08616d37eedd6fa568a`;
- `wayne_direction_pair_census.csv`: `f83c031c43f376dcf6b6d6d65c2cb4dfeff3140e99f5ad61348f55ebf8ac3653`;
- `wayne_direction_confirmation_health.csv`: `eff0f34e9f8f7549e3296ec06825fe3ae5bde2c09e5d683142b19226e3f1cc36`;
- `wayne_direction_monthly_reach_summary.csv`: `609f8e26518c4d402cd69d1f006a14bd095a7f4c773c6ce7d9f927d1fb6843b5`;
- `wayne_direction_pooled_structure_ledger.csv`: `109670859abfa9362c3cc85463fc9a1236a76326985aa68e69b9d7addb46421d`;
- `wayne_direction_pooled_monthly_reach.csv`: `df1d64b051e4534769a436f7feb650cbfbd7b69b8e75a64c9451b463b924034d`.
