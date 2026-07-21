# IFVG Entry-Confirmation Ablation Design — 2026-07-21

## Decision problem

The frozen reversal candidate already identifies a sweep, reclaim, protected pivot, break of structure, acceptance and entry. The IFVG work package asks one narrower question:

> Does a causally known, directionally aligned inversion fair value gap improve the quality of those existing reversal decisions enough to justify lost opportunity coverage?

The objective is not to create another discretionary pattern library or to search for the most attractive IFVG settings.

## Causal fair value gap definition

A fair value gap is recognized only after the third five-minute candle closes.

### Bullish FVG

At bar `i`, a bullish FVG exists when:

`low[i] > high[i-2]`

Zone:

- lower boundary: `high[i-2]`;
- upper boundary: `low[i]`.

### Bearish FVG

At bar `i`, a bearish FVG exists when:

`high[i] < low[i-2]`

Zone:

- lower boundary: `high[i]`;
- upper boundary: `low[i-2]`.

No wick, midpoint or displacement requirement is imposed in the primary definition. Zone size and displacement are recorded as diagnostics before they become potential future gates.

## Causal inversion definition

An original FVG becomes an IFVG only on a later bar close:

- a bearish FVG becomes a bullish IFVG when a later close is above its upper boundary;
- a bullish FVG becomes a bearish IFVG when a later close is below its lower boundary.

The inversion timestamp is the close/decision time of that later bar. The original FVG cannot invert on the same bar on which it is created.

## Directional alignment

- long reversal signal → bullish IFVG created by inversion of a bearish FVG;
- short reversal signal → bearish IFVG created by inversion of a bullish FVG.

An IFVG must invert after the reversal sweep and no later than the existing entry decision. Pre-sweep inversions do not qualify for the primary confirmation variants.

## Reset and gap rules

- FVG and IFVG state is partitioned by the deterministic strategy-state epoch.
- A zone created before a reset interval cannot invert or confirm a signal after that reset.
- A signal path truncated by the gap-safe contract cannot use an IFVG beyond the truncation boundary.
- No missing bar is synthesized.

## Zone-touch definition

For `IFVG_ZONE_TOUCH`, after inversion and before the existing reversal entry decision, price must trade into the closed interval between the IFVG lower and upper boundaries. The inversion bar itself does not count as the required post-inversion touch.

The existing reversal entry price and timing remain unchanged. This variant is a confirmation filter, not a replacement entry engine.

## Analysis layers

### 1. Frozen-population cohort analysis

Annotate every signal/trade from the frozen gap-safe reversal run. Compare confirmed and unconfirmed cohorts without changing the portfolio sequence.

Purpose:

- understand conditional association;
- report coverage and outcome concentration;
- avoid confusing position-overlap effects with pattern quality.

### 2. Implementable portfolio-filter analysis

Apply the confirmation rule before trade simulation and enforce the existing single-position rule. Removing one signal may allow a later signal that was previously blocked; every such consequence must be attributed.

Purpose:

- measure the actual implementable filtered strategy;
- reconcile removed, retained and newly enabled trades.

## Predeclared variants

1. `IFVG_OBSERVE`
2. `IFVG_CONFIRM_ANY`
3. `IFVG_CONFIRM_RECENT_3`
4. `IFVG_CONFIRM_RECENT_6`
5. `IFVG_CONFIRM_RECENT_12`
6. `IFVG_ZONE_TOUCH`

The age of an IFVG is measured in completed five-minute decision bars from inversion through the existing entry bar.

## Required diagnostics

For each signal:

- aligned IFVG present;
- inversion index and time;
- IFVG age in bars;
- zone lower and upper boundary;
- zone size in points and ATR fractions;
- originating FVG index and time;
- minutes from sweep to inversion;
- minutes from inversion to entry;
- post-inversion zone touch;
- IFVG direction and strategy-state epoch.

## Interpretation rules

- Higher expectancy with very low coverage is not automatically useful.
- A portfolio improvement caused mainly by newly enabled later trades must be stated explicitly.
- Any result that fails chronological or neighbourhood stability is rejected or held.
- A pattern discovered only in one session, weekday or direction is not promoted without separate fresh-data confirmation.
- Negative evidence is a valid result and must be preserved.
