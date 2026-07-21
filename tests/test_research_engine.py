import pandas as pd

from dtr_lab.research.engine import StrategyConfig, metrics


def test_metrics_basic():
    frame = pd.DataFrame(
        {
            "pnl_r": [1.0, -1.0, 2.0],
            "holding_minutes": [5, 10, 15],
            "mfe_r": [1, 1, 2],
            "mae_r": [0.2, 1, 0.3],
        }
    )
    out = metrics(frame)
    assert out["trades"] == 3
    assert abs(out["net_r"] - 2.0) < 1e-9
    assert out["max_drawdown_r"] == 1.0


def test_config_is_immutable():
    cfg = StrategyConfig()
    assert cfg.pivot_len == 1
