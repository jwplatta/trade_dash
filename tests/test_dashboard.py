from trade_dash.dashboard import pnl_timeseries, portfolio_metrics, sample_positions


def test_sample_positions_has_expected_columns() -> None:
    positions = sample_positions()
    assert list(positions.columns) == ["symbol", "side", "quantity", "price", "pnl"]
    assert len(positions.index) == 4


def test_portfolio_metrics_summarizes_positions() -> None:
    metrics = portfolio_metrics(sample_positions())
    assert [metric.label for metric in metrics] == [
        "Gross Exposure",
        "Net P&L",
        "Open Positions",
    ]
    assert metrics[1].value.startswith("$")


def test_pnl_timeseries_shape() -> None:
    history = pnl_timeseries()
    assert list(history.columns) == ["day", "net_pnl"]
    assert len(history.index) == 5
