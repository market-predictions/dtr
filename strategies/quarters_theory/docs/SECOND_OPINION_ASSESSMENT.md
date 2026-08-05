# Assessment of the Independent Second Opinion

## Accepted

- Raw barrier probabilities are mostly geometry and must be expressed as excess over a matched null.
- Structural rejection and executable stop boundaries must be aligned.
- Roundness-matched controls are more decisive than arbitrary shifted non-round grids.
- The 250-pip claim must add information beyond ordinary 50- and 100-pip lattices.
- Episode census and empirical power must precede long-horizon strategy gates.
- Short-horizon crossing behaviour should be tested before multi-day targets.
- Cross-pair calendar dependence, carry, event/trade reconciliation and extreme-event handling are required later.

## Accepted with modification

- Power is a blocking question, but the review did not establish an exact factor-of-five deficiency.
- A timed strategy requires joint target/stop/timeout economics; its terminal 2:1 barrier geometry is still mathematically 2:1.
- A 60-minute null materially weakens the order-clustering mechanism but does not logically disprove every multi-day pattern.
- Reciprocal inversion is diagnostic, not decisive, because institutional quote convention matters.
- Both FX trading time and realised-volatility time should be reported.

## Not adopted

- Categorical claims that no independent evidence exists anywhere.
- A subjective low-single-digit prior as a programme input.
- Exact event counts and power estimates from the supplied Gaussian simulation.
- The supplied finite-horizon null probabilities.
- The claim that the 100-pip grid necessarily dominates operationally before execution is tested.

## Defects found in the review code

- The null script used the first return to Q from the original crossing rather than the first return after P75, invalidating its C1 conditioning.
- It compared time-limited simulations with untimed gambler's-ruin probabilities.
- The strategy simulation granted three full days from P75 although the proposed rule measured three days from Q.
- A distance-squared diffusion scale was described as median first-passage time.

The conceptual criticism was incorporated. Its numerical outputs were not treated as validation and were replaced with corrected empirical work.
