"""Volatility skew chart: implied vol by strike for calls and puts."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def build_vol_skew_chart(
    opts: pd.DataFrame,
    spot: float,
    strike_range: float = 300.0,
    title: str = "Volatility Skew",
) -> go.Figure:
    """Line chart: implied vol vs strike for calls and puts of a single expiry."""
    df = opts.copy()
    df["K"] = pd.to_numeric(df["strike"], errors="coerce")
    df["vol"] = pd.to_numeric(df["volatility"], errors="coerce")
    df["oi"] = pd.to_numeric(df["open_interest"], errors="coerce").fillna(0)
    df = df.dropna(subset=["K", "vol", "contract_type"])
    df = df[(df["K"] >= spot - strike_range) & (df["K"] <= spot + strike_range)]
    df = df[df["vol"] > 0]

    # OTM + first 10 ITM strikes for each side
    _itm_call_strikes = sorted(df.loc[df["contract_type"].str.upper() == "CALL", "K"].unique())
    _itm_call_strikes = [k for k in _itm_call_strikes if k < spot][-10:]
    call_min = _itm_call_strikes[0] if _itm_call_strikes else spot

    _itm_put_strikes = sorted(df.loc[df["contract_type"].str.upper() == "PUT", "K"].unique())
    _itm_put_strikes = [k for k in _itm_put_strikes if k > spot][:10]
    put_max = _itm_put_strikes[-1] if _itm_put_strikes else spot

    call_df = df[(df["contract_type"].str.upper() == "CALL") & (df["K"] >= call_min)]
    put_df  = df[(df["contract_type"].str.upper() == "PUT")  & (df["K"] <= put_max)]

    calls_vol = call_df.groupby("K")["vol"].mean().sort_index()
    puts_vol  = put_df.groupby("K")["vol"].mean().sort_index()

    calls_oi = call_df.groupby("K")["oi"].sum().reindex(calls_vol.index, fill_value=0)
    puts_oi  = put_df.groupby("K")["oi"].sum().reindex(puts_vol.index, fill_value=0)

    all_vols = pd.concat([calls_vol, puts_vol]).dropna()
    if all_vols.empty:
        return go.Figure()
    y_min = max(0, all_vols.min() * 0.95)
    y_max = all_vols.max() * 1.05

    fig = go.Figure()

    # OI bars on right axis
    fig.add_trace(go.Bar(
        x=calls_oi.index, y=calls_oi.values,
        name="Call OI",
        marker_color="green", opacity=0.3,
        yaxis="y2",
    ))
    fig.add_trace(go.Bar(
        x=puts_oi.index, y=puts_oi.values,
        name="Put OI",
        marker_color="red", opacity=0.3,
        yaxis="y2",
    ))

    # IV lines on left axis
    fig.add_trace(go.Scatter(
        x=calls_vol.index, y=calls_vol.values,
        name="Call IV",
        line={"color": "green", "width": 1.5},
        mode="lines+markers",
        marker={"size": 4},
    ))
    fig.add_trace(go.Scatter(
        x=puts_vol.index, y=puts_vol.values,
        name="Put IV",
        line={"color": "red", "width": 1.5},
        mode="lines+markers",
        marker={"size": 4},
    ))

    fig.add_vline(x=spot, line_dash="dash", line_color="white", annotation_text=f"Spot {spot:.0f}")
    fig.update_layout(
        title=title,
        xaxis_title="Strike",
        xaxis={"dtick": 25},
        yaxis={"title": "Implied Volatility (%)", "range": [y_min, y_max]},
        yaxis2={"title": "Open Interest", "overlaying": "y", "side": "right", "showgrid": False},
        barmode="overlay",
        template="plotly_dark",
        legend={"orientation": "h", "y": 1.02},
        margin={"l": 40, "r": 60, "t": 40, "b": 40},
    )
    return fig
