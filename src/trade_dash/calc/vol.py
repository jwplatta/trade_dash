"""Volatility calculation functions."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.stats import pearsonr


def realized_vol(prices: pd.Series, window: int, periods_per_year: int = 252) -> pd.Series:
    """Horizon-matched annualized realized volatility from log returns.

    Formula: 100 * sqrt((periods_per_year / window) * rolling_sum(log_return²))

    This matches the VIX construction: annualized variance is the sum of squared
    returns over the horizon scaled by (A / H_bars), where A is periods per year
    and H_bars is the window length. Use window=trading days in horizon and
    periods_per_year=252 for daily data; scale both proportionally for intraday.
    """
    log_returns: pd.Series = np.log(prices / prices.shift(1))
    rolling_sum: pd.Series = (log_returns ** 2).rolling(window=window).sum()
    return pd.Series(
        100.0 * np.sqrt((periods_per_year / window) * rolling_sum),
        index=prices.index,
    )


def iv_rv_spread(iv: pd.Series, rv: pd.Series) -> pd.Series:
    """Elementwise IV minus RV."""
    diff: pd.Series = iv - rv
    return diff


def vix_spx_correlation(spx: pd.DataFrame, vix: pd.DataFrame) -> float:
    """Pearson correlation between aligned SPX and VIX close series."""
    merged = pd.merge(
        spx[["datetime", "close"]].rename(columns={"close": "spx"}),
        vix[["datetime", "close"]].rename(columns={"close": "vix"}),
        on="datetime",
        how="inner",
    ).dropna()
    if len(merged) < 2:
        return float("nan")
    return float(pearsonr(merged["spx"].to_numpy(), merged["vix"].to_numpy()).statistic)


def expected_move(spot: float, vix9d_close: float) -> tuple[float, float]:
    """One-day expected move: ± spot * (VIX9D / 100) * sqrt(1/252).

    Returns (lower, upper).
    """
    move = spot * (vix9d_close / 100.0) * math.sqrt(1.0 / 252.0)
    return spot - move, spot + move
