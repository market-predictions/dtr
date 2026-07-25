# Asian Sweep Fingerprint Study — Binding Label Clarification v1.2

Date frozen: `2026-07-25`  
Branch: `agent/asia-sweep-fingerprint-study`  
Applies to: fingerprint preregistration v1.1.0  
Status: `FROZEN_BEFORE_DEVELOPMENT_OUTCOME_INSPECTION`

This clarification resolves two path-label edge cases before the 2015–2021 development ledgers are inspected. It does not change the primitive sweep threshold, feature families, validation partitions, model families or future validation gates.

## 1. Exact 09:00 lower bound

A sweep may occur between 08:00 and 10:00 Amsterdam, but primary `MIDPOINT_SUCCESS_09_10` requires the first midpoint passage to occur inside the half-open interval `[09:00, 10:00)` Amsterdam.

A midpoint first reached before 09:00 is classified as `EARLY_MIDPOINT`. It remains in the anatomy ledger but is not a primary success for the stated ICT reversal-window hypothesis.

A pre-09:00 sweep may still be a primary success when its first midpoint passage occurs at or after 09:00 and before 10:00, subject to the unchanged adverse-barrier ordering rule.

## 2. Sequential two-sided ambiguity

When the opposite Asian boundary is swept after a candidate event begins but before that event reaches either its midpoint target or adverse continuation barrier, the earlier event is classified as `TWO_SIDED_AMBIGUOUS`.

An opposite-side sweep occurring only after the earlier event has resolved does not retroactively invalidate the resolved event. The later sweep remains a separate candidate with its own first-passage outcome.

Same-minute dual-boundary sweeps remain ambiguous because one-minute OHLC data cannot resolve the intrabar ordering.

## 3. Governance

The implementation and tests for these rules were committed before pair-level 2015–2021 fingerprint artifacts were accepted. Neither clarification was selected from observed development results.
