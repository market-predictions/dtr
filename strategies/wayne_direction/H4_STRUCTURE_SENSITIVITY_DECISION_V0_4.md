# Wayne Direction-First H4 Structural Sensitivity — Decision v0.4

Date: 2026-07-27  
Authoritative run: `30227738024`  
Evaluated head: `5bf382c60537bc2cf592136f6198759206199266`  
Artifact: `wayne-h4-direction-sensitivity`  
Artifact digest: `sha256:7fbda62274f61c95f91a755e4e481ebee79eaca736da7b9fa67394fe358f5106`

## Binding decision

`FAIL_H4_MONTHLY_ALIGNMENT_SAMPLE_REVIEW`

The H4 transition-count gate passed. The simultaneous month-open alignment gate failed.

## H4 transition census

| Pair | Bull | Bear | Total |
|---|---:|---:|---:|
| AUDUSD | 41 | 34 | 75 |
| EURUSD | 34 | 34 | 68 |
| GBPUSD | 37 | 46 | 83 |
| USDCAD | 40 | 39 | 79 |
| USDCHF | 45 | 46 | 91 |
| USDJPY | 39 | 40 | 79 |
| **Pooled** | **236** | **239** | **475** |

All six pairs exceeded 40 confirmations. The frozen transition gate of 300 pooled confirmations and four-pair breadth therefore passed.

Every development year from 2015 through 2021 contributed between 55 and 78 confirmations.

## Structural funnel

Bullish:

- 1,057 double bottoms;
- 452 breaks of structure;
- 382 retests;
- 324 confirmed higher lows;
- 236 continuation higher highs.

Bearish:

- 1,105 double tops;
- 474 breaks of structure;
- 395 retests;
- 334 confirmed lower highs;
- 239 continuation lower lows.

## H4 moving-average health

At the structural confirmation bar:

- 54 bullish expanding and 26 bullish stable;
- 62 bearish expanding and 34 bearish stable;
- 176 of 475 confirmations, or 37.05%, had aligned healthy H4 averages.

H4 structure frequently confirms before EMA21/55/200 have fully reordered and diverged.

H4 structural runs remained persistent:

- bullish median 30.5 H4 bars, mean 85.05, maximum 1,158;
- bearish median 33 H4 bars, mean 72.79, maximum 647.

## Monthly-zone alignment

There were 486 unique monthly-zone months.

| H4 state at month open | Months |
|---|---:|
| Aligned structure and healthy MAs | **0** |
| Aligned structure but unhealthy MAs | 53 |
| No H4 direction | 210 |
| Opposite H4 direction | 223 |

Every pair had zero `ALIGNED_HEALTHY` months. The gate required 80 pooled months and at least 10 in four pairs, so it failed with zero observations.

The zero is coherent rather than a coding defect. A monthly buy zone commonly occurs during a bullish pullback, when bullish structure may still exist but H4 averages are compressed or conflicted. Healthy bullish H4 averages more often coincide with price already being in the upper monthly zone. The bearish case mirrors this.

## Descriptive month-end reach

These are development diagnostics, not strategy results.

| H4 state | Side | Target | N | Rate |
|---|---|---|---:|---:|
| Aligned but unhealthy | Bull | M4 | 31 | 38.71% |
| Aligned but unhealthy | Bull | R2 | 31 | 29.03% |
| Aligned but unhealthy | Bear | M1 | 22 | 36.36% |
| Aligned but unhealthy | Bear | S2 | 22 | 22.73% |
| No H4 direction | Bull | M4 | 109 | 19.27% |
| No H4 direction | Bull | R2 | 109 | 11.01% |
| No H4 direction | Bear | M1 | 101 | 26.73% |
| No H4 direction | Bear | S2 | 101 | 17.82% |
| Opposite H4 direction | Bull | M4 | 102 | 17.65% |
| Opposite H4 direction | Bull | R2 | 102 | 6.86% |
| Opposite H4 direction | Bear | M1 | 121 | 19.83% |
| Opposite H4 direction | Bear | S2 | 121 | 6.61% |

The strongest descriptive group is aligned H4 structure with not-yet-healthy MAs. Its sample is only 53 months, so this is a roadmap signal, not an authorized edge.

## Post-decision timing diagnostic

After the primary zero-at-open result, a non-preregistered diagnostic counted when a zone month first developed both aligned H4 structure and healthy H4 averages:

- within one trading day: 3 of 486;
- within three trading days: 12;
- within five trading days: 32;
- within ten trading days: 84;
- at any time in the month: 173.

These counts are exploratory. They show that the layers develop sequentially rather than simultaneously.

## Interpretation

The framework should be modeled as:

1. D1, macro, regime and seasonality provide strategic permission;
2. monthly pivots provide location;
3. H4 structure turns in the permitted direction;
4. H4 averages subsequently reorder and diverge;
5. reach is evaluated only after that completed confirmation.

The H4 structural definition has adequate sample and remains frozen. The failed month-open conjunction must not be rescued by loosening structure or MA thresholds.

## Consequences

- D1 remains strategic context;
- H4 remains the current structural transition layer;
- simultaneous month-open conjunction is rejected;
- MA health becomes a subsequent confirmation event;
- macro, regime, seasonality and execution outcomes remain closed;
- daily-pivot research stays archived;
- no Pine or deployment is authorized.

## Next valid study

Preregister a staged sequence:

- month opens in zone or touches it during the first five pivot days;
- H4 structural confirmation follows in the zone direction;
- H4 averages become stable or expanding afterward;
- evaluate monthly reach from the completed confirmation timestamp;
- use five pivot days as primary and ten days only as a labeled development sensitivity.

## Artifact hashes

- decision JSON: `f9f29f6c5532574cc158faede55fd5d8378ea791e5399dc858af8c3b02b14caa`;
- pair census: `7f3d7587c4e45140b3254b936c56b72d73d7013e5b7b1c1bb8f1159b156ff945`;
- confirmation health: `73b1016eebad708728c02406136fb920022028a8304227052d946ec24e6a7e13`;
- monthly categories: `f243fbbdd0a391647bfa3ad087a53380cc15b44ac14f78e8aed2753651cea2ed`;
- monthly reach: `8808ac34655c29921b30195c4efd7c43dc1922ee175b494e000ba1d7c1f58332`;
- pooled structure ledger: `2374384b17e760782c0f4f693589436b8d00ab2f70afa456d8286ff649eea876`;
- pooled attribution: `e6b2713a69caa93615efca329d11cd984bce28eaa32f7d0442f307322332947a`.
