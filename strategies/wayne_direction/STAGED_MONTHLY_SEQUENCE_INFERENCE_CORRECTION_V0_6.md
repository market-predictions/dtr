# Wayne Staged Monthly Sequence — Inference Correction v0.6

Date: 2026-07-27
Frozen pair-source run: `30253362740`

## Audit finding

The pair construction, causal sequence timestamps, stage classifications, target availability and reach outcomes were correct. The first pooled aggregator, however, shuffled treatment labels at the side-opportunity row level during permutation inference.

The v0.5 preregistration defines the cluster as instrument × month. A month can contain both bullish and bearish opportunities, so row-level shuffling can create treatment combinations that did not occur and can understate dependence.

## Correction

The corrected permutation:

- keeps each instrument-month treatment vector intact;
- orders side rows deterministically;
- permutes complete treatment vectors only between clusters of the same size;
- remains stratified by instrument-year;
- retains 5,000 permutations and all frozen effect, sample, breadth and q-value gates.

A regression proves that identical two-side treatment bundles cannot be broken into impossible assignments.

## Frozen evidence boundary

No pair job is rerun and no market event is changed. The correction workflow downloads the six exact pair artifacts from run `30253362740` and recomputes only pooled inference.

The original aggregate artifact remains an audit record but is superseded for p-values and q-values by the clustered correction artifact. The binding sample decision was already a failure and cannot become a pass through this correction.
