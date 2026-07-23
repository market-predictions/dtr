# Independent Review — First Asian Sweep Proxy Baseline

**Date:** 2026-07-23  
**Work package:** `AS-WP-20260723-07`  
**Review type:** same-session clean-room replication and artifact comparison

## Scope

Review the first preregistered development-period baseline for source integrity, shadow-engine parity, aggregate calculations, promise classification and compliance with the no-tuning/no-lockbox rules.

This is an independent implementation and calculation pass within the same AI session. It is not an external human, broker, exchange, licensing or legal audit.

## Evidence reviewed

- frozen work package and baseline configuration committed before the official workflow completed;
- repository CI and isolated Asian Sweep test results;
- production-versus-shadow synthetic parity tests;
- official NQ and ES private workflow jobs;
- official aggregate artifact digest `sha256:c37fc13777643e25c668fefd108d6466c90e6c568acd7681bb151f4387cf682c`;
- official 690-row combined derived trade ledger;
- independent local preview ledger generated before the official workflow;
- official baseline summary and fixed classification rules.

## Workflow review

Both instrument jobs passed:

- canonical private artifact download;
- registered checksum verification;
- event-ledger reconstruction;
- independent shadow replay;
- result-boundary checks;
- removal of canonical/private source files before artifact upload.

The aggregate job passed and confirmed:

- no lockbox access;
- no optimization;
- no CME-futures validation claim;
- no deployment authorization.

## Independent ledger replication

The official 690-row ledger was sorted and compared with the independently generated preview ledger.

Results:

- shape: 690 rows × 31 columns in both ledgers;
- instrument/date/window/variant/direction/status/reason identity: exact match;
- entry and exit timestamps: exact match;
- entry, stop, target and exit prices: exact match;
- holding and gap minutes: exact match;
- gross R and commission R: exact match within floating-point representation;
- maximum observed net-R difference: `4.44e-16`.

The official result therefore reproduces the independent preview trade for trade.

## Metric review

The maximum-drawdown calculation was checked separately. It uses cumulative net-R equity with an initial zero point and measures peak-to-trough drawdown. A unit case `[+1, -2, -3, +2]` correctly returns `5R`, preventing the earlier one-trade-range error.

Recomputed pooled metrics match the official summary:

- AS-A: 363 exits, -81.70R, -0.225R expectancy, PF 0.708;
- AS-B: 107 exits, -5.75R, -0.054R expectancy, PF 0.922;
- AS-C: 191 exits, -26.93R, -0.141R expectancy, PF 0.789;
- AS-D: 29 exits, -5.00R, -0.172R expectancy, PF 0.702.

All four pooled gross expectancies before commission were negative.

## Classification review

The preregistered classification was applied without modification after outcomes were visible.

Every variant had non-positive pooled expectancy, so each correctly receives:

`NOT_PROMISING_CURRENT_SPEC`

The overall classification is therefore also:

`NOT_PROMISING_CURRENT_SPEC`

AS-B is closest to flat, but remains negative in NQ and ES and fails the minimum ES sample requirement. AS-D's positive NQ result has only 11 trades and is contradicted by ES. Neither observation justifies subgroup selection or lockbox access.

## Bias and leakage review

No evidence was found of:

- use of data after 2024-06-30;
- parameter tuning after viewing results;
- selective exclusion of windows, directions, weekdays or years;
- variant combination;
- active DTR signal or result reuse;
- raw private market-data publication;
- CME-futures or deployment claims.

## Verdict

`APPROVE_BASELINE_RESULT_STOP_CURRENT_SPEC`

The current AS-A through AS-D specification should not proceed to historical validation, DTR combination, Pine implementation or deployment research.

Any continuation should begin with a new preregistered market hypothesis rather than filtering this failed baseline.
