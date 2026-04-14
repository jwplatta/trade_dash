"""Tests for the options snapshot loader."""
from __future__ import annotations

from datetime import date

import pytest

from trade_dash.data.options import find_latest_snapshots, list_expirations, load_options_snapshot


def test_list_expirations_returns_dates() -> None:
    exps = list_expirations("SPXW")
    assert len(exps) > 0
    assert all(isinstance(d, date) for d in exps)


def test_find_latest_snapshots_returns_paths() -> None:
    today = date.today()
    snapshots = find_latest_snapshots("SPXW", start_date=today, days_out=10)
    assert isinstance(snapshots, dict)
    for _, path in snapshots.items():
        assert path.exists(), f"Snapshot file missing: {path}"


def test_load_options_snapshot_columns() -> None:
    today = date.today()
    snapshots = find_latest_snapshots("SPXW", start_date=today, days_out=5)
    if not snapshots:
        pytest.skip("No SPXW snapshots available for today's window")
    path = next(iter(snapshots.values()))
    df = load_options_snapshot(path)
    required = ["contract_type", "strike", "open_interest", "gamma", "underlying_price"]
    for col in required:
        assert col in df.columns, f"Missing column: {col}"


def test_find_latest_snapshots_0dte_exclusion() -> None:
    today = date.today()
    with_0dte = find_latest_snapshots("SPXW", start_date=today, days_out=5, include_0dte=True)
    without_0dte = find_latest_snapshots("SPXW", start_date=today, days_out=5, include_0dte=False)
    assert len(without_0dte) <= len(with_0dte)
