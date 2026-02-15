from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ASSETS_DIR = Path(__file__).parent / "assets"


@pytest.fixture
def real_aapl_df() -> pd.DataFrame:
    """AAPL 1-year daily OHLCV from yfinance (static fixture)."""
    df = pd.read_csv(ASSETS_DIR / "aapl_1y.csv", index_col="Date", parse_dates=True)
    return df


@pytest.fixture
def sample_ohlcv_df() -> pd.DataFrame:
    points = 120
    dates = pd.date_range("2025-01-01", periods=points, freq="D")
    rng = np.random.default_rng(42)
    base = np.linspace(100.0, 130.0, points)
    noise = rng.normal(0.0, 0.6, points)
    close = base + noise
    open_ = close + rng.normal(0.0, 0.5, points)
    high = np.maximum(open_, close) + np.abs(rng.normal(0.4, 0.2, points))
    low = np.minimum(open_, close) - np.abs(rng.normal(0.4, 0.2, points))
    volume = rng.integers(900, 1800, points)

    df = pd.DataFrame(
        {
            "Open": open_,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
        },
        index=dates,
    )
    df.attrs["ticker"] = "AAPL"
    return df
