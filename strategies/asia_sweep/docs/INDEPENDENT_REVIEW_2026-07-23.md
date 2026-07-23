# Asia Sweep Foundation — Independent Review Pass

## Review method

A clean-room review pass was performed after implementation and again against the published pull-request diff, using the accepted roadmap, separation requirement and greater objective of finding strategies that are consistently profitable. This is an independent analytical pass within the same AI work session, not an external human audit.

## Verdict

`APPROVE_FOUNDATION_WITH_BLOCKERS_BEFORE_PNL`

The foundation is relevant to the broader strategy-discovery objective because it tests a simple, transferable market hypothesis on both NQ and ES and requires incremental evidence over a simpler reclaim control. The architecture correctly treats it as a separate strategy rather than a DTR enhancement.

## Strengths

- Strategy identity and evidence are cleanly separated from DTR.
- The four-variant family is small enough to support multiple-testing control.
- Entry timestamps occur after determining bar closes.
- AS-D waits for right-side swing confirmation before using the reaction level.
- The first qualifying sweep owns the event, preventing retrospective replacement by a later sweep.
- Rejected events are retained, which supports funnel and selection-bias analysis.
- Same-bar double sweeps are rejected rather than resolved optimistically.
- AS-C uses causal preceding five-minute history and does not reset its body reference at the execution-window boundary.
- Tests are physically and operationally separate from DTR tests.
- ES cannot be silently run with an invented source.

## Resolved during published-diff review

### RR1 — Displacement reference reset at execution-window start

The initial implementation calculated the trailing body median only inside each execution window. This could suppress early-London displacement signals and create a time-of-day artifact.

**Resolution:** compute the median from all available preceding five-minute bars before filtering to the execution window. Added an early-London regression test.

### RR2 — Repository line-length policy

The initial published diff contained lines above the repository's 100-character Ruff limit.

**Resolution:** reformatted the new Python files and manually verified the edited files contain no lines above 100 characters. Ruff itself could not be installed in the restricted local environment, so CI confirmation remains required.

## Findings requiring action before P&L

### R1 — Session completeness is not yet enforced

The current detector requires non-empty Asia and execution windows, but it does not yet require the expected number of one-minute bars or reject unsafe gaps. A partial session could therefore produce an incorrect range.

**Required:** connect the repository's integrity metadata or add a neutral completeness contract before historical P&L.

### R2 — NQ loader assumptions are source-specific

The proposed runner borrows the existing loader, which expects the current NQ schema and drops the final date. ES may use a different schema or source.

**Required:** introduce a provider-neutral loader adapter or explicitly require identical schema in the ES manifest.

### R3 — Failed-retest definition is intentionally narrow

The one-right-bar pivot and short eight-bar horizon are preregistered implementation choices, not established market truths.

**Required:** treat AS-D as one declared candidate, not as the definitive interpretation of the social-media setup. Do not tune it after validation inspection.

### R4 — No execution parity yet

The ledger stores raw close, stop and target levels but does not yet model next-minute fills, commissions, slippage, gaps or time exits.

**Required:** connect a neutral execution adapter only after event audit. Preserve conservative stop-first collisions.

### R5 — DTR baseline protection is documented but not rerun here

No existing DTR file was edited, which minimizes risk, but the canonical baseline was not rerun in this tool environment.

**Required:** CI or a full local checkout must reproduce the locked 495-trade benchmark before any shared-infrastructure extraction.

### R6 — Strategy relevance depends on transfer, not headline NQ profit

A positive NQ full-sample result alone would not support the greater goal.

**Required:** enforce matched-date NQ/ES results, concentration gates, paired ablations and fresh OOS before calling the strategy solid.

## Roadmap alignment

- WP-AS-00/01 documentation: substantially complete.
- WP-AS-02 data qualification: NQ referenced but unresolved; ES blocked.
- WP-AS-03 isolation architecture: complete at signal boundary; neutral execution extraction pending.
- WP-AS-04 event ledger: foundation complete; completeness/gap metadata pending.
- WP-AS-05 variants: implemented.
- WP-AS-06 deterministic tests: initial nine-test suite complete; full 20-case adversarial set pending.
- WP-AS-07 onward: not authorized yet.

## Recommendation

Merge only as a research foundation after CI passes. Continue autonomously with data qualification and event audit. Do not inspect P&L until the separation, completeness, gap and execution contracts are frozen.
