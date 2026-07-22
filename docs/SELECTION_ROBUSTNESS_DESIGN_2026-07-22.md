# Selection Robustness and Execution Contract — Design

## 1. Evidence boundary

The corrected causal benchmark is fixed at 495 trades and may not be retuned in this work package. The historical headline came from staged evaluation of 904 configurations. Validation metrics participated in selection, so ordinary confidence intervals around the selected trade stream do not answer the familywise question.

This work package distinguishes:

1. **exact historical reconstruction** — reproduce the original candidate configurations and stage chronology;
2. **current-code causal rerun** — rerun a frozen candidate universe under v0.4.0 execution;
3. **selection inference** — evaluate the best result relative to the whole frozen universe;
4. **fresh OOS** — explicitly outside scope and not inspected.

No result from category 2 may be presented as exact category 1 evidence unless configuration and chronology hashes match.

## 2. Common observation units

### Primary: session-date × session

Each observation represents one named session on one market date. Candidate return is the sum of causal portfolio R attributed to that observation, with zero assigned when the candidate takes no trade.

Reasons:

- preserves the strategy's natural session decision unit;
- keeps session concentration visible;
- permits candidates with different trade counts to align;
- avoids treating each selected trade as an exchangeable observation;
- supports date/session block resampling.

### Sensitivity: calendar market date

Candidate returns are summed across sessions for each market date. This tests whether conclusions depend on treating same-day sessions separately.

### Excluded primary units

- individual trades: candidates have different trade sets and no natural one-to-one alignment;
- five-minute bars: excessive zero inflation and serial dependence;
- months only: sample too small for primary familywise inference.

## 3. Candidate identity

Every matrix column must record:

- stable candidate ID;
- original pack or stage;
- full strategy parameter hash;
- parent/base configuration hash;
- whether it belongs to exact historical reconstruction or current-code rerun;
- trade count, active observation count, and total R;
- return-stream SHA-256.

Duplicate parameter hashes or identical return streams must be reported and may be collapsed only in a separately labeled effective-universe sensitivity.

## 4. Familywise tests

### Centered max-t bootstrap

For the aligned matrix:

1. calculate each candidate's mean return and standard error on the chosen observation unit;
2. center every candidate return stream under the null;
3. resample market dates in blocks, preserving all candidate columns jointly;
4. calculate the maximum candidate t-statistic per resample;
5. compare the selected candidate's observed t-statistic with that maximum distribution.

The joint resampling preserves candidate dependence.

### Reality-check style best-mean test

Also test the observed maximum mean return against the distribution of maximum centered means under the same joint block resampling.

### Reselection stability

For each resample, reapply the frozen selection score where its required metrics can be reconstructed. Report:

- selection frequency of the historical winner;
- frequency by pack and parameter family;
- entropy/effective number of selected candidates;
- probability that the winner changes;
- distribution of winner-minus-runner-up margin.

### PBO / CSCV

Use CSCV only if the aligned sample and candidate universe satisfy practical partition requirements. Otherwise report `NOT_APPLIED_ASSUMPTIONS_NOT_MET`; do not emit a decorative PBO number.

## 5. Plateau diagnostics

A plateau must be assessed in parameter space and return-stream space.

Report:

- nearest candidates by normalized parameter distance;
- nearest candidates by return correlation;
- proportion of neighbors positive in development, validation, later, and full sample;
- median and dispersion of neighbor expectancy and return/DD;
- winner's rank stability under leave-one-half-year-out and leave-one-session-out analyses;
- duplicate or effectively identical variants.

A strong single winner surrounded by weak neighbors fails the plateau gate even when familywise p is small.

## 6. Explicit execution architecture

Canonical imports must not rely on `research.__init__` mutating `engine` symbols.

Target architecture:

- `engine.py`: signal primitives and execution implementation, with explicit policy argument at public orchestration boundary;
- `integrity.py`: gap classification and causal liquidation helpers without monkey-patching;
- canonical `run_backtest`: causal `liquidate_unsafe` default or required explicit policy;
- historical policies available only through clearly named research-regression entry points;
- manifests reject an omitted or unknown execution policy;
- tests cover package import, direct module import, different import order, and historical regression paths.

No trade outcome or signal may change during this refactor. The 495-trade benchmark is an exact regression gate.

## 7. Stop conditions

Stop and classify `EXACT_RECONSTRUCTION_BLOCKED` when:

- stage base configurations cannot be recovered;
- leaderboard rows lack sufficient parameters;
- original selected chronology cannot be distinguished from later inspection;
- current code cannot reproduce original candidate IDs without hidden assumptions.

Even under that state, a new frozen causal 904-candidate universe may be built as a separate experiment, but it must not be called the original selection correction.

## 8. Decision interpretation

- A familywise pass plus broad plateau stability supports historical research credibility only.
- A familywise fail or ambiguous result strengthens the requirement to rely on the preregistered fresh OOS test.
- No historical result authorizes deployment.
