from __future__ import annotations

import json

import numpy as np

from dtr_lab.strategies.asia_sweep.runner_optimization_outputs import _json_safe


def test_json_safe_converts_nested_numpy_scalars() -> None:
    payload = _json_safe(
        {
            "gate": np.bool_(True),
            "count": np.int64(5),
            "metric": np.float64(0.125),
            "nested": [np.bool_(False)],
        }
    )
    encoded = json.dumps(payload)
    assert '"gate": true' in encoded
    assert payload == {
        "gate": True,
        "count": 5,
        "metric": 0.125,
        "nested": [False],
    }
