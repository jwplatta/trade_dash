"""Gamma Map tab: options positioning and key levels."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from trade_dash.calc.gex import (
    find_call_wall,
    find_put_wall,
    find_zero_gamma_level,
    net_gex_by_price,
    net_gex_by_strike,
)
from trade_dash.charts.gex_aggregate import build_gex_aggregate_chart
from trade_dash.charts.gex_single import build_gex_single_expiry_chart
from trade_dash.data.candles import load_candles
from trade_dash.data.options import find_latest_snapshots, list_expirations, load_options_snapshot


def render_gamma_map_tab(options_dir: Path, candle_dir: Path) -> None:
    st.subheader("Gamma Map")

    col1, col2, col3 = st.columns(3)
    with col1:
        days_out = int(st.slider("Days out", min_value=1, max_value=30, value=10, key="gm_days"))
    with col2:
        include_0dte = st.checkbox("Include 0DTE", value=True, key="gm_0dte")
    with col3:
        symbol = str(
            st.selectbox("Symbol", ["SPXW", "SPX", "QQQ", "DIA"], index=0, key="gm_symbol")
        )

    try:
        spx_candles = load_candles("SPX", "day", data_dir=candle_dir)
        spot = float(spx_candles["close"].iloc[-1])
    except FileNotFoundError:
        st.error("SPX candle data not found.")
        return

    today = date.today()
    snapshots = find_latest_snapshots(
        symbol,
        start_date=today,
        days_out=days_out,
        include_0dte=include_0dte,
        data_dir=options_dir,
    )

    if not snapshots:
        st.warning(f"No {symbol} options snapshots found for next {days_out} days.")
        return

    all_opts = pd.concat([load_options_snapshot(p) for p in snapshots.values()], ignore_index=True)

    strike_gex = net_gex_by_strike(all_opts, spot=spot)
    with st.spinner("Computing GEX by price grid..."):
        price_gex = net_gex_by_price(all_opts, spot=spot)

    call_strike, call_level = find_call_wall(strike_gex)
    put_strike, put_level = find_put_wall(strike_gex)
    zgl = find_zero_gamma_level(
        prices=price_gex["price"].to_numpy(dtype=float),
        gex=price_gex["net_gex"].to_numpy(dtype=float),
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Call Wall", f"{call_strike:.0f}", f"{call_level:,.0f}")
    col2.metric("Put Wall", f"{put_strike:.0f}", f"{put_level:,.0f}")
    col3.metric("Zero Gamma Level", f"{zgl:.1f}" if zgl is not None else "N/A")

    fig_agg = build_gex_aggregate_chart(
        strike_gex, price_gex, spot, title=f"{symbol} GEX Aggregate ({days_out}d)"
    )
    st.plotly_chart(fig_agg, use_container_width=True)

    st.subheader("GEX Single Expiry")
    available_exps = list_expirations(symbol, data_dir=options_dir)
    if available_exps:
        selected_exp = date.fromisoformat(
            str(
                st.selectbox(
                    "Expiration",
                    options=[d.isoformat() for d in available_exps],
                    key="gm_expiry",
                )
            )
        )
        single_snapshots = find_latest_snapshots(
            symbol,
            start_date=selected_exp,
            days_out=0,
            include_0dte=True,
            data_dir=options_dir,
        )
        if single_snapshots:
            single_opts = load_options_snapshot(next(iter(single_snapshots.values())))
            fig_single = build_gex_single_expiry_chart(
                single_opts, spot=spot, title=f"{symbol} GEX {selected_exp}"
            )
            st.plotly_chart(fig_single, use_container_width=True)
