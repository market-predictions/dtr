# Independent Review — DTR-NQ-WP-20260721-01

## Review stance

The reviewer assumes the apparent DTR edge is false until data integrity, reproducibility, and execution semantics survive attempts to disprove it. This review evaluates the baseline-integrity implementation independently from candidate construction.

## Scope reviewed

- gap classification consumption by the strategy runner;
- session-range and post-range setup state;
- open-trade behavior across missing data;
- preservation of the historical baseline;
- manifest reproducibility;
- import and optimization bypass paths;
- test coverage and CI;
- governance artifacts and scope discipline.

## Material findings

### Finding 1 — Baseline mutation risk

**Initial condition:** the first implementation routed the frozen candidate directly through the new rejection policy.

**Risk:** this would intentionally change the trade set and cause the historic 504-trade regression to fail without preserving a machine-runnable pre-safety reference. A safety improvement must not silently rewrite historical evidence.

**Required correction:** introduce two explicit manifests using identical strategy parameters:

- `DTR_PY_NQ_CANDIDATE_0_1` with `gap_policy: observe_only`;
- `DTR_PY_NQ_CANDIDATE_0_1_GAP_SAFE` with `gap_policy: reject_unsafe`.

**Status:** corrected and tested.

### Finding 2 — Resume-timestamp blind spot

**Initial condition:** overlap checks used only the first timestamp after a gap.

**Risk:** a gap can begin inside a session range, setup path, or open trade and resume after that window ends. Testing only the resume timestamp can miss the contamination entirely.

**Required correction:** represent every classified gap as the complete interval between the last observed pre-gap bar and the first observed post-gap bar. Reject or truncate whenever that interval overlaps the evaluated window.

**Status:** corrected with dedicated interval-overlap tests.

### Finding 3 — Research-run bypass risk

**Risk:** callers importing the legacy engine or optimization functions in a different order could bypass the integrity wrapper.

**Required correction:** route standard package and direct engine entry points through the integrity-safe implementation before optimization functions capture their runner references. Retain the captured legacy runner only for the explicit observe-only reference path.

**Status:** corrected and covered by regression tests.

### Finding 4 — Lint reproducibility

**Initial condition:** Ruff was unpinned and executed redundantly inside both Python matrix jobs. Existing violations were not clearly attributable.

**Required correction:** pin Ruff 0.15.22, separate lint from pytest, retain a short-lived Ruff report artifact, and record narrowly scoped pre-existing lint debt rather than applying global ignores.

**Status:** corrected. CI run `29850412195` passed lint and pytest on Python 3.11 and 3.12.

## Behavioral contract after correction

### Observe-only reference

- preserves historical strategy behavior and expected regression metrics;
- reports contaminated ranges, truncated-path opportunities, and unsafe trade bridges;
- does not remove trades;
- exists solely to reproduce and explain the prior candidate.

### Reject-unsafe candidate

- rejects a session range when a reset interval intersects the defining range;
- truncates the post-range signal window at the first missing-data interval;
- excludes an open trade when its lifetime intersects an unsafe interval;
- never fills or synthesizes absent bars;
- reports every integrity rejection in the funnel;
- uses exactly the same strategy parameters as the reference candidate.

## Validation evidence

- Pinned Ruff gate: passed.
- Python 3.11 pytest matrix: passed.
- Python 3.12 pytest matrix: passed.
- Clean-data preservation tests: passed.
- Intra-five-minute gap test: passed.
- Session-range contamination test: passed.
- Signal-path reset test: passed.
- Unsafe open-trade overlap test: passed.
- Full-interval resume-after-window tests: passed.
- Manifest policy and backward-compatibility tests: passed.

## Unresolved limitations

1. The full checksum-matched NQ archive is not stored in Git and was unavailable in the CI environment.
2. The observe-only 504-trade regression must still be executed against the local archive.
3. Gap-safe aggregate metrics, trade deltas, and artifact hashes are not yet frozen.
4. Continuous-contract rollover and back-adjustment methodology remain unresolved.
5. Timestamp meaning, daylight-saving transitions, session boundaries, and supplied VWAP resets remain provisional.
6. The gap-safe exclusion policy avoids fabricating execution through missing data, but it does not estimate what a real fill would have been.
7. Legacy lint debt in the large engine and optimizer is explicitly quarantined for a separate cleanup work package.

## Full-dataset execution review

The checksum-matched archive reproduced the frozen reference exactly:

- trades: `504`;
- net R: `84.16435914242919`;
- maximum drawdown: `14.107857513807524R`.

The identical-parameter gap-safe run produced:

- trades: `491`;
- net R: `88.49578342152539`;
- maximum drawdown: `14.107857513807524R`.

Every changed trade was attributed:

- `9` contaminated session ranges;
- `4` unsafe gaps during open trades;
- `0` added trades;
- `0` unexplained differences.

Both manifests were rerun into clean directories. All required CSV, Parquet, funnel, attribution, and summary artifacts were byte-identical between first and second execution.

### Interpretation challenge

The 4.331424R increase in sanitized net R is not an optimization result. It arises from removing contaminated observations. The effect is not uniformly positive: Asia and London improve, while New York declines by 1.022007R because its two removed contaminated trades were net profitable. The later-research slice improves by only 0.134078R. Therefore the integrity correction should not be represented as stronger evidence of edge.

## Remaining limitations

1. Continuous-contract rollover and back-adjustment methodology remain unresolved.
2. Timestamp meaning, daylight-saving transitions, session boundaries, and supplied VWAP resets remain provisional.
3. The gap-safe policy excludes execution through missing data rather than estimating hypothetical fills.
4. No post-December-2025 paper-forward sample is available.
5. Legacy lint debt in the large engine and optimizer remains explicitly quarantined for a separate cleanup work package.

## Final promotion decision

`PROMOTE_TO_CONTINUATION_RESEARCH`

This decision authorizes an independent continuation research branch under the locked gap-safe data contract. It does **not** approve:

- production deployment;
- parameter retuning of the reversal candidate;
- combining reversal and continuation before independent evidence;
- profitability claims;
- cross-market extrapolation.

The continuation branch must demonstrate independently positive walk-forward evidence and acceptable opportunity coverage before any adaptive routing or combination is considered.
