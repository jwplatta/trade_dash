"""GEX (Gamma Exposure) calculation functions."""
from __future__ import annotations

import math

import numpy as np
import numpy.typing as npt
import pandas as pd


def _bs_gamma(
    s: npt.NDArray[np.float64],
    k: npt.NDArray[np.float64],
    t: npt.NDArray[np.float64],
    sigma: npt.NDArray[np.float64],
    r: float = 0.0,
    q: float = 0.0,
) -> npt.NDArray[np.float64]:
    """Black-Scholes gamma. Port from docs/black_scholes.py."""
    sqrt_t = np.sqrt(np.maximum(t, 1e-10))
    d1 = (np.log(s / k) + (r - q + 0.5 * sigma**2) * t) / (sigma * sqrt_t)
    pdf_d1 = np.exp(-0.5 * d1**2) / math.sqrt(2 * math.pi)
    result: npt.NDArray[np.float64] = pdf_d1 / (s * sigma * sqrt_t)
    return result


def net_gex_by_strike(
    opts: pd.DataFrame,
    spot: float,
    strike_range: float = 300.0,
) -> pd.DataFrame:
    """Compute net GEX by strike. Returns DataFrame[strike, net_gex].

    Formula: gamma * open_interest * spot² per contract.
    Calls positive, puts negative. Filtered to ±strike_range around spot.
    """
    df = opts.copy()

    is_call = (df["contract_type"] == "CALL").to_numpy(dtype=bool)
    k = pd.to_numeric(df["strike"], errors="coerce").to_numpy(dtype=float)
    oi = pd.to_numeric(df["open_interest"], errors="coerce").to_numpy(dtype=float)
    gam = pd.to_numeric(df["gamma"], errors="coerce").to_numpy(dtype=float)

    gex_each = gam * oi * (spot**2)
    sign = np.where(is_call, 1.0, -1.0)
    net_gex_each = gex_each * sign

    gex_df = pd.DataFrame({"strike": k, "net_gex": net_gex_each})
    net: pd.DataFrame = gex_df.groupby("strike")["net_gex"].sum().reset_index()

    mask = (net["strike"] >= spot - strike_range) & (net["strike"] <= spot + strike_range)
    return net[mask].reset_index(drop=True)


def net_gex_by_price(
    opts: pd.DataFrame,
    spot: float,
    price_range: float = 300.0,
    n_points: int = 601,
) -> pd.DataFrame:
    """Compute net GEX on a price grid using Black-Scholes gamma.

    Returns DataFrame[price, net_gex].
    Port the algorithm from docs/intraday.py::calculate_zero_gamma_line
    but return the full grid (not just the ZGL crossing).
    """
    df = opts.copy()

    # Parse expiration datetime (3 PM CT expiry)
    df["expiration_dt"] = pd.to_datetime(df["expiration_date"]) + pd.Timedelta(
        hours=15, minutes=15
    )

    # Time to expiry: use the expiration_dt as-is, compute relative to a fixed ref.
    # For a pure function we compute T from the expiration datetime relative to now=0.
    # In practice, the caller should ensure opts has a T column or we use the expiration date.
    # We compute T from epoch to expiration as a relative time in years.
    # To stay pure (no datetime.now()), we compute T using raw timestamps and
    # treat the snap time as the fetch time embedded in the data. We use the
    # same approach as docs/intraday.py but accept that T is computed from a
    # reference that makes the values reasonable.
    # NOTE: We use pd.Timestamp.now() only for T computation since this is a
    # calculation function without I/O; it reads system time for the grid calc.
    now = pd.Timestamp.now()
    df["T"] = (df["expiration_dt"] - now).dt.total_seconds() / (365.0 * 24 * 3600)
    df["T"] = df["T"].clip(lower=(5.0 / (365.0 * 24 * 60)))

    df["iv"] = pd.to_numeric(df["theoretical_volatility"], errors="coerce") / 100.0
    df["K"] = pd.to_numeric(df["strike"], errors="coerce")
    df["OI"] = pd.to_numeric(df["open_interest"], errors="coerce")

    df = df.dropna(subset=["iv", "K", "OI", "T"])
    df = df[(df["iv"] > 0) & (df["OI"] > 0)].copy()

    if df.empty:
        return pd.DataFrame({"price": [], "net_gex": []})

    is_call = (df["contract_type"] == "CALL").to_numpy(dtype=bool)
    k_arr = df["K"].to_numpy(dtype=float)
    t_arr = df["T"].to_numpy(dtype=float)
    iv_arr = df["iv"].to_numpy(dtype=float)
    oi_arr = df["OI"].to_numpy(dtype=float)

    prices_grid = np.linspace(spot - price_range, spot + price_range, n_points)

    net_gex_vals: list[float] = []
    for p in prices_grid:
        s_arr = np.full_like(k_arr, float(p), dtype=float)
        gam = _bs_gamma(s=s_arr, k=k_arr, t=t_arr, sigma=iv_arr, r=0.0, q=0.0)
        gex_each = gam * oi_arr * (float(p) ** 2)
        net_gex = float(gex_each[is_call].sum()) - float(gex_each[~is_call].sum())
        net_gex_vals.append(net_gex)

    return pd.DataFrame({"price": prices_grid, "net_gex": np.array(net_gex_vals, dtype=float)})


def find_zero_gamma_level(
    prices: npt.NDArray[np.float64],
    gex: npt.NDArray[np.float64],
) -> float | None:
    """Find the price where net GEX crosses zero via linear interpolation.

    Port the sign-change detection from docs/intraday.py::calculate_zero_gamma_line.
    Returns None if no crossing found.
    """
    sign = np.sign(gex)

    # Handle zeros by forward-filling
    sign_filled = sign.copy()
    last_nonzero: float | None = None
    for i in range(len(sign)):
        if sign[i] != 0:
            last_nonzero = float(sign[i])
        elif last_nonzero is not None:
            sign_filled[i] = last_nonzero

    idx = np.where(np.diff(sign_filled) != 0)[0]

    if len(idx) == 0:
        return None

    # Use first crossing and interpolate
    i = int(idx[0])
    x1, x2 = float(prices[i]), float(prices[i + 1])
    y1, y2 = float(gex[i]), float(gex[i + 1])

    zgl = x1 + (0.0 - y1) * (x2 - x1) / (y2 - y1) if y2 != y1 else (x1 + x2) / 2.0

    return float(zgl)


def find_call_wall(strike_gex: pd.DataFrame) -> tuple[float, float]:
    """Return (strike, net_gex) for the largest positive net GEX."""
    pos = strike_gex[strike_gex["net_gex"] > 0]
    if pos.empty:
        return float("nan"), float("nan")
    strikes = pos["strike"].to_numpy(dtype=float)
    gex_vals = pos["net_gex"].to_numpy(dtype=float)
    i = int(gex_vals.argmax())
    return float(strikes[i]), float(gex_vals[i])


def find_put_wall(strike_gex: pd.DataFrame) -> tuple[float, float]:
    """Return (strike, net_gex) for the largest negative net GEX."""
    neg = strike_gex[strike_gex["net_gex"] < 0]
    if neg.empty:
        return float("nan"), float("nan")
    strikes = neg["strike"].to_numpy(dtype=float)
    gex_vals = neg["net_gex"].to_numpy(dtype=float)
    i = int(gex_vals.argmin())
    return float(strikes[i]), float(gex_vals[i])
