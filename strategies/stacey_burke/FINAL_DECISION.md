# Stacey Burke FX Reversal Programme — Final Decision

Date: `2026-07-25`  
Version: `v0.3.0-gate-b-rejection`  
Decision: `FAIL_GATE_B_STOP_STACEY_BURKE_REVERSAL_PROGRAMME`

## Executive conclusion

The mechanically frozen previous-FX-day high/low sweep-and-reclaim hypothesis occurs frequently, but it does not produce a positive control-adjusted 60-minute reversal effect on the 2015–2021 discovery sample.

The event census passed with 2,423 retained events. The controlled study matched 2,393 observable events to 11,965 deterministic controls. The pooled event-minus-control effect was slightly negative, its date-blocked confidence interval crossed zero, its clustered permutation result was non-significant, and positive attribution was too narrow across pairs and factor blocks.

Under the preregistered rules, the Stacey Burke SB-1 reversal programme is rejected and closed. No threshold relaxation, alternate horizon, subgroup selection, strategy construction, validation run, holdout inspection, Pine conversion or deployment is authorized.

## Frozen research object

- Ten-pair factor-diverse FX universe.
- Dukascopy BID/ASK M1 data.
- Previous FX trading day defined 17:00–17:00 `America/New_York`.
- London study window 07:00–10:00 `Europe/London`.
- Previous-day high or low excursion of at least `0.05 × ATR20`.
- Non-resetting reclaim within 15 minutes.
- One retained event per instrument/session.
- Reversal-signed midpoint return exactly 60 minutes after reclaim.
- Five deterministic controls from distinct dates, matched within pair/year/weekday/15-minute London bucket on pre-event 15-minute return and trailing 60-minute realized volatility.

## Source and census gates

Source qualification passed for all ten instruments across 2015–2025 plus 2026 YTD.

The 2015–2021 event census passed all feasibility, breadth and concentration gates:

- pooled retained events: `2,423`;
- all ten pairs contributed;
- all four factor blocks contributed;
- largest pair share: `12.92%`;
- largest date share: `0.29%`.

Frozen aggregate census-ledger SHA-256:

`862ec9c28f6e8450b59f6a34da2571a4a3c25075013f11492be8cfc946653533`

## Controlled-study result

GitHub Actions workflow: `Stacey Burke Controlled Study`  
Run: `30148536476` / run number `1`  
Head: `f05645f9394b552ebb9573a41bb77db280781f70`

### Pooled evidence

| Metric | Result |
|---|---:|
| Census events | 2,423 |
| Matched observable events | 2,393 |
| Unmatched/unobservable events | 30 |
| Matched controls | 11,965 |
| Mean event outcome | `+0.000451 ATR20` |
| Mean control outcome | `+0.002159 ATR20` |
| Mean event-minus-control effect | `-0.001709 ATR20` |
| Calendar-date blocks | 1,256 |
| 95% date-block bootstrap interval | `[-0.010309, +0.006900] ATR20` |
| Bootstrap probability mean > 0 | `35.26%` |
| Date-clustered permutation p-value | `0.670733` |
| Positive pairs | `4 / 10` |
| Positive factor blocks | `1 / 4` |

### Pair attribution

| Pair | Matched events | Mean effect, ATR20 |
|---|---:|---:|
| AUDUSD | 214 | `+0.003039` |
| EURGBP | 304 | `-0.014138` |
| EURJPY | 252 | `-0.008778` |
| EURUSD | 275 | `+0.014162` |
| GBPJPY | 254 | `+0.005300` |
| GBPUSD | 293 | `-0.005694` |
| NZDUSD | 172 | `-0.008904` |
| USDCAD | 159 | `-0.004567` |
| USDCHF | 299 | `-0.008661` |
| USDJPY | 171 | `+0.017809` |

### Factor-block attribution

| Factor block | Matched events | Mean effect, ATR20 |
|---|---:|---:|
| Europe cross | 304 | `-0.014138` |
| JPY | 677 | `+0.003219` |
| USD commodity | 545 | `-0.002949` |
| USD Europe | 867 | `-0.000419` |

## Gate B disposition

Integrity gates passed `6 / 6`:

- all ten pairs present;
- one consistent frozen definition;
- no strategy execution or P&L;
- exactly five controls per event;
- five distinct control dates per event;
- all decision values finite.

Scientific gates passed `1 / 6`:

| Gate | Result |
|---|---|
| At least 400 matched events | Pass |
| Mean effect at least `+0.02 ATR20` | Fail |
| Bootstrap lower bound above zero | Fail |
| Permutation p-value no greater than 0.05 | Fail |
| At least 7/10 positive pairs | Fail |
| At least 3/4 positive factor blocks | Fail |

The failure is not marginal. The pooled estimate is negative, the confidence interval includes economically negligible positive and negative values, and breadth is substantially below the frozen requirements.

## Independent reconstruction

The final Gate B artifact was independently reconstructed outside the workflow from its event and control ledgers.

The reconstruction confirmed exactly:

- 2,393 unique events;
- 11,965 controls;
- five controls for every event;
- five distinct control dates for every event;
- no control from the event's own date;
- same-instrument matching;
- exact control means and event-minus-control arithmetic;
- pooled means;
- pair and factor attribution;
- 10,000-iteration date-block bootstrap with seed `20260725`;
- 10,000-iteration date-clustered matched-set permutation with seed `20260726`;
- every integrity and scientific gate outcome.

No implementation discrepancy was found.

## Scientific interpretation

The frequent sweep-and-reclaim pattern is a descriptive market event, not evidence of a standalone 60-minute reversal mechanism. Events did not outperform closely matched non-event minutes. The small positive results in four pairs and the JPY block cannot be selected retrospectively because the pooled primary endpoint failed and breadth was preregistered.

This result rejects the tested mechanism, not every possible concept associated with Stacey Burke. Any future Burke-family investigation must begin with a genuinely different, independently motivated hypothesis, a new preregistration and evidence not used to rescue SB-1.

## Protected evidence

- 2022–2023 validation returns were not inspected.
- 2024–2025 holdout returns remain untouched.
- 2026 YTD remains monitoring-only and was not used.
- No strategy entries, stops, targets, fills, costs, R multiples or P&L were calculated.

## Final authorization state

Authorized:

- retain source, census, controlled-study code and compact evidence for audit and reproducibility;
- manually reproduce the frozen rejection;
- reuse generic source, matching and inference infrastructure for genuinely independent research programmes.

Not authorized:

- 2022–2023 Stacey Burke validation;
- SB-1 executable design;
- alternative thresholds, windows, delays, horizons or filters;
- pair or factor-block cherry-picking;
- SB-2/SB-3 as post-failure substitutes;
- Pine, alerts, sizing, paper trading or live deployment.

The Stacey Burke previous-day sweep-and-reclaim reversal programme is complete and rejected.