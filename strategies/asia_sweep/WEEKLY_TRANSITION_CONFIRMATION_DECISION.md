# Asian Sweep Weekly-Transition Continuation — Confirmation Decision

Date: 2026-07-26  
Decision: `FAIL_WEEKLY_TRANSITION_CONFIRMATION_STOP`  
Confirmation: EURUSD and GBPUSD, 2020–2022  
Warm-up: 2019 only  
Final holdout: 2023–2025 unopened

## Authoritative evidence

- GitHub Actions run: `30215668140`;
- evaluated head: `c06c5ab925cb5c47d6a0311d4fa195bc5f0cfa8c`;
- artifact: `asia-sweep-weekly-transition-confirmation`;
- artifact digest: `sha256:fe5cb421174d9d4969d4e0707de4978af441c5cb81f95aaaa9fd25443399f1e5`;
- all tests, lint, source isolation, pair reconstruction, target construction and aggregation completed successfully;
- the run failed only at the deliberate scientific authorization step;
- the downstream 2023–2025 final-holdout job was skipped.

## Protected-data integrity

The confirmation workflow created pair-specific source directories containing exactly:

- 2019 BID/ASK files for causal warm-up;
- 2020, 2021 and 2022 BID/ASK files for confirmation.

The workflow explicitly rejected any 2023–2025 file in the confirmation directories. The final-holdout job depended on a complete confirmation pass and therefore never started.

## Reconstruction census

| Pair | Enriched T0 events | Enriched target rows | Transition events | Reference events | Transition events by year |
|---|---:|---:|---:|---:|---|
| EURUSD | 690 | 3,449 | 22 | 41 | 2020: 1; 2021: 9; 2022: 12 |
| GBPUSD | 716 | 3,578 | 18 | 31 | 2020: 5; 2021: 8; 2022: 5 |
| **Pooled** | **1,406** | **7,027** | **40** | **72** | **2020: 6; 2021: 17; 2022: 17** |

The 40-event transition population met the frozen pooled sample minimum and contained 22 EURUSD and 18 GBPUSD events.

## Primary target

Primary: `EXT_OPPOSING_LIQUIDITY_1400`

| Metric | Confirmation result | Frozen requirement | Result |
|---|---:|---:|---|
| Events | 40 | >= 40 | Pass |
| Positives | 6 | >= 10 | **Fail** |
| Minimum events per pair | 18 | >= 15 | Pass |
| Hit rate | 15.00% | — | — |
| Reference hit rate | 12.50% | — | — |
| Absolute hit-rate lift | +2.50 pp | >= +3.00 pp | **Fail** |
| Mean stressed EV | -0.304R | > 0R | **Fail** |
| Reference mean stressed EV | -0.448R | — | — |
| Mean-EV lift | +0.144R | >= +0.150R | **Fail** |
| Median stressed R:R | 4.065R | >= 2.50R | Pass |
| Events retaining >=1.25R | 100% | >= 90% | Pass |
| Positive-EV pairs | 0 of 2 | 2 of 2 | **Fail** |
| Positive-EV years | 1 of 3 | >= 2 of 3 | **Fail** |
| Pair concentration | 55.0% | <= 70% | Pass |
| Year concentration | 42.5% | <= 50% | Pass |
| Bootstrap probability EV > 0 | 14.4% | >= 80% | **Fail** |
| Bootstrap 10th percentile | -0.698R | > -0.10R | **Fail** |
| Fixed-4R corroboration | -0.267R | > 0R | **Fail** |

## Pair and year attribution

### Pairs

| Pair | Events | Positives | Hit rate | Mean stressed EV | Median stressed R:R |
|---|---:|---:|---:|---:|---:|
| EURUSD | 22 | 3 | 13.64% | -0.354R | 4.163R |
| GBPUSD | 18 | 3 | 16.67% | -0.244R | 4.065R |

Both pairs were negative. The result is not caused by one pair overwhelming the other.

### Years

| Year | Events | Positives | Hit rate | Mean stressed EV |
|---|---:|---:|---:|---:|
| 2020 | 6 | 0 | 0.00% | -1.000R |
| 2021 | 17 | 2 | 11.76% | -0.612R |
| 2022 | 17 | 4 | 23.53% | +0.248R |

The isolated positive result in 2022 cannot rescue the frozen three-year confirmation. Selecting 2022 after inspection would be a prohibited year-regime rescue.

## Diagnostic targets

| Target | Events | Positives | Hit rate | Mean stressed EV | EV lift vs reference | Bootstrap P(EV>0) |
|---|---:|---:|---:|---:|---:|---:|
| Fixed 2R by 11:00 | 40 | 10 | 25.00% | -0.267R | -0.081R | 11.28% |
| Fixed 3R by 12:00 | 40 | 6 | 15.00% | -0.411R | +0.045R | 6.63% |
| Fixed 4R by 14:00 | 40 | 6 | 15.00% | -0.267R | +0.124R | 19.97% |
| Opposing liquidity by 14:00 | 40 | 6 | 15.00% | -0.304R | +0.144R | 14.40% |
| Opposite boundary by 11:00 | 40 | 4 | 10.00% | -0.573R | +0.087R | 1.50% |

No target produced positive pooled EV. No diagnostic target can replace or rescue the failed primary target under the frozen contract.

## Scientific interpretation

The 2015–2019 descriptive discovery did not replicate in untouched 2020–2022 data.

The transition condition still modestly improved hit rate and EV relative to a broader countertrend-continuation reference, but the improvement was insufficient and the absolute economics remained strongly negative. This distinction matters:

- the weekly-transition label contains some information;
- that information does not create an executable T0 strategy under the tested stop and target geometry;
- the discovery-period positive expectancy was not stable out of sample.

The positive 2022 slice is too small and arrived after two negative years. It is evidence of instability, not authorization for a volatility, year or macro-regime rescue.

## Binding decision

`FAIL_WEEKLY_TRANSITION_CONFIRMATION_STOP`

Consequences:

- 2023–2025 remains unopened;
- no final or combined holdout is run;
- no execution-P&L reconstruction is authorized;
- no target, threshold, weekday, pair, direction, phase, stop or year rescue is permitted;
- no Pine, alerts, paper trading, sizing or deployment is authorized;
- this weekly-transition continuation programme is closed.

## Programme-level conclusion

Across the completed weekly-profile research:

1. early-week retracement did not improve reversal back toward the old HTF trend;
2. Monday/Tuesday retracement continuation was sparse and negative;
3. the later weekly-transition continuation effect looked promising in 2015–2019 discovery data but failed untouched 2020–2022 confirmation.

The weekly-profile insight is descriptively valid, but the current Asian Sweep entry, stop and target architecture does not convert it into a stable executable edge.