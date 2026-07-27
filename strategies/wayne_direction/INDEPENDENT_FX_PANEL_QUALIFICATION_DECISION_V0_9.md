# Wayne Independent FX Panel Qualification Decision v0.9

Date: 2026-07-27  
Authoritative run: `30259833965`  
Artifact: `wayne-replication-panel-decision`  
Artifact digest: `sha256:65664988a90e34b3ec03a3a7cdea92176aa085a06b9cf8aa35fd90611267c7db`

## Binding decision

`PASS_PANEL_QUALIFICATION_OPEN_REPLICATION_OUTCOMES`

No Wayne structure event, monthly location, target reach, return or P&L was inspected during this phase.

## Frozen candidate panel

- EURGBP
- EURJPY
- GBPJPY
- NZDUSD

No replacement symbol was added after qualification began.

## Results

| Pair | Active calendar | Median spread | P95 spread | P99 spread | Full D1 | Full H4 | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| EURGBP | 70.93% | 0.9 pip | 2.0 pips | 5.1 pips | 100.00% | 99.94% | qualify |
| EURJPY | 70.99% | 0.6 pip | 1.6 pips | 4.4 pips | 100.00% | 99.93% | qualify |
| GBPJPY | 70.97% | 1.6 pips | 3.7 pips | 9.9 pips | 100.00% | 99.94% | qualify |
| NZDUSD | 70.81% | 1.1 pips | 2.1 pips | 5.1 pips | 99.94% | 99.89% | qualify |

Every pair also had:

- exact 2015–2021 calendar-minute partitions;
- zero BID/ASK active-quote mismatches;
- zero invalid active OHLC rows;
- zero invalid or negative active close spreads;
- complete seven-year coverage;
- all preregistered source gates passed.

## Implementation correction

The first qualification attempt applied a full-calendar Boolean mask to an active-only spread series when constructing annual spread summaries. This was an index-alignment implementation error, not a source defect. The annual slice now uses the active spread series' own datetime index, and a regression test freezes that behavior.

The frozen candidate set and all source-quality thresholds remained unchanged.

## Authorization

The exact day-10 technical sequence may now be run on all four qualified pairs with no changes to:

- monthly location;
- H4 structure;
- moving-average health;
- day-10 landmark;
- target availability;
- conservative or stretch targets;
- clustered inference.

The 2022–2025 partitions remain excluded. Yield, VIX, seasonality, macro, execution and P&L remain closed pending the replication decision.
