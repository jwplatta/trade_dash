"""SMA volume chart."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from trade_dash.calc.ma import sma, validate_windows


def build_sma_volume_chart(
    candles: pd.DataFrame,
    fast_window: int,
    slow_window: int,
) -> go.Figure:
    """Bar chart: volume + fast MA + slow MA of volume. Raises ValueError if windows invalid."""
    validate_windows(fast=fast_window, slow=slow_window)
    fast_ma = sma(candles["volume"], window=fast_window)
    slow_ma = sma(candles["volume"], window=slow_window)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=candles["datetime"], y=candles["volume"],
        name="Volume", marker_color="steelblue", opacity=0.5,
    ))
    fig.add_trace(go.Scatter(
        x=candles["datetime"], y=fast_ma,
        name=f"Fast MA ({fast_window})", line={"color": "orange", "width": 1.5},
    ))
    fig.add_trace(go.Scatter(
        x=candles["datetime"], y=slow_ma,
        name=f"Slow MA ({slow_window})", line={"color": "cyan", "width": 1.5},
    ))
    fig.update_layout(
        title="Volume with Moving Averages",
        xaxis_title="Date/Time",
        yaxis_title="Volume",
        template="plotly_dark",
        legend={"orientation": "h", "y": 1.02},
        margin={"l": 40, "r": 20, "t": 40, "b": 40},
    )
    return fig
