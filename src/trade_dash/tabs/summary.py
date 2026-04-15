"""Summary tab: instant read of market conditions."""

from __future__ import annotations

import math
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from trade_dash.calc.gex import net_gex_by_strike
from trade_dash.calc.ma import validate_windows
from trade_dash.calc.vol import expected_move, realized_vol
from trade_dash.charts.price import build_sma_price_chart
from trade_dash.data.candles import load_candles
from trade_dash.data.options import find_latest_snapshots, load_options_snapshot


def render_summary_tab(candle_dir: Path, options_dir: Path) -> None:
    st.subheader("Summary")

    col1, col2 = st.columns(2)
    with col1:
        fast_window = int(st.number_input("Fast MA window", min_value=1, value=10, key="sum_fast"))
        slow_window = int(st.number_input("Slow MA window", min_value=2, value=50, key="sum_slow"))
    with col2:
        days_out = int(
            st.slider("GEX days out", min_value=1, max_value=30, value=10, key="sum_days")
        )

    try:
        validate_windows(fast_window, slow_window)
    except ValueError as e:
        st.error(str(e))
        return

    spx = load_candles("SPX", "day", data_dir=candle_dir)
    vix = load_candles("VIX", "day", data_dir=candle_dir)
    try:
        vix9d = load_candles("VIX9D", "day", data_dir=candle_dir)
    except FileNotFoundError:
        vix9d = None

    spot = float(spx["close"].iloc[-1])

    rv30 = realized_vol(spx["close"], window=30).dropna()
    rv9 = realized_vol(spx["close"], window=9).dropna()
    vix_close = float(vix["close"].iloc[-1])
    vix9d_close = float(vix9d["close"].iloc[-1]) if vix9d is not None else float("nan")

    spread_30 = vix_close - float(rv30.iloc[-1]) if not rv30.empty else float("nan")
    spread_9 = (
        vix9d_close - float(rv9.iloc[-1]) if (not rv9.empty and vix9d is not None) else float("nan")
    )
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("IV−RV (30D)", f"{spread_30:.2f}" if not math.isnan(spread_30) else "N/A")
    col2.metric("IV−RV (9D)", f"{spread_9:.2f}" if not math.isnan(spread_9) else "N/A")
    if not math.isnan(vix9d_close):
        lower, upper = expected_move(spot=spot, vix9d_close=vix9d_close)
        col3.metric("Expected Move ↑", f"{upper:.1f}")
        col4.metric("Expected Move ↓", f"{lower:.1f}")
    else:
        col3.metric("Expected Move ↑", "N/A")
        col4.metric("Expected Move ↓", "N/A")

    today = date.today()
    snapshots = find_latest_snapshots(
        "SPXW", start_date=today, days_out=days_out, data_dir=options_dir
    )
    if snapshots:
        all_opts = pd.concat(
            [load_options_snapshot(p) for p in snapshots.values()], ignore_index=True
        )
        strike_gex = net_gex_by_strike(all_opts, spot=spot)
        pos = strike_gex[strike_gex["net_gex"] > 0]
        neg = strike_gex[strike_gex["net_gex"] < 0]
        call_strike = (
            float(pos.loc[pos["net_gex"].idxmax(), "strike"]) if not pos.empty else float("nan")
        )
        call_level = float(pos["net_gex"].max()) if not pos.empty else float("nan")
        put_strike = (
            float(neg.loc[neg["net_gex"].idxmin(), "strike"]) if not neg.empty else float("nan")
        )
        put_level = float(neg["net_gex"].min()) if not neg.empty else float("nan")

        col1, col2 = st.columns(2)
        col1.metric("Call Wall Strike", f"{call_strike:.0f}", f"GEX: {call_level:,.0f}")
        col2.metric("Put Wall Strike", f"{put_strike:.0f}", f"GEX: {put_level:,.0f}")

        st.subheader("Key Strikes")
        top_calls = strike_gex.nlargest(3, "net_gex").assign(type="Call")
        top_puts = strike_gex.nsmallest(3, "net_gex").assign(type="Put")
        key_table = pd.concat([top_calls, top_puts]).rename(
            columns={"strike": "Strike", "net_gex": "GEX Level", "type": "Type"}
        )
        st.dataframe(
            key_table[["Type", "Strike", "GEX Level"]].reset_index(drop=True),
            use_container_width=True,
        )

    st.subheader("SPX Price")
    fig = build_sma_price_chart(spx.tail(60), fast_window, slow_window, title="SPX (Last 60 Days)")
    st.plotly_chart(fig, use_container_width=True)
