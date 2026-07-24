# Handover — Research Cycle Acceleration

Date completed: 2026-07-24  
Branch: `agent/research-cycle-acceleration-wp1`  
PR: `#44`  
Work packages: `STOIC123-WP-20260724-07`, `-08`, `-09`  
Status: `COMPLETE`

## Objective completed

The strategy research cycle was accelerated without weakening frozen-source integrity, causal signal construction, one-minute execution, promotion gates, independent review or maintainability.

The former all-at-once workflow is no longer required for every variation. The platform now separates inexpensive rejection from full certification.

## Delivered operating model

### Screen

- designated discovery partition only;
- candidate baseline and simple mechanism diagnostic;
- no bootstrap, matched controls or complete review package;
- deterministic futility rejection;
- no promotion authority.

### Validate

- candidate cost and delay stresses;
- candidate-only preliminary bootstrap;
- candidate/stress independent review and attribution;
- deterministic primary futility stopping;
- no promotion authority.

### Certify

- all frozen partitions;
- complete candidate inference and independent reviews;
- candidate-only matched controls;
- all promotion gates;
- exact frozen-evidence parity;
- sole accelerated mode with promotion authority.

### Legacy

- retained former complete execution path;
- all diagnostic bootstraps and both historical matched-control families;
- used as a regression reference.

## Architecture delivered

- Content-addressed Parquet caches for resampled bars and detected event ledgers.
- Canonical input/configuration hashes and cache metadata validation.
- Exact single-stream cost repricing from gross R and initial risk.
- Deterministic batched date-block bootstrap equal to the former loop.
- JSON/CSV timing telemetry for every major stage.
- Independent partition certification runner.
- Four-way GitHub Actions certification matrix.
- Deterministic aggregate runner for combined ledgers, reviews and gates.
- Frozen-reference parity comparator.
- Discovery-only variation contract with dependency signatures and holdout protection.

## Real-data evidence

### Sequential benchmark

Workflow: `30097374605`  
Artifact: `stoic-research-cycle-acceleration-benchmark`

| Cycle | Wall time |
|---|---:|
| Cold-cache screen | 9.81s |
| Warm-cache screen | 4.54s |
| Staged validation with primary futility rejection | 5.58s |
| Full accelerated certification | 52.56s |

Parity outcome:

- 17 decision-relevant candidate summary rows matched within `1e-12`;
- 19 of 19 promotion gates matched;
- final decision matched exactly;
- raw source data absent from the published benchmark artifact.

### Parallel certification

Workflow: `30097964143`  
Artifact: `stoic-research-cycle-parallel-result`

| Partition | Compute wall time |
|---|---:|
| 2015–2019 primary | 21.45s |
| 2020–2022 crisis/regime | 17.27s |
| 2023–2025 recent holdout | 17.91s |
| 2026 YTD monitoring | 4.61s |

- Serial partition compute sum: `61.24s`.
- Parallel compute lower bound: `21.45s`.
- Compute acceleration: `2.85x`.
- Full candidate, gate and decision parity passed.

## Profiling conclusion

Full sequential certification stage totals showed:

- matched controls: `25.83s`;
- source loading: `8.58s`;
- ordinary simulation: `5.03s`;
- resampling: `2.37s`;
- full-sequence detection: `2.35s`;
- other detection: `4.55s`;
- all decision bootstraps: `0.06s`.

A Numba/GPU rewrite was deliberately not implemented. Ordinary simulation was not the dominant bottleneck, and adding a second optimized execution kernel would create disproportionate parity and maintenance risk. JIT work should be reconsidered only after profiling a future strategy family.

## Key files

- `src/stoic_123_lab/research_runtime.py`
- `src/stoic_123_lab/research_cache.py`
- `src/stoic_123_lab/cost_repricing.py`
- `src/stoic_123_lab/research_batch.py`
- `src/stoic_123_lab/reporting.py`
- `src/stoic_123_lab/usa500_rth_study.py`
- `scripts/run_stoic_usa500_accelerated.py`
- `scripts/run_stoic_usa500_partition.py`
- `scripts/aggregate_stoic_usa500_partitions.py`
- `scripts/run_stoic_usa500_batch_screen.py`
- `scripts/compare_stoic_acceleration_parity.py`
- `.github/workflows/stoic-research-cycle-benchmark.yml`
- `.github/workflows/stoic-research-cycle-parallel.yml`
- `strategies/stoic_123/governance/RESEARCH_CYCLE_ACCELERATION_2026-07-24.md`

## Validation files

- `tests/test_stoic_123_research_acceleration.py`
- `tests/test_stoic_123_bootstrap_batching.py`
- `tests/test_stoic_123_research_batch.py`

## Operational usage

A future new strategy family should follow this sequence:

1. preregister a genuinely new mechanism and a discovery partition;
2. run a discovery-only batch screen;
3. freeze the surviving candidate family and record all inspected variations;
4. run validation mode;
5. reject immediately when mandatory futility gates fail;
6. certify only frozen survivors on untouched partitions;
7. require complete parity and independent review before promotion.

## Known maintenance items

- The external private content-addressed source registry remains a future platform improvement; current workflows reuse frozen Actions artifacts and derived caches.
- `usa500_rth_study.py` retains one narrowly scoped temporary Ruff `UP035` exception introduced by connector-based editing. Remove it during the next structural rewrite after moving the `Callable` import to `collections.abc`.
- The current discovery batch runner shares caches and dependency signatures but does not yet vectorize all variations into one simulator invocation. Add deeper batching only after a real new strategy family demonstrates that it is necessary.

## Research boundary

The acceleration work does not reopen the rejected mechanical Stoic 1-2-3 family. No real parameter sweep was executed. Batch infrastructure may only be used for a new preregistered mechanism on designated discovery data.

No Pine port, sizing, alert, paper-trading or live-use authorization follows from this platform work.
