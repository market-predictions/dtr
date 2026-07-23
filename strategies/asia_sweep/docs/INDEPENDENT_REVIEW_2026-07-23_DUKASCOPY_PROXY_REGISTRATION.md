# Asia Sweep Dukascopy Proxy Registration — Independent Review

## Review method

A clean-room analytical review was performed against PR #26, its acquisition and normalization evidence, the frozen data/activity contracts, the standalone roadmap, and the wider requirement to prevent proxy data from being mistaken for futures evidence. This is an independent reasoning pass within the same AI work session, not an external human or legal audit.

## Verdict

`APPROVE_PRIVATE_PROXY_REGISTRATION_FOR_MERGE_BLOCK_EVENT_LEDGER_AND_PNL`

The package may merge as a private, structural proxy-data registration. It must not enable the event runner, strategy P&L, futures execution claims, redistribution, or deployment.

## Confirmed

- The two datasets are labelled Dukascopy index-CFD proxies, not NQ/ES futures.
- All eight yearly acquisitions cover 2022–2025 only.
- Each canonical proxy retains exactly 2,103,840 source minutes.
- UTC is authoritative; ET values retain explicit offsets.
- Duplicate, off-grid, adjacency and OHLC defects fail loudly.
- Zero-volume source rows are retained as carry-forward quotes and separated from activity.
- The 10-minute stale-run gate is tied to five-minute signal geometry and was not selected from returns.
- Source revisions are disclosed rather than reconciled silently.
- No market data are committed to Git.
- No DTR signal, benchmark or result file is changed.
- No P&L or optimization was generated.

## Defects found and resolved

### DR1 — Package-API rate limiting

The first multi-year `dukascopy-node` approach failed with HTTP 429 before normalization.

**Resolution:** recover the proven static daily BI5 transport from prior DTR work and freeze it before inspecting event results.

### DR2 — Positive-volume-only normalization

Removing zero-volume carry-forward rows converted complete source intervals into apparent gaps.

**Resolution:** retain the complete source quote grid and audit activity independently.

### DR3 — DST ambiguity

Offset-free New York strings could collapse the repeated autumn hour.

**Resolution:** keep UTC authoritative and serialize New York timestamps with their UTC offset.

### DR4 — Ruff UTC modernization

The downloader used `datetime.timezone.utc`, rejected by the repository's Ruff configuration.

**Resolution:** use `datetime.UTC`; original repository CI is green.

### DR5 — Source-snapshot drift

USATECH changed by one active row and USA500 by five active rows relative to earlier qualifications.

**Resolution:** disclose the differences, prohibit blending snapshots and use only the newly checksummed canonical snapshot.

## Remaining blockers

1. Proxy UTC-to-New-York and activity-aware loader is not implemented.
2. The event ledger can currently emit an entry exactly at execution-window end.
3. Official NQ-proxy and ES-proxy event ledgers are not frozen.
4. The required 50-event audit per proxy is incomplete.
5. Provider authorization for continued automated acquisition remains unresolved.
6. Proxy evidence cannot resolve CME futures roll, volume, costs or fills.
7. Post-entry execution and P&L remain disconnected.

## Recommendation

Merge the private registration only after the final branch restores ordinary Asia Sweep CI, adds blocked proxy manifests and passes both repository CI and isolated Python 3.11/3.12 tests. Then open a separate event-semantics work package. Keep P&L prohibited.
