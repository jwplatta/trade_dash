"""Options chain snapshot loader."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from trade_dash.config import OPTIONS_DIR

_OPTIONS_DTYPES: dict[str, Any] = {
    "strike": "float64",
    "open_interest": "float64",
    "gamma": "float64",
    "delta": "float64",
    "theta": "float64",
    "vega": "float64",
    "theoretical_volatility": "float64",
    "underlying_price": "float64",
    "mark": "float64",
    "bid": "float64",
    "ask": "float64",
    "total_volume": "float64",
}


def _parse_filename(path: Path) -> tuple[date, datetime] | None:
    """Parse expiration date and fetch datetime from filename stem.

    Pattern: {SYMBOL}_exp{YYYY-MM-DD}_{YYYY-MM-DD}_{HH-MM-SS}
    """
    parts = path.stem.split("_")
    if len(parts) < 4:
        return None
    try:
        exp_date = date.fromisoformat(parts[1].removeprefix("exp"))
        fetch_dt = datetime.strptime(f"{parts[2]}_{parts[3]}", "%Y-%m-%d_%H-%M-%S")
        return exp_date, fetch_dt
    except ValueError:
        return None


@st.cache_data(ttl=300)
def list_expirations(
    symbol: str,
    data_dir: Path = OPTIONS_DIR,
) -> list[date]:
    """Return sorted list of all available expiration dates from filenames (no CSV reads)."""
    seen: set[date] = set()
    for path in data_dir.glob(f"{symbol}_exp*.csv"):
        parsed = _parse_filename(path)
        if parsed:
            seen.add(parsed[0])
    return sorted(seen)


@st.cache_data(ttl=30)
def find_latest_snapshots(
    symbol: str,
    start_date: date,
    days_out: int,
    include_0dte: bool = True,
    data_dir: Path = OPTIONS_DIR,
) -> dict[date, Path]:
    """Return {expiry_date: most_recent_snapshot_path} for expirations in window."""
    end_date = date.fromordinal(start_date.toordinal() + days_out)
    best: dict[date, tuple[datetime, Path]] = {}

    for path in data_dir.glob(f"{symbol}_exp*.csv"):
        parsed = _parse_filename(path)
        if not parsed:
            continue
        exp_date, fetch_dt = parsed
        if not (start_date <= exp_date <= end_date):
            continue
        if not include_0dte and exp_date == start_date:
            continue
        if exp_date not in best or fetch_dt > best[exp_date][0]:
            best[exp_date] = (fetch_dt, path)

    return {exp: info[1] for exp, info in sorted(best.items())}


@st.cache_data(ttl=3000)
def find_all_snapshots_for_expiry(
    symbol: str,
    expiry: date,
    data_dir: Path = OPTIONS_DIR,
) -> list[tuple[datetime, Path]]:
    """Return all (fetch_datetime, path) pairs for a given expiry, sorted by time."""
    results = []
    for path in data_dir.glob(f"{symbol}_exp{expiry}_*.csv"):
        parsed = _parse_filename(path)
        if parsed and parsed[0] == expiry:
            results.append((parsed[1], path))
    return sorted(results)


@st.cache_data(ttl=3600)
def load_options_snapshot(path: Path) -> pd.DataFrame:
    """Load a single options snapshot CSV with typed columns."""
    df = pd.read_csv(path, dtype=_OPTIONS_DTYPES)  # type: ignore[arg-type]
    df["expiration_date"] = pd.to_datetime(df["expiration_date"])
    return df
