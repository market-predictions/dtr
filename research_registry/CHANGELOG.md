# Research Registry Changelog

## v1.2.0 — 2026-08-08

### Added

- `DFXC-20260808-003-pivot-daily-wick-holdout`: exact protected 2022–2025 confirmation of the frozen Daily-pivot × H1 wick interaction.
- `DFXC-20260808-004-pivot-weekly-h4-zone-geometry`: preregistered seven-geometry Weekly/H4 spacing/ATR robustness family.
- Principal holdout-authorization record, two weekly implementation-deviation records, machine summaries, final report, implementation validation, claim and assurance handover.

### Scientific state

- Daily/H1 protected holdout **CONFIRMS**: +1.08 pp pivot-specific wick interaction, 95% CI [+0.65,+1.54] pp; 10/10 pair effects, 4/4 years, both preregistered halves and all leave-one-pair-out pools positive.
- The Daily/H1 2022–2025 holdout is now consumed for that exact question.
- The inherited Weekly/H4 zone is confirmed to be spacing-relative, not ATR-based.
- Weekly/H4 `SP10` (0–10% adjacent-pivot spacing core versus equal-width 40–50% control) is the sole joint survivor of the seven-geometry family: structural +1.00 pp; wick interaction +1.62 pp, 95% CI [+0.52,+2.69] pp, Holm p=0.0308.
- `SP15`, `SP20_REF`, `SP25` and all three ATR-capped hybrids fail the joint wick gate.
- Weekly/H4 2022–2025 outcomes were not inspected; `SP10` remains an internal candidate requiring future independent confirmation.

### Reproducibility

- Two preliminary Weekly/H4 challenger runs were invalidated before scientific acceptance because `SP20_REF` did not exactly reproduce the parent result.
- Final boundary semantics reproduce the parent SP20 structural and wick point estimates exactly to floating-point precision.
- Separate compact-ledger arithmetic validation recomputed the Daily holdout, SP10 and SP20 primary effects exactly.

### Governance

- Implementation candidate is ready for independent `governance_release_assurance`.
- No Weekly/H4 holdout exposure, strategy/P&L, Pine, alerts, sizing or live deployment is authorized.

## v1.1.0 — 2026-08-08

### Added

- Prospectively preregistered `DFXC-20260808-001-pivot-multiscale-terminal`.
- Prospectively conditional `DFXC-20260808-002-pivot-wick-rejection`.
- Scale-aligned pivot/leg mapping test: D/H1, W/H4, M/D1, Q/W1, Y/MN1 plus H1 mismatch benchmarks.
- Strict later-bar endpoint-confirmation amendment to prevent wick/termination circularity.
- Compact multiscale and wick result records, final internal report, evidence manifest and implementation-validation record.

### Scientific state

- Daily/H1 and Weekly/H4 terminal-zone mappings pass the frozen internal structural gate.
- Monthly/D1, Quarterly/W1 and Yearly/MN1 fail; higher-timeframe scale alignment does not rescue those pivot horizons.
- Daily/H1 pivot-core wick interaction passes internally at +0.92 pp beyond generic wick exhaustion.
- Weekly/H4 wick interaction remains failed because its uncertainty interval crosses zero / p=0.0744.
- Protected 2022–2025 remains unopened.

### Governance

- Implementation validation is complete.
- Independent `governance_release_assurance` remains pending; no holdout, strategy or deployment authority is created by these internal results.

## v1.0.0 — 2026-08-08

### Added

- Canonical research name **Dukascopy FX Cash** and machine ID `dukascopy_fx_cash_m1_bid_ask_v1`.
- Durable study/result object model with immutable `DFXC-*` study IDs.
- Machine-readable and human-readable master indexes.
- Branch-resident evidence contract using exact Git commit SHAs.
- Falsification, holdout, assurance, negative-result and prohibited-rescue fields.
- Registry validator, deterministic index renderer and CI-covered tests.
- Retrospective normalized entries for Quarters Theory Stage-1, ten-pair Quarters confirmation, classic-pivot target/stall/reversal falsification and pivot spatial-zone follow-up.
- Historical migration queue for older Dukascopy FX branches.

### Compatibility

- Existing permanent private cache, Drive folder, source checksums and legacy catalog key remain unchanged.
- Strategy-specific implementations remain in their existing locations.
- No raw market data is added to Git.
- No protected holdout is opened.

### Governance

The initial registry candidate was implementation-complete and independently validated before merge to `main`.
