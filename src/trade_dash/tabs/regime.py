"""Regime tab: direction and stability analysis."""

from __future__ import annotations

import math
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

from trade_dash.calc.ma import validate_windows
from trade_dash.charts.price import build_sma_price_chart
from trade_dash.charts.volume import build_sma_volume_chart
from trade_dash.config import SCHWAB_CANDLE_DIR
from trade_dash.data.candles import list_available_dates, load_candles

_INTRADAY_FREQS = {"1min", "5min", "30min"}
_BARS_PER_DAY = {"1min": 390, "5min": 78, "30min": 13, "day": 1}


def _x_range(df: pd.DataFrame, start_sel: date, end_sel: date, freq: str) -> list:
    """Return the xaxis range to trim off the warmup period."""
    if freq in _INTRADAY_FREQS:
        start_ts = pd.Timestamp(start_sel, tz="UTC")
        mask = df["datetime"] >= start_ts
        display_start = int(mask.idxmax()) if mask.any() else 0
        return [display_start - 0.5, len(df) - 0.5]
    else:
        return [
            pd.Timestamp(start_sel, tz="UTC"),
            pd.Timestamp(end_sel, tz="UTC") + pd.Timedelta(days=1),
        ]


def render_regime_tab(candle_dir: Path) -> None:
    st.subheader("Regime")

    col_ctrl, col_chart = st.columns([1, 3])

    with col_ctrl:
        freq = (
            st.selectbox("Frequency", ["1min", "5min", "30min", "day"], index=1, key="reg_freq")
            or "5min"
        )
        fast_window = int(st.number_input("Fast MA", min_value=1, value=9, key="reg_fast"))
        slow_window = int(st.number_input("Slow MA", min_value=2, value=30, key="reg_slow"))

        try:
            validate_windows(fast_window, slow_window)
        except ValueError as e:
            st.error(str(e))
            return

        try:
            start_avail, end_avail = list_available_dates("SPX", str(freq), data_dir=candle_dir)
        except FileNotFoundError:
            st.error(f"No SPX data for frequency: {freq}")
            return

        today = date.today()
        default_start = max(date(today.year, today.month, 1), start_avail.date())

        start_sel = st.date_input("Start", value=default_start, key="reg_start")
        end_sel = st.date_input("End", value=end_avail.date(), key="reg_end")

    # Load with warmup so MAs are valid at the start of the display range.
    # Scale warmup by frequency: intraday bars are small fractions of a day,
    # so slow_window bars may only need a few calendar days, not slow_window*3.
    bars_per_day = _BARS_PER_DAY.get(str(freq), 1)
    trading_days_needed = max(1, math.ceil(slow_window / bars_per_day))
    warmup_days = trading_days_needed * 2 + 4  # 2× buffer + weekend/holiday padding
    warmup_start = date.fromisoformat(str(start_sel)) - timedelta(days=warmup_days)

    spx = load_candles("SPX", str(freq), start=warmup_start, end=end_sel, data_dir=candle_dir)

    if spx.empty:
        with col_chart:
            st.warning("No data for selected range.")
        return

    with col_chart:
        try:
            es = load_candles(
                "^ES", str(freq), start=warmup_start, end=end_sel, data_dir=SCHWAB_CANDLE_DIR
            )
            vol_fig = build_sma_volume_chart(es, title=f"ES Volume ({freq})", freq=str(freq))
            vol_fig.update_xaxes(range=_x_range(es, start_sel, end_sel, str(freq)))
            st.plotly_chart(vol_fig, use_container_width=True)
        except FileNotFoundError:
            st.info("ES volume data not available.")

        price_fig = build_sma_price_chart(
            spx, fast_window, slow_window, title=f"SPX ({freq})", freq=str(freq)
        )
        price_fig.update_xaxes(range=_x_range(spx, start_sel, end_sel, str(freq)))
        st.plotly_chart(price_fig, use_container_width=True)
