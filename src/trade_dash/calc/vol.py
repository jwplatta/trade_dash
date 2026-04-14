"""Volatility calculation functions."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.stats import pearsonr


def realized_vol(prices: pd.Series, window: int, ann_factor: int = 252) -> pd.Series:
    """Annualized realized volatility from log returns.

    Formula: 100 * sqrt(ann_factor / window * rolling_sum(log_return²))
    Matches docs/IV_RV_Comparison.ipynb notebook.
    """
    ratio: pd.Series = prices / prices.shift(1)
    log_returns: pd.Series = ratio.apply(np.log)
    squared: pd.Series = log_returns**2
    rolling_sum: pd.Series = squared.rolling(window=window).sum()
    return pd.Series(
        100.0 * np.sqrt(ann_factor / window * rolling_sum),
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
