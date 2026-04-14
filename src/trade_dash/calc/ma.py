"""Moving average calculation functions."""
from __future__ import annotations

import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    """Simple moving average."""
    result: pd.Series = series.rolling(window=window).mean()
    return result


def validate_windows(fast: int, slow: int) -> None:
    """Raise ValueError if fast >= slow or either is non-positive."""
    if fast <= 0 or slow <= 0:
        raise ValueError(f"Window sizes must be positive, got fast={fast}, slow={slow}")
    if fast >= slow:
        raise ValueError(f"fast window ({fast}) must be less than slow window ({slow})")
