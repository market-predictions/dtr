# ruff: noqa: E402, I001

from . import engine as _engine
from .engine import StrategyConfig, load_zip, metrics
from .integrity import (
    IntegrityFunnel,
    build_session_table,
    prepare_market_arrays,
    resample_5m,
    run_backtest,
)

# Standard package and direct engine imports must resolve to the integrity-safe entry points.
# integrity.py captured the original implementations before these assignments. The patch must
# occur before optimize imports its engine references.
_engine.build_session_table = build_session_table
_engine.prepare_market_arrays = prepare_market_arrays
_engine.resample_5m = resample_5m
_engine.run_backtest = run_backtest

from .manifest import (
    ResearchManifest,
    file_sha256,
    load_manifest,
    resolve_dataset_path,
    verify_dataset,
)
from .optimize import candidate_grid, evaluate_configs

__all__ = [
    "IntegrityFunnel",
    "ResearchManifest",
    "StrategyConfig",
    "build_session_table",
    "candidate_grid",
    "evaluate_configs",
    "file_sha256",
    "load_manifest",
    "load_zip",
    "metrics",
    "prepare_market_arrays",
    "resample_5m",
    "resolve_dataset_path",
    "run_backtest",
    "verify_dataset",
]
