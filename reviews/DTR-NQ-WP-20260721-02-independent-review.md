# Independent Review — DTR-NQ-WP-20260721-02

## Review stance

Assume the continuation edge is false until the event definition, execution model, chronological evidence, cost stress, and selection history survive attempts to disprove it.

## Scope reviewed

- structural separation from reversal;
- first-breakout and acceptance state logic;
- immediate and pullback entry routes;
- pre-entry failure accounting;
- failed-breakout and structural exits;
- gap-safe execution;
- full funnel reconciliation;
- manifests and deterministic artifact generation;
- timing, risk, cost, session, bootstrap, and walk-forward stress;
- promotion and combination restrictions.

## Findings

### 1. Unfiltered continuation fails

All four predeclared structural variants are negative overall. Immediate entry is decisively poor. Two-bar pullback is the least bad baseline, but remains negative in development and aggregate results.

Status: **confirmed**.

### 2. The late timing lead is plausible but selected

A delay of approximately 60–70 minutes after range completion produces a positive parameter plateau for two-bar pullbacks. The mechanism is plausible because a later break follows prolonged balance. However, this timing condition was identified after diagnostic screening on the same finite dataset.

Status: **research lead, not independent confirmation**.

### 3. Risk/exit robustness is encouraging

All 12 predeclared late-60 risk and exit variants remain positive in development, validation, and later research. The result is not dependent on one exact stop or target setting.

Status: **passed as exploratory robustness**.

### 4. Cost robustness is insufficient

Two-tick slippage turns development negative. Four-tick slippage turns the aggregate result negative. The lead is sensitive to execution friction.

Status: **failed strong cost-stress gate**.

### 5. Statistical confidence is insufficient

Trade and month-block bootstrap intervals include zero. The late-60 population contains only 147 trades, with 71 trades in the expanding walk-forward test and nine in the final fold.

Status: **failed statistical promotion gate**.

### 6. Session stability is incomplete

London is the strongest contributor. New York and Asia are not positive in every period. Selecting London now would add another post-selection layer.

Status: **insufficient for session-specific promotion**.

### 7. Determinism and implementation quality

- Manifest-driven baseline and key stress runs reproduce byte-for-byte.
- Gap-policy enforcement remains `reject_unsafe`.
- Frozen reversal manifests and metrics are unchanged.
- Pinned Ruff and the full Python 3.11/3.12 test matrix are required before merge.

Status: **passed**.

## Promotion decision

`HOLD_FOR_FRESH_DATA`

This decision authorizes:

- merging the continuation engine and negative/held research evidence;
- retaining `CONT_A2_PULLBACK_LATE60` as a named research lead;
- moving to the next independent module on the current roadmap.

This decision does **not** authorize:

- combination with reversal;
- further timing, session, or exit tuning on the current sample;
- production deployment;
- Pine implementation;
- profitability claims.

## Reassessment gate

Reassess only when at least one of the following exists:

1. genuinely new post-December-2025 NQ data;
2. a separately approved out-of-sample futures dataset;
3. corrected timestamp/rollover semantics that materially change event construction.
