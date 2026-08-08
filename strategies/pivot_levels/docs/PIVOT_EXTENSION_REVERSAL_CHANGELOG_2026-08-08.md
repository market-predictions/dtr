# Extension-Conditioned Reversal — Full Changelog

## v0.1.0 — 2026-08-08

### Added
- Prospectively frozen generic strong-H1-rejection universe independent of Daily pivot selection.
- Lagged Daily ATR20 directional-extension metric from NY17 FX-day open to rejection extreme.
- Frozen E0/E1/E2/E3 extension bins.
- Real Dukascopy BID/ASK executable 1H/2H/4H/8H countertrend outcomes.
- Pair-year clustered continuous extension slope and extreme-vs-low extension contrasts.
- 4H same-pair/same-direction cooldown robustness.
- Extension-matched S2/R2 and S1/R1 incremental pivot tests.
- Direct-source 20-observation execution/extension audit.

### Scientific result
- Pooled extension slope is small positive, but extreme-extension 4H expectancy remains negative and historical stability fails.
- Recent 2022–2025 behavior is substantially more mean-reverting after extreme extension than 2015–2021.
- S2/R2 does not add reversal expectancy after extension is controlled.
- Decision: `REJECT_EXTENSION_CONDITIONED_REVERSAL_NO_STABLE_EXECUTABLE_EDGE`.

### Known limitations
- 2015–2025 is an exposed research environment; only this exact extension architecture was prospectively frozen.
- Extreme extension is rare, producing materially wider uncertainty.
- No commissions beyond quoted spread or ordinary slippage were added.
- The positive pooled continuous slope is regime-unstable and cannot be represented as a trading rule.

### Next
- Preserve 2026 YTD unopened.
- Do not optimize extension thresholds, horizons, pivots, sessions, weekdays, stops or targets on this failed architecture.
- Any continuation requires a materially different market hypothesis.
