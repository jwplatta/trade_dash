"""Gamma Map tab: options positioning and key levels."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from trade_dash.calc.gex import (
    net_gex_by_price,
    net_gex_by_strike,
)
from trade_dash.charts.gex_aggregate import build_gex_aggregate_chart
from trade_dash.charts.gex_single import build_gex_single_expiry_chart
from trade_dash.charts.vol_skew import build_vol_skew_chart
from trade_dash.data.options import find_latest_snapshots, list_expirations, load_options_snapshot


def render_gamma_map_tab(options_dir: Path, candle_dir: Path) -> None:
    st.subheader("Gamma Map")

    @st.fragment(run_every="30s")
    def _render() -> None:
        col_ctrl, col_chart = st.columns([1, 3])

        with col_ctrl:
            days_out = int(
                st.slider("Days out", min_value=1, max_value=30, value=10, key="gm_days")
            )
            include_0dte = st.toggle("Include 0DTE", value=True, key="gm_0dte")
            symbol = str(
                st.selectbox("Symbol", ["SPXW", "SPX", "QQQ", "DIA"], index=0, key="gm_symbol")
            )
            range_pct = float(
                st.slider(
                    "Strike range (% of spot)",
                    min_value=1,
                    max_value=25,
                    value=5,
                    step=1,
                    key="gm_range_pct",
                )
            )

        today = date.today()
        snapshots = find_latest_snapshots(
            symbol,
            start_date=today,
            days_out=days_out,
            include_0dte=include_0dte,
            data_dir=options_dir,
        )

        if not snapshots:
            with col_chart:
                st.warning(f"No {symbol} options snapshots found for next {days_out} days.")
            return

        all_opts = pd.concat(
            [load_options_snapshot(p) for p in snapshots.values()], ignore_index=True
        )

        spot_series = pd.to_numeric(all_opts["underlying_price"], errors="coerce").dropna()
        if spot_series.empty:
            with col_chart:
                st.error("No valid underlying_price in options data.")
            return
        spot = float(spot_series.iloc[0])
        strike_range = round(spot * range_pct / 100)

        strike_gex = net_gex_by_strike(all_opts, spot=spot, strike_range=strike_range)
        with st.spinner("Computing GEX by price grid..."):
            price_gex = net_gex_by_price(all_opts, spot=spot, price_range=strike_range)

        fig_agg = build_gex_aggregate_chart(
            strike_gex, price_gex, spot, title=f"{symbol} GEX Aggregate ({days_out}d)"
        )

        # Single expiry section
        available_exps = list_expirations(symbol, data_dir=options_dir)
        # Descending order; default to most recent
        available_exps_desc = sorted(available_exps, reverse=True)

        with col_ctrl:
            st.divider()
            selected_exp_str: str | None = None
            if available_exps_desc:
                selected_exp_str = str(
                    st.selectbox(
                        "Single expiry",
                        options=[d.isoformat() for d in available_exps_desc],
                        index=0,
                        key="gm_expiry",
                    )
                )

        with col_chart:
            st.plotly_chart(fig_agg, use_container_width=True)

            if selected_exp_str:
                selected_exp = date.fromisoformat(selected_exp_str)
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
                        single_opts,
                        spot=spot,
                        strike_range=strike_range,
                        title=f"{symbol} GEX {selected_exp}",
                    )
                    st.subheader("GEX Single Expiry")
                    st.plotly_chart(fig_single, use_container_width=True)

                    fig_skew = build_vol_skew_chart(
                        single_opts,
                        spot=spot,
                        strike_range=strike_range,
                        title=f"{symbol} Vol Skew {selected_exp}",
                    )
                    st.subheader("Volatility Skew")
                    st.plotly_chart(fig_skew, use_container_width=True)

    _render()
