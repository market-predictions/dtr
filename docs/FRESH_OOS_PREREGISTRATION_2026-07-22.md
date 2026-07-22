# Fresh NQ Out-of-Sample Preregistration

## Status

`PREREGISTERED_SPECIFICATION_DATA_NOT_ACQUIRED`

This document must be committed before any January–July 2026 performance data are inspected.

## Data qualification

The fresh source must provide:

- NQ one-minute OHLCV through at least 2026-07-21;
- explicit timezone and bar-open/bar-close semantics;
- individual-contract identifiers or documented continuous-contract roll/adjustment methodology;
- no Excel-row truncation;
- checksum, source, license, schema, first/last timestamp, missing-bar audit, and roll metadata.

A dataset that cannot resolve timestamp and contract construction may be used for ingestion development but not for the decisive test.

## Frozen strategy

Use `DTR_PY_NQ_CANDIDATE_0_1_CAUSAL_GAP` with no parameter changes and causal `liquidate_unsafe` handling.

No session, weekday, direction, stop, target, regime, entry, or cost parameter may be changed after data inspection.

## Primary period

- start: 2026-01-01 or the first complete qualified market session thereafter;
- end: 2026-07-21;
- exclude only incomplete source dates and exclusions declared by the data-quality manifest;
- report all excluded dates and reasons.

## Primary research-continuation gate

All must hold:

1. net R > 0;
2. expectancy ≥ 0.08R per trade;
3. profit factor ≥ 1.15;
4. at least 80 completed trades;
5. no single session×weekday cell contributes more than 50% of fresh net R;
6. the trade-per-eligible-session rate remains within ±30% relative of the corrected historical rate;
7. one-, two-, and four-tick cost stress is reported, with two-tick expectancy > 0;
8. no unresolved data-quality or contract-roll event explains more than 20% of fresh net R.

Passing this gate authorizes continued paper research only, not deployment.

## Failure and ambiguity

- Expectancy ≤ 0 or net R ≤ 0: stop promotion and retain the strategy as historical research.
- Expectancy between 0 and 0.08R: extend the frozen observation period; do not retune.
- Fewer than 80 trades: treat the test as underpowered and extend forward.
- Material funnel or concentration shift: diagnose market/data drift before interpreting returns.

## Deployment remains separately blocked

Even a pass requires:

- multiple-testing-aware interpretation of the historical selection process;
- Python/Pine trade-for-trade parity;
- realistic TradingView execution validation;
- paper-forward observation;
- explicit risk and whole-contract sizing review.
