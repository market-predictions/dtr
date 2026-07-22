# DTR Optimization Lab Status

## Current work package

`DTR-NQ-WP-20260722-06 — Baseline validity reset`

Status: **claimed; causal design complete; implementation starting**

Branch: `agent/nq-baseline-validity-reset`

Decision state: `DEPLOYMENT_BLOCKED_PENDING_BASELINE_RESET`

## Trigger

An independent source-and-evidence review found that the current `reject_unsafe` benchmark retrospectively discards trades when an unsafe data gap occurs after entry. The rule uses the simulated future exit and changes later portfolio eligibility using future information.

The 491-trade benchmark is therefore preserved for historical reproducibility but suspended as the active comparison baseline.

## Locked primary dataset

Dataset SHA-256:

`8d3f157a422636e5b8dda51cc3a3d9209c50cb53f9b279d3e14b627ce59370dc`

NQ remains the sole research base. Raw data remains outside Git.

## Historical benchmarks

### Observe-only reference

- trades: `504`;
- expectancy: `0.1669927760762483R`;
- net R: `84.16435914242919R`;
- maximum drawdown: `14.107857513807524R`.

This result bridges missing data and is retained only for regression.

### Retrospective gap-reject benchmark

- trades: `491`;
- expectancy: `0.180235811449135R`;
- net R: `88.49578342152539R`;
- maximum drawdown: `14.107857513807524R`.

This result is noncausal for four open-trade gap cases and may not be used for deployment or final module comparison.

## Active reset tasks

- causal conservative open-trade gap liquidation;
- exact baseline refreeze and changed-trade attribution;
- timestamp bar-open versus bar-close evidence;
- continuous-contract rollover sensitivity;
- committed baseline uncertainty and selection-pressure code;
- session×weekday concentration analysis;
- no-retune reruns of continuation, IFVG, CISD, and entry routing.

## Blocked work

PR #5 — reversal entry-routing ablation — remains draft and blocked. Its completed preliminary evidence is preserved but must be rerun against the corrected benchmark.

## Closed module decisions under review

- continuation: `HOLD_FOR_FRESH_DATA`;
- IFVG confirmation: `REJECT_NO_INCREMENTAL_VALUE`;
- CISD confirmation: `REJECT_NO_INCREMENTAL_VALUE`;
- entry routing: preliminary `REJECT_NO_INCREMENTAL_VALUE` on the suspended benchmark.

These decisions remain informative but are not final until no-retune reruns complete.

## Deployment restrictions

No production deployment, Pine strategy port, position sizing recommendation, or profitability claim is authorized.

Fresh 2026 data may not be inspected until the corrected benchmark and preregistered continuation/deployment gate are committed.
