"""Dashboard data and rendering helpers."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class DashboardMetric:
    """Single KPI displayed in the dashboard header."""

    label: str
    value: str
    delta: str


def sample_positions() -> pd.DataFrame:
    """Return sample position data for the initial dashboard view."""
    return pd.DataFrame(
        [
            {"symbol": "SPY", "side": "Long", "quantity": 120, "price": 524.18, "pnl": 1840.50},
            {"symbol": "QQQ", "side": "Long", "quantity": 75, "price": 448.72, "pnl": 1265.40},
            {"symbol": "IWM", "side": "Short", "quantity": 40, "price": 207.11, "pnl": -382.15},
            {"symbol": "TLT", "side": "Long", "quantity": 55, "price": 91.47, "pnl": 214.80},
        ]
    )


def portfolio_metrics(positions: pd.DataFrame) -> list[DashboardMetric]:
    """Summarize the sample portfolio into KPI cards."""
    gross_exposure = float((positions["quantity"] * positions["price"]).sum())
    net_pnl = float(positions["pnl"].sum())
    winners = int((positions["pnl"] > 0).sum())
    total = int(len(positions.index))

    return [
        DashboardMetric("Gross Exposure", f"${gross_exposure:,.0f}", "+2.4%"),
        DashboardMetric("Net P&L", f"${net_pnl:,.0f}", "+1.1% today"),
        DashboardMetric("Open Positions", str(total), f"{winners}/{total} green"),
    ]


def pnl_timeseries() -> pd.DataFrame:
    """Return a simple daily P&L curve for the line chart."""
    return pd.DataFrame(
        {
            "day": ["Mon", "Tue", "Wed", "Thu", "Fri"],
            "net_pnl": [1200, 1680, 1435, 1895, 2938],
        }
    )
