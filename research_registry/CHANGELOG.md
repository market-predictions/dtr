# Research Registry Changelog

## v1.4.0 — 2026-08-08

### Added

- `DFXC-20260808-006-pivot-daily-level-decomposition`: named-level decomposition of the confirmed Daily/H1 pivot-wick association, with S1/R1 versus S2/R2 frozen as the primary diagnostic contrast.
- `DFXC-20260808-007-pivot-daily-time-weekday`: prospectively frozen Tokyo/London/New York Hour-1/2/3 and Monday-Friday forward-response study for Daily S1/R1 + strong H1 rejection.
- Causal forward endpoints from the next contiguous H1 open, including FWD1/FWD2/FWD4/FWD8 and 4H MFE/MAE.
- Explicit third-session-hour buckets, DST-safe local session clocks, NY17 weekday classification, S2/R2 and outer-zone controls, and 4H overlap/cooldown robustness.

### Scientific state

- Named-level reconstruction is concentrated at first-order S1/R1: **+2.393 pp** interaction versus **+0.203 pp** at S2/R2, a **+2.190 pp** descriptive tier contrast. Because the historical heavy terminal ledger cannot be replayed exactly, this remains `DESCRIPTIVE_ONLY` and creates no level-selection authority.
- The causal S1/R1 + strong-H1-wick baseline is not an immediate positive reversal strategy: mean FWD4 is approximately **−0.009 ATR**, with its clustered-bootstrap interval crossing zero.
- None of the nine preregistered Tokyo/London/New York Hour-1/2/3 FWD4 comparisons survives Holm correction; global session-phase heterogeneity is unsupported (p≈0.33).
- Weekday directional heterogeneity is unsupported (p≈0.55).
- The 2022–2025 apparent third-hour improvement does not replicate in 2015–2019 or 2020–2021; pooled H3 versus H1/H2 over 2015–2025 is approximately **+0.007 ATR** with a confidence interval crossing zero.
- Time nevertheless changes **movement magnitude** materially: London H1-H3 and New York H1-H2 expand both favorable and adverse 4H excursion, while Tokyo H2-H3 suppress both. Time is therefore retained as execution/volatility context rather than a directional entry filter.

### Reproducibility / administration

- The independent 2015–2025 full-history event implementation reproduces all 65,135 separately built 2022–2025 event keys, pivot groups, distances, wick values, ATR values, forward returns and excursion fields exactly.
- A deterministic 4H same-side/group cooldown leaves the time and weekday conclusions unchanged.
- Repaired inherited study-006 registry metadata to the canonical schema (`structural`, `DESCRIPTIVE_ONLY`, standard holdout labels, explicit controls/evidence/artifacts/provenance) without changing scientific estimates or interpretation.
- Registered both studies in machine and rendered indexes.

### Governance

- Implementation evidence, claims and handovers are prepared; independent `governance_release_assurance` remains pending.
- No extra session-hour mining, weekday mining, session×weekday mining, Pine, alerting, sizing or live trading is authorized.

## v1.3.0 — 2026-08-08

### Added

- `DFXC-20260808-005-pivot-fibonacci-substitution`: prospectively preregistered standard-Fibonacci pivot formula substitution for the established Daily→H1 and Weekly→H4 response architectures.
- Frozen standard Fibonacci coordinates: PP plus/minus 0.382, 0.618 and 1.000 prior-period range.
- Same-engine classic comparator and paired Fibonacci-minus-Classic formula-difference inference.
- Formula-substitution report, compact machine result, evidence manifest, implementation-validation record, work claim and assurance handover.

### Scientific state

- Daily Fibonacci→H1 preserves the pivot-specific wick phenomenon internally: **+1.052 pp**, 95% CI **[+0.634,+1.473] pp**, positive in 9/10 pairs; structural terminal effect **+1.314 pp**.
- Weekly Fibonacci→H4 SP10 is directionally positive but **borderline**: **+1.234 pp**, CI **[+0.012,+2.441] pp**, Holm p=0.0488, positive in 7/10 pairs.
- Paired Fibonacci-minus-Classic wick intervals cross zero on both horizons; **Fibonacci superiority is not established**.
- The most defensible interpretation is that Daily/H1 exhaustion is not uniquely dependent on classic floor-pivot algebra; range-derived local reference geometry can preserve the phenomenon under Fibonacci redistribution.
- Classic Daily/H1 remains the mature protected-holdout-confirmed benchmark; classic Weekly/H4 SP10 remains the stronger current weekly candidate.

### Reproducibility

- An initial provisional detector reconstruction was rejected before accepted Fibonacci conclusions because it updated the current-bar extreme before testing the earlier candidate, violating the frozen strict-later anti-circularity ordering.
- After restoring Amendment-02 event ordering, classic primary wick interactions reproduce the frozen parent headline effects within approximately **0.01 percentage point** on both horizons.
- Companion structural comparator effects retain recorded residuals of approximately +0.103 pp Daily and +0.066 pp Weekly because the historical large parent terminal-event ledger was intentionally not committed and cannot be replayed byte-for-byte.
- That residual is treated as immaterial to the robust Daily Fibonacci conclusion but material to the inference-boundary Weekly result.

### Data / governance

- Fibonacci outcomes use 2015–2021 only.
- 2022–2025 is not relabelled as a pristine Fibonacci holdout after its prior exposure in the related classic Daily/H1 programme.
- Implementation is release-candidate ready; independent `governance_release_assurance` remains required before merge.
- No formula retuning, alternative Fibonacci ratios, P&L strategy, Pine, alerts, sizing or live deployment is authorized.

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
