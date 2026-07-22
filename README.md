# DTR Optimization Lab

Python-first research and validation framework for the Daytrading Rauf strategy.

## Current decision

`CONTINUE_RESEARCH_DO_NOT_DEPLOY`

The reversal concept remains positive on the available NQ history after correcting a noncausal missing-data rule. It is not approved for capital deployment, Pine strategy release, or position-sizing recommendations.

## Evidence hierarchy

### Active corrected research benchmark

`DTR_PY_NQ_CANDIDATE_0_1_CAUSAL_GAP`

- 495 trades;
- 0.173746993R expectancy;
- 86.004761R net;
- profit factor 1.366383;
- maximum drawdown 14.107858R;
- return-to-drawdown 6.096231.

Open positions are liquidated causally when an unsafe missing-data gap becomes observable. The exit uses no better than the worse of active-stop execution and first post-gap-open execution.

### Historical references

- Observe-only: 504 trades, 0.166993R expectancy, 84.164359R net. This may bridge missing data and is retained for regression only.
- Retrospective reject: 491 trades, 0.180236R expectancy, 88.495783R net. This used future gap information and is suspended.
- Rolling walk-forward procedure: 289 test trades, 0.151217R expectancy, 43.701603R net. Four folds selected four different configs; this is historical procedure evidence, not pristine OOS.

## Validity status

- **Timestamp:** unresolved. Vendor ETH VWAP supports HLC3 × volume but cannot distinguish bar-open from bar-close labels.
- **Continuous contract:** unresolved. Roll-adjacent exclusion is material, but candidate dates do not prove splice contamination.
- **Selection pressure:** unresolved. Descriptive block-bootstrap intervals are positive, but no aligned 904-candidate return matrix exists for familywise correction.
- **Concentration:** material. London Friday is the largest cell; London removal reduces expectancy to approximately 0.102R.
- **Fresh OOS:** not run. A qualified 2026-data test is preregistered.
- **Python/Pine parity:** not run.

## Module decisions after corrected-baseline rerun

- Continuation: `HOLD_FOR_FRESH_DATA`; the 147-trade late-60 lead is 0.108895R but negative at four-tick slippage.
- IFVG: `REJECT_NO_INCREMENTAL_VALUE`.
- CISD: `REJECT_NO_INCREMENTAL_VALUE`; retest remains diagnostic only.
- First-pullback/hybrid routing: `REJECT_NO_INCREMENTAL_VALUE`; PR #5 remains draft pending rebase.

## Reproducible runs

```bash
pip install -e ".[dev,research]"

python scripts/run_manifest.py \
  configs/manifests/nq_candidate_0_1_causal_gap.yaml

python scripts/run_baseline_validity_review.py \
  configs/manifests/nq_candidate_0_1_causal_gap.yaml \
  --out reports/nq_baseline_validity

python scripts/run_continuation_manifest.py \
  configs/manifests/nq_continuation_structural_baseline.yaml

python scripts/run_continuation_manifest.py \
  configs/manifests/nq_continuation_late60_stress.yaml

python scripts/run_ifvg_manifest.py \
  configs/manifests/nq_ifvg_ablation.yaml

python scripts/run_cisd_manifest.py \
  configs/manifests/nq_cisd_ablation.yaml
```

Each manifest verifies the registered dataset checksum. Raw market data and bulk reports remain outside Git.

## Research policy

1. Data and execution semantics precede optimization.
2. Every decision must be causal at the time it is made.
3. Full-sample, walk-forward, and pristine OOS results are reported separately.
4. Cohort association and implementable portfolio effects remain separate.
5. Negative results are retained.
6. Rejected modules are not combined to rescue them.
7. Fresh data is not inspected before preregistration.
8. A Python result is not a production strategy.

## Primary evidence

- `docs/BASELINE_VALIDITY_RESEARCH_2026-07-22.md`
- `docs/FRESH_OOS_PREREGISTRATION_2026-07-22.md`
- `results/2026-07-22/nq_baseline_validity_summary.json`
- `results/2026-07-22/nq_baseline_reset_consolidated_summary.json`
