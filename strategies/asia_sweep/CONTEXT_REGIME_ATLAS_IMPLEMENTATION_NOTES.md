# Context and Regime Atlas — Implementation Notes

The implementation deliberately keeps the atlas separate from the frozen fingerprint model. It reconstructs the exact T5 eligibility population, appends only pre-event context, and evaluates coarse states without adding those fields to the validated model bundle.

The workflow fails at its final authorization step when fewer than two independent factor families pass. Such a workflow failure is a scientific stop result after evidence upload, not an orchestration failure.

The complete pair ledgers are retained because they are required for independent causal and arithmetic reconstruction. Raw BID/ASK source remains in private source artifacts and is not republished.
