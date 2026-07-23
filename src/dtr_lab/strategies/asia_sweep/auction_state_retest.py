from __future__ import annotations

import pandas as pd

from .auction_state import _forward_metrics, _validate_minutes


def attach_retest_forward_metrics(
    ledger: pd.DataFrame,
    one_minute: pd.DataFrame,
) -> pd.DataFrame:
    """Measure held-retest continuation from its own causal detection timestamp."""

    required = {
        "retest_resume",
        "retest_detection_timestamp",
        "window_end",
        "hypothesis_direction",
        "reference_high",
        "reference_low",
    }
    missing = required.difference(ledger.columns)
    if missing:
        raise ValueError(f"ledger missing retest fields: {sorted(missing)}")
    minutes = _validate_minutes(one_minute).set_index("timestamp")
    output = ledger.copy(deep=True)
    metric_rows: list[dict[str, object]] = []
    for _, row in output.iterrows():
        detection_time = pd.Timestamp(row["state_detection_timestamp"])
        state = "UNRESOLVED"
        if bool(row["retest_resume"]) and pd.notna(row["retest_detection_timestamp"]):
            detection_time = pd.Timestamp(row["retest_detection_timestamp"])
            state = "ACCEPTANCE"
        metrics = _forward_metrics(
            minutes,
            detection_time,
            pd.Timestamp(row["window_end"]),
            int(row["hypothesis_direction"]),
            float(row["reference_high"]),
            float(row["reference_low"]),
            state,
        )
        metric_rows.append({f"retest_{key}": value for key, value in metrics.items()})
    metrics_frame = pd.DataFrame(metric_rows, index=output.index)
    return pd.concat([output, metrics_frame], axis=1)
