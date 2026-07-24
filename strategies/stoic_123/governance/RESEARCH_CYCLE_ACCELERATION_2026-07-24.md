# Research Cycle Acceleration — Architecture and Operating Contract

Date: 2026-07-24  
Work packages: `STOIC123-WP-20260724-07` through `-09`

## Operating modes

### Screen

Purpose: reject weak variations cheaply.

- designated discovery partition only;
- baseline candidate plus simple mechanism diagnostic;
- no bootstrap, matched controls or full independent package;
- no trade-ledger publication;
- deterministic futility stop;
- cannot promote.

### Validate

Purpose: test survivors before spending full certification resources.

- decision partitions until a mandatory primary gate fails;
- candidate cost and delay stresses;
- 1,000-iteration candidate bootstrap;
- candidate/stress review and attribution;
- no matched controls;
- cannot promote.

### Certify

Purpose: make the formal retain/hold/reject decision.

- all frozen partitions;
- full candidate bootstrap and independent reviews;
- candidate-only matched controls;
- complete promotion gates;
- exact source and result parity requirements;
- only mode allowed to authorize promotion.

### Legacy

Purpose: preserve the former complete execution path for regression comparison.

- all diagnostic bootstraps;
- both historical matched-control families;
- no accelerated cost repricing;
- no change to prior frozen evidence.

## Dependency and cache model

The cache key includes a schema version, namespace and canonicalized input components. Current cached layers are:

1. resampled execution, management and map bars;
2. management event ledgers;
3. full-sequence, EMA-break and retest event ledgers.

The raw or normalized source hash remains part of the lineage. A cache mismatch, metadata mismatch or row-count mismatch fails closed.

## Exact accelerations

- Cost stresses are repriced algebraically from gross R and initial risk for single-stream execution.
- The date-block bootstrap generates the same random index stream in NumPy batches and is bit-for-bit equal to the former iteration loop.
- Partition concurrency changes only wall time; seeds, source hashes and aggregation order remain deterministic.

## Measured results

Sequential benchmark workflow `30097374605`:

- screen cold: `9.81s`;
- screen warm: `4.54s`;
- validation with futility stop: `5.58s`;
- full accelerated certification: `52.56s`;
- parity: 17 candidate summary rows, 19 gates and final decision exact within `1e-12`.

Parallel workflow `30097964143`:

- partition serial compute sum: `61.24s`;
- parallel compute lower bound: `21.45s`;
- compute acceleration: `2.85x`;
- frozen-evidence parity passed.

## Profiling result

Full certification stage totals:

| Stage | Time |
|---|---:|
| Matched controls | 25.83s |
| Source loading | 8.58s |
| Ordinary simulation | 5.03s |
| Resampling | 2.37s |
| Full-sequence detection | 2.35s |
| Other detection | 4.55s |
| All decision bootstraps | 0.06s |

The next optimization target is persistent source storage and richer cache reuse, not a GPU or Numba rewrite.

## Commands

```bash
python scripts/run_stoic_usa500_accelerated.py --mode screen ...
python scripts/run_stoic_usa500_accelerated.py --mode validate ...
python scripts/run_stoic_usa500_accelerated.py --mode certify ...
python scripts/run_stoic_usa500_partition.py --partition primary_forward ...
python scripts/run_stoic_usa500_batch_screen.py --batch-design <discovery.yaml> ...
```

## Research restrictions

- Batch mode is discovery-only and cannot access holdouts.
- Fast modes cannot authorize promotion.
- No losing year or partition may be removed.
- Proxy identity remains explicit.
- The closed Stoic family may not be reopened through a batch sweep of inspected parameters.
