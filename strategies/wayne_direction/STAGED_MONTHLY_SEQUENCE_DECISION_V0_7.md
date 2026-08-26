# Wayne Staged Monthly Sequence — Decision v0.7

Date: 2026-07-27

## Authoritative evidence

Pair construction run: `30253362740`  
Pair-construction head: `2617b9b7c011d8a2fcef1409d94fd430ff0b4b55`  
Corrected clustered aggregate run: `30254100112`  
Corrected aggregate head: `eec0f53a6d17ae67df5034bf9ff95861d4ebb9a1`  
Corrected artifact: `wayne-staged-monthly-sequence-clustered-decision`  
Artifact digest: `sha256:4c2a3a31f9e4e6588df0fbafbd6f5f8dec127135b3c23c4ec7a657379c45a38a`

## Binding decision

`FAIL_STAGED_SEQUENCE_PRIMARY_SAMPLE`

The frozen day-5 primary sequence did not produce enough completed opportunities for promotion. The day-10 development sensitivity produced a strong conservative-target association, but it also failed its frozen sample gate and cannot authorize macro, regime, seasonality, execution or deployment work.

## Population and causal sequence

- instruments: AUDUSD, EURUSD, GBPUSD, USDCAD, USDCHF and USDJPY;
- development period: 2015–2021 only;
- primary location: month open or completed H4 close in M2–P for bullish and P–M3 for bearish;
- sequence: location → new H4 structural turn → aligned stable/expanding H4 EMA21/55/200 state;
- final confirmation must occur by pivot day 5 for the primary test or day 10 for the labeled sensitivity;
- targets touched before or on the fixed landmark are unavailable;
- treatment-control reach starts after the fixed landmark;
- no D1/H4 threshold, target or time-window search was performed.

The pooled ledger contains:

- 3,128 target-level rows;
- 1,564 unique side-specific opportunities;
- 764 primary `CLOSE_IN_ZONE` opportunities;
- 800 labeled `RANGE_TOUCH` opportunities;
- zero duplicate instrument × opportunity × target-tier rows;
- exactly the six frozen pairs and seven frozen years.

## Primary day-5 census

There were 15 active primary completions:

| Pair | Active day-5 sequences |
|---|---:|
| AUDUSD | 4 |
| EURUSD | 4 |
| GBPUSD | 3 |
| USDCAD | 2 |
| USDCHF | 1 |
| USDJPY | 1 |
| **Pooled** | **15** |

The gate required 50 pooled opportunities, at least five in four pairs, at least 30 still-available conservative-target treatment observations and at least 100 controls.

Observed available conservative-target treatment count: 11.  
Observed available control count: 730.  
Pair breadth at five events: zero.

The primary sample gate therefore failed on every treatment-side requirement.

## Day-10 sensitivity census

There were 36 active primary-location completions by day 10:

| Pair | Active day-10 sequences |
|---|---:|
| AUDUSD | 9 |
| EURUSD | 7 |
| GBPUSD | 10 |
| USDCAD | 3 |
| USDCHF | 4 |
| USDJPY | 3 |
| **Pooled** | **36** |

The sensitivity gate required 80 pooled opportunities, at least eight in four pairs, at least 40 still-available conservative-target treatment observations and at least 120 controls.

Observed available conservative-target treatment count: 25.  
Observed available control count: 674.  
Pair breadth at eight events: two.

The sensitivity sample gate therefore also failed.

## Corrected planned comparisons

Permutation inference preserves complete treatment bundles within same-size instrument-month clusters and remains stratified by instrument-year.

| Test | Treatment N | Control N | Treatment reach | Control reach | Lift | Clustered p | BH q |
|---|---:|---:|---:|---:|---:|---:|---:|
| Day 5 conservative | 11 | 730 | 45.45% | 18.08% | +27.37 pp | 0.1192 | 0.1589 |
| Day 5 stretch | 11 | 744 | 27.27% | 10.75% | +16.52 pp | 0.3027 | 0.3027 |
| Day 10 conservative | 25 | 674 | 48.00% | 12.31% | +35.69 pp | 0.0002 | 0.0008 |
| Day 10 stretch | 31 | 705 | 19.35% | 8.23% | +11.13 pp | 0.0518 | 0.1036 |

The day-5 results are neither sufficiently sampled nor statistically reliable after clustered correction.

The day-10 conservative result is large, survives clustered permutation and is positive in five eligible pairs and five eligible years. It remains exploratory because:

- only 25 available treatment observations exist;
- only two pairs reach the frozen eight-event breadth floor;
- the ten-day window was explicitly sensitivity-only;
- the primary day-5 test failed;
- EURUSD has a negative day-10 conservative effect;
- the result has not been replicated on an independent instrument panel or locked period.

## Stage hierarchy at day 10

For conservative targets that remained available after day 10:

| Day-10 stage | N | Month-end reach |
|---|---:|---:|
| Complete and active | 25 | 48.00% |
| Pre-existing aligned | 119 | 19.33% |
| Complete but decayed | 23 | 17.39% |
| Location only | 448 | 10.94% |
| Structure without healthy MAs | 45 | 8.89% |
| Structure failed | 39 | 7.69% |

This ordering supports the staged causal interpretation. A newly completed and still-active H4 structure-plus-health sequence is materially different from merely having an old trend state or location alone.

## Concentration diagnostics

Among the 36 active day-10 opportunities:

- bullish: 22;
- bearish: 14;
- month-open location: 30;
- later H4-close location: 6;
- MA health on the structure-confirmation bar: 15;
- MA health strictly later: 21;
- D1 relation at location: 6 aligned, 21 neutral/no D1 direction and 9 opposed.

The result is not dependent on same-bar MA confirmation. It is also not evidence that aligned D1 structure should become mandatory: most active opportunities did not have aligned D1 structure, and the tiny D1-aligned subset did not outperform.

Pair-level day-10 conservative treatment reach:

| Pair | Available treatment N | Reached | Rate |
|---|---:|---:|---:|
| AUDUSD | 5 | 4 | 80.00% |
| EURUSD | 4 | 0 | 0.00% |
| GBPUSD | 7 | 3 | 42.86% |
| USDCAD | 3 | 1 | 33.33% |
| USDCHF | 3 | 2 | 66.67% |
| USDJPY | 3 | 2 | 66.67% |

These cells are too small for pair-specific trading rules.

## Interpretation

The research supports three conclusions:

1. The simultaneous month-open conjunction was correctly rejected. Structure and MA health need time to develop after monthly location.
2. Five pivot days are generally too short for the full sequence. Only 15 active completions occurred across 42 pair-years.
3. An unchanged ten-day sequence is a credible replication hypothesis, but not a validated edge or executable strategy.

The correct response is not to loosen structural confirmation, weaken MA health, count pre-consumed targets or extend the window again. Those actions would convert a sample limitation into post-outcome optimization.

## Roadmap consequence

- freeze the exact day-10 sequence unchanged as `REPLICATION_CANDIDATE`;
- do not promote it on the current six-pair development population;
- qualify an independent, broader liquid-FX panel before opening outcomes;
- preserve 2022–2025 as locked chronological confirmation rather than using it to rescue development sample;
- allow macro/regime point-in-time source engineering, but keep macro/regime/seasonality outcome integration closed;
- keep daily-pivot optimization archived;
- keep execution, Pine, alerts, sizing and deployment blocked.

## Artifact hashes

- decision JSON: `521d34d087e4dda2809a1c21326510e705a90c516075311bf4d53a3cc7f55e57`;
- planned comparisons: `58554252e4898cf0ae14cf5bb12111386ab4e8e516eebfb7720b6f2c3e322183`;
- pooled ledger: `53776496e7a815fe158bcc1baaf82342f90a787082f065d45432fd025d751c97`;
- primary stage census: `8ca20c684d3f2d34d8f0dcb63fcf448e791ac7df64f96eda58769baa1c15f1bb`;
- sensitivity stage census: `d4e2c6207f461fa01a9fa7e4ed1a3e72d80713a23999262fd12a7f81726b66aa`;
- day-5 signal reach: `e28e03880856aaaba3c450fe8eb7713c07005684ac9b9e43c6324c16f17d1e4b`;
- day-10 signal reach: `77537b1596d94e1d1cbd7abae31e3c501d8f1d291c13036372d9f6c960a331e3`.
