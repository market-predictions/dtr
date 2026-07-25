# Asian Sweep — Reversal / Continuation Triage Roadmap

Date recorded: `2026-07-26`  
Status: `POST_FINAL_HOLDOUT_RESEARCH_HYPOTHESIS`

## Strategic question

Can the same causal Asian Sweep information distinguish three operational states five minutes after the sweep?

1. high-quality reversal candidate;
2. high-quality same-direction continuation candidate;
3. unresolved or low-confidence event that should be avoided.

## Why this is valid

The current reversal model estimates the probability of a strict midpoint reversal. It does not follow that `1 - P(reversal)` equals `P(continuation)`.

Non-reversal events include:

- immediate continuation;
- false reversal followed by continuation;
- stalled reaction;
- reversal completed too early;
- reversal completed after 10:00;
- two-sided ambiguity;
- other unresolved paths.

A continuation model therefore requires its own causal target and validation. Treating all low reversal scores as continuation would create label contamination and force trades in genuinely ambiguous states.

## Proposed architecture

Create a separate branch after the reversal final holdout:

`agent/asia-sweep-continuation-triage`

### Model A — reversal probability

Retain the already frozen T5 reversal model unchanged.

### Model B — continuation probability

Preregister a continuation target based on same-side price extension after T5, with first-passage ordering against the Asian midpoint and any reversal-invalidating boundary. The exact continuation distance and clock horizon must be frozen before outcome analysis.

Candidate continuation fingerprints should include:

- failure to reclaim or shallow reclaim depth;
- repeated closes outside the Asian range;
- adverse-versus-favourable excursion imbalance at T5;
- failed retest of the swept boundary;
- no reversal-side structure break;
- continued same-side liquidity consumption;
- residual unswept liquidity beyond the sweep;
- displacement and close location in the sweep direction;
- time × ATR-normalized Asian-range width;
- cross-pair confirmation of broad USD continuation.

### Decision policy

The eventual policy must be three-way:

- reversal only when `P(reversal)` is high and `P(continuation)` is low;
- continuation only when `P(continuation)` is high and `P(reversal)` is low;
- abstain when both are low, both are high, or confidence is insufficient.

No signal is generated solely because the reversal threshold is missed.

## Evaluation

Required metrics should include:

- PR-AUC and calibration for reversal and continuation separately;
- confusion between continuation, false reversal, stalled and late-reversal classes;
- selective accuracy at fixed coverage;
- reversal and continuation Hit@1 by pair-week;
- contradiction rate where both models are high;
- abstention rate;
- regret from choosing the wrong directional state;
- pair, year, weekday and side stability;
- spread/slippage feasibility only after predictive validation.

## Evidence boundary

Once 2024–2025 is opened for the reversal final holdout, it is no longer untouched evidence for this new continuation hypothesis.

A rigorous continuation programme should therefore use:

- 2015–2023 for development and grouped temporal cross-validation;
- 2024–2025 only as explicitly post-hoc/exploratory anatomy if used at all;
- prospective 2026+ data and/or preregistered external-pair transfer as independent validation.

The continuation branch must not alter the reversal model or reinterpret the reversal holdout result.

## Roadmap order

1. complete the frozen 2024–2025 reversal holdout;
2. if the reversal holdout passes, freeze executable reversal research separately;
3. open the continuation branch and preregister its target;
4. construct competing-risk / multiclass anatomy;
5. develop a separate continuation classifier;
6. combine the two classifiers into a three-way abstaining triage policy;
7. validate prospectively before strategy P&L or deployment.

## Current disposition

The construct is accepted as a valid next research path, but not as an inference that low reversal quality automatically implies profitable continuation.