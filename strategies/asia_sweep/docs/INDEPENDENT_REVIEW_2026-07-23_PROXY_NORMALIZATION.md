# Independent Review — Proxy Normalization Contract

**Date:** 2026-07-23  
**Work package:** `AS-WP-20260723-06`  
**Branch:** `agent/asia-sweep-proxy-normalization-contract`  
**Strategy:** `ASIA_SWEEP_STANDALONE_V0`

## Review status

`APPROVE_SYNTHETIC_PROXY_NORMALIZATION_FOR_MERGE_PRIVATE_EXECUTION_BLOCKED`

This is an independent analytical and programmatic clean-room pass performed in the same AI work session. It is not an external human, provider, broker, exchange, licensing, legal or production-readiness audit.

## Scope reviewed

The review covers only the synthetic adapter from Dukascopy-style index-CFD proxy events and BID one-minute bars to the previously frozen instrument-specific Asian Sweep integration contract.

No private market data are loaded. No real proxy or CME futures execution is performed. No real-data return, MFE, MAE, optimization or variant ranking is generated.

## Strategic conclusion

The adapter answers one narrow question: how should a 0.001-precision BID proxy path be transformed deterministically into a 0.25-grid, instrument-specific synthetic execution stress path without filling gaps, changing activity or hiding price adjustments?

The answer is a directionally pessimistic scenario, not a claim that proxy quotes reproduce CME futures trades.

## Frozen directional policy

### Long events

- event entry and protective stop are ceiled to the execution grid;
- entry-minute open is ceiled;
- later opens are floored;
- highs are floored so favorable excursions are not overstated;
- lows are floored so adverse excursions are not understated;
- closes are floored.

### Short events

- event entry and protective stop are floored to the execution grid;
- entry-minute open is floored;
- later opens are ceiled;
- highs are ceiled so adverse excursions are not understated;
- lows are ceiled so favorable excursions are not overstated;
- closes are ceiled.

OHLC envelope repair is limited to placing the normalized open and close inside high/low. It cannot add an excursion beyond the minimum required for valid OHLC.

## Material review findings and corrections

### 1. Exact source identity was initially incomplete

The first implementation identified only a generic synthetic proxy kind. It did not freeze the provider instrument or price side.

Correction:

- `source_instrument` is required in `ProxyNormalizationConfig`;
- NQ-like fixtures bind to `usatechidxusd` and ES-like fixtures to `usa500idxusd` in tests;
- the only supported source side is `BID`;
- event fields, frame attributes, source-event digests and normalization digests all include source identity;
- mismatched source instrument or price side fails before normalization.

### 2. The normalization policy identifier was initially extensible

An arbitrary policy string could have become a hidden research parameter.

Correction:

- only `DIRECTIONAL_PESSIMISTIC_V1` is accepted;
- alternative policies require a separate preregistered work package.

### 3. Derived-target arithmetic noise needed separate handling

Entry, stop and OHLC are market-observed prices and remain exact source-grid only. The 2.0R target is derived arithmetic and can contain insignificant binary-float noise.

Correction:

- entry, stop and all OHLC remain strict-grid with no tolerance;
- the reported target is accepted only when it differs from the canonical source-grid 2.0R target by no more than one-millionth of a source increment;
- the canonical target is used for digests and normalization;
- reported and canonical targets are both retained for audit;
- a test fixture using a Python float that collapsed back to the same decimal was corrected to an explicit off-grid decimal string.

### 4. Source gaps and activity remain facts

The adapter:

- sorts timestamps deterministically;
- rejects duplicate, naïve and off-minute timestamps;
- preserves missing minutes as missing;
- preserves activity values exactly;
- rejects rows before event entry or after execution-window end;
- does not forward-fill or synthesize tradable bars.

### 5. Exact Decimal arithmetic is used

All source-grid validation and floor/ceiling operations use `Decimal`. The execution tick must be an exact integer multiple of the source quote increment. Binary-float rounding does not define normalization behavior.

### 6. Evidence remains auditable

Normalized frames retain:

- source OHLC columns;
- normalized OHLC columns;
- envelope-repair flags;
- source instrument and BID side;
- policy version;
- source event digest;
- source frame digest;
- normalization digest;
- source increment and execution tick.

The normalized event retains raw source entry, stop, canonical target and reported target alongside normalized geometry.

### 7. Integration and DTR isolation remain intact

The normalized output is sealed to the frozen WP5 event key and event-contract digest. Static inspection confirms the normalization module does not call execution, private loaders or the active DTR signal engine.

## Validation evidence

On the reviewed implementation head before governance closure:

- repository Ruff passed;
- full repository tests passed on Python 3.11 and 3.12;
- isolated Asian Sweep suite passed on Python 3.11 and 3.12;
- isolated suite count: **223 passed**;
- exact source-symbol and BID-side binding passed;
- policy-version lock passed;
- strict source-grid and Decimal floor/ceiling cases passed;
- long and short directional pessimism passed;
- risk-collapse rejection passed;
- duplicate, naïve, off-minute and invalid-OHLC rejection passed;
- timestamp, gap and activity preservation passed;
- source/event/frame swap detection passed;
- source and normalization digest determinism passed;
- source-row order invariance passed;
- normalized outputs satisfied the frozen WP5 binding contract;
- one synthetic target execution confirmed compatibility without enabling a real-data path;
- no private data, real execution, P&L, optimization or variant ranking was produced.

Repository-wide NumPy/pandas timedelta deprecation warnings remain separate warning debt.

## Remaining blockers

- private Dukascopy normalization has not been run;
- no private normalization audit packet exists;
- no manual source-versus-normalized bar audit exists;
- no CME futures basis, timestamp, roll, volume, spread or fill evidence exists;
- BID-only proxy data cannot establish ask-side or futures trade behavior;
- the directional policy is a conservative scenario, not observed execution truth;
- real-data execution, MFE, MAE and P&L remain prohibited;
- variant comparison and optimization remain prohibited;
- provider authorization for future automated acquisition remains unresolved.

## Final verdict

The synthetic proxy normalization contract is deterministic, causal, directionally pessimistic and sufficiently isolated to merge after exact-head repository CI, isolated Asian Sweep CI and unchanged private no-P&L event-audit stability gates pass.

Merge authorizes only a separate private normalization-audit work package. It does not authorize executing normalized private paths or calculating strategy P&L.
