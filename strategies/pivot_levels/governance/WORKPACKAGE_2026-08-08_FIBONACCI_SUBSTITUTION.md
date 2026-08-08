# Work Package — Fibonacci Pivot Formula Substitution

Date: 2026-08-08
Work package: `PIV-WP-20260808-05`
Role: `implementation_operations`
State: `PREREGISTERED`

## Objective

Repeat the two successful pivot/wick relationships with standard Fibonacci-calculated pivot levels while changing only the pivot formula:

- Daily Fibonacci pivots → H1, inherited 0–20% normalized-spacing core / 30–50% outer control;
- Weekly Fibonacci pivots → H4, inherited SP10 0–10% core / 40–50% equal-width outer control.

Compare each Fibonacci result directly with a classic-pivot comparator recalculated from the same market data and pair-year blocks.

## Scientific unit

`DFXC-20260808-005-pivot-fibonacci-substitution`.

## Data boundary

Canonical **Dukascopy FX Cash**, ten pairs, M1 BID/ASK midpoint structural measurement.

- development: 2015–2019;
- internal validation: 2020–2021;
- 2022–2025 is not treated as a pristine holdout for this related new hypothesis;
- no 2026 outcome inspection.

## Frozen formula

`PP=(H+L+C)/3`, range `R=H-L`.

Fibonacci pivots:

- R1/S1 = PP ± 0.382R;
- R2/S2 = PP ± 0.618R;
- R3/S3 = PP ± 1.000R.

No alternative Fibonacci ratios.

## Frozen response logic

- Daily→H1: ATR24 lagged one H1 bar, 0.75 ATR reversal threshold, strictly later-bar terminal confirmation, 20% spacing core.
- Weekly→H4: ATR24 lagged one H4 bar, 0.75 ATR reversal threshold, strictly later-bar terminal confirmation, SP10 spacing core.
- directional wick strong >=30%, weak <10%; five frozen wick bins.

## Inference

- 5,000 pair-year clustered bootstrap draws;
- separate two-hypothesis Holm families for Fibonacci structural effects and wick interactions;
- development/validation sign stability;
- >=6/10 positive pair effects;
- every leave-one-pair-out pooled effect positive;
- monotonic core wick gradient;
- paired Fibonacci-minus-Classic effect distribution by pair-year block.

## Non-scope

- no new zone search;
- no ATR zone variants;
- no alternative Fibonacci coefficients;
- no pair, pivot-level, wick-threshold or session selection;
- no P&L, entry, stop, target, Pine, alerts, sizing or deployment.

## Acceptance criteria

- preregistration committed before outcome computation;
- permanent cache reused and data boundaries enforced;
- classic comparator reproduces parent Daily/H1 and Weekly/H4 2015–2021 effects under the inherited geometries;
- all Fibonacci positive and negative results retained;
- formula-difference uncertainty reported;
- registry record, result, report and evidence stored durably;
- implementation candidate not self-certified; independent assurance remains separate.
