"""Candle (OHLCV) data loader with caching."""
from __future__ import annotations

import subprocess
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from trade_dash.config import CANDLE_DIR

_FREQ_TO_SUFFIX: dict[str, str] = {
    "day": "day",
    "1min": "1min",
    "5min": "5min",
    "30min": "30min",
}


def _candle_path(symbol: str, freq: str, data_dir: Path = CANDLE_DIR) -> Path:
    suffix = _FREQ_TO_SUFFIX.get(freq, freq)
    return data_dir / f"{symbol}_{suffix}.csv"


@st.cache_data(ttl=300)
def load_candles(
    symbol: str,
    freq: str,
    start: date | None = None,
    end: date | None = None,
    data_dir: Path = CANDLE_DIR,
) -> pd.DataFrame:
    """Load candle CSV. Full file is cached; start/end slices the cached DataFrame."""
    path = _candle_path(symbol, freq, data_dir)
    if not path.exists():
        raise FileNotFoundError(f"Candle file not found: {path}")

    df = pd.read_csv(
        path,
        parse_dates=["datetime"],
        dtype={
            "open": "float64",
            "high": "float64",
            "low": "float64",
            "close": "float64",
            "volume": "float64",
        },
    )
    df = df[["datetime", "open", "high", "low", "close", "volume"]]

    if start is not None:
        start_ts = pd.Timestamp(start, tz="UTC") if df["datetime"].dt.tz is not None else pd.Timestamp(start)
        df = df[df["datetime"] >= start_ts]
    if end is not None:
        end_ts = pd.Timestamp(end, tz="UTC") if df["datetime"].dt.tz is not None else pd.Timestamp(end)
        df = df[df["datetime"] <= end_ts]

    return df.reset_index(drop=True)


@st.cache_data(ttl=3600)
def list_available_dates(
    symbol: str, freq: str, data_dir: Path = CANDLE_DIR
) -> tuple[datetime, datetime]:
    """Return (earliest, latest) datetime from the candle file without loading it all."""
    path = _candle_path(symbol, freq, data_dir)
    if not path.exists():
        raise FileNotFoundError(f"Candle file not found: {path}")

    first_row = pd.read_csv(path, nrows=1, parse_dates=["datetime"])
    start_dt: datetime = first_row["datetime"].iloc[0].to_pydatetime()

    result = subprocess.run(
        ["tail", "-n", "2", str(path)], capture_output=True, text=True, check=True
    )
    last_line = result.stdout.strip().splitlines()[-1]
    end_dt: datetime = pd.Timestamp(last_line.split(",")[0]).to_pydatetime()

    return start_dt, end_dt
