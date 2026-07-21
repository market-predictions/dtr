# Independent Review — DTR-NQ-WP-20260721-03

## Review stance

Assume IFVG confirmation has no incremental edge until causal implementation, opportunity coverage, chronological stability, portfolio sequencing, cost stress, and determinism demonstrate otherwise.

## Scope reviewed

- FVG creation and inversion causality;
- bullish and bearish directional symmetry;
- reset-epoch and unsafe-gap isolation;
- alignment after the reversal sweep and before entry;
- age-window and zone-touch semantics;
- frozen-cohort versus implementable-portfolio analysis;
- position-overlap consequences;
- chronological and cost stability;
- manifest reproducibility, tests, and governance discipline.

## Material findings

### Finding 1 — IFVG is too common to be a strong discriminator

An aligned IFVG exists on 455 of 491 frozen baseline trades. `IFVG_CONFIRM_ANY` therefore preserves 92.7% of trades while lowering expectancy from 0.180236R to 0.168419R.

**Conclusion:** the broad IFVG condition is descriptive of the existing reversal process, not an independent decision edge.

### Finding 2 — Stricter timing does not form a robust plateau

The three-, six-, and twelve-bar rules all lower aggregate expectancy. Their later-research expectancies deteriorate to 0.044450R, 0.063801R, and 0.080036R respectively.

**Conclusion:** timing sensitivity is non-monotonic and chronologically unstable.

### Finding 3 — Cohort results cannot be substituted for portfolio results

The frozen recent-three cohort has 0.182110R expectancy, marginally above the 0.180236R baseline. Filtering earlier signals enables five later trades that lose 3.453931R, reducing implementable portfolio expectancy to 0.168385R.

**Conclusion:** portfolio sequencing is material and has been correctly attributed. The marginal cohort result is not a tradable improvement.

### Finding 4 — IFVG absence is not a valid rejection signal

The 36 unconfirmed baseline trades have 0.329584R expectancy, but the small cohort is unstable: validation is approximately flat and later research contains only nine trades.

**Conclusion:** neither IFVG presence nor absence supports a promotable filter.

### Finding 5 — Zone touch reduces opportunity more than risk

The zone-touch rule retains 212 trades and lowers maximum drawdown, but expectancy falls to 0.153369R and return-to-drawdown remains inferior to baseline.

**Conclusion:** lower drawdown is primarily lower exposure, not better decision quality.

### Finding 6 — Cost stress preserves the rejection

At one-, two-, and four-tick slippage, every filtered portfolio remains below the corresponding observe baseline.

**Conclusion:** realistic cost variation does not reveal hidden IFVG value.

### Finding 7 — No implementation or reproducibility defect explains the result

Long/short symmetry, causal timing, reset invalidation, post-inversion touch, config-signature protection, portfolio attribution, strict manifest validation, and the full repository suite pass. The canonical run reproduces the 491-trade frozen baseline and 52 artifacts are byte-identical across clean repeats.

**Conclusion:** the negative result is a research finding, not an unresolved implementation failure.

## Validation evidence

- Pinned Ruff: passed.
- Pytest Python 3.11: passed.
- Pytest Python 3.12: passed.
- Frozen observe regression: passed.
- Causal bullish and bearish inversion fixtures: passed.
- Reset-epoch invalidation fixture: passed.
- Sweep-to-entry causality fixture: passed.
- Zone-touch and age-window fixture: passed.
- Portfolio attribution fixture: passed.
- Manifest schema and checksum fixtures: passed.
- Canonical clean-repeat artifact comparison: 52/52 byte-identical.
- Exact changed-trade attribution: complete; no unexplained differences.

## Independent decision

`REJECT_NO_INCREMENTAL_VALUE`

Approved actions:

- merge the causal IFVG detector, tests, manifest runner, and negative evidence;
- retain IFVG as an optional diagnostic field;
- close the IFVG work package;
- advance to a separately scoped CISD ablation.

Prohibited actions:

- no IFVG confirmation in the reversal candidate;
- no post-hoc age, size, session, weekday, direction, or zone threshold tuning on this sample;
- no combination with the held continuation lead;
- no production or Pine implementation based on this IFVG result.
