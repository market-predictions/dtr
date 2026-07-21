# DTR Optimization Lab

Python-first research and optimization framework for the Daytrading Rauf (DTR) strategy.

## Research policy

TradingView is parked as the primary research environment. The Lab starts from the known DTR market concept and tests structural alternatives directly on historical market data. Pine and TradingView are used later to implement and validate a small number of robust finalists, not to define the Python baseline.

The workflow is:

1. validate and normalize market data;
2. implement DTR market logic as explicit, testable Python modules;
3. instrument the complete setup funnel and rejection reasons;
4. run staged experiments for BOS/MSS, sweeps, regime, calendar, timing, risk, and exits;
5. perform walk-forward, cost-stress, parameter-neighbourhood, and Monte Carlo checks;
6. add new modules only when they demonstrate independent value;
7. port no more than a few robust finalists back to Pine.

## Current scope

The first market is NQ futures using one-minute data from late December 2022 through 10 December 2025. The current research engine implements the reversal branch with:

- London 2AM, New York 9AM, and Asia 7PM session ranges;
- first one-sided range sweep and reclaim;
- configurable protected pivots and BOS definitions;
- impulse and acceptance requirements;
- break-close and retest entries;
- efficiency-ratio, ADX, VWAP, weekday, and session filters;
- structural/ATR stops, TP1, runner, breakeven, time close, and maximum hold;
- one-minute intrabar stop/target simulation;
- complete funnel counters and attribution.

Continuation, IFVG/CISD, H1Vol, Weekly VWAP, higher-timeframe scoring, and footprint logic remain separate work packages.

## Reproducible research runs

A research run is defined by a YAML manifest containing:

- dataset path and SHA-256 checksum;
- timestamp and timezone assumptions;
- development, validation, and later-research periods;
- complete `StrategyConfig` parameters;
- execution and random-seed assumptions;
- optional regression expectations.

Run the current candidate with:

```bash
pip install -e ".[dev,research]"
python scripts/run_manifest.py configs/manifests/nq_candidate_0_1.yaml
```

The command verifies the dataset checksum, runs the strategy, checks the frozen baseline, and writes deterministic CSV, Parquet, JSON, funnel, and attribution artifacts under `reports/<run_id>/`.

## Parameter research

The staged pack runner remains available for controlled research:

```bash
python scripts/run_research.py data/raw/NQ_Futures_-_1min_Bar_2022_2025.zip --pack bos
```

Available packs are `baseline`, `bos`, `sweep`, `regime`, `timing`, `risk`, and `exit`.

## First research run

The first staged run evaluated **904 controlled configurations**. The current research candidate is `DTR_PY_NQ_CANDIDATE_0_1`.

Methodology, results, limitations, and artifacts are documented in:

- `docs/RESEARCH_RUN_2026-07-21.md`
- `configs/nq_candidate_0_1.yaml`
- `configs/manifests/nq_candidate_0_1.yaml`
- `results/2026-07-21/`

These are research findings, not production-performance claims. Continuous-contract rollover and exact timestamp semantics remain unresolved, and no post-December-2025 paper-forward sample exists yet.

## Data policy

Raw market datasets and generated bulk artifacts are not committed to normal Git history. Dataset provenance, checksums, schema, and audit findings are committed under `data/catalog.yaml` and `docs/`.

## Operating principles

- No ranking by net profit alone.
- Every filter reports performance effect and opportunity coverage.
- Entry and exit modules are tested separately before combinations.
- Chronological forward folds are mandatory.
- Parameter plateaus are preferred over sharp optima.
- Cost stress and conservative intrabar assumptions are mandatory.
- A Python winner is not automatically a production strategy.
- TradingView is a later implementation-validation target, not the primary optimizer.

## Status

**v0.2.1 — manifest-driven reproducibility and baseline-integrity work in progress.**
