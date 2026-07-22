# NQ Baseline Validity Reset — 2026-07-22

## Decision

`CONTINUE_RESEARCH_DO_NOT_DEPLOY`

The reversal concept remains positive on the available historical sample after correcting the noncausal gap rule. It is not deployable because timestamp semantics, continuous-contract construction, multiple-testing adjustment, pristine fresh data, and Python/Pine parity remain unresolved.

## Root-cause correction

The former `reject_unsafe` policy simulated a trade through its future exit, then retrospectively removed it when an unsafe gap occurred while the position was open. It also changed subsequent portfolio availability using the future gap timestamp.

The corrected `liquidate_unsafe` policy acts only when the first post-gap bar becomes observable:

- no missing intragap path is synthesized;
- a long exits at no better than the worse of active-stop execution and post-gap-open execution;
- a short uses the symmetric rule;
- gap-through-stop losses are allowed;
- the actual resume timestamp controls later portfolio eligibility;
- gap timestamps, duration, liquidation price, and reason are stored per trade.

## Evidence hierarchy

| Evidence | Trades | Expectancy | Net R | PF | Max DD | Return/DD | Interpretation |
|---|---:|---:|---:|---:|---:|---:|---|
| Observe-only historical reference | 504 | 0.166993R | 84.164359R | 1.3511 | 14.107858R | 5.9658 | Regression only; bridges missing data |
| Suspended retrospective reject | 491 | 0.180236R | 88.495783R | 1.3820 | 14.107858R | 6.2728 | Noncausal; retained only for attribution |
| Corrected causal benchmark | 495 | 0.173747R | 86.004761R | 1.3664 | 14.107858R | 6.0962 | Active historical research benchmark |
| Historical rolling walk-forward procedure | 289 | 0.151217R | 43.701603R | — | — | — | Four different selected configs; not pristine OOS |

Exactly four trades formerly removed after entry are now causally liquidated. They add −2.491022R versus the suspended 491-trade benchmark. No retained trade changes and no unexplained portfolio sequencing differences remain.

## Causal gap outcomes

The four gap liquidations occur in December 2022, April 2023, June 2023, and August 2024. Three exit near or through the active stop; one had reached TP1 before the gap and remains positive. The August 2024 case is 0.700627R worse than the observe-only time-close result because causal liquidation uses the first observable post-gap price.

## Timestamp semantics

Vendor ETH VWAP is reproduced to rounding error by cumulative HLC3 × volume (`RMSE ≈ 2.88e-06`). This identifies the price basis but does not determine timestamp labeling:

- the dataset contains no 18:00 observations;
- bar-open 18:01/reset 18:00, bar-open 18:01/reset 18:01, and bar-close labeling for the 18:00–18:01 interval are observationally equivalent;
- the source description says only “date and time of the bar.”

Decision: `UNRESOLVED`.

## Rollover sensitivity

Calendar roll-candidate sensitivity is material:

| Exclusion | Trades retained | Expectancy | Net R | Net R removed |
|---|---:|---:|---:|---:|
| None | 495 | 0.173747R | 86.004761R | — |
| Candidate dates | 484 | 0.155027R | 75.033098R | 10.971663R |
| ±1 market session | 468 | 0.139534R | 65.302138R | 20.702623R |
| ±3 market sessions | 458 | 0.128810R | 58.995174R | 27.009588R |

Candidate dates do not display obvious splice jumps or systematic volume discontinuities. The evidence therefore demonstrates calendar/volatility concentration, not proven back-adjustment contamination. Contract metadata remains required.

## Concentration

London remains the strongest session. Removing it leaves 324 trades, 0.102071R expectancy, and 33.070913R net.

London Friday is the largest single cell: 45 trades, 0.621799R expectancy, and 27.980958R net. Removing it leaves 450 trades, 0.128942R expectancy, 58.023803R net, and 3.898817 return/DD.

The system is concentrated, but the interaction table does not support the stronger claim that it is exclusively “London Thursday/Friday plus noise.” London Wednesday, New York Tuesday/Thursday, and Asia Wednesday/Thursday also contribute materially; New York Wednesday and Asia Tuesday are weak or negative.

## Descriptive uncertainty

Fixed-seed 95% intervals for mean historical expectancy:

- trade bootstrap: `[0.061458R, 0.287527R]`;
- month-block bootstrap: `[0.064236R, 0.287177R]`;
- session-date block bootstrap: `[0.062574R, 0.286320R]`.

These intervals describe the corrected selected strategy. They do not correct for the 904-configuration research process.

Multiple-testing status: `UNRESOLVED_NO_ALIGNED_904_CANDIDATE_RETURN_MATRIX`.

The former selected-trade IID `probability_net_positive` figure is no longer treated as strategy-validity evidence.

## Funnel correction

The earlier funnel reported BOS and impulse as identical because impulse qualification occurred before `bos_pass` was counted and `impulse_pass` used an unconditional expression.

The corrected funnel separates:

- raw BOS detections: 997;
- impulse-qualified BOS: 919;
- acceptance passes: 592;
- trend/entry signals: 508;
- executed trades: 495.

The no-op invalidation block and misleading comment were removed. Trade logic is unchanged.

## No-retune module reruns

All original thresholds and definitions were preserved.

### Continuation

All four unfiltered structural variants remain negative. `CONT_A2_PULLBACK_LATE60` remains a research lead only:

- 147 trades;
- 0.108895R expectancy;
- 16.007565R net;
- 8.003633R maximum drawdown;
- four-tick slippage: −0.041928R expectancy.

Decision: `HOLD_FOR_FRESH_DATA`.

### IFVG

All five filters remain inferior to the corrected baseline. `IFVG_CONFIRM_ANY` produces 459 trades and 0.161524R expectancy; stricter variants reduce coverage and efficiency further.

Decision: `REJECT_NO_INCREMENTAL_VALUE`.

### CISD

Broad sequence confirmation produces 313 trades and 0.134300R expectancy. The retest route has 76 trades, 0.239976R expectancy, and 2.959019 return/DD versus 6.096231 baseline.

Decision: `REJECT_NO_INCREMENTAL_VALUE`; retest remains diagnostic only.

### Entry routing

The exact predeclared PR #5 routes were rerun locally against the corrected benchmark:

- break close: 495 trades, 86.004761R, 6.096231 return/DD;
- first pullback: 295 trades, 62.217406R, 3.727015 return/DD;
- hybrid: 323 trades, 69.184846R, 3.303033 return/DD.

Decision: `REJECT_NO_INCREMENTAL_VALUE`. PR #5 remains draft until rebased and republished after this reset merges.

## Reproducibility

- local suite: 75 tests passed;
- corrected baseline canonical repeat: exact regression;
- baseline validity: 15/15 artifacts byte-identical;
- IFVG: 52/52;
- CISD: 52/52;
- continuation structural: 30/30;
- continuation late-60: 30/30;
- entry routing: 33/33.

## Restrictions

No deployment, position-sizing recommendation, Pine strategy port, module rescue combination, or fresh-data inspection is authorized by this work package.
