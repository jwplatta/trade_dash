"""GEX aggregate chart: strike bars + price-grid line + spot + ZGL."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from trade_dash.calc.gex import find_zero_gamma_level


def build_gex_aggregate_chart(
    strike_gex: pd.DataFrame,
    price_gex: pd.DataFrame,
    spot: float,
    title: str = "GEX Aggregate",
) -> go.Figure:
    """Mixed bar (net GEX by strike) + line (net GEX by price) + spot + ZGL markers.

    Args:
        strike_gex: DataFrame with columns [strike, net_gex]
        price_gex: DataFrame with columns [price, net_gex]
        spot: Current underlying price
        title: Chart title
    """
    zgl = find_zero_gamma_level(
        prices=price_gex["price"].to_numpy(dtype=float),
        gex=price_gex["net_gex"].to_numpy(dtype=float),
    )

    colors: list[str] = ["green" if g >= 0 else "red" for g in strike_gex["net_gex"]]

    # Scale the price-grid line to match the strike bar y-axis range
    max_bar = float(np.abs(strike_gex["net_gex"]).max()) or 1.0
    max_line = float(np.abs(price_gex["net_gex"]).max()) or 1.0
    scale = max_bar / max_line

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=strike_gex["strike"],
            y=strike_gex["net_gex"],
            name="Net GEX by Strike",
            marker_color=colors,
            opacity=0.7,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=price_gex["price"],
            y=price_gex["net_gex"] * scale,
            name="Net GEX by Price (scaled)",
            line={"color": "yellow", "width": 2},
        )
    )
    fig.add_hline(y=0, line_dash="solid", line_color="white", line_width=0.5)
    fig.add_vline(
        x=spot,
        line_dash="dash",
        line_color="white",
        annotation_text=f"Spot {spot:.0f}",
        annotation_position="top right",
    )
    if zgl is not None:
        fig.add_vline(
            x=zgl,
            line_dash="dot",
            line_color="yellow",
            annotation_text=f"ZGL {zgl:.0f}",
            annotation_position="top left",
        )
    fig.update_layout(
        title=title,
        xaxis_title="Strike / Price",
        xaxis={"dtick": 25},
        yaxis_title="Net GEX",
        template="plotly_dark",
        legend={"orientation": "h", "y": 1.02},
        margin={"l": 40, "r": 20, "t": 40, "b": 40},
        bargap=0.1,
    )
    return fig
