# Independent Review — GBPUSD Adapter and Frozen Phase One

Date: 2026-07-23
Status: `PASS_IMPLEMENTATION__REJECT_STRATEGY_TRANSFER`

## Data review

- Outer source SHA-256 verified: `44df46cfd7bce946074ae2f541a654cff907c7cc9a8bc43fac8b4090624e860e`.
- Eight annual bid/ask compressed members matched their embedded checksums.
- Deterministic high/close remapping reduced OHLC violations to zero.
- 2,103,840 source minutes produced 1,488,077 active minutes and 615,763 inactive carry-forward minutes.
- Duplicate timestamps: zero.
- Negative open/close spread observations: zero.
- Median spread: 0.9 pip; 95th percentile: 2.0 pips.

## Causality and execution review

- Midpoint bars are used only for signal formation.
- Long entry/exit uses ask/bid; short entry/exit uses bid/ask.
- Long stops trigger on bid low; short stops trigger on ask high.
- Gap-through stops use the worse executable side open.
- Spread is embedded in fills and not double-counted as a fixed cost.
- The phase-one YAML remained byte-identical.

## Engine equivalence review

The optimized detector was compared against the original pandas state machine on 5,000 synthetic bars containing trend changes, overlap variation, map changes, and explicit gaps. For every frozen arm, funnel counts and complete event frames matched exactly.

## Ledger reconstruction

All six independent reviews passed:

- trade count match;
- net R match;
- expectancy match;
- zero overlapping positions;
- zero invalid initial risks;
- zero chronology violations.

## Scientific conclusion

All six arms are materially negative. Five have wholly negative 95% date-block bootstrap intervals; the strict-base arm's interval reaches slightly above zero but its observed expectancy is -0.596R over 163 trades. The evidence rejects direct GBPUSD transfer. Further parameter search on this same mechanism would be post-hoc rescue and is not authorized.
