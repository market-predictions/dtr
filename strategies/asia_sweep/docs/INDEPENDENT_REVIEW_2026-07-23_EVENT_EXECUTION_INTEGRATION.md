# Independent Review — Event-to-Execution Integration

**Date:** 2026-07-23  
**Work package:** `AS-WP-20260723-05`  
**Branch:** `agent/asia-sweep-event-execution-integration`  
**Strategy:** `ASIA_SWEEP_STANDALONE_V0`

## Review status

`APPROVE_SYNTHETIC_INTEGRATION_FOR_MERGE_REAL_DATA_PNL_BLOCKED`

This is an independent analytical and programmatic clean-room pass performed in the same AI work session. It is not an external human, broker, exchange, legal, licensing or production-readiness audit.

## Scope reviewed

The review covered only the standalone synthetic bridge between:

1. frozen Asia Sweep event records; and
2. the frozen one-minute neutral execution simulator.

Reviewed files include the integration adapter, adversarial tests, work-package contract and branch diff. No active DTR signal, benchmark, evidence or result file is changed.

## Strategic conclusion

The adapter now answers one narrow question deterministically: can one already-frozen synthetic event be mapped into one instrument-specific execution configuration and replayed against the correct bound synthetic minute path without altering signal semantics?

The package does not answer whether the strategy is profitable, whether Dukascopy proxy prices can be translated safely into CME futures prices, or whether the simulated cost model represents live execution.

## Material review findings and corrections

### 1. Mixed-instrument economics were initially possible

The first implementation allowed one batch to contain different instruments while using one `ExecutionConfig`. That could silently apply one tick size, point value and commission schedule to another instrument.

Correction:

- every `IntegrationConfig` is now bound to one explicit instrument;
- row mapping rejects an event whose instrument differs from the configured economics;
- packet replay rejects mixed instruments before execution;
- tests demonstrate that NQ-like and ES-like point values produce distinct commission-R results under separate configurations.

This correction is architectural and independent of strategy outcomes.

### 2. Minute fixtures were not initially bound to their event

A generic synthetic marker did not prove that a supplied minute frame belonged to the event key under which it was passed. Two same-session fixtures could therefore be swapped accidentally.

Correction:

- each synthetic minute frame is sealed with the stable event key;
- each frame also carries a SHA-256 digest of all execution-relevant event facts;
- changed stop/target/timestamp payloads retain the identity key but change the contract digest;
- swapped frames and same-identity payload drift fail before simulation.

### 3. Event identity and payload are separated deliberately

The stable event key contains only immutable identity:

- instrument;
- trade date;
- execution window;
- variant.

The event-contract digest additionally contains:

- signal status;
- direction;
- canonical New York entry timestamp;
- entry, stop and target in integer ticks;
- frozen 2.0R target ratio.

This preserves a stable row identity while making execution-relevant revisions auditable.

### 4. Time and window semantics are strict

The adapter requires:

- timezone-aware event timestamps;
- causal conversion to `America/New_York`;
- one-minute alignment;
- local entry date equal to `trade_date`;
- entry inside the declared half-open London or New York window;
- wall-calendar window construction across DST changes.

No elapsed-time shortcut or timestamp rounding is used.

### 5. Price semantics are strict-grid only

The adapter requires event entry, stop, target and every minute OHLC value to lie on the configured tick grid. It does not round, snap, infer or translate prices.

This is appropriate for synthetic integration tests. It is not a valid proxy-to-futures normalization policy.

### 6. Batch determinism is explicit

The reviewed batch path:

- rejects duplicate identity keys;
- rejects missing minute frames;
- rejects orphan or malformed frame-map keys;
- sorts output by stable event key;
- requires batch output to match independent row execution;
- requires integrated prefix replay for every event;
- preserves event packets and minute frames unchanged.

### 7. Active DTR isolation remains intact

Static inspection confirms the integration module does not call `dtr_lab.research.engine.generate_signals()` or import the active DTR signal engine. The published branch diff is confined to standalone Asia Sweep code, tests and governance.

## Validation evidence

On the reviewed code head before governance closure:

- repository Ruff passed;
- full repository tests passed on Python 3.11;
- full repository tests passed on Python 3.12;
- isolated Asia Sweep suite passed on Python 3.11;
- isolated Asia Sweep suite passed on Python 3.12;
- isolated suite count: **185 passed**;
- input-order invariance passed;
- batch-versus-row equality passed;
- target and post-entry data-gap integrated prefix replay passed;
- long and short event mapping passed;
- UTC/New York and DST mapping passed;
- instrument-economics separation passed;
- swapped-frame and payload-drift rejection passed;
- no private data, real execution or strategy P&L was generated.

Repository-wide NumPy/pandas timedelta deprecation warnings remain warning debt. They do not invalidate this package, but they should be handled separately rather than hidden inside integration work.

## Remaining blockers

The following remain prohibited or unresolved:

- private Dukascopy proxy execution;
- CME futures execution;
- proxy price normalization or tick translation;
- verification of CME continuous-contract, roll and timestamp semantics;
- futures-valid point value, commission, spread and slippage evidence;
- real-data MFE, MAE, holding-time or P&L output;
- variant comparison or optimization;
- NQ/ES portfolio combination;
- DTR/Asia diversification analysis;
- Pine Script or deployment claims;
- provider authorization for future automated proxy acquisition.

## Final verdict

The synthetic event-to-execution integration is sufficiently deterministic, causal and isolated to merge after exact-head repository CI, isolated Asia Sweep CI and unchanged no-P&L proxy event-audit stability gates pass.

Merge does not authorize real-data execution or P&L. The next package may design and adversarially test a separate proxy source adapter, but must freeze source identity, price normalization, instrument economics and unresolved-data behavior before any private dataset is connected to execution.
