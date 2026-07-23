# Dukascopy Proxy Activity and Staleness Contract

## Status

`FROZEN_BEFORE_OFFICIAL_EVENT_RECOMPUTATION`

## Decision problem

Dukascopy's static index feed provides a complete one-minute bid-quote grid. Minutes with no reported activity are emitted as zero-volume carry-forward rows rather than omitted. The research framework must preserve price continuity without treating stale quotes as evidence that the market was actively tradable.

## Canonical row policy

- Retain every source row.
- Preserve UTC as the authoritative timestamp.
- Preserve New York wall time with an explicit UTC offset.
- Preserve source volume and add `is_active_quote = 1` when volume is positive, otherwise `0`.
- Never fill, delete or reinterpret rows based on later strategy outcomes.

## Frozen interval gate

The following gate is evaluated separately for:

- the 18:00–02:00 New York Asia range;
- each execution window;
- the causal path from the relevant audit start through the signal timestamp.

An interval is eligible only when all conditions hold:

1. Every expected one-minute timestamp exists in the half-open interval.
2. At least one row has positive source volume.
3. The maximum consecutive run of zero-volume rows is no more than 10 minutes.

Failure reasons remain distinct:

- `missing_minute_grid`;
- `no_positive_volume_activity`;
- `stale_quote_run_exceeded`.

## Why 10 minutes

The strategy's signal clock is five minutes. A stale run longer than 10 minutes would create more than two consecutive five-minute bars derived entirely from unchanged, zero-volume source quotes. Such bars can distort sweep, reclaim, displacement and retest semantics even though no data row is technically missing.

The threshold was selected from execution-time geometry and source continuity, not P&L or signal success.

## Observed structural evidence, 2022–2025

Both proxies contain 1,043 weekday observations for each frozen window. Every complete observation has the expected row count: 480 Asia minutes, 240 London minutes and 180 New York minutes.

### USATECH proxy

| Window | Median positive minutes | 5th percentile | 95th percentile max stale run | Intervals over 10 minutes | All-zero intervals |
|---|---:|---:|---:|---:|---:|
| Asia | 480 | 473 | 7 | 22 | 11 |
| London | 240 | 240 | 0 | 13 | 11 |
| New York | 180 | 180 | 0 | 15 | 11 |

### USA500 proxy

| Window | Median positive minutes | 5th percentile | 95th percentile max stale run | Intervals over 10 minutes | All-zero intervals |
|---|---:|---:|---:|---:|---:|
| Asia | 472 | 403 | 6 | 18 | 11 |
| London | 240 | 234 | 2 | 16 | 12 |
| New York | 180 | 179 | 1 | 16 | 11 |

Long stale runs cluster around full holidays, early closes and identifiable feed interruptions. Normal live overnight activity differs between proxies, which is why a universal positive-volume percentage threshold is rejected.

## DST policy

UTC remains unique and monotonic. New York timestamps include their UTC offset, so repeated local times during the autumn DST transition remain distinguishable. Session logic must convert from UTC to `America/New_York`; it may not parse an offset-free local timestamp and silently collapse repeated times.

The Monday–Friday research windows do not directly begin on the Sunday DST transition hour, but preserving offset-aware timestamps is still required for deterministic cross-session handling.

## Source-revision policy

A reacquisition may differ from an earlier artifact because Dukascopy can revise its historical feed. Any difference must be recorded at row level, and the newly acquired checksummed snapshot becomes canonical for that research run. Rows may not be blended across snapshots.

The current USATECH revision is one row at `2024-10-09T23:05:00Z`: an earlier artifact reported positive activity, while the reacquired feed reports a zero-volume carry-forward quote.

## Prohibitions

- Do not drop all zero-volume rows.
- Do not interpret positive volume as CME futures volume.
- Do not tune the stale-run threshold from returns or winning trades.
- Do not forward-fill a missing source timestamp.
- Do not classify a structurally complete but stale interval as tradable.
- Do not combine proxy activity evidence with futures execution claims.
