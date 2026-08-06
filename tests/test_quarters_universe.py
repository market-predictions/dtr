from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "aggregate_quarters_crosspair.py"
    spec = importlib.util.spec_from_file_location("quarters_universe_aggregate", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_positive_stable_requires_both_periods_and_positive_interval() -> None:
    module = _load_module()
    positive = {"point": 1.0}
    negative = {"point": -1.0}
    interval_positive = {"ci_low": 0.1}
    interval_crosses_zero = {"ci_low": -0.1}

    assert module._is_positive_stable(positive, positive, interval_positive)
    assert not module._is_positive_stable(positive, negative, interval_positive)
    assert not module._is_positive_stable(negative, positive, interval_positive)
    assert not module._is_positive_stable(positive, positive, interval_crosses_zero)


def test_confirmation_decision_cannot_rescue_demoted_theory() -> None:
    module = _load_module()
    assert module._confirmation_decision(0) == "CONFIRM_GLOBAL_DEMOTION_NO_PAIR_EXCEPTIONS"
    assert (
        module._confirmation_decision(1)
        == "GLOBAL_DEMOTION_STANDS_ISOLATED_PAIR_EXCEPTIONS_ONLY"
    )
    assert (
        module._confirmation_decision(2)
        == "GLOBAL_DEMOTION_STANDS_ISOLATED_PAIR_EXCEPTIONS_ONLY"
    )
    assert (
        module._confirmation_decision(3)
        == "GLOBAL_DEMOTION_STANDS_UNEXPECTED_BREADTH_REQUIRES_NEW_PREREGISTRATION"
    )
    assert (
        module._confirmation_decision(7)
        == "GLOBAL_DEMOTION_STANDS_UNEXPECTED_BREADTH_REQUIRES_NEW_PREREGISTRATION"
    )


def test_universe_contains_registered_ten_pair_panel() -> None:
    module = _load_module()
    assert module.EXPECTED_PAIRS == {
        "EURUSD",
        "GBPUSD",
        "USDCHF",
        "AUDUSD",
        "NZDUSD",
        "USDCAD",
        "USDJPY",
        "EURJPY",
        "GBPJPY",
        "EURGBP",
    }
    assert len(module.CONFIRMATION_PAIRS) == 7
