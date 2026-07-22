# E6 Advanced Blocks 0–3 Research — 2026-07-22

## Decision

`RETAIN_E6_NO_NEW_FILTER_ADVANCE_TO_SEQUENCING`

E6 remains the working research baseline. The mechanism audit strongly supports the prior-day-extreme exclusion, but none of the frozen path-quality or reward-space rules improves the E6 portfolio sufficiently to qualify as a fresh out-of-sample challenger.

No strategy, Pine, sizing or deployment change follows from this historical study.

## Provenance and regression

The supplied NQ one-minute archive reproduced the registered SHA-256 exactly:

`8d3f157a422636e5b8dda51cc3a3d9209c50cb53f9b279d3e14b627ce59370dc`

Both mandatory references reproduced exactly:

| Reference | Trades | Net R | Expectancy | Max DD | Return/DD |
|---|---:|---:|---:|---:|---:|
| Timing-corrected unfiltered control | 477 | 42.5775 | 0.0893 | 16.4265 | 2.5920 |
| E6 working baseline | 304 | 48.9376 | 0.1610 | 8.6326 | 5.6689 |

The normal execution assumptions remained one tick slippage on entry, one tick on exit and $2.25 commission per side. The timestamp shift, Tuesday–Friday calendar, Asia/London/New York sessions, gap liquidation, stops, targets, partial and time exit were unchanged.

## Block 1 — E6 mechanism audit

### Result

`SUPPORTED`

The audit compared isolated causal outcomes for signals retained by E6 with signals rejected because the directional session-range extreme was within 0.25 completed-D1 ATR of the corresponding prior-day extreme.

| Cohort | Signals | Expectancy | Median R | Win rate | PF | MFE | MAE | Stop first | TP1 hit | TP2 hit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| E6 kept, context available | 296 | **0.1681** | 0.4027 | 52.0% | 1.358 | 1.466R | 0.721R | 44.6% | 45.6% | 11.5% |
| Rejected near prior-day extreme | 182 | **−0.0564** | −1.0043 | 42.9% | 0.899 | 1.261R | 0.771R | 51.6% | 37.9% | 7.7% |
| Context unavailable | 14 | −0.2143 | −1.0131 | 35.7% | 0.674 | 1.130R | 0.830R | 57.1% | 35.7% | 7.1% |

The kept-minus-rejected expectancy difference was **+0.2244R**. Rejected setups had a 7.1 percentage-point higher stop-first rate, lower MFE, lower TP1 hit rate and lower TP2 hit rate.

The kept cohort had higher expectancy in all three tested calendar years and in Asia, London and New York. The effect was also present in both long and short directions, although it was stronger for longs.

### Interpretation

The E6 edge does not appear to come primarily from greater measured structural clearance. The clearance difference was small and failed the preregistered mechanism marker. Instead, near-prior-day-extreme reversals behaved like lower-quality reversals: less favorable excursion, more stop-first outcomes, fewer partial-target hits and fewer runner hits.

This is consistent with increased continuation or failed-reversal risk when the initial range already forms too close to the prior-day directional extreme. The audit supports retaining E6’s mechanism. It does not authorize changing the 0.25 ATR threshold.

## Blocks 2 and 3 — Frozen candidate results

| Candidate | Trades | Net R | Expectancy | Max DD | Return/DD | 2-tick/side expectancy | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| E6 baseline | 304 | **48.94** | 0.161 | **8.63** | **5.67** | 0.143 | Working baseline |
| P1: path ≤12 bars | 93 | 23.79 | 0.256 | 8.47 | 2.81 | 0.240 | Reject |
| P2: BOS quality 2/3 | 225 | 36.51 | 0.162 | 11.45 | 3.19 | 0.145 | Shadow only |
| P3: entry extension ≤0.35R | 208 | 38.25 | 0.184 | 9.57 | 4.00 | 0.166 | Shadow only |
| R1: clear to TP1 | 99 | 24.01 | 0.243 | 8.23 | 2.92 | 0.224 | Reject |
| R2: clear to runner | 46 | 16.57 | 0.360 | 3.43 | 4.82 | 0.344 | Predeclared shadow only |
| I1: BOS quality + TP1 clearance | 76 | 17.36 | 0.228 | 6.53 | 2.66 | 0.211 | Predeclared shadow only |

### Paired portfolio inference

Every candidate produced less total return than E6 after full portfolio resequencing:

| Candidate | Incremental net R | 95% date-block interval | Probability of improvement | Familywise p |
|---|---:|---:|---:|---:|
| P1 | −25.15R | [−62.35, +10.43] | 8.9% | 1.000 |
| P2 | −12.43R | [−35.21, +9.30] | 13.6% | 1.000 |
| P3 | −10.69R | [−34.61, +12.71] | 18.7% | 1.000 |
| R1 | −24.93R | [−61.38, +10.15] | 8.3% | 1.000 |
| R2 | −32.37R | [−73.45, +7.93] | 5.6% | 1.000 |
| I1 | −31.57R | [−70.66, +6.19] | 5.0% | Shadow; no promotion test |

An independent reviewer repeated the date-block analysis with a different seed. All intervals again included zero and every observed incremental result remained negative.

### Candidate interpretation

- **P1:** higher conditional expectancy but only 93 trades, lower portfolio return and negative 2025. `REJECT`.
- **P2:** almost identical expectancy to E6, larger drawdown and lower return/DD. `SHADOW_ONLY` under the frozen 180–249 trade classification, but not a priority challenger.
- **P3:** the most plausible rule; expectancy rose to 0.184R and all years remained positive, but net return fell 10.69R, drawdown increased and return/DD declined. `SHADOW_ONLY`; retain only as a long-history or cross-market replication hypothesis.
- **R1:** high conditional expectancy but only 99 trades and 24.93R less total return. `REJECT`.
- **R2:** 46 trades and excessive concentration. `SHADOW_ONLY` solely because the framework predeclared it as a shadow diagnostic.
- **I1:** 76 trades, 31.57R less than E6 and failed half-year concentration. `SHADOW_ONLY` by preregistration; no further combination testing.

## Changed-trade attribution

All common trades reproduced identical P&L. Filtering sometimes enabled a later trade because an earlier E6 position was absent:

| Candidate | Common | Removed | Added replacements | Removed net R | Added net R |
|---|---:|---:|---:|---:|---:|
| P1 | 90 | 214 | 3 | 26.02R | 0.87R |
| P2 | 224 | 80 | 1 | 13.03R | 0.60R |
| P3 | 207 | 97 | 1 | 11.97R | 1.28R |
| R1 | 99 | 205 | 0 | 24.93R | 0.00R |
| R2 | 46 | 258 | 0 | 32.37R | 0.00R |
| I1 | 76 | 228 | 0 | 31.57R | 0.00R |

No unexplained trade differences or overlapping positions were found.

## Independent review and determinism

The independent review verified the source checksum, exact control and E6 regressions, all metrics and cost stresses, causal D1/weekly timestamps, sweep ≤ reclaim ≤ BOS ≤ entry ordering, every candidate mask, changed-trade attribution, non-overlapping positions, the mechanism classification and all final dispositions.

Two complete executions produced identical content for all 17 runner artifacts, including decompressed diagnostic tables.

## Conclusions

### Strategic

E6 is strengthened as a coherent working baseline. The prior-day-extreme proximity rule removes a genuinely weak reversal cohort rather than merely improving results through arbitrary sample selection.

The additional path and clearance rules mostly raise conditional expectancy by discarding large portions of profitable E6 activity. They do not improve the portfolio-level decision problem.

### Tactical

- retain E6 unchanged;
- do not add P1, P2, P3, R1, R2 or I1;
- retain P3 only as a secondary replication hypothesis;
- do not search neighboring thresholds or combine candidates;
- do not change the primary fresh-OOS Arms 0/A/B/C.

### Operational

Blocks 0–3 are complete. The next permitted block is the separately frozen portfolio-sequencing study: S0 current global sequencing, S1 first trade per ETH market date, S2 60-minute cooldown and S3 risk-normalized independent session sleeves.

No later result may alter the completed Blocks 0–3 definitions or decisions.
