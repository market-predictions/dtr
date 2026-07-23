# Work Package AS-WP-20260723-07 — First Proxy Baseline and Independent Shadow Replay

## Objective

Run one frozen development-period baseline to determine whether the current Asia Sweep specification shows enough promise to justify further research.

The baseline uses the registered private Dukascopy NQ and ES index-CFD proxies and an independent shadow replay of the already-frozen normalization and execution semantics. It does not connect private data to the production synthetic-only adapter and does not claim CME-futures validity.

## Research question

Does any preregistered Asia Sweep variant produce a positive, sufficiently broad after-cost result in both NQ and ES proxies during the development period?

## Frozen data scope

- NQ proxy: Dukascopy `usatechidxusd`, BID, full one-minute quote grid.
- ES proxy: Dukascopy `usa500idxusd`, BID, full one-minute quote grid.
- Development period only: `2023-01-01` through `2024-06-30` inclusive.
- Historical-validation and later-research partitions remain unopened.
- Canonical source checksums must match the registered manifests.
- Provider authorization remains unresolved; raw source data may not be committed or uploaded in result artifacts.

## Frozen strategy variants

1. `AS_A_AGGRESSIVE_RECLAIM`
2. `AS_B_WICK_QUALIFIED`
3. `AS_C_DISPLACEMENT`
4. `AS_D_FAILED_RETEST`

No variant may be added, removed, combined or tuned after outcomes are visible.

## Frozen normalization

The independent replay must reproduce `DIRECTIONAL_PESSIMISTIC_V1`:

- source increment: `0.001`;
- execution tick: `0.25`;
- long event entry and stop: ceiling to execution grid;
- short event entry and stop: floor to execution grid;
- normalized risk must exceed one execution tick;
- target: exactly `2.0R` from normalized event entry and stop;
- long entry-minute open: ceiling; later OHLC: floor;
- short entry-minute open: floor; later OHLC: ceiling;
- minimal OHLC-envelope repair only;
- timestamps, missing minutes and activity flags remain unchanged.

## Frozen execution assumptions

- entry: normalized one-minute open at the exact signal timestamp;
- entry slippage: one tick adverse;
- protective-stop slippage: one tick adverse;
- market/time/data exit slippage: one tick adverse;
- collision policy: stop first;
- maximum inactive run: 10 minutes;
- target: `2.0R` from the slipped entry and fixed normalized stop;
- time exit: execution-window-end open;
- NQ proxy point value: `$20`;
- ES proxy point value: `$50`;
- commission: `$2.25` per side;
- full position; no partials, breakeven move or re-entry.

## Independent shadow-replay boundary

- The baseline engine must not call the production `normalize_proxy_fixture`, `execute_mapped_event` or `simulate_execution` functions.
- It must reproduce their frozen semantics independently.
- Synthetic unit fixtures must demonstrate parity on target, stop, gap, time-exit, activity and commission cases.
- Any unexplained parity mismatch invalidates the baseline.
- This is independent code replication within the same session, not an external human audit.

## Required outputs

Per trade:

- instrument, date, window, variant and direction;
- normalized event entry, stop and target;
- actual slipped entry and execution target;
- exit timestamp, exit price and reason;
- gross points, gross R, commission R and net R;
- holding minutes, collision flag and gap minutes;
- explicit blocked or unresolved reason.

Per instrument and pooled per variant:

- signal count;
- exited, blocked and unresolved count;
- net R and expectancy;
- gross expectancy before commission;
- win rate and profit factor;
- maximum drawdown in R;
- return/drawdown ratio;
- target, stop and time-exit rates;
- 2023 and 2024-H1 net R;
- London/New York and long/short breakdowns.

## Preregistered promise classification

A variant is `PROMISING_DEVELOPMENT_SCREEN` only when all are true:

1. at least 50 exited trades in NQ proxy;
2. at least 50 exited trades in ES proxy;
3. positive net expectancy in each proxy;
4. pooled equal-event net expectancy at least `+0.05R`;
5. pooled profit factor at least `1.10`;
6. positive pooled net R in both 2023 and 2024 H1;
7. blocked plus unresolved executions do not exceed 2% of signals;
8. neither instrument contributes more than 75% of positive pooled net R.

Other classifications:

- `PROMISING_BUT_INSUFFICIENT_SAMPLE`: all profitability conditions pass but either proxy has fewer than 50 exits.
- `MIXED_NOT_PROMOTABLE`: pooled expectancy is positive but cross-instrument, period or concentration conditions fail.
- `NOT_PROMISING_CURRENT_SPEC`: every variant has non-positive pooled expectancy.
- `INVALID_BASELINE`: checksum, parity, normalization, source-integrity or unresolved-execution gates fail.

The classification rules may not be changed after the results are generated.

## Prohibited

- using 2024-07-01 or later data;
- optimization, parameter search or selective filtering;
- ranking after excluding unfavorable windows, weekdays, directions or years;
- combining variants;
- DTR strategy comparison;
- CME-futures or deployment claims;
- Pine implementation;
- altering the frozen event ledgers after seeing performance.

## Acceptance criteria

1. The baseline configuration and promise rules are committed before the official workflow runs.
2. Source checksums and development dates are enforced.
3. Independent synthetic parity tests pass.
4. The official NQ and ES baseline workflows complete without source leakage.
5. Aggregate results reproduce under rerun.
6. A same-session independent review checks calculations and classification.
7. The result report states clearly whether the current specification has promise.

## Decision consequence

- A passing variant authorizes deeper development diagnostics only; it does not authorize lockbox testing or deployment.
- If all variants are `NOT_PROMISING_CURRENT_SPEC`, the current specification should be stopped. Any follow-up must be a separately preregistered conceptual redesign, not post-hoc filtering of this baseline.
