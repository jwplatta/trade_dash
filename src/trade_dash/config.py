"""Environment-variable-backed path configuration for trade_dash."""
from __future__ import annotations

import os
from pathlib import Path

_HOME = Path.home()
_TICKRAKE = _HOME / ".tickrake" / "data"

DATA_DIR: Path = Path(os.getenv("TRADE_DASH_DATA_DIR", str(_TICKRAKE)))
CANDLE_DIR: Path = Path(
    os.getenv("TRADE_DASH_CANDLE_DIR", str(_TICKRAKE / "history" / "ibkr-paper"))
)
OPTIONS_DIR: Path = Path(
    os.getenv("TRADE_DASH_OPTIONS_DIR", str(_TICKRAKE / "options" / "schwab"))
)
