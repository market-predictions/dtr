# Corrected Long-Only Counterfactual — 2026-07-23

## Root cause

The first exploratory long-only run set `allow_short: false` on the same configuration used to detect management events. That disabled both short entries and complete opposite short Step-3 sequences that normally close open long trades. The run therefore changed two dimensions at once: entry direction and exit logic.

The corrected contract is:

- entry detector: long signals only;
- management detector: both long and short sequences remain observable;
- an opposite short Step-3 may close a long;
- no short position may be opened.

The original long-only artifacts are superseded and may not be used for promotion, comparison, or roadmap decisions.

## Corrected findings

### NQ proxy

Only the no-map control changed. Four long positions exited earlier on valid opposite short management signals rather than later protective stops.

- no-map: 695 trades, 66.177639R net, 0.095220R expectancy, 109.646217R maximum drawdown;
- EMA map: unchanged at 294 trades, 63.736293R net, 0.216790R expectancy;
- EMA plus breakout: unchanged at 165 trades, 49.214774R net, 0.298271R expectancy;
- strict close: unchanged at 275 trades, 53.059197R net, 0.192943R expectancy.

Every NQ-proxy 95% date-block interval still crosses zero. EMA map remains the primary exploratory candidate because it is positive in all four observed calendar years. Strict close remains secondary. EMA plus breakout remains diagnostic because 2023 is negative.

### ES proxy

Only the no-map control changed. Twelve long positions received earlier opposite-signal exits.

- no-map: 681 trades, 72.584319R net, 0.106585R expectancy, 60.746438R maximum drawdown;
- mapped candidates remain weak or negative;
- the no-map 95% interval remains below and above zero;
- 2024 remains negative.

ES proxy does not independently validate the NQ mapped candidates.

### GBPUSD

The corrected no-map control improved but remained decisively negative:

- 682 trades;
- -276.465057R net;
- -0.405374R expectancy;
- 95% date-block interval: -0.643039R to -0.111630R.

All mapped GBPUSD arms were unchanged and negative. GBPUSD remains rejected.

## Decision

`CORRECTED_COUNTERFACTUAL_RETAINS_NQ_HYPOTHESIS_NO_PROMOTION`

The correction does not overturn the exploratory NQ candidate ranking, but it invalidates the original no-map long-only artifacts. The next legitimate step is a preregistered replication on the checksum-qualified NQ futures archive with simpler mechanism controls, costs, delayed execution, chronological attribution, matched-time controls, and all-required promotion gates.

Compact corrected summaries and inference are stored under `strategies/stoic_123/results/2026-07-23/`. Trade-level ledgers and raw market data remain outside Git.
