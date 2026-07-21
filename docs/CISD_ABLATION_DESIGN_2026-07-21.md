# NQ CISD Entry-Confirmation Design — 2026-07-21

## Decision problem

Does a close-confirmed change from opposite candle-body delivery into the reversal direction improve the existing DTR reversal decision enough to justify rejecting trades without that confirmation?

CISD terminology is used inconsistently in discretionary trading material. The research engine therefore does not assume a universal definition. It tests two versioned anchor contracts against the same frozen reversal population.

## Strategic contract

- Instrument: NQ futures.
- Decision bars: five minutes.
- Execution bars: one minute.
- Primary target: frozen 491-trade gap-safe reversal baseline.
- Research standard: incremental value before combination.
- Null hypothesis: CISD confirmation does not improve coverage-adjusted, chronological, and cost-stressed reversal performance.

## Causal event model

### Opposite delivery

For an intended bullish reversal, an opposite-delivery candle has `close < open`. For an intended bearish reversal, it has `close > open`. Doji candles terminate a contiguous sequence and do not belong to either direction.

### Sequence construction

Starting at the sweep bar, contiguous opposite-delivery candles form a sequence. The sequence becomes knowable when the first non-opposite candle closes or the entry decision window ends.

An unconfirmed sequence expires when a newer opposite-delivery sequence begins. This prevents stale anchors from surviving a fresh delivery leg.

### Anchor contracts

- **Sequence anchor:** open of the first candle in the sequence.
- **Last-candle anchor:** open of the final candle in the sequence.

### Confirmation

- Bullish: first later five-minute close strictly above the chosen anchor.
- Bearish: first later five-minute close strictly below the chosen anchor.
- Confirmation cannot occur on or before the final sequence candle.
- Confirmation must occur no earlier than the sweep and no later than the existing reversal entry bar.
- Event state cannot cross a reset epoch.

### Retest

A retest exists when, after sequence-anchor confirmation and before the existing entry decision, a later bar range touches the anchor price. Same-bar confirmation is not counted as a retest.

## Predeclared variants

1. `CISD_OBSERVE` — annotation only.
2. `CISD_SEQUENCE_CONFIRM` — sequence-anchor confirmation.
3. `CISD_LAST_CANDLE_CONFIRM` — last-candle-anchor confirmation.
4. `CISD_SEQUENCE_RECENT_3` — sequence confirmation no more than three bars before entry.
5. `CISD_SEQUENCE_RECENT_6` — sequence confirmation no more than six bars before entry.
6. `CISD_SEQUENCE_RETEST` — sequence confirmation plus post-confirmation anchor retest.

## Diagnostics before filters

Record but do not initially filter:

- sequence length;
- aggregate body displacement;
- displacement relative to ATR;
- anchor distance from entry;
- bars and minutes from sweep to confirmation;
- bars and minutes from confirmation to entry;
- session, direction, weekday, and chronological period.

## Portfolio contract

The engine must report two distinct objects:

1. **Frozen cohort:** baseline trades whose existing signal has the required CISD annotation.
2. **Implementable portfolio:** rerun of the frozen signal stream with the CISD gate, allowing removed earlier positions to expose later signals.

Any newly enabled trade must be separately attributed. Cohort performance may not be presented as an implementable strategy result.

## Operational safeguards

- Reuse the frozen signal generator and one-minute simulator.
- Reject unsafe open-trade bridges.
- Validate a signature of all signal-generating parameters.
- Do not change reversal stops, exits, costs, sessions, or signal logic.
- Generate deterministic CSV, Parquet, JSON, funnel, cohort, and changed-trade artifacts.

## Test matrix

- bullish sequence-anchor confirmation;
- bearish symmetry;
- last-candle versus first-sequence anchor difference;
- no confirmation on the sequence-ending candle;
- newer sequence expiry;
- doji sequence termination;
- three/six-bar age windows;
- post-confirmation retest;
- reset-epoch invalidation;
- prepared-context config mismatch;
- portfolio sequencing attribution;
- strict manifest and checksum validation;
- frozen observe regression.

## Stop rule

If the predeclared variants do not show independent, chronological, cost-robust improvement with acceptable coverage, record a rejection and move on. Do not search body-size, sequence-length, session, or direction thresholds to rescue CISD on the same dataset.
