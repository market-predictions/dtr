# Dukascopy Proxy Qualification — 2026-07-23

## Verdict

`REGISTER_STRUCTURALLY_QUALIFIED_PRIVATE_PROXY_DATA_BLOCK_EVENT_LEDGER_AND_PNL`

The reacquired Dukascopy index-CFD proxy snapshots are suitable for private, descriptive Asia Sweep data and event-semantics research. They are not CME futures, do not establish futures execution validity, and remain blocked from the event runner until UTC-to-New-York conversion and source-activity integrity are implemented and tested.

## Canonical artifacts

| Research ID | Normalized archive | SHA-256 | Rows | Active | Zero volume |
|---|---|---|---:|---:|---:|
| `NQ_PROXY_DUKASCOPY_USATECH` | `NQ_PROXY_DUKASCOPY_USATECH_M1_BID_FULL_GRID_UTC_ET.zip` | `b98f08a0fd35255c09232d41da10ee84559587067b48e942cccdbe37b0b888c4` | 2,103,840 | 1,366,578 | 737,262 |
| `ES_PROXY_DUKASCOPY_USA500` | `ES_PROXY_DUKASCOPY_USA500_M1_BID_FULL_GRID_UTC_ET.zip` | `a2342f9d64695d8ecb618a907600b4de0b1433ba65d25c1f0ac3d0566ab9a72f` | 2,103,840 | 1,348,073 | 755,767 |

Deterministic GZIP hashes:

- NQ: `7f4ba44759264a627ed374a50066411133664b3b4332e12cd5635f73bc3275a8`
- ES: `fa3f5076135b7bb27ad40221c80b2d5f10282f327e97241ec32232e4faf02f38`

Workflow evidence:

- head: `c758451edd09cd9e7af71c289fb62b8d205b1a8f`;
- run: `29996917493`;
- normalized artifact digest: `sha256:1ebbac7dd92bd61c21988102b227d7e706ba51e3669e4f3c4aa647fa48d1276e`.

## Structural checks

Both snapshots pass:

- 2,103,840 retained source minutes covering `2022-01-01T00:00:00Z` through `2025-12-31T23:59:00Z`;
- unique UTC timestamps;
- zero off-grid timestamps;
- zero non-one-minute adjacent gaps;
- valid OHLC invariants;
- offset-aware New York timestamps with no duplicate absolute instants;
- observed minimum quote increment approximately `0.001` index points.

The UTC timestamp is authoritative. New York timestamps retain an explicit offset so the repeated autumn DST hour cannot collapse.

## Quote-grid and activity semantics

Dukascopy emits a complete one-minute quote grid. Zero-volume rows are source-provided carry-forward quotes, not missing bars and not proof of market activity. The canonical archive retains them and adds `is_active_quote`.

The frozen interval gate requires:

1. every expected one-minute timestamp in the half-open interval;
2. at least one positive-volume minute;
3. no consecutive zero-volume run longer than 10 minutes.

The rule applies independently to the Asia range, execution window and causal pre-signal path. It was selected from five-minute signal geometry, not strategy returns.

## Eligible structural sample

Before signal generation, the gate leaves:

| Instrument | London dates | New York dates |
|---|---:|---:|
| NQ proxy | 1,021 | 1,017 |
| ES proxy | 1,022 | 1,021 |
| Matched NQ/ES | 1,015 | 1,013 |

These are structural eligibility counts, not trades.

## Source revisions

### USATECH

An earlier artifact and the reacquired snapshot differ at `2024-10-09T23:05:00Z`. The earlier source reported an active candle; the current source reports a flat zero-volume carry-forward quote. The affected Asia range already fails the frozen stale-run gate with a 66-minute inactive run, so the revision cannot alter an official eligible event.

### USA500

The earlier qualification recorded 1,348,078 positive-volume rows; the current snapshot has 1,348,073. The earlier raw artifact is unavailable for row-level reconciliation. The five-row aggregate difference remains unresolved and the reacquired checksummed snapshot stands alone. No rows are blended between snapshots.

## Provider-use status

`PROVIDER_AUTHORIZATION_UNRESOLVED`

The data remain private workflow artifacts. No raw or normalized market data are committed, published or redistributed. Official Dukascopy terms reviewed on 2026-07-23 contain limited non-commercial-use language, restrictions on redistribution and language that may require consent for automated access. Applicability to this static BI5 workflow is not certified here. Future automated reacquisition requires authorization confirmation.

## Explicit limitations

- CFD index proxies, not CME NQ or ES futures;
- bid-only candles;
- source volume is not futures volume;
- no futures roll or contract-splice evidence;
- no futures slippage, commission or fill evidence;
- provider-use authorization unresolved;
- proxy timezone/activity adapter not yet implemented;
- official 50-event-per-instrument audit not yet complete;
- end-of-window entry semantic defect not yet corrected;
- no P&L calculated or inspected.

## Next authorization

Proceed to a separate event-semantics work package that:

1. loads UTC proxy rows and converts causally to `America/New_York`;
2. implements the frozen activity gate with separate rejection reasons;
3. rejects entries at or after execution-window end;
4. generates official no-P&L ledgers;
5. audits at least 50 NQ-proxy and 50 ES-proxy events.

Execution simulation and P&L remain prohibited.
