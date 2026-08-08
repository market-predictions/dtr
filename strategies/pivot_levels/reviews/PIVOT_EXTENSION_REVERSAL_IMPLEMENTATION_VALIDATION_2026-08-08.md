# Implementation Validation — Extension-Conditioned Reversal

Study: `DFXC-20260808-010-extension-conditioned-reversal`

## Validation status

`IMPLEMENTATION_VALIDATED / SCIENTIFIC_GATE_FAIL / INDEPENDENT_ASSURANCE_PENDING`

## Checks

- Preregistration was committed before pooled outcome calculation.
- Amendment 01 froze bootstrap algebra and matched-stratum weighting before pooled outcomes.
- Generic signal universe is independent of pivot selection.
- NY17 day open and lagged Daily ATR20 use only information available by signal time.
- H1 strong-wick threshold remains fixed at 30%.
- Dual-strong ambiguous H1 bars are excluded symmetrically.
- 2015–2025 only was opened for this study.
- 2026 YTD ending exclusive 2026-07-24 was not opened.
- Executable direction is side-correct: long ASK entry/BID exit; short BID entry/ASK exit.
- No missing-hour/weekend bridge is allowed.
- Pair-year clustered bootstrap uses 5,000 deterministic draws.
- 4H same-pair/same-direction cooldown robustness was executed.
- S2/R2 and S1/R1 incremental tests use frozen 0.25-Daily-ATR extension strata.
- 20 direct-source 2024 observations reproduce extension, entry price and REV4 with maximum absolute error 0.0.

## Result integrity

The pooled continuous extension slope is positive, but the preregistered promotion gate fails because extreme-extension expectancy is not positive/robust and historical partition stability fails. This validation record does not reinterpret that failure.

No threshold retuning, horizon switching, pair selection, pivot selection, session/day filter, stop/target optimization or 2026 exposure is authorized.

This record is implementation validation only and is not independent `governance_release_assurance`.
