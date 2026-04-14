"""Streamlit application for the trading dashboard."""

from __future__ import annotations

import streamlit as st

from trade_dash.dashboard import pnl_timeseries, portfolio_metrics, sample_positions


def render_dashboard() -> None:
    """Render the main Streamlit dashboard."""
    st.set_page_config(
        page_title="trade_dash",
        page_icon=":chart_with_upwards_trend:",
        layout="wide",
    )

    positions = sample_positions()
    metrics = portfolio_metrics(positions)
    history = pnl_timeseries()

    st.title("trade_dash")
    st.caption("Streamlit trading dashboard scaffold with sample portfolio data.")

    metric_columns = st.columns(len(metrics))
    for column, metric in zip(metric_columns, metrics, strict=True):
        column.metric(metric.label, metric.value, metric.delta)

    left, right = st.columns((1.5, 1))

    with left:
        st.subheader("Portfolio P&L")
        st.line_chart(history, x="day", y="net_pnl", use_container_width=True)

        st.subheader("Positions")
        st.dataframe(positions, use_container_width=True, hide_index=True)

    with right:
        st.subheader("Watchlist")
        st.markdown(
            "\n".join(
                [
                    "- `NVDA` momentum continues above the 20-day trend.",
                    "- `AAPL` earnings week implied move is elevated.",
                    "- `TSLA` volume expansion warrants a volatility check.",
                ]
            )
        )

        st.subheader("Notes")
        st.info(
            "Replace the sample data sources in `trade_dash.dashboard` with your market feeds, "
            "portfolio feeds, or both, then extend the layout with filters, charts, and account "
            "views."
        )


if __name__ == "__main__":
    render_dashboard()
