from __future__ import annotations

import aggregate_wayne_staged_sequence as aggregate

from dtr_lab.strategies.wayne_direction.cluster_stats import (
    cluster_permutation_p_value,
)


def _clustered_permutation(
    data,
    *,
    treatment_column,
    outcome_column,
    observed_effect,
    seed,
):
    return cluster_permutation_p_value(
        data,
        treatment_column=treatment_column,
        outcome_column=outcome_column,
        observed_effect=observed_effect,
        seed=seed,
        samples=aggregate.PERMUTATION_SAMPLES,
    )


if __name__ == "__main__":
    aggregate._permutation_p_value = _clustered_permutation
    aggregate.main()
