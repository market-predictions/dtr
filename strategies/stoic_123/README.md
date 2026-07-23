# Stoic Edge 1-2-3 Research Framework

Status: **separate research strategy; not part of the DTR signal family**

This directory governs a mechanical, causal test of the published Stoic Edge 1-2-3 sequence on the available NQ archive and the qualified Dukascopy USA500 dataset. The USA500 stream is labelled `ES_PROXY` throughout because it is a bid-CFD proxy with ES-equivalent execution economics, not CME ES futures.

## Market question

Does a map-first break → retest → predeclared base → confirmed breakout sequence produce a repeatable intraday continuation edge after realistic costs, and does the mechanism transfer from NQ to an S&P 500 proxy without instrument-specific tuning?

## Isolation contract

- Separate source namespace: `src/stoic_123_lab`.
- Separate strategy governance: `strategies/stoic_123`.
- Separate runner and outputs: `scripts/run_stoic_123.py` and a dedicated result directory.
- No changes to DTR signal generation, E5/E6 rules, baselines, selection decisions, or DTR result ledgers.
- Shared use is limited to qualified data loaders and established repository dependencies.
- NQ and `ES_PROXY` results remain separate. Pooled optimization is prohibited.

## Causal rule translation

1. **Higher-timeframe map** — a declared 60-minute map qualifies direction through one frozen map mode.
2. **Step 1: break** — the execution bar must close beyond both the 10 and 20 EMAs by a declared ATR buffer. A wick does not count.
3. **Step 2: retest and base** — price returns to the EMA zone, then a compact overlapping base forms. The retest bar is excluded from the base.
4. **Boundary lock** — the base high and low are frozen when the base first qualifies. They cannot move after later price information arrives.
5. **Step 3: confirmation** — a later bar closes beyond the frozen boundary. The baseline fill is the next available one-minute open.
6. **Protective risk** — the initial stop is outside the opposite frozen boundary. Gaps beyond the declared tolerance liquidate rather than bridge missing prices.
7. **Technical exit** — the remaining position exits on a complete opposite 1-2-3 signal from the management timeframe declared before entry.
8. **Maximum hold** — a separate fail-safe prevents indefinite exposure when no opposite technical sequence appears.

## Frozen phase-one family

`configs/phase1.yaml` contains six preregistered arms:

- no-map mechanical control;
- 60-minute EMA alignment map;
- recent 60-minute breakout map;
- EMA plus breakout map;
- stricter Step-2 base;
- stricter Step-1 and Step-3 closes.

The family is deliberately small. It tests the article's unresolved definitions without turning the historical sample into an unrestricted optimizer.

## Run

```bash
python scripts/run_stoic_123.py \
  --nq /path/to/frozen_nq_archive.zip \
  --es-proxy /path/to/usa500_2022_2025.csv \
  --config strategies/stoic_123/configs/phase1.yaml \
  --out results/stoic_123/2026-07-23/phase1
```

The runner verifies source checksums, audits data, runs every arm separately on both instruments, validates event chronology, simulates one-minute execution, reconstructs the trade ledger through an independent arithmetic path, and writes:

- `summary.csv`;
- `inference.csv`;
- `data_audit.csv`;
- `independent_review.csv`;
- per-arm event, management-event, trade, and funnel files;
- `decision.json`;
- `run_manifest.json`.

## Promotion standard

A profitable full-sample result is insufficient. A finalist must show:

- positive net expectancy after declared costs;
- acceptable drawdown and concentration;
- chronological stability;
- date-block uncertainty that is not dominated by a few days;
- relevance on both NQ and `ES_PROXY`, while permitting different effect sizes;
- robustness to nearby, preregistered definitions;
- no causal, boundary, overlap, or gap-handling audit failures.

Passing phase one authorizes additional paper research only. It does not authorize live trading, position sizing, a Pine port, or relabelling the proxy as ES futures.
