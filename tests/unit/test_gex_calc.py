"""Tests for GEX calculation functions."""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from trade_dash.calc.gex import (
    find_call_wall,
    find_put_wall,
    find_zero_gamma_level,
    net_gex_by_strike,
)
from trade_dash.data.options import find_latest_snapshots, load_options_snapshot


@pytest.fixture()
def spxw_opts() -> pd.DataFrame:
    snapshots = find_latest_snapshots("SPXW", start_date=date(2026, 4, 14), days_out=5)
    if not snapshots:
        pytest.skip("No SPXW snapshots available")
    dfs = [load_options_snapshot(path) for path in snapshots.values()]
    return pd.concat(dfs, ignore_index=True)


def test_net_gex_by_strike_columns(spxw_opts: pd.DataFrame) -> None:
    spot = float(spxw_opts["underlying_price"].iloc[0])
    result = net_gex_by_strike(spxw_opts, spot=spot)
    assert "strike" in result.columns
    assert "net_gex" in result.columns
    assert len(result) > 0


def test_net_gex_by_strike_has_both_signs(spxw_opts: pd.DataFrame) -> None:
    spot = float(spxw_opts["underlying_price"].iloc[0])
    result = net_gex_by_strike(spxw_opts, spot=spot)
    assert result["net_gex"].max() > 0
    assert result["net_gex"].min() < 0


def test_find_call_wall_returns_positive_gex(spxw_opts: pd.DataFrame) -> None:
    spot = float(spxw_opts["underlying_price"].iloc[0])
    strike_gex = net_gex_by_strike(spxw_opts, spot=spot)
    strike, level = find_call_wall(strike_gex)
    assert level > 0
    assert strike > 0


def test_find_put_wall_returns_negative_gex(spxw_opts: pd.DataFrame) -> None:
    spot = float(spxw_opts["underlying_price"].iloc[0])
    strike_gex = net_gex_by_strike(spxw_opts, spot=spot)
    _, level = find_put_wall(strike_gex)
    assert level < 0


def test_find_zero_gamma_level_finds_crossing() -> None:
    prices = np.array([5000.0, 5100.0, 5200.0, 5300.0])
    gex = np.array([-100.0, -50.0, 50.0, 100.0])
    zgl = find_zero_gamma_level(prices, gex)
    assert zgl is not None
    assert 5100.0 < zgl < 5200.0


def test_find_zero_gamma_level_returns_none_when_no_crossing() -> None:
    prices = np.array([5000.0, 5100.0, 5200.0])
    gex = np.array([10.0, 20.0, 30.0])
    assert find_zero_gamma_level(prices, gex) is None
