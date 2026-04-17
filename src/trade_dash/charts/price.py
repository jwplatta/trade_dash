"""SMA price line chart."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from trade_dash.calc.ma import sma, validate_windows

_INTRADAY_FREQS = {"1min", "5min", "30min"}


def _day_boundary_ticks(datetimes: pd.Series) -> tuple[list[int], list[str]]:
    """One tick per trading day for integer-index intraday charts."""
    dates = datetimes.dt.normalize()  # vectorized date extraction
    changed = pd.Series([True], index=[dates.index[0]]).reindex(dates.index, fill_value=False)
    changed |= dates != dates.shift(1)
    tick_vals = changed[changed].index.tolist()
    tick_text = dates[changed].dt.strftime("%-m/%-d").tolist()
    return tick_vals, tick_text


def build_sma_price_chart(
    candles: pd.DataFrame,
    fast_window: int,
    slow_window: int,
    title: str = "Price with Moving Averages",
    freq: str = "day",
) -> go.Figure:
    """Line chart: close + fast MA + slow MA. Raises ValueError if windows invalid."""
    validate_windows(fast=fast_window, slow=slow_window)
    fast_ma = sma(candles["close"], window=fast_window)
    slow_ma = sma(candles["close"], window=slow_window)

    intraday = freq in _INTRADAY_FREQS
    if intraday:
        x = list(range(len(candles)))
        tick_vals, tick_text = _day_boundary_ticks(candles["datetime"])
        hover_labels = candles["datetime"].dt.strftime("%m/%d %H:%M").tolist()
        hover_tmpl = "%{text}<br>%{y:.2f}<extra></extra>"
    else:
        x = candles["datetime"]
        hover_labels = None
        hover_tmpl = None

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x,
            y=candles["close"],
            name="Close",
            line={"color": "white", "width": 1},
            opacity=0.7,
            text=hover_labels,
            hovertemplate=hover_tmpl,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x,
            y=fast_ma,
            name=f"Fast MA ({fast_window})",
            line={"color": "orange", "width": 1.5},
            text=hover_labels,
            hovertemplate=hover_tmpl,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x,
            y=slow_ma,
            name=f"Slow MA ({slow_window})",
            line={"color": "cyan", "width": 1.5},
            text=hover_labels,
            hovertemplate=hover_tmpl,
        )
    )
    fig.update_layout(
        title=title,
        xaxis_title="Date/Time",
        yaxis_title="Price",
        template="plotly_dark",
        legend={"orientation": "h", "y": 1.02},
        margin={"l": 40, "r": 20, "t": 40, "b": 40},
    )
    if intraday:
        fig.update_xaxes(tickvals=tick_vals, ticktext=tick_text, tickangle=-45)
    return fig
