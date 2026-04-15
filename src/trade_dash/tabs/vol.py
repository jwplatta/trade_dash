"""Vol tab: IV vs realized vol analysis."""

from __future__ import annotations

import contextlib
from pathlib import Path

import pandas as pd
import streamlit as st

from trade_dash.calc.vol import iv_rv_spread, realized_vol, vix_spx_correlation
from trade_dash.charts.vix_term import build_vix_term_chart
from trade_dash.charts.vol_spread import build_iv_rv_chart
from trade_dash.data.candles import list_available_dates, load_candles


def render_vol_tab(candle_dir: Path) -> None:
    st.subheader("Volatility")

    col1, col2 = st.columns(2)
    with col1:
        window_choice = st.radio("Window", ["9D", "30D"], horizontal=True, key="vol_window")
    with col2:
        freq = (
            st.selectbox("Frequency", ["day", "1min", "5min", "30min"], index=0, key="vol_freq")
            or "day"
        )

    window = 9 if window_choice == "9D" else 30
    iv_symbol = "VIX9D" if window_choice == "9D" else "VIX"

    try:
        start_avail, end_avail = list_available_dates("SPX", str(freq), data_dir=candle_dir)
    except FileNotFoundError:
        st.error("SPX data not available.")
        return

    start_sel = st.date_input("Start", value=start_avail.date(), key="vol_start")
    end_sel = st.date_input("End", value=end_avail.date(), key="vol_end")

    spx = load_candles("SPX", str(freq), start=start_sel, end=end_sel, data_dir=candle_dir)

    try:
        iv_candles = load_candles(
            iv_symbol, str(freq), start=start_sel, end=end_sel, data_dir=candle_dir
        )
    except FileNotFoundError:
        st.error(f"{iv_symbol} data not available for frequency {freq}.")
        return

    rv = realized_vol(spx["close"], window=window)
    merged = pd.merge(
        spx[["datetime"]].assign(rv=rv.values),
        iv_candles[["datetime", "close"]].rename(columns={"close": "iv"}),
        on="datetime",
        how="inner",
    ).dropna()

    if merged.empty:
        st.warning("No overlapping data for selected range.")
        return

    spread = iv_rv_spread(merged["iv"], merged["rv"])

    try:
        vix_full = load_candles("VIX", str(freq), start=start_sel, end=end_sel, data_dir=candle_dir)
        corr = vix_spx_correlation(spx, vix_full)
        st.metric(f"VIX-SPX Correlation ({freq})", f"{corr:.3f}")
    except FileNotFoundError:
        st.info(f"VIX data not available for frequency {freq}.")

    fig = build_iv_rv_chart(
        iv=merged["iv"],
        rv=merged["rv"],
        spread=spread,
        datetimes=merged["datetime"],
        window_label=str(window_choice),
    )
    st.plotly_chart(fig, use_container_width=True)

    try:
        vix = load_candles("VIX", str(freq), start=start_sel, end=end_sel, data_dir=candle_dir)
        vix9d = load_candles("VIX9D", str(freq), start=start_sel, end=end_sel, data_dir=candle_dir)
        vix1d: pd.DataFrame | None = None
        if str(freq) != "day":
            with contextlib.suppress(FileNotFoundError):
                vix1d = load_candles(
                    "VIX1D", str(freq), start=start_sel, end=end_sel, data_dir=candle_dir
                )
        st.plotly_chart(build_vix_term_chart(vix, vix9d, vix1d), use_container_width=True)
    except FileNotFoundError as e:
        st.info(f"VIX term structure incomplete: {e}")
