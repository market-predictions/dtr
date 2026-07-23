# Work Package — NQ Long-Only Mechanism and Futures Replication

Work package: `STOIC123-WP-20260723-02`
Date opened: 2026-07-23
Date closed: 2026-07-23
Branch: `agent/stoic-nq-long-only-validation`
Status: `COMPLETE_NO_PROMOTION`

## Strategic question

Does the exploratory long-only result represent a genuine Stoic 1-2-3 continuation effect, or merely generic Nasdaq long drift, altered exit behavior, or CFD-proxy-specific evidence?

## Root-cause correction

The informal long-only counterfactual disabled short entries and opposite short management signals. This package corrected the contract so entry direction may be restricted while the management detector remains two-directional.

## Frozen source

- NQ futures research archive.
- SHA-256: `8d3f157a422636e5b8dda51cc3a3d9209c50cb53f9b279d3e14b627ce59370dc`.
- Period: 2022-12-26 18:00 ET through 2025-12-10 23:58 ET.
- 1,047,382 rows.
- Continuous-contract roll and exact timestamp semantics remain unresolved.
- Raw data remained outside Git and were removed before artifact upload.

## Frozen candidates and controls

Candidates:

1. `S123_M0_NO_MAP_CONTROL`;
2. `S123_M1_EMA_MAP`;
3. `S123_C1_STRICT_CLOSE`;
4. `S123_M3_EMA_PLUS_BREAKOUT`.

Controls and tests:

- both-direction, long-only, and short-only full sequences;
- EMA break only;
- EMA break plus retest;
- 50 deterministic matched-time controls;
- one-tick baseline and two-tick stress;
- one-minute and five-minute delays;
- annual, expanding-year, RTH/overnight, concentration, exposure, and date-block inference;
- nine all-required numerical gates;
- matched-control holding-period, coverage, and p95 veto.

## Execution

Workflow run: `30036385787`
Artifact SHA-256: `92f747b5ae07d252abb4bb0720b3aeaab8f3ebb3264ac27310425b4918c2a6e9`

The workflow passed:

- Ruff;
- 28 focused validation and Stoic tests;
- exact source and phase-one checksum preflight;
- complete scenario execution;
- final matched-control veto;
- raw-data removal and no-raw-data artifact gate;
- compact artifact upload.

Full repository CI passed on the final validation implementation.

## Results

- No-map: 555 long trades, +75.71R, +0.136R expectancy, 4/9 gates.
- EMA map: 252 long trades, -1.83R, -0.007R expectancy, 2/9 gates.
- Strict close: 226 long trades, +10.97R, +0.049R expectancy, 4/9 gates.
- EMA plus breakout: 147 long trades, +41.56R, +0.283R expectancy, 5/9 gates.
- Every 95% date-block interval crossed zero.
- No arm passed every numerical gate.
- All four arms were vetoed by the matched-control contract.

## Independent review

All 32 scenario trade ledgers were independently reconstructed. Trade counts, net R, expectancy, direction, chronology, positive risk, and non-overlap passed. All 36 numerical gate results were independently reproduced. The final matched-control veto was verified against the frozen 90% event-coverage rule.

## Decision

`NO_PROMOTION_STOP_NQ_LONG_ONLY_CURRENT_SAMPLE`

- Reject EMA-map long-only on actual NQ futures.
- Do not promote strict close or EMA plus breakout.
- Do not retune the current sample.
- Preserve the observed no-map short-side asymmetry only as a post-hoc fresh-data hypothesis.
- Keep Pine, sizing, alerts, paper deployment, and live use blocked.

## Restrictions retained

- No DTR changes.
- No pooled instrument result.
- No same-sample parameter, timeframe, session, delay, stop, target, exit, or matched-control redesign.
- No deployment or profitability authorization.
