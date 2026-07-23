# Handover — STOIC123-WP-20260723-02

Date: 2026-07-23
Branch: `agent/stoic-nq-long-only-validation`
Pull request: #36
Status: `COMPLETE_NO_PROMOTION`

## Delivered

- Corrected entry-direction versus management-direction architecture.
- Frozen NQ long-only validation design.
- Causal EMA-break and retest controls.
- Deterministic matched-time controls and conservative comparability veto.
- Cached parity-tested validation execution.
- Exact source/config preflight and private-data cleanup workflow.
- Complete NQ futures execution, compact results, independent review, decision, changelog, roadmap, and status closure.

## Final evidence

- Workflow run: `30036385787`.
- Artifact SHA-256: `92f747b5ae07d252abb4bb0720b3aeaab8f3ebb3264ac27310425b4918c2a6e9`.
- Source SHA-256: `8d3f157a422636e5b8dda51cc3a3d9209c50cb53f9b279d3e14b627ce59370dc`.
- Phase-one SHA-256: `5d6909bd5740e1cdea9bd3d47a9818289a6faa8b9a61338726afdc53289ff805`.
- Independent reconstruction: 32/32 scenario ledgers passed.
- Numerical selection: no candidate passed all nine gates.
- Matched-control selection: all four candidates vetoed.

## Final decision

`NO_PROMOTION_STOP_NQ_LONG_ONLY_CURRENT_SAMPLE`

The proxy-derived EMA-map long-only hypothesis failed on actual NQ futures. The current sample must not be mined further for directional, session, delay, or exit variants.

## Next legitimate route

No immediate implementation phase is authorized. A new Stoic study requires qualified unseen or materially longer contract-audited data and a new preregistration. The observed no-map short-side asymmetry is a post-hoc hypothesis only.

## Merge note

PR #36 remains stacked on PR #23 and must not merge before its base. Raw market data and bulk workflow ledgers remain outside Git.
