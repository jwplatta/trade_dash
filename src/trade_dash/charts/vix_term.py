"""VIX term structure chart: VIX + VIX9D + optional VIX1D."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def build_vix_term_chart(
    vix: pd.DataFrame,
    vix9d: pd.DataFrame,
    vix1d: pd.DataFrame | None = None,
    title: str = "VIX Term Structure",
) -> go.Figure:
    """Line chart: VIX vs VIX9D (vs VIX1D if provided) for contango check."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=vix["datetime"],
            y=vix["close"],
            name="VIX (30D)",
            line={"color": "red", "width": 2},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=vix9d["datetime"],
            y=vix9d["close"],
            name="VIX9D",
            line={"color": "orange", "width": 2},
        )
    )
    if vix1d is not None:
        fig.add_trace(
            go.Scatter(
                x=vix1d["datetime"],
                y=vix1d["close"],
                name="VIX1D",
                line={"color": "yellow", "width": 2},
            )
        )
    fig.update_layout(
        title=title,
        xaxis_title="Date/Time",
        yaxis_title="VIX Level",
        template="plotly_dark",
        legend={"orientation": "h", "y": 1.02},
        margin={"l": 40, "r": 20, "t": 40, "b": 40},
    )
    return fig
