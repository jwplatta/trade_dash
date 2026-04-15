"""Regime tab: direction and stability analysis."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from trade_dash.calc.ma import validate_windows
from trade_dash.calc.vol import vix_spx_correlation
from trade_dash.charts.price import build_sma_price_chart
from trade_dash.charts.volume import build_sma_volume_chart
from trade_dash.data.candles import list_available_dates, load_candles


def render_regime_tab(candle_dir: Path) -> None:
    st.subheader("Regime")

    col1, col2, col3 = st.columns(3)
    with col1:
        freq = st.selectbox("Frequency", ["1min", "5min", "30min", "day"], index=1, key="reg_freq")
    with col2:
        fast_window = int(st.number_input("Fast MA", min_value=1, value=9, key="reg_fast"))
        slow_window = int(st.number_input("Slow MA", min_value=2, value=21, key="reg_slow"))

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

    with col3:
        start_sel = st.date_input("Start", value=start_avail.date(), key="reg_start")
        end_sel = st.date_input("End", value=end_avail.date(), key="reg_end")

    spx = load_candles("SPX", str(freq), start=start_sel, end=end_sel, data_dir=candle_dir)

    if spx.empty:
        st.warning("No data for selected range.")
        return

    try:
        vix = load_candles("VIX", str(freq), start=start_sel, end=end_sel, data_dir=candle_dir)
        corr = vix_spx_correlation(spx, vix)
        st.metric("SPX-VIX Correlation", f"{corr:.3f}")
    except FileNotFoundError:
        st.info("VIX data not available for this frequency.")

    try:
        es = load_candles("ES", str(freq), start=start_sel, end=end_sel, data_dir=candle_dir)
        st.plotly_chart(
            build_sma_volume_chart(es, fast_window, slow_window),
            use_container_width=True,
        )
    except FileNotFoundError:
        st.info("ES volume data not available.")

    st.plotly_chart(
        build_sma_price_chart(spx, fast_window, slow_window, title=f"SPX ({freq})"),
        use_container_width=True,
    )
