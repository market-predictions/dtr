# Asia Sweep Standalone Research

This directory contains a strategy research program that is intentionally separate from Daytrading Rauf.

## Identity

- Strategy: `ASIA_SWEEP_STANDALONE_V0`
- Instruments: NQ and ES
- Signal timeframe: five-minute bars
- Execution source: one-minute bars
- Status: preregistration and signal-foundation work only
- Deployment: prohibited

## Separation

Asia Sweep may reuse the repository's audited data loader, resampling and later execution primitives. It must not call or modify the active DTR signal engine. All Asia Sweep manifests, governance, reports and tests live under this directory. Implementation code lives under `src/dtr_lab/strategies/asia_sweep/`.

## Current scope

The foundation implements a deterministic event ledger for four predeclared signal variants:

- AS-A: aggressive same-bar reclaim;
- AS-B: wick-qualified reclaim;
- AS-C: displacement confirmation;
- AS-D: failed-retest confirmation.

P&L simulation is intentionally not connected yet. First the data contract, event semantics, causality tests and DTR baseline protection must pass.

## Run the separate tests

```bash
PYTHONPATH=src pytest -c strategies/asia_sweep/pytest.ini
```

The repository's default `pytest` configuration does not discover this directory. That is intentional: DTR regression tests and Asia Sweep research tests remain distinct.

## Run the event-ledger foundation

```bash
python scripts/run_asia_sweep_manifest.py \
  strategies/asia_sweep/configs/manifests/nq_development.yaml
```

The ES manifest is blocked until a qualified ES dataset and checksum are registered.

## Evidence policy

A profitable historical result is not sufficient. Promotion requires independent positivity in NQ and ES, cost robustness, concentration controls, familywise-aware interpretation, historical lockbox validation and fresh out-of-sample evidence.
