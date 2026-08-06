# Quarters Theory Destination and Exhaustion Preregistration

- **Programme:** `QT-DESTINATION-EXHAUSTION-V1`
- **Work package:** `QT-WP-20260807-04`
- **Frozen date:** 2026-08-07
- **Status:** `PREREGISTERED_BEFORE_NEW_OUTCOMES`
- **Prior programme:** canonical 250-pip post-crossing continuation is closed and failed.

## Research distinction

This programme does not retest whether price continues after crossing a canonical 250-pip level. It tests a materially different mechanism:

1. established directional legs may terminate disproportionately near canonical 250-pip levels;
2. qualified trends approaching a round level may complete more often when that destination is a canonical 250-pip level;
3. after a qualified trend reaches a canonical 250-pip level, reversal may occur before equal-sized extension more often than at matched noncanonical round levels.

No result may retrospectively amend the failed continuation decision.

## Data contract

- Source: registered private `Dukascopy FX Cache`; no historical reacquisition.
- Pairs: EURUSD, GBPUSD, USDCHF, AUDUSD, NZDUSD, USDCAD, USDJPY, EURJPY, GBPJPY, EURGBP.
- Construction: M1 separate BID/ASK, UTC; midpoint OHLC for structural analysis.
- Development: 2015–2019.
- Internal validation: 2020–2021.
- Holdout: 2022–2025 remains unopened.
- JPY prices use source pip size `0.01`; other pairs use `0.0001`. All analysis is performed directly in source pips.
- Every annual source file must match its embedded SHA-256 before analysis.

## Shared preprocessing

1. Preserve calendar-minute rows. A minute is active only when both BID and ASK volume are greater than zero.
2. Form midpoint OHLC from BID and ASK.
3. Aggregate to UTC H1 bars only when at least 80% of constituent minutes are active.
4. Calculate H1 true range and ATR24 as the rolling mean of the preceding 24 valid H1 true ranges, lagged one H1 bar for causal tests.
5. Canonical phase is `price_pips mod 250 = 0`. Controls are phases 50, 100, 150 and 200 on the same 50-pip lattice.

## A1 — Independent trend-leg terminal clustering

### Leg detector

Use a directional-change ZigZag on valid H1 midpoint bars, independent of Quarter levels.

- Reversal threshold: `0.75 × lagged ATR24`.
- In an up leg, update the running high. Freeze the reversal threshold at the H1 bar that sets each new high. Confirm the endpoint when a subsequent H1 low is at least the frozen threshold below that high.
- In a down leg, use the symmetric rule.
- Endpoint timestamp and price are the running extreme, not the later confirmation bar.
- Require leg amplitude of at least `1.00 × lagged ATR24` measured at the endpoint.
- Exclude endpoints without valid lagged ATR24 or where confirmation crosses a year boundary.

### Primary endpoint

For each confirmed endpoint, calculate proximity to each phase's nearest level. With a fixed ±15-pip window:

`score_A1 = I(within 15 pips of phase 0) - 0.25 × sum(I(within 15 pips of phases 50/100/150/200))`.

Primary effect: mean `score_A1`.

### A1 gate

A1 passes only when:

- development effect > 0;
- validation effect > 0;
- combined year-preserving pair-week block-bootstrap 95% interval lower bound > 0;
- at least 6 of 10 pair-level combined effects are positive;
- leave-one-pair-out pooled effect remains positive.

Secondary phase counts, distances and direction splits cannot rescue a failed primary gate.

## A2 — Causal destination-completion test

### Qualified incoming trend at H1 close

At H1 close `t0`, a trend qualifies when all conditions are met using information available by `t0`:

- four-hour signed close displacement magnitude is at least `0.75 × lagged ATR24`;
- four-hour directional efficiency `abs(close_t0 - close_t-4) / sum(abs(hourly close changes))` is at least 0.60;
- the close lies in the outer 20% of the preceding four-hour high-low range in the displacement direction;
- the next 50-pip lattice level in that direction is 5–45 pips from the close;
- that target was not touched during the preceding four H1 bars;
- no overlapping active episode exists for the same pair, direction and target.

### Outcome

From the first active M1 minute after `t0`, follow for at most 24 hours:

- success: target is touched first;
- failure: price reaches an adverse level `0.50 × lagged ATR24` from the event close first;
- same-minute target and failure: ambiguous;
- neither: timeout.

Primary signed outcome:

- +1 target first;
- -1 failure first;
- 0 timeout or ambiguous.

### Matched phase effect

Compare phase 0 targets with noncanonical phases within frozen strata:

- pair;
- year;
- direction;
- UTC four-hour session;
- remaining-distance bin: 5–14.999, 15–24.999, 25–34.999, 35–45 pips;
- lagged ATR24 tercile within pair-year;
- efficiency band: 0.60–0.699, 0.70–0.799, 0.80–1.00.

Use harmonic treated/control stratum weighting. Primary effect is phase-0 mean signed outcome minus control mean signed outcome.

### A2 gate

A2 passes only when:

- development matched effect > 0;
- validation matched effect > 0;
- combined pair-week block-bootstrap 95% interval lower bound > 0;
- at least 6 of 10 pair-level raw phase-0-minus-control effects are positive;
- leave-one-pair-out matched effect remains positive.

Secondary resolved hit rate, timeout, time-to-target and adverse excursion cannot rescue the primary endpoint.

## A3 — Arrival reversal before extension

A3 uses only A2 episodes that successfully touch their target after a qualified incoming trend.

From the first target-touch minute, observe the next four hours:

- reversal barrier: 25 pips against the incoming trend from the target level;
- extension barrier: 25 pips beyond the target in the incoming trend direction;
- reversal first = +1;
- extension first = -1;
- timeout or same-minute ambiguity = 0.

Use the same frozen matching variables as A2, with target-touch UTC four-hour session replacing event session. Primary effect is phase-0 signed reaction minus controls.

### A3 gate

A3 passes only when the same temporal, interval, breadth and leave-one-pair-out requirements defined for A2 pass.

## Multiplicity and programme decision

The three primary hypotheses form one family. A result is promotable only when its two-sided pair-week block-bootstrap p-value passes Holm correction across A1, A2 and A3, in addition to its individual gate.

Programme decisions:

- no primary test passes: `REJECT_DESTINATION_EXHAUSTION_MECHANISM`;
- A1 only passes: `STRUCTURAL_CLUSTERING_ONLY_NO_CAUSAL_TARGET_EDGE`;
- A2 passes, A3 fails: `TARGET_EFFECT_SUPPORTED_REVERSAL_UNSUPPORTED`;
- A3 passes, A2 fails: `ARRIVAL_REACTION_ONLY_REQUIRES_NEW_MECHANISM_REVIEW`;
- A2 and A3 pass: `AUTHORIZE_SEPARATE_STRATEGY_PREREGISTRATION`;
- any result failing temporal or pair breadth remains descriptive only.

## Restrictions

- No parameter variation after outcomes.
- No phase, pair, year, session or threshold rescue.
- No opening of 2022–2025.
- No execution P&L, entries, stops, targets, Pine, alerts, sizing, paper trading or deployment in this work package.
- Any future strategy requires a separate preregistration and independent assurance.
