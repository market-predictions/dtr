# Asia Sweep Data-Integrity Gate — Independent Review Pass

## Review method

A clean-room analytical review was performed against the published PR #24 diff, its failed and corrected CI runs, the standalone roadmap, and the broader objective of finding strategies that are consistently profitable. This is an independent reasoning pass within the same AI work session, not an external human audit.

## Verdict

`APPROVE_DATA_INTEGRITY_FOR_MERGE_BLOCK_EVENT_RESULTS_AND_PNL`

The changes materially improve research validity without touching DTR alpha logic or producing performance results. Both the original repository CI and the dedicated Asia Sweep CI pass on the corrected head.

## What the review confirmed

- Asia Sweep remains a separate strategy and evidence track.
- The raw source adapter no longer silently deduplicates timestamps or drops the final date.
- Incomplete Asia ranges cannot create signals.
- Missing data before the determining bar blocks the event causally.
- A gap that occurs only after a valid signal cannot retrospectively erase it.
- `NO_SWEEP` requires a complete execution window.
- AS-C requires a complete causal 20-bar body reference.
- Duplicate pytest module names were removed so DTR and Asia tests remain operationally separate.
- The isolated suite passes on Python 3.11 and 3.12.
- Existing DTR lint and tests remain green.
- No P&L, optimization, or combined-strategy result was generated.

## Defects found and corrected during review

### DR1 — Silent source repair inherited from DTR loader

The initial runner reused a loader that sorted, deduplicated, and dropped the final date. Those behaviors are unsuitable for a separate data-quality gate because they can conceal defects.

**Resolution:** added a strict Asia-specific ZIP/CSV adapter with explicit schema, duplicate rejection, off-grid rejection, and no automatic final-date removal.

### DR2 — Pytest module collision

The separate Asia suite introduced `test_integrity.py`, colliding with DTR's existing file of the same module name under pytest's import mode.

**Resolution:** renamed the Asia module to `test_asia_interval_integrity.py`. This preserves physical test separation and passes both Python versions.

### DR3 — Ruff import formatting

The new data-adapter test had a noncanonical import block.

**Resolution:** applied Ruff's exact fix preview. The repository lint gate now passes.

### DR4 — CI output was initially truncated

The first failed test logs could not be reviewed reliably through abbreviated job output.

**Resolution:** the dedicated Asia workflow now uploads full pytest reports before enforcing the test gate. This improves future auditability without weakening failures.

## Remaining blockers before event results

### R1 — Current NQ timestamp semantics remain unresolved

The existing NQ validity research reports no observations labelled 18:00. Under the strict 18:00–02:00 Asia contract, this may make sessions appear incomplete depending on whether timestamps represent bar opens or closes.

**Required:** preregister and run both plausible timestamp interpretations, or obtain vendor documentation that resolves the label convention. Never select the interpretation by profitability.

### R2 — Continuous-contract construction remains unresolved

A strict event ledger does not resolve whether roll adjustment or contract splicing affects Asia levels and sweep behavior.

**Required:** register individual-contract metadata or documented continuous-contract methodology and perform roll-adjacent sensitivity before decisive validation.

### R3 — ES data remain unregistered

No ES path, checksum, source schema, timestamp semantics, or contract construction is registered.

**Required:** register a qualified ES dataset. Do not infer its schema from NQ.

### R4 — No data-backed manual event audit has occurred

Synthetic tests validate implementation semantics, not correspondence with real market bars.

**Required:** generate event ledgers without P&L and manually review at least 50 NQ and 50 ES events across directions, windows, DST transitions, gaps, and roll-adjacent dates.

### R5 — Post-entry execution is intentionally absent

The event ledger records raw entry, stop, and target levels but does not simulate fills, costs, same-minute collisions, time exits, or causal gap liquidation.

**Required:** connect a neutral execution adapter only after real-event semantics are audited and frozen.

## Relevance to the greater goal

This work does not provide evidence that Asia Sweep is profitable. It does improve the probability that any later result will be interpretable rather than an artifact of missing bars, silent source repair, lookahead, or test coupling.

The strategy should advance only if it later demonstrates:

- positive independent expectancy in NQ and ES;
- robustness to costs and timestamp interpretation;
- incremental value beyond the simple reclaim control;
- acceptable concentration and drawdown behavior;
- familywise-aware historical support;
- fresh out-of-sample confirmation.

## Recommendation

Merge the data-integrity gate after the final documentation sync passes CI. Continue with data registration and event-only audit. Keep historical P&L blocked until the unresolved timestamp, roll, ES, and event-audit requirements are satisfied.
