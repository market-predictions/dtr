# Dukascopy Data Source Review — 2026-07-21

## Decision

Dukascopy is accepted as a **candidate secondary market-data provider** for the DTR Optimization Lab, subject to an access-and-licensing gate and a technical pilot.

It will **not replace or mutate the frozen NQ futures baseline**. The existing NQ dataset remains the reference dataset for the current reversal candidate, reproducibility work, and gap-safety implementation.

Dukascopy data will be introduced through a provider-neutral acquisition layer and used later for:

1. longer-history structural validation;
2. common-window comparison across index CFDs;
3. FX and metals transfer studies with asset-specific execution assumptions;
4. comparison of one-minute and derived five-minute results;
5. testing whether DTR logic is a market-structure effect or an NQ-specific result.

Dukascopy index CFDs are not CME futures. `USATECHIDXUSD`, `USA500IDXUSD`, and related instruments must therefore be treated as structural proxies, not as substitutes for NQ, ES, or YM execution data.

## Assessment of `giuse88/duka`

Repository: <https://github.com/giuse88/duka>

The project demonstrated the useful core idea: automate Dukascopy downloads over date ranges and convert the source into ticks or candles. Its code is MIT licensed.

The package itself is **not approved as a production dependency** for DTR because:

- its latest repository commit dates from August 2017;
- it targets Python 3.5 and its published package is approximately a decade old;
- timestamp handling is timezone-naive and applies custom daylight-saving adjustments;
- price scaling is hard-coded for a small set of exceptional symbols;
- candle output is generated only from ask prices;
- spread, bid candles, and volume are discarded from candle output;
- local `time.mktime` semantics can make output depend on the machine timezone;
- its gap loop can emit repeated candles from the same tick bucket across missing intervals;
- it does not provide the provenance, resumability, checksum, schema, and safety contracts required by the DTR Lab.

The repository is useful as historical reference code, but copying it directly would import hidden data-quality risk into the research engine.

## Preferred implementation path

### Primary path: small Python adapter over the official Dukascopy API

Dukascopy currently documents:

- an instrument-list API;
- historical candle access;
- bid and ask offer sides;
- tick, 10-second, one-minute, 10-minute, one-hour, and daily periods;
- a maximum of 5,000 records per historical request.

The DTR codebase should remain Python-first. A native adapter keeps dependency, manifest, test, and provenance handling inside the existing architecture.

### Independent oracle: `dukascopy-node`

Repository: <https://github.com/Leo4815162342/dukascopy-node>

`dukascopy-node` is actively maintained and released version 1.49.0 on 2026-07-16. That release rewrote its engine around Dukascopy's JSON API. It includes instrument metadata, batching, caching, multiple timeframes, and broad asset coverage.

It should initially be used as:

- an instrument-catalog reference;
- an independent output-comparison oracle for pilot windows;
- an optional acquisition fallback when explicitly approved and version-pinned.

It should not become an unpinned hidden dependency in the Python research runner.

## Access and data-rights gate

The MIT license for either downloader covers downloader source code, not Dukascopy market-data rights.

Dukascopy's website terms restrict automated scraping and database construction without prior consent, while Dukascopy separately offers an API-for-developers application and API key. Before automated bulk acquisition, the project must record one of:

- approved official API access and applicable terms;
- written permission for the intended private research use;
- another documented lawful access basis reviewed for this project.

Until that gate passes:

- no unattended bulk scraper is approved;
- no raw Dukascopy dataset is committed to Git;
- the roadmap may develop provider interfaces, fixtures, and mocked tests only;
- a user-initiated official export may be evaluated separately if its terms permit the intended use.

## Data-model requirements

The provider-neutral canonical schema must preserve source semantics rather than force every asset into the current NQ layout.

Minimum metadata:

- provider and provider version;
- provider instrument id and human-readable instrument name;
- asset class and instrument type;
- timestamp in UTC;
- source timezone and bar-open/bar-close semantics;
- requested timeframe and source timeframe;
- bid, ask, or derived-mid price basis;
- OHLC values;
- available volume or tick-count fields and their exact meaning;
- pip or point value;
- session calendar;
- contract or CFD specification where available;
- request parameters and acquisition timestamp;
- raw-response checksum and canonical-file checksum;
- gap, duplicate, and invalid-row audit results.

For FX and CFDs, bid and ask data must remain distinguishable. A midpoint series may be derived for signal research, but spread-aware execution must use the correct side:

- long entries generally pay ask and liquidate on bid;
- short entries generally sell on bid and cover on ask.

Dukascopy activity or quote volume must not be described as centralized futures exchange volume.

## Technical pilot

The pilot is non-blocking for the current NQ work.

### Initial basket

1. `EURUSD` — liquid FX control instrument.
2. `XAUUSD` — globally traded metal with different volatility and session behaviour.
3. `USA500IDXUSD` — S&P 500 CFD proxy.
4. `USATECHIDXUSD` — Nasdaq-100 CFD proxy.
5. `USA30IDXUSD` — Dow CFD proxy, if confirmed by the live instrument catalog.

Energy commodities and individual equities are deferred until the first basket passes because broker-CFD contract definitions, trading breaks, corporate actions, and historical availability introduce additional normalization work.

### Pilot sequence

1. Obtain and document approved API access.
2. Snapshot the live instrument catalog and metadata.
3. Download short controlled windows for bid and ask one-minute candles.
4. Store raw responses outside Git with checksums.
5. Normalize to canonical UTC Parquet without filling missing bars silently.
6. Derive five-minute bars from canonical one-minute data.
7. Compare a sample against Dukascopy's official interface or JForex output.
8. Compare the Python adapter with a pinned `dukascopy-node` result for identical requests.
9. Audit duplicates, gaps, session breaks, price scales, spreads, and bar boundaries.
10. Run the DTR setup funnel without optimizing parameters.
11. Promote the source only if the same manifest reproduces identical canonical hashes and research artifacts.

## Research use and sequencing

### Current phase

Continue the existing NQ work unchanged:

- manifest rerun;
- artifact locking;
- unsafe-gap state resets;
- timestamp and rollover resolution.

The Dukascopy adapter is a parallel data-engineering workstream and does not invalidate or restart the NQ candidate.

### Before cross-market optimization

The first Dukascopy pass must use the frozen DTR candidate without retuning. Its purpose is to measure transportability, setup coverage, failure modes, and the effect of provider/instrument differences.

Only after the fixed-candidate comparison may asset-specific development windows be opened. FX, metals, index CFDs, and futures must retain separate cost models and must not be pooled into one headline backtest.

### Promotion meanings

- **Provider validated:** acquisition and normalization are trustworthy.
- **Structural transfer observed:** the fixed DTR concept retains useful behaviour on another market.
- **Asset-specific candidate:** parameters were selected within that asset's training window.
- **Execution candidate:** validated on data that matches the intended tradable instrument and venue closely enough for execution claims.

A Dukascopy index-CFD result may reach the first three states, but it cannot by itself validate CME futures execution.

## Acceptance gates

Dukascopy becomes an approved research provider only when:

1. access rights and automation terms are documented;
2. timestamps and bar boundaries are explicit and tested;
3. bid/ask and price-scale semantics are correct for every pilot instrument;
4. no downloader fabricates bars across missing periods;
5. all gaps and market closures are classified;
6. raw and canonical checksums are recorded;
7. repeated runs are deterministic;
8. a controlled sample agrees with an independent reference;
9. provider-specific execution and volume limitations are disclosed;
10. cross-market reports distinguish futures, spot FX, metals, and CFDs.

## Final recommendation

Proceed, but integrate the **data source**, not the legacy downloader as-is.

The best architecture is:

- keep NQ as the frozen primary baseline;
- add a provider-neutral Python acquisition contract;
- use the official Dukascopy API after approval;
- use current `dukascopy-node` as a pinned comparison oracle;
- pilot one-minute bid/ask data on a small cross-asset basket;
- delay full-history acquisition and cross-market optimization until data integrity is proven.
