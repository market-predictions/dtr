# Fibonacci Pivot Formula Substitution — Implementation Validation

Date: 2026-08-08  
Study: `DFXC-20260808-005-pivot-fibonacci-substitution`  
Role: `implementation_operations`  
Status: `PASS_WITH_RECORDED_REPRODUCTION_LIMITATION`

## Validation objective

Validate that the Fibonacci study changes only the pivot-coordinate formula and that the reconstructed classic comparator is sufficiently faithful to interpret the formula substitution without silently tuning to the desired outcome.

This is implementation validation, not independent `governance_release_assurance`.

## Frozen-method verification

- Standard Fibonacci formula only: 0.382 / 0.618 / 1.000 range offsets around PP.
- Daily/H1 retains 0–20% core and 30–50% outer geometry.
- Weekly/H4 retains SP10 0–10% core and 40–50% outer geometry.
- H1/H4 ATR24 lagged-one-bar, 0.75 ATR directional-change terminal detector retained.
- Strictly-later confirmation ordering recovered from the frozen parent Amendment 02 and applied before accepted outcome analysis.
- Strong wick >=30%; weak <10%; frozen five bins retained.
- Ten pairs retained; no pair or named-level removal.
- 2015–2019 development and 2020–2021 internal validation only.
- 2022–2025 not inspected as a Fibonacci outcome window.
- 5,000 pair-year clustered bootstrap and separate two-hypothesis Holm families applied.

## Rejected provisional implementation

The first reconstruction updated a current-candle new extreme before testing whether the current close confirmed the previously stored candidate. That ordering is incompatible with the frozen anti-circularity amendment and over-associated terminal labels with large wicks.

No Fibonacci conclusion from that provisional run is accepted as primary evidence.

The corrected implementation follows Amendment 02 exactly at the event-order level:

1. current close tests only a candidate established on a strictly earlier response candle;
2. only if no reversal is confirmed may the current high/low replace the candidate;
3. after confirmation, the current candle supplies the initial opposite-leg candidate.

## Classic comparator reproduction

Primary wick interactions after correction:

- Daily/H1 frozen parent: +0.920648 pp; reconstructed: +0.929707 pp; absolute error **0.009059 pp**.
- Weekly/H4 SP10 frozen parent: +1.615771 pp; reconstructed: +1.606638 pp; absolute error **0.009133 pp**.

Companion structural effects:

- Daily/H1 frozen parent: +1.023167 pp; reconstructed: +1.126656 pp; absolute error **0.103489 pp**.
- Weekly/H4 SP10 frozen parent: +1.001905 pp; reconstructed: +1.068356 pp; absolute error **0.066451 pp**.

The primary wick comparator is therefore reproduced closely, while a smaller but non-zero structural residual remains.

## Root cause / evidence limitation

The parent programme persisted compact count/results evidence and a SHA-256 identity for its large local runner, but the heavy runner and terminal ledgers were intentionally not committed to Git. The current environment therefore cannot replay the exact historical terminal ledger byte-for-byte.

The residual is not repaired by calibrating parameters or selecting an alternative detector. It is retained as an explicit limitation.

## Scientific impact assessment

- **Daily Fibonacci/H1:** the primary wick result is well separated from zero (CI +0.634 to +1.473 pp). The comparator residual is too small to plausibly change the sign or broad conclusion.
- **Weekly Fibonacci/H4:** the primary wick result is marginal (CI +0.012 to +2.441 pp, Holm p=0.0488). The remaining reproduction uncertainty is material to whether it should be called a formal promotion candidate. It is therefore classified borderline rather than promoted.
- Formula-superiority claims are not supported on either horizon because paired Fibonacci-minus-Classic wick intervals include zero.

## Validation decision

`PASS_WITH_RECORDED_REPRODUCTION_LIMITATION`

The study is suitable for a presentable internal conclusion if the Weekly/H4 result is explicitly qualified as borderline and independent assurance is not bypassed.
