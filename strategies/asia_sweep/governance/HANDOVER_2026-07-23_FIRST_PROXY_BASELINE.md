# Handover — First Asian Sweep Proxy Baseline

## Delivered

- preregistered first development-period baseline;
- independent shadow normalization and execution replay;
- production-versus-shadow synthetic parity tests;
- protected NQ and ES private-data workflow;
- pooled aggregate classifier;
- official result report;
- independent ledger-level replication review.

## Official workflow

- workflow: `Asia Sweep First Proxy Baseline`;
- run: `30022356560`;
- head: `4093eb6395aa2ed448a91df16c99a949caa4419f`;
- NQ job: success;
- ES job: success;
- aggregate job: success;
- aggregate artifact digest: `sha256:c37fc13777643e25c668fefd108d6466c90e6c568acd7681bb151f4387cf682c`.

## Result

`NOT_PROMISING_CURRENT_SPEC`

- AS-A pooled expectancy: `-0.225R`;
- AS-B pooled expectancy: `-0.054R`;
- AS-C pooled expectancy: `-0.141R`;
- AS-D pooled expectancy: `-0.172R`.

All four pooled gross expectancies before commission were negative.

## Review

The official 690-row trade ledger reproduced the independent preview trade for trade. Identity, timestamps and prices matched exactly. Net-R differences were limited to floating-point representation (`4.44e-16` maximum).

Review verdict:

`APPROVE_BASELINE_RESULT_STOP_CURRENT_SPEC`

## Preserved boundaries

- no data after 2024-06-30;
- no lockbox access;
- no tuning or subgroup selection;
- no variant combination;
- no DTR comparison;
- no raw private market data committed or uploaded;
- no CME-futures validity or deployment claim.

## Decision

`STOP_CURRENT_SPEC_NO_LOCKBOX_NO_POSTHOC_FILTER_MINING`

The AS-A through AS-D family should not proceed to historical validation, portfolio combination, Pine implementation or deployment research.

## Possible future work

A future work package is permitted only if it starts from a materially different, preregistered market hypothesis. It may use the standalone Asian Sweep framework and data infrastructure, but it may not rescue the current specification by selecting favorable windows, directions, weekdays, years or instruments after this result.
