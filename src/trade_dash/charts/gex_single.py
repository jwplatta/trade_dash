"""GEX single-expiry chart: separate call and put walls."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def build_gex_single_expiry_chart(
    opts: pd.DataFrame,
    spot: float,
    strike_range: float = 300.0,
    title: str = "GEX Single Expiry",
) -> go.Figure:
    """Grouped bar chart: call GEX and put GEX (negated) separately by strike."""
    df = opts.copy()
    df = df.dropna(subset=["gamma", "open_interest", "strike"])
    df = df[pd.to_numeric(df["open_interest"], errors="coerce") > 0]

    df["gex"] = (
        pd.to_numeric(df["gamma"], errors="coerce")
        * pd.to_numeric(df["open_interest"], errors="coerce")
        * (spot**2)
    )
    df["K"] = pd.to_numeric(df["strike"], errors="coerce")
    df = df.dropna(subset=["gex", "K"])
    mask = (df["K"] >= spot - strike_range) & (df["K"] <= spot + strike_range)
    df = df[mask]

    calls = df[df["contract_type"].str.upper() == "CALL"].groupby("K")["gex"].sum()
    puts = df[df["contract_type"].str.upper() == "PUT"].groupby("K")["gex"].sum()

    all_strikes = sorted(set(calls.index) | set(puts.index))
    call_vals = [float(calls.get(k, 0.0)) for k in all_strikes]
    put_vals = [-float(puts.get(k, 0.0)) for k in all_strikes]  # negate for display

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=all_strikes, y=call_vals, name="Call GEX", marker_color="green", opacity=0.7,
    ))
    fig.add_trace(go.Bar(
        x=all_strikes, y=put_vals, name="Put GEX (negated)", marker_color="red", opacity=0.7,
    ))
    fig.add_vline(x=spot, line_dash="dash", line_color="white",
                  annotation_text=f"Spot {spot:.0f}")
    fig.add_hline(y=0, line_color="white", line_width=0.5)
    fig.update_layout(
        title=title,
        xaxis_title="Strike",
        yaxis_title="GEX",
        barmode="group",
        template="plotly_dark",
        legend={"orientation": "h", "y": 1.02},
        margin={"l": 40, "r": 20, "t": 40, "b": 40},
    )
    return fig
