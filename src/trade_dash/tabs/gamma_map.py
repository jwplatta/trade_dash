"""Gamma Map tab: options positioning and key levels."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from trade_dash.calc.flow import compute_intraday_flow
from trade_dash.calc.gex import (
    net_gex_by_price,
    net_gex_by_strike,
)
from trade_dash.calc.spread import compute_intraday_spread
from trade_dash.charts.flow_heatmap import build_flow_heatmap_chart
from trade_dash.charts.gex_aggregate import build_gex_aggregate_chart
from trade_dash.charts.gex_heatmap import build_gex_heatmap_chart, compute_gex_history
from trade_dash.charts.gex_single import build_gex_single_expiry_chart
from trade_dash.charts.spread_heatmap import build_spread_heatmap_chart
from trade_dash.charts.vol_skew import build_vol_skew_chart
from trade_dash.data.options import (
    find_all_snapshots_for_expiry,
    find_latest_snapshots,
    list_expirations,
    load_options_snapshot,
)


def render_gamma_map_tab(options_dir: Path, candle_dir: Path) -> None:
    st.subheader("Gamma Map")

    @st.fragment(run_every="5m")
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

        # Single expiry controls (shared across both sub-tabs)
        available_exps = list_expirations(symbol, data_dir=options_dir)
        available_exps_desc = sorted(available_exps, reverse=True)

        with col_ctrl:
            st.divider()
            selected_exp_str: str | None = None
            if available_exps_desc:
                exp_options = [d.isoformat() for d in available_exps_desc]
                today_iso = today.isoformat()
                default_idx = next((i for i, s in enumerate(exp_options) if s == today_iso), 0)
                selected_exp_str = str(
                    st.selectbox(
                        "Single expiry",
                        options=exp_options,
                        index=default_idx,
                        key="gm_expiry",
                    )
                )

        with col_chart:
            tab_gex, tab_chains, tab_history, tab_intraday = st.tabs(
                ["GEX", "Chains", "Chain GEX History", "Intraday"]
            )

            with tab_gex:
                st.plotly_chart(fig_agg, use_container_width=True)

            with tab_chains:
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

            with tab_history:
                if selected_exp_str:
                    selected_exp = date.fromisoformat(selected_exp_str)

                    # Cache key: recompute only when symbol/expiry/spot/range changes
                    hist_key = (symbol, selected_exp_str, round(spot), strike_range)
                    if st.session_state.get("_gex_hist_key") != hist_key:
                        with st.spinner("Computing GEX history..."):
                            all_expiry_snapshots = find_all_snapshots_for_expiry(
                                symbol, expiry=selected_exp, data_dir=options_dir
                            )
                            top_strikes, timestamps, matrix = compute_gex_history(
                                all_expiry_snapshots, spot=spot, strike_range=strike_range
                            )
                        st.session_state["_gex_hist_key"] = hist_key
                        st.session_state["_gex_hist_top_strikes"] = top_strikes
                        st.session_state["_gex_hist_timestamps"] = timestamps
                        st.session_state["_gex_hist_matrix"] = matrix
                    else:
                        top_strikes = st.session_state["_gex_hist_top_strikes"]
                        timestamps = st.session_state["_gex_hist_timestamps"]
                        matrix = st.session_state["_gex_hist_matrix"]

                    # Slider adjusts visible window — figure rebuilds instantly from stored data
                    x_range = None
                    if timestamps and len(timestamps) > 1:
                        ts_min, ts_max = timestamps[0], timestamps[-1]
                        sel_start, sel_end = st.slider(
                            "Time range",
                            min_value=ts_min,
                            max_value=ts_max,
                            value=(ts_min, ts_max),
                            format="MM/DD HH:mm",
                            key="gm_history_range",
                        )
                        x_range = (sel_start, sel_end)

                    fig_heatmap = build_gex_heatmap_chart(
                        top_strikes,
                        timestamps,
                        matrix,
                        spot=spot,
                        title=f"{symbol} GEX History {selected_exp}",
                        x_range=x_range,
                    )
                    st.plotly_chart(fig_heatmap, use_container_width=True)

            with tab_intraday:
                if selected_exp_str:
                    selected_exp = date.fromisoformat(selected_exp_str)

                    col_ct, col_date, col_wt = st.columns([3, 2, 1])
                    with col_ct:
                        ct_filter = str(
                            st.radio(
                                "Contract type",
                                options=["ALL", "CALL", "PUT"],
                                horizontal=True,
                                key="gm_intraday_ct",
                            )
                        )
                    with col_date:
                        intraday_date = st.date_input(
                            "Sample date",
                            value=date.today(),
                            key="gm_intraday_date",
                        )
                    with col_wt:
                        weight_by_delta = st.toggle(
                            "Weight by delta", value=True, key="gm_intraday_weight_delta"
                        )
                    bucket_minutes = int(
                        st.select_slider(
                            "Sample interval (minutes)",
                            options=[1, 5, 10, 15, 20, 25, 30],
                            value=5,
                            key="gm_intraday_bucket",
                        )
                    )

                    all_expiry_snapshots = find_all_snapshots_for_expiry(
                        symbol, expiry=selected_exp, data_dir=options_dir
                    )
                    flow_key = (
                        symbol,
                        selected_exp_str,
                        round(spot),
                        strike_range,
                        ct_filter,
                        bucket_minutes,
                        weight_by_delta,
                        intraday_date,
                        len(all_expiry_snapshots),
                    )
                    with st.spinner("Computing intraday flow..."):
                        if st.session_state.get("_flow_key") != flow_key:
                            flow_strikes, flow_timestamps, flow_matrix, flow_prices = (
                                compute_intraday_flow(
                                    all_expiry_snapshots,
                                    spot=spot,
                                    moneyness_pct=range_pct / 100,
                                    contract_filter=ct_filter,
                                    bucket_minutes=bucket_minutes,
                                    weight_by_delta=weight_by_delta,
                                    target_date=intraday_date,
                                )
                            )
                            st.session_state["_flow_key"] = flow_key
                            st.session_state["_flow_strikes"] = flow_strikes
                            st.session_state["_flow_timestamps"] = flow_timestamps
                            st.session_state["_flow_matrix"] = flow_matrix
                            st.session_state["_flow_prices"] = flow_prices
                        else:
                            flow_strikes = st.session_state["_flow_strikes"]
                            flow_timestamps = st.session_state["_flow_timestamps"]
                            flow_matrix = st.session_state["_flow_matrix"]
                            flow_prices = st.session_state["_flow_prices"]

                        fig_flow = build_flow_heatmap_chart(
                            flow_strikes,
                            flow_timestamps,
                            flow_matrix,
                            prices=flow_prices,
                            title=f"{symbol} Intraday Flow {selected_exp}",
                        )
                    st.plotly_chart(fig_flow, use_container_width=True)

                    st.divider()
                    col_sct, col_sdate, _ = st.columns([2, 2, 2])
                    with col_sct:
                        spread_ct = str(
                            st.radio(
                                "Contract type",
                                options=["CALL", "PUT"],
                                horizontal=True,
                                key="gm_spread_ct",
                            )
                        )
                    with col_sdate:
                        spread_date = st.date_input(
                            "Sample Date",
                            value=date.today(),
                            key="gm_spread_date",
                        )
                    spread_bucket_minutes = int(
                        st.select_slider(
                            "Sample interval (minutes)",
                            options=[1, 5, 10, 15, 20, 25, 30],
                            value=5,
                            key="gm_spread_bucket",
                        )
                    )

                    spread_key = (
                        symbol,
                        selected_exp_str,
                        round(spot),
                        strike_range,
                        spread_ct,
                        spread_bucket_minutes,
                        spread_date,
                        len(all_expiry_snapshots),
                    )
                    with st.spinner("Computing spread heatmap..."):
                        if st.session_state.get("_spread_key") != spread_key:
                            spread_strikes, spread_ts, spread_matrix, spread_prices = (
                                compute_intraday_spread(
                                    all_expiry_snapshots,
                                    spot=spot,
                                    moneyness_pct=range_pct / 100,
                                    contract_filter=spread_ct,
                                    bucket_minutes=spread_bucket_minutes,
                                    target_date=spread_date,
                                )
                            )
                            st.session_state["_spread_key"] = spread_key
                            st.session_state["_spread_strikes"] = spread_strikes
                            st.session_state["_spread_ts"] = spread_ts
                            st.session_state["_spread_matrix"] = spread_matrix
                            st.session_state["_spread_prices"] = spread_prices
                        else:
                            spread_strikes = st.session_state["_spread_strikes"]
                            spread_ts = st.session_state["_spread_ts"]
                            spread_matrix = st.session_state["_spread_matrix"]
                            spread_prices = st.session_state["_spread_prices"]

                        fig_spread = build_spread_heatmap_chart(
                            spread_strikes,
                            spread_ts,
                            spread_matrix,
                            prices=spread_prices,
                            title=f"{symbol} Bid-Ask Spread Z {selected_exp} ({spread_ct})",
                        )
                    st.plotly_chart(fig_spread, use_container_width=True)

    _render()
