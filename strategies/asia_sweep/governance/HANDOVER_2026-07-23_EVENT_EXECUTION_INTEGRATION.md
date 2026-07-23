# Handover — Event-to-Execution Integration

**Date:** 2026-07-23  
**Work package:** `AS-WP-20260723-05`  
**Branch:** `agent/asia-sweep-event-execution-integration`  
**Pull request:** `#33`

## Delivered

- Added `src/dtr_lab/strategies/asia_sweep/integration.py`.
- Added strict synthetic event-to-execution mapping.
- Added deterministic stable event keys.
- Added execution-relevant event-contract digests.
- Added one-instrument-per-configuration economics binding.
- Added event-bound synthetic minute-frame sealing.
- Added deterministic one-instrument packet replay.
- Added integrated prefix replay.
- Added adversarial integration tests.
- Added permanent independent review and governance updates.

## Frozen integration semantics

### Identity

A stable event key is the SHA-256 digest of:

- instrument;
- trade date;
- execution window;
- preregistered variant.

### Payload audit

A separate event-contract digest covers:

- signal status;
- direction;
- canonical New York entry timestamp;
- event entry, stop and target expressed in integer ticks;
- frozen 2.0R target ratio.

### Instrument economics

- One `IntegrationConfig` is bound to exactly one instrument.
- Every event in a packet must match that instrument.
- Tick size, point value, commission and slippage therefore cannot be shared silently across NQ-like and ES-like events.

### Event mapping

- Only `SIGNAL` rows are executable.
- Direction must be exactly `1` or `-1`.
- Variant must be one of AS-A through AS-D.
- Entry timestamp must be timezone-aware, one-minute aligned and inside the declared half-open execution window.
- Local entry date must equal the event trade date.
- Event entry, stop and target must be finite and tick aligned.
- Event target must equal 2.0R from the event entry and fixed stop.
- The mapped execution signal retains the fixed event stop and frozen 2.0R target ratio.

### Minute-frame binding

Each synthetic minute frame must carry:

- the frozen synthetic execution marker;
- the stable event key;
- the event-contract digest.

A swapped frame or a frame built for an earlier revision of the same event fails before simulation.

### Batch replay

- Duplicate stable keys are prohibited.
- Missing, orphan and malformed frame-map keys are prohibited.
- Output is sorted by stable event key.
- Batch replay must equal independent row replay.
- Integrated prefix replay is required for every event.
- Inputs remain immutable.

## Review corrections

1. Bound configurations and packets to one instrument after review found that mixed instruments could inherit the same point value and commission economics.
2. Bound minute fixtures to event identity after review found that generic synthetic marking did not prevent frame swaps.
3. Added payload digests so execution-relevant revisions remain visible even when identity is unchanged.
4. Added strict local-date and execution-window membership.
5. Rejected fractional, boolean and non-finite directions.
6. Rejected missing/non-string identities and malformed frame-map keys.
7. Applied the pinned Ruff model-import order exactly and removed the temporary diagnostic workflow.

## Validation

Reviewed implementation gates:

- repository Ruff: passed;
- repository tests Python 3.11: passed;
- repository tests Python 3.12: passed;
- isolated Asia Sweep tests Python 3.11: passed;
- isolated Asia Sweep tests Python 3.12: passed;
- isolated suite: 185 passed;
- clean-room review verdict: `APPROVE_SYNTHETIC_INTEGRATION_FOR_MERGE_REAL_DATA_PNL_BLOCKED`.

Final exact-head CI and unchanged private proxy event-audit stability must still pass after governance closure before merge.

## Explicitly not delivered

- no private proxy execution;
- no CME futures execution;
- no proxy-to-futures price conversion;
- no real-data P&L, MFE or MAE;
- no variant ranking or optimization;
- no NQ/ES portfolio simulation;
- no DTR combination;
- no Pine Script or deployment work.

## Next authorized package

A separate work package may design and adversarially test a proxy execution-source adapter. It must remain no-P&L until source identity, price normalization, instrument economics, source activity, unresolved exits and proxy-versus-futures limitations are frozen and independently reviewed.

The current package does not authorize connecting private data to the execution simulator.
