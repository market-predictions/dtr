# Changelog — Daily H1 Continuation Management

## v0.1.0 — 2026-08-08

### Changed

- Added a new decision-role study for an existing continuation position encountering Daily S1/R1 plus a strong completed H1 rejection.
- Frozen `EXIT_NOW` versus 1H/2H/4H/8H continuation holding with 4H as the primary endpoint.
- Used executable BID liquidation for incoming longs at R1 and ASK liquidation for incoming shorts at S1.
- Added matched S1/R1 outer-zone and S2/R2 controls, pair-year clustered inference, 4H cooldown robustness and direct-source audit.
- Preserved 2026 YTD as conditional fresh evidence; it was not opened because the internal promotion gate failed.

### Why

The preceding executable-entry study showed that the structural S1/R1 rejection association does not create a profitable fresh reversal entry after quoted spread. The next first-principles question was therefore whether the same event has value for managing an already-open continuation position.

### Result

- S1/R1 core HOLD4: +0.0050 ATR, CI [-0.0094,+0.0189].
- Matched outer HOLD4: +0.0156 ATR.
- Core-minus-outer: -0.0106 ATR, CI [-0.0302,+0.0089].
- Development and validation core effects are positive; only 3/10 pairs are negative.
- Cooldown leaves core HOLD4 positive.

Decision: `REJECT_EXIT_NOW_MANAGEMENT_RULE_NO_ABSOLUTE_OR_PIVOT_SPECIFIC_4H_EDGE`.

### Known limitations

- The original entry and accumulated P&L of the hypothetical existing position are intentionally outside scope.
- 2015-2025 is exposed in related pivot research; only the management decision semantics were newly preregistered.
- This rejects a simple universal exit rule, not every conceivable position-management policy.

### Next roadmap items

- Do not optimize this failed management rule.
- Keep 2026 YTD sealed for a genuinely new frozen hypothesis.
- Complete exact-head CI and independent assurance of the research record.
- Reassess whether the pivot programme has another materially distinct market question before further testing.
