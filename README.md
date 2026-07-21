# DTR Optimization Lab

Python-first research and optimization framework for the Daytrading Rauf (DTR) strategy.

## Research policy

TradingView is parked as the primary research environment. The Lab tests explicit market hypotheses directly on historical data, instruments every setup funnel, performs chronological and cost robustness checks, and ports only a small number of independently supported finalists back to Pine.

The workflow is:

1. validate and normalize market data;
2. implement market logic as causal, testable modules;
3. report the full opportunity and rejection funnel;
4. test structural alternatives and context modules independently;
5. distinguish cohort association from implementable portfolio effects;
6. run chronological, cost, neighbourhood, walk-forward, and uncertainty checks;
7. reject modules that do not add value rather than combining them in search of a rescue effect;
8. port no more than a few robust finalists to Pine.

## Current scope

The first market is NQ futures using one-minute data from late December 2022 through 10 December 2025. NQ remains the sole optimization base for the current program. Other instruments and providers are deferred.

### Frozen reversal baseline

`DTR_PY_NQ_CANDIDATE_0_1_GAP_SAFE`

- 491 trades;
- 0.180235811449135R expectancy;
- 88.49578342152539R net;
- profit factor 1.3819983049452256;
- 14.107857513807524R maximum drawdown.

The original 504-trade observe-only reference is also preserved for historical reproducibility.

### Continuation branch

The standalone continuation engine is implemented. All unfiltered variants failed. `CONT_A2_PULLBACK_LATE60` is retained under `HOLD_FOR_FRESH_DATA`; it may not be combined with reversal or tuned further on the current sample.

### IFVG module

The causal IFVG detector, manifest runner, fixtures, and evidence are implemented. The decision is `REJECT_NO_INCREMENTAL_VALUE`: all five predeclared implementable IFVG filters lower aggregate expectancy versus the frozen reversal baseline. IFVG remains available for diagnostics only.

CISD is the next independent entry-confirmation work package.

## Installation

```bash
pip install -e ".[dev,research]"
```

## Reproducible research runs

### Frozen reference

```bash
python scripts/run_manifest.py configs/manifests/nq_candidate_0_1.yaml
```

### Gap-safe reversal baseline

```bash
python scripts/run_manifest.py configs/manifests/nq_candidate_0_1_gap_safe.yaml
```

### Continuation structural baseline

```bash
python scripts/run_continuation_manifest.py \
  configs/manifests/nq_continuation_structural_baseline.yaml
```

### Held continuation stress candidate

```bash
python scripts/run_continuation_manifest.py \
  configs/manifests/nq_continuation_late60_stress.yaml
```

### IFVG ablation

```bash
python scripts/run_ifvg_manifest.py \
  configs/manifests/nq_ifvg_ablation.yaml
```

Each manifest verifies the registered dataset checksum and writes deterministic research artifacts under `reports/<run_id>/`. Raw market data and bulk generated reports are excluded from Git.

## Evidence

Primary methodology and results are documented in:

- `docs/RESEARCH_RUN_2026-07-21.md`;
- `docs/NQ_GAP_SAFE_COMPARISON_2026-07-21.md`;
- `docs/CONTINUATION_RESEARCH_2026-07-21.md`;
- `docs/IFVG_ABLATION_RESEARCH_2026-07-21.md`;
- `results/2026-07-21/`.

These are research findings, not production-performance claims. Continuous-contract rollover, exact timestamp and daylight-saving semantics, session boundaries, and supplied VWAP reset semantics remain unresolved. No post-December-2025 paper-forward sample is included.

## Data policy

Raw market datasets and generated bulk artifacts are not committed to normal Git history. Dataset provenance, checksums, schema, and audit findings are committed under `data/catalog.yaml` and `docs/`.

## Operating principles

- No ranking by net profit alone.
- Every filter reports performance effect and opportunity coverage.
- Cohort and implementable portfolio results are separate.
- Entry, exit, and context modules are tested independently before combinations.
- Chronological forward evidence is mandatory.
- Parameter plateaus are preferred over sharp optima.
- Cost stress and conservative intrabar assumptions are mandatory.
- Missing bars are never silently synthesized into market structure.
- Negative results are retained and close the tested line of inquiry.
- A Python winner is not automatically a production strategy.
- TradingView is a later implementation-validation target, not the primary optimizer.

## Status

**v0.3.1 — gap-safe reversal baseline locked; continuation held for fresh data; IFVG rejected; CISD next.**
