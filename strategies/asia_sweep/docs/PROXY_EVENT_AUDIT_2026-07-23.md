# Asia Sweep Proxy Event Audit — 2026-07-23

## Verdict

`FREEZE_PRIVATE_PROXY_EVENT_SEMANTICS_EXECUTION_AND_PNL_BLOCKED`

The registered Dukascopy USATECH and USA500 index-CFD proxy snapshots now support reproducible, private, event-only Asia Sweep research. UTC-to-New-York conversion, source activity, minute-grid integrity, causal pre-signal eligibility and half-open execution-window boundaries are frozen for proxy event generation.

This verdict does not authorize post-entry execution simulation, P&L, optimization, variant selection, deployment or CME futures claims.

## Scope and source identity

| Research instrument | Source instrument | Canonical ZIP SHA-256 | Data identity |
|---|---|---|---|
| `NQ_PROXY` | Dukascopy `USATECHIDXUSD` | `b98f08a0fd35255c09232d41da10ee84559587067b48e942cccdbe37b0b888c4` | bid-only index-CFD proxy |
| `ES_PROXY` | Dukascopy `USA500IDXUSD` | `a2342f9d64695d8ecb618a907600b4de0b1433ba65d25c1f0ac3d0566ab9a72f` | bid-only index-CFD proxy |

Canonical source workflow run: `29996917493`.

The source files remain private GitHub Actions inputs and are removed before derived audit artifacts are uploaded. No market-data file is committed to Git.

## Frozen event semantics

- UTC is the authoritative source clock.
- Session logic uses timezone-aware `America/New_York` wall time.
- Asia range: 18:00 previous date through 02:00 trade date, half-open.
- London window: 02:00–06:00, half-open.
- New York window: 08:30–11:30, half-open.
- Every expected one-minute timestamp must exist.
- An audited interval must contain at least one positive-activity minute.
- No consecutive zero-volume source run may exceed 10 minutes.
- Asia-range activity must pass in full.
- Only the causal path through the determining bar can block an observed signal or rejection.
- Later inactivity cannot retroactively erase a prior decision.
- `NO_SWEEP` requires a complete and active full execution window.
- `entry_timestamp` must be strictly earlier than execution-window end.

## Development event inventory

The development partition is 2023-01-01 through 2024-06-30. Each variant contains 780 instrument-date-window records, or 3,120 records per proxy across four preregistered variants.

### NQ proxy

| Variant | Signal | Rejected | No sweep | Ineligible |
|---|---:|---:|---:|---:|
| AS-A aggressive reclaim | 212 | 509 | 45 | 14 |
| AS-B wick qualified | 59 | 662 | 45 | 14 |
| AS-C displacement | 108 | 613 | 45 | 14 |
| AS-D failed retest | 11 | 710 | 45 | 14 |

### ES proxy

| Variant | Signal | Rejected | No sweep | Ineligible |
|---|---:|---:|---:|---:|
| AS-A aggressive reclaim | 151 | 555 | 60 | 14 |
| AS-B wick qualified | 48 | 658 | 60 | 14 |
| AS-C displacement | 83 | 623 | 60 | 14 |
| AS-D failed retest | 18 | 688 | 60 | 14 |

These are event-semantic counts across competing variants. They are not executed trades and contain no performance information.

## Integrity outcomes

For each proxy, the same 14 instrument-date-window records are ineligible in every variant:

- 10 have no positive source activity during the Asia range;
- 4 exceed the frozen 10-minute stale-run limit during the Asia range.

Grid integrity, Asia values, activity metrics, first-sweep identity, direction, sweep OHLC and morphology are invariant across variants for every shared instrument-date-window key.

Two ES signals on 2024-01-22 remain valid even though a later 38-minute stale run occurs in the New York window. Their causal pre-signal paths are fully active, demonstrating that future source inactivity does not alter an earlier observable decision.

One NQ AS-C candidate on 2023-03-16 would have entered at exactly 06:00. It is correctly retained as `REJECTED` with `entry_at_or_after_window_end` rather than emitted as a signal.

## Deterministic 50-event audits

Each proxy has a deterministic 50-event sample covering all four variants, both execution windows, long/short/directionless rows, signals, rejections, no-sweep rows, ineligible rows and declared edge reasons.

| Instrument | Sample SHA-256 | Independent reconstruction | Private five-minute evidence rows | Evidence SHA-256 |
|---|---|---:|---:|---|
| NQ proxy | `3df84d3c7a86b8b5a08ebe1663dfcd549502db2c78dfdf5a9305e8ed5b03a8fe` | 50/50 exact | `6900` | `4713235aa50afa60b8b06deecb2a5fe0cf0e0425800fbec8ee7e2bc0905da42e` |
| ES proxy | `0c693e6d0a1372f1ca9c8262d41ee104c77b0b0b32d7c2496bbf7c9a34fc60d4` | 50/50 exact | `6888` | `1c92e59aa7eacd53cb661122482d53484a029263feec1ed77e187005dca84da8` |

The independent validator does not call the production signal builder. It re-derives session bounds, source activity, Asia extrema, first sweep, morphology, displacement, failed-retest state, entry boundary and raw risk geometry directly from the canonical one-minute source.

Private five-minute OHLC evidence contains the complete Asia range and execution window for every sampled record. It is stored only in the derived workflow artifacts and is not committed to Git.

## CI and artifact evidence

- Exact-head repository Ruff and tests pass on Python 3.11 and 3.12.
- Exact-head isolated Asia Sweep tests pass on Python 3.11 and 3.12.
- NQ and ES private event-audit jobs pass checksum verification, event generation, deterministic sampling, independent reconstruction and no-P&L enforcement.
- Event-audit workflow run: `30003836567`.
- NQ derived artifact digest: `sha256:54d3bbe10b256a3d41f5afb173c5540b1b389c0c01d9eb9e557e436c85bfe883`.
- ES derived artifact digest: `sha256:7e091227df36879fd9eed5c5ad4cb11653db59eb6b8fe4379c91ba1af4d197d5`.

## Explicit limitations

- The datasets are CFD index proxies, not CME NQ or ES futures.
- Bid-only proxy candles cannot establish futures fills, slippage, commissions or volume behavior.
- Proxy evidence contains no futures contract or roll construction.
- Provider authorization for future automated acquisition remains unresolved.
- The independent review is a clean-room analytical and programmatic pass in the same AI work session, not an external human or legal audit.
- Post-entry execution, conservative intrabar collision handling, gap liquidation, time exits and P&L remain unimplemented.
- No variant has been selected, promoted or compared on returns.

## Next authorization

The proxy event-semantic layer may merge. The next work package may design a neutral execution adapter and its synthetic adversarial tests, but must keep P&L blocked until:

1. the execution contract is frozen;
2. same-minute stop/target, entry-stop, gap and time-exit tests pass;
3. the locked DTR benchmark is reproduced before shared execution infrastructure is extracted;
4. futures-confirmation requirements remain explicit.
