# NQ Gap-Safe Baseline Comparison — 2026-07-21

## Decision

`PROMOTE_TO_CONTINUATION_RESEARCH`

This decision closes the baseline-integrity implementation gate. It does not approve production use, parameter retuning, or profitability claims.

## Reproducibility

- Dataset SHA-256: `8d3f157a422636e5b8dda51cc3a3d9209c50cb53f9b279d3e14b627ce59370dc`
- Execution commit: `6f4812817a9b85f659c605b38af506a72d51d5fa`
- Strategy parameters identical: **True**
- Frozen reference regression: **passed**
- Reference clean rerun byte-identical: **True**
- Gap-safe clean rerun byte-identical: **True**

## Primary metrics

| Metric | Reference | Gap-safe | Delta |
|---|---:|---:|---:|
| Trades | 504 | 491 | -13 |
| Net R | 84.164359 | 88.495783 | 4.331424 |
| Expectancy R | 0.166993 | 0.180236 | 0.013243 |
| Win rate | 50.5952% | 51.1202% | 0.5249% |
| Profit factor | 1.351059 | 1.381998 | 0.030939 |
| Max drawdown R | 14.107858 | 14.107858 | 0.000000 |
| Return / DD | 5.965779 | 6.272801 | 0.307022 |

The gap-safe run removes 13 trades and increases net R by 4.331424R. This is descriptive only: removed observations were contaminated by missing data, so the change is not an optimization gain.

## Trade attribution

| Classification | Trades removed | Removed trades net R |
|---|---:|---:|
| `contaminated_session_range` | 9 | -2.541029 |
| `unsafe_gap_during_open_trade` | 4 | -1.790395 |

- Added trades: **0**
- Unexplained differences: **0**
- Setup-path truncation occurred in 31 eligible sessions, but it did not remove an otherwise completed trade in this frozen candidate.

## Session effect

| Session | Trades delta | Net R delta | Interpretation |
|---|---:|---:|---|
| ASIA_7PM | -9 | 3.292325 | Nine contaminated observations removed; net result improves. |
| LONDON_2AM | -2 | 2.061106 | Two contaminated observations removed; net result improves. |
| NEW_YORK_9AM | -2 | -1.022007 | Two contaminated observations removed; both were net profitable, so sanitized net R declines. |

## Period stability

- Development: 249 → 243 trades; net R +2.303617; maximum drawdown unchanged.
- Validation: 126 → 124 trades; net R +0.865371; maximum drawdown improves by 0.865371R.
- Later research: 125 → 121 trades; net R +0.134078; maximum drawdown unchanged.

The correction does not depend solely on the development period, but its magnitude is small in the later-research slice. It should therefore be treated as integrity cleanup rather than stronger evidence of edge.

## Funnel changes

- Eligible sessions: 1686
- Session ranges rejected: 19
- Session paths truncated: 31
- Entry signals: 517 → 508
- Unsafe open-trade bridges rejected: 4
- Final trades: 504 → 491

## Locked gap-safe regression

- Trades: `491`
- Net R: `88.49578342152539`
- Maximum drawdown R: `14.107857513807524`

Artifact hashes are recorded in `results/2026-07-21/nq_candidate_0_1_gap_safe_summary.json`.

## Remaining limitations

- This is a data-integrity correction, not a parameter optimization result.
- Continuous-contract rollover and back-adjustment methodology remain unresolved.
- Timestamp meaning, daylight-saving transitions, session boundaries, and supplied VWAP reset semantics remain provisional.
- The gap-safe policy excludes execution through missing data rather than estimating hypothetical fills.
- No post-December-2025 paper-forward sample is included.

## Next work package

Build the continuation engine independently. Do not combine it with reversal unless continuation shows independently positive, walk-forward evidence under the same gap-safe data contract.
