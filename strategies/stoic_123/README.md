# Stoic Edge 1-2-3 Research Framework

Status: **separate research strategy; not part of the DTR signal family**

This directory governs a mechanical, causal test of the published Stoic Edge 1-2-3 sequence. Supported streams are the qualified NQ futures archive, explicitly labelled Dukascopy `NQ_PROXY` and `ES_PROXY` index-CFD archives, and Dukascopy GBPUSD bid/ask data. Proxy results are never relabelled as CME futures.

## Market question

Does a map-first break → retest → predeclared base → confirmed breakout sequence produce a repeatable intraday continuation edge after realistic costs, and does the mechanism transfer across instruments without instrument-specific tuning?

## Isolation contract

- Separate source namespace: `src/stoic_123_lab`.
- Separate strategy governance: `strategies/stoic_123`.
- Separate runner and outputs: `scripts/run_stoic_123.py` and a dedicated result directory.
- No changes to DTR signal generation, E5/E6 rules, baselines, selection decisions, or DTR result ledgers.
- Instrument results remain separate. Pooled optimization is prohibited.
- `NQ_PROXY` and `ES_PROXY` are bid-CFD research proxies, not CME futures.

## Causal rule translation

1. **Higher-timeframe map** — a declared 60-minute map qualifies direction through one frozen map mode.
2. **Step 1: break** — the execution bar must close beyond both the 10 and 20 EMAs by a declared ATR buffer. A wick does not count.
3. **Step 2: retest and base** — price returns to the EMA zone, then a compact overlapping base forms. The retest bar is excluded from the base.
4. **Boundary lock** — the base high and low are frozen when the base first qualifies. They cannot move after later price information arrives.
5. **Step 3: confirmation** — a later bar closes beyond the frozen boundary. The baseline fill is the next available one-minute open.
6. **Protective risk** — the initial stop is outside the opposite frozen boundary. Gaps beyond the declared tolerance liquidate rather than bridge missing prices.
7. **Technical exit** — the remaining position exits on a complete opposite 1-2-3 signal from the management timeframe declared before entry.
8. **Maximum hold** — a separate fail-safe prevents indefinite exposure when no opposite technical sequence appears.

## GBPUSD execution contract

- The original private archive is checksum-gated.
- The known source-writer defect is repaired explicitly: stored `high` is BI5 close and stored `close` is BI5 high.
- Rows where both bid and ask volume are zero are inactive carry-forward minutes and are excluded from tradable data.
- Signal detection uses midpoint OHLC.
- Long entries buy ask and long exits sell bid.
- Short entries sell bid and short exits buy ask.
- Stop triggers use bid lows for longs and ask highs for shorts.
- Spread is embedded in fills; declared slippage is applied additionally and commission remains explicit.

## Frozen phase-one family

`configs/phase1.yaml` contains six preregistered arms:

- no-map mechanical control;
- 60-minute EMA alignment map;
- recent 60-minute breakout map;
- EMA plus breakout map;
- stricter Step-2 base;
- stricter Step-1 and Step-3 closes.

The configuration SHA-256 remains `5d6909bd5740e1cdea9bd3d47a9818289a6faa8b9a61338726afdc53289ff805`.

## Run

Run one or more streams without pooling:

```bash
python scripts/run_stoic_123.py \
  --nq-proxy /path/to/NQ_PROXY_DUKASCOPY_USATECH_M1_BID_FULL_GRID_UTC_ET.zip \
  --es-proxy /path/to/ES_PROXY_DUKASCOPY_USA500_M1_BID_FULL_GRID_UTC_ET.zip \
  --gbpusd /path/to/GBPUSD_DUKASCOPY_M1_BID_ASK_ACTIVE_UTC_REPAIRED.csv.gz \
  --config strategies/stoic_123/configs/phase1.yaml \
  --out results/stoic_123/2026-07-23/phase1
```

`--nq` remains available for the checksum-qualified NQ futures archive. At least one source argument is required.

The runner verifies checksums, audits data, caches required resamples, runs each arm separately, validates event chronology, simulates one-minute execution, reconstructs every trade ledger through an independent arithmetic path, and writes summaries, inference, audits, events, trades, funnels, decisions, and a run manifest.

## Current GBPUSD decision

The untouched six-arm family was run over 2022-2025. All six arms were negative and classified `NO_EDGE`. The strongest result by expectancy was still materially negative: the no-map control produced 1,233 trades, -555.69R net, and -0.451R expectancy. GBPUSD transfer is rejected at phase one; no tuning is authorized from this result.

## Promotion standard

A profitable full-sample result is insufficient. A finalist must show positive net expectancy after declared costs, acceptable drawdown and concentration, chronological stability, date-block uncertainty not dominated by a few days, cross-instrument relevance, nearby-definition robustness, and zero causal or execution-audit failures.

Passing phase one authorizes additional paper research only. It does not authorize live trading, position sizing, a Pine port, or relabelling proxies as futures.
