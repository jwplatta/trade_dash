"""SMA price line chart."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from trade_dash.calc.ma import sma, validate_windows


def build_sma_price_chart(
    candles: pd.DataFrame,
    fast_window: int,
    slow_window: int,
    title: str = "Price with Moving Averages",
) -> go.Figure:
    """Line chart: close + fast MA + slow MA. Raises ValueError if windows invalid."""
    validate_windows(fast=fast_window, slow=slow_window)
    fast_ma = sma(candles["close"], window=fast_window)
    slow_ma = sma(candles["close"], window=slow_window)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=candles["datetime"], y=candles["close"],
        name="Close", line={"color": "white", "width": 1}, opacity=0.7,
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
        title=title,
        xaxis_title="Date/Time",
        yaxis_title="Price",
        template="plotly_dark",
        legend={"orientation": "h", "y": 1.02},
        margin={"l": 40, "r": 20, "t": 40, "b": 40},
    )
    return fig
