# Daily H1 Execution Entry — Implementation Validation

Study: `DFXC-20260808-008-pivot-daily-execution-entry`

## Validation disposition

`IMPLEMENTATION_VALIDATED_SCIENTIFIC_GATE_FAILED`

## Checks

- Used only permanent cached Dukascopy FX Cash archives; no acquisition occurred.
- Source universe: ten canonical pairs, M1 BID and ASK, 2015–2025 only.
- 2026 YTD members were never opened by the execution runner or control runner.
- H1 event keys were asserted one-for-one against the frozen parent event ledger and H1 midpoint cache.
- Executable side semantics: long ASK entry/BID exit; short BID entry/ASK exit.
- Active-minute semantics and continuity rules match preregistration Amendment 01.
- Primary ledger contains 68,118 S1/R1 core signals; 64,267 are jointly evaluable.
- Pair-year clustered bootstrap used 5,000 deterministic draws.
- 4H cooldown robustness preserves the negative confirmation expectancy.
- Matched outer and S2/R2 controls use identical execution mechanics.
- Population-wide parent midpoint versus executable immediate correlation is 0.9981; mean deterioration (-0.0873 ATR) is consistent with observed spread scale (0.0842 ATR at entry).
- Separate direct-source audit: 20 randomly sampled 2024 observations, max absolute immediate error 0.0, max confirmation error 0.0, trigger match 20/20.

## Scientific boundary

The statistically significant confirmation improvement does not satisfy the preregistered economic gate because confirmation expectancy remains negative with its entire 95% CI below zero. The outer-zone falsification control improves more than the pivot core. No stop/target phase is authorized.

## Assurance

Implementation validation is not independent governance assurance. `governance_release_assurance` remains pending.