# Work Package — Fibonacci Pivot Formula Substitution

Date: 2026-08-08
Work package: `PIV-WP-20260808-05`
Role: `implementation_operations`
State: `RELEASE_CANDIDATE_READY`

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

## Result

### Daily Fibonacci → H1

- wick interaction: **+1.052 pp**, 95% CI **[+0.634,+1.473] pp**;
- development +1.292 pp; validation +0.456 pp;
- structural terminal effect: **+1.314 pp**, CI **[+1.115,+1.515] pp**;
- wick positive in 9/10 pairs; structural positive in 10/10;
- all pooled leave-one-pair-out effects positive;
- wick-severity gradient monotonic.

Disposition: `SUPPORTED_INTERNAL` as an alternative representation, not as a superior formula.

### Weekly Fibonacci → H4 SP10

- wick interaction: **+1.234 pp**, 95% CI **[+0.012,+2.441] pp**;
- raw/Holm p=0.0488;
- development +1.480 pp; validation +0.614 pp;
- structural terminal effect: **+1.159 pp**, CI **[+0.641,+1.667] pp**;
- wick positive in 7/10 pairs; structural positive in 9/10;
- all pooled leave-one-pair-out effects positive;
- wick-severity gradient monotonic.

Disposition: `BORDERLINE / INDETERMINATE FOR PROMOTION`. The point estimate passes the numerical internal gate but sits too close to zero for the remaining comparator-reproduction limitation to be ignored.

### Formula comparison

- Daily Fib minus Classic wick delta: **+0.122 pp**, paired CI **[-0.338,+0.573] pp**.
- Weekly Fib minus Classic wick delta: **−0.373 pp**, paired CI **[-1.631,+0.880] pp**.

Neither horizon establishes Fibonacci superiority.

## Comparator validation

A first provisional reconstruction was rejected before Fibonacci conclusions because it updated the current candle extreme before testing the previous candidate, violating the frozen strict-later anti-circularity ordering.

After applying Amendment 02 exactly at the event-order level, reconstructed classic primary wick interactions are within approximately **0.01 pp** of the frozen parent values on both horizons. Companion structural effects retain residual differences of about **0.103 pp Daily** and **0.066 pp Weekly**, because the historical parent runner/terminal-event ledger was intentionally not committed and cannot be replayed byte-for-byte.

Validation status: `PASS_WITH_RECORDED_REPRODUCTION_LIMITATION`.

## Non-scope

- no new zone search;
- no ATR zone variants;
- no alternative Fibonacci coefficients;
- no pair, pivot-level, wick-threshold or session selection;
- no P&L, entry, stop, target, Pine, alerts, sizing or deployment.

## Acceptance status

- [x] preregistration committed before outcome computation;
- [x] permanent cache reused and data boundaries enforced;
- [x] classic comparator reconstructed with primary wick endpoints within ~0.01 pp of frozen parents;
- [x] all Fibonacci positive and negative results retained;
- [x] formula-difference uncertainty reported;
- [x] registry result/report/validation evidence stored durably;
- [ ] independent `governance_release_assurance` of exact candidate;
- [ ] merge after assurance PASS.

Implementation does not self-certify the candidate.
