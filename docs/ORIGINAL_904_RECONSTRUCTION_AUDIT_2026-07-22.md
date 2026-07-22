# Original 904-Candidate Reconstruction Audit

## Decision

`EXACT_RECONSTRUCTION_BLOCKED`

This decision applies specifically to reconstruction of the **original staged selection chronology** described on 2026-07-21. It does not prevent a newly frozen causal rerun of the same six grid definitions.

## Preserved evidence

The repository preserves:

- the six candidate-grid definitions in commit `8be5c79406ff6cc988fdb1965cf98dc44cd07b09`;
- the pack sizes: BOS 96, sweep 120, regime 200, exit 216, timing 192 and risk 80;
- the `robust_score` formula used by the optimizer;
- the command-line pack runner;
- the final selected configuration `DTR_PY_NQ_CANDIDATE_0_1`;
- the narrative statement that modules were optimized sequentially;
- the final aggregate, attribution and rolling-walk-forward summaries.

## Missing evidence

The repository and searchable commit history do not preserve:

1. the six original pack leaderboards;
2. the complete row-level parameters and metrics for all 904 evaluated configurations;
3. the selected winner from each pack;
4. the exact base configuration supplied to each subsequent pack;
5. the order in which `timing`, `exit` and `risk` bases were updated beyond the narrative pack listing;
6. the candidate return streams or trade lists needed to align the historical universe;
7. hashes of the original leaderboards or stage-transition configurations;
8. a machine-readable log distinguishing decisions made before versus after inspection of later-period results.

Git commit search found no commit containing `leaderboard`; only the grid generator, runner, final candidate and selected-result summaries were committed.

## Why the final candidate is insufficient

The final candidate proves the endpoint but not the path. Because each pack was generated around a mutable base configuration, the same six grid definitions can yield different 904-member universes depending on which earlier winner was carried forward.

Reconstructing stage bases from the final candidate would use hindsight and could silently choose a chronology favorable to the known endpoint. That would not be a valid correction for selection pressure.

## Permitted next experiment

A separate experiment may freeze:

- the accepted causal v0.4.0 engine;
- one explicitly declared common base;
- the six preserved grid definitions;
- the pack order;
- all candidate identities and parameter hashes;
- causal `liquidate_unsafe` execution;
- aligned session-date × session and calendar-date return matrices;
- fixed-seed familywise inference.

This experiment must be labeled:

`CURRENT_CODE_CAUSAL_904_UNIVERSE`

It must not be described as reproducing the original 2026-07-21 optimization chronology.

## Consequence for historical claims

The original selected strategy cannot receive a valid ex-post familywise p-value from the surviving repository artifacts. Its historical evidence remains selection-contaminated. The newly frozen causal universe can measure how exceptional the accepted candidate is relative to a declared current-code neighborhood, but it cannot erase the missing original chronology.

## Deployment implication

`DO_NOT_DEPLOY` remains unchanged. Qualified fresh out-of-sample evidence remains the decisive gate.
