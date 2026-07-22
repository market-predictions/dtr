from __future__ import annotations

import importlib


def test_package_import_does_not_mutate_engine_symbols() -> None:
    engine = importlib.import_module("dtr_lab.research.engine")
    original_run_backtest = engine.run_backtest
    original_resample = engine.resample_5m
    original_build_sessions = engine.build_session_table
    original_prepare = engine.prepare_market_arrays

    research = importlib.import_module("dtr_lab.research")

    assert engine.run_backtest is original_run_backtest
    assert engine.resample_5m is original_resample
    assert engine.build_session_table is original_build_sessions
    assert engine.prepare_market_arrays is original_prepare
    assert research.run_backtest is not engine.run_backtest
    assert research.resample_5m is not engine.resample_5m
    assert research.build_session_table is not engine.build_session_table


def test_optimizer_uses_explicit_integrity_entry_points() -> None:
    optimize = importlib.import_module("dtr_lab.research.optimize")
    integrity = importlib.import_module("dtr_lab.research.integrity")

    assert optimize.run_backtest is integrity.run_backtest
    assert optimize.prepare_market_arrays is integrity.prepare_market_arrays


def test_canonical_gap_policy_defaults_to_causal_liquidation() -> None:
    import inspect

    integrity = importlib.import_module("dtr_lab.research.integrity")
    optimize = importlib.import_module("dtr_lab.research.optimize")

    assert inspect.signature(integrity.run_backtest).parameters["gap_policy"].default == "liquidate_unsafe"
    assert inspect.signature(optimize.evaluate_configs).parameters["gap_policy"].default == "liquidate_unsafe"
