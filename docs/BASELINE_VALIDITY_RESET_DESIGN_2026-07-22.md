# Baseline Validity Reset — Causal and Statistical Design

## Decision problem

Determine whether the NQ reversal strategy retains credible research value after correcting the noncausal open-trade gap rule and explicitly testing timestamp, rollover, concentration, and selection-pressure risks.

## Causal gap contract

- No trade may be accepted or rejected using a gap not yet observable.
- Ex-ante contaminated session ranges and signal paths remain rejected or truncated.
- When an unsafe gap becomes observable while a position is open, liquidate at the first post-gap observation.
- Long execution is no better than the worse of active-stop execution and post-gap-open execution; short logic is symmetric.
- Losses beyond the nominal stop are allowed.
- Actual liquidation time controls subsequent portfolio eligibility.
- Gap reason, interval, duration, and price are explicit artifacts.

## Timestamp test

Compare vendor ETH VWAP against reconstructed hypotheses for bar-open and bar-close labeling, multiple reset alignments, and price bases. A VWAP match is not conclusive when hypotheses are observationally equivalent.

## Rollover test

Create quarterly calendar-roll candidates, report discontinuity diagnostics, and exclude candidate dates plus one- and three-session windows without changing strategy parameters. This bounds sensitivity but does not replace contract metadata.

## Statistical review

Commit fixed-seed trade, month-block, and session-date bootstrap code. Treat selected-strategy intervals as descriptive. Do not claim familywise selection validity without an aligned candidate-return matrix.

## Module reruns

Continuation, IFVG, CISD, and entry routing must be rerun without threshold or parameter changes after the corrected benchmark is frozen.

## Promotion language

The corrected benchmark may authorize continued research only. Deployment additionally requires qualified fresh data, Python/Pine parity, and paper-forward evidence.
