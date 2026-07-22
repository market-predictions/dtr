# DTR Optimization Lab Status

## Current work package

`DTR-NQ-WP-20260722-19 — Six-step roadmap correction and Nasdaq-proxy validation`

Status: **timestamp and neutral-risk gates complete; proxy acquisition/OOS execution in progress**

## Evidence hierarchy

### Execution regression benchmark

`DTR_PY_NQ_CANDIDATE_0_1_CAUSAL_GAP`

- 495 trades;
- 86.004761R net;
- 0.173747R expectancy.

This bar-open-labelled result remains a historical execution regression only.

### Scientific NQ reference control

`DTR_CAUSAL_BAR_CLOSE_RANGE_SHIFT_MINUS1`

- 477 trades;
- 42.577515R net;
- 0.089261R expectancy;
- 16.426493R maximum drawdown.

The maintenance-boundary census supports bar-close labels: 732 normal `17:00 → 18:01` pairs, zero normal `16:59 → 18:00` pairs, and no candidate reopen at exactly 18:00. Decision: `SUPPORT_BAR_CLOSE_RETAIN_SHIFT_MINUS_ONE`.

### Frozen historical challenger

`E6_EXCLUDE_NEAR_PRIOR_DAY_DIRECTIONAL_EXTREME`

- 304 trades;
- 48.937550R net;
- 0.160979R expectancy.

E6 remains a historically suggestive challenger. It is not statistically promoted over the unfiltered reference.

### Working NQ policy candidate

`E6_NO_FOMC_DAY`

- 291 trades;
- 53.483342R net;
- 0.183792R expectancy.

This is the user-selected paper-research policy candidate, not a validated or deployment baseline. Original E6 and the unfiltered reference remain mandatory controls.

No deployment baseline exists.

## Neutral reference risk recalibration

Observed $100,000 account under normal costs:

- 0.50% risk: $122,595 final equity; 7.94% maximum drawdown.
- 1.00% risk: $147,582 final equity; 15.34% maximum drawdown.
- 1.50% risk: $174,491 final equity; 22.24% maximum drawdown.

At normal costs, the resampled probability of reaching a 20% drawdown is approximately:

- 0.50% risk: 1.0–1.5%;
- 1.00% risk: 32.4–33.7%;
- 1.50% risk: 77.3–77.8%.

At severe four-tick-per-side costs, 1.00% risk reaches 20% drawdown in approximately 60.7–61.7% of resamples. No live sizing authorization follows.

## Research freeze

Further 2023–2025 NQ threshold, weekday, session, event, entry, exit, sequencing, interaction and sizing searches are frozen. The original 904-selection chronology remains permanently unreconstructible from surviving artifacts.

## Nasdaq-proxy programme

Preregistered before 2026 performance inspection:

- acquire temporary Dukascopy `usatechidxusd` one-minute data from 2022-01-01 through 2026-07-23 end-exclusive;
- qualify timestamps, gaps, OHLC, DST conversion and session coverage;
- compare 2022–2025 NQ futures and proxy price movement, session structure and strategy decisions;
- run sealed 2026 proxy OOS arms: unfiltered reference, fixed E6, and fixed E6 no-FOMC;
- keep data and returns separate from NQ futures and delete raw proxy data after use.

This is Nasdaq-100 bid-CFD proxy evidence, not CME NQ futures validation.

## Existing unresolved gates

- authoritative vendor timestamp metadata: documentation limitation, while the working interpretation is resolved by census;
- NQ continuous-contract methodology: `UNRESOLVED`;
- qualified fresh CME NQ OOS comparison: `NOT_RUN`;
- 2026 Dukascopy Nasdaq-proxy OOS: `PREREGISTERED_IN_PROGRESS`;
- Python/Pine parity: `NOT_RUN`.

## Scope restrictions

No additional NQ in-sample optimization, proxy-specific retuning, pooled NQ/proxy portfolio, dynamic sizing, Pine port, live sizing recommendation, leverage increase or deployment is authorized.
