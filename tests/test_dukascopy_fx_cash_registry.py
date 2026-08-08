from pathlib import Path

from dtr_lab.research_registry import CANONICAL_PAIRS, validate_registry


ROOT = Path(__file__).resolve().parents[1]


def test_dukascopy_fx_cash_registry_is_valid() -> None:
    assert validate_registry(ROOT) == []


def test_dukascopy_fx_cash_pair_universe_is_frozen() -> None:
    assert CANONICAL_PAIRS == {
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
