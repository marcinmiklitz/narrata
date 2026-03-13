"""Tests for data format adapters and close-only mode."""

import numpy as np
import pandas as pd
import pytest

from narrata import from_ccxt, from_coingecko, narrate

# ---------------------------------------------------------------------------
# from_ccxt
# ---------------------------------------------------------------------------

SAMPLE_CCXT = [
    [1710000000000, 67000.0, 67500.0, 66800.0, 67200.0, 1234.5],
    [1710000900000, 67200.0, 67300.0, 67000.0, 67100.0, 987.6],
    [1710001800000, 67100.0, 67400.0, 67050.0, 67350.0, 1100.2],
    [1710002700000, 67350.0, 67600.0, 67300.0, 67550.0, 800.0],
    [1710003600000, 67550.0, 67700.0, 67400.0, 67450.0, 950.3],
]


def _make_ccxt_rows(n: int = 60) -> list[list[float]]:
    """Generate n ccxt-format rows with realistic 15-min crypto data."""
    rng = np.random.default_rng(42)
    base_ts = 1710000000000
    rows = []
    price = 67000.0
    for i in range(n):
        ts = base_ts + i * 900_000
        o = price
        h = o + abs(rng.normal(50, 20))
        low = o - abs(rng.normal(50, 20))
        c = o + rng.normal(0, 30)
        v = float(rng.integers(500, 3000))
        rows.append([ts, o, h, low, c, v])
        price = c
    return rows


def test_from_ccxt_basic():
    df = from_ccxt(SAMPLE_CCXT)
    assert list(df.columns) == ["Open", "High", "Low", "Close", "Volume"]
    assert isinstance(df.index, pd.DatetimeIndex)
    assert len(df) == 5


def test_from_ccxt_with_ticker():
    df = from_ccxt(SAMPLE_CCXT, ticker="BTC/USDT")
    assert df.attrs["ticker"] == "BTC/USDT"


def test_from_ccxt_sorted():
    reversed_rows = list(reversed(SAMPLE_CCXT))
    df = from_ccxt(reversed_rows)
    assert df.index.is_monotonic_increasing


def test_from_ccxt_empty_raises():
    with pytest.raises(Exception, match="at least one row"):
        from_ccxt([])


def test_from_ccxt_short_row_raises():
    with pytest.raises(Exception, match="at least 6 elements"):
        from_ccxt([[1710000000000, 67000.0, 67500.0]])


def test_from_ccxt_narrate_integration():
    rows = _make_ccxt_rows(60)
    df = from_ccxt(rows, ticker="BTC/USDT")
    text = narrate(df)
    assert "BTC/USDT" in text
    assert "RSI(14):" in text


# ---------------------------------------------------------------------------
# from_coingecko
# ---------------------------------------------------------------------------

SAMPLE_COINGECKO = {
    "prices": [
        [1710000000000, 67200.0],
        [1710086400000, 67500.0],
        [1710172800000, 67100.0],
        [1710259200000, 67800.0],
        [1710345600000, 68000.0],
    ],
    "total_volumes": [
        [1710000000000, 25e9],
        [1710086400000, 28e9],
        [1710172800000, 22e9],
        [1710259200000, 30e9],
        [1710345600000, 27e9],
    ],
}


def _make_coingecko_data(n: int = 60) -> dict:
    """Generate n days of CoinGecko-format data."""
    rng = np.random.default_rng(42)
    base_ts = 1710000000000
    prices = []
    volumes = []
    price = 67000.0
    for i in range(n):
        ts = base_ts + i * 86_400_000
        price += rng.normal(0, 200)
        prices.append([ts, price])
        volumes.append([ts, float(rng.integers(20e9, 40e9))])
    return {"prices": prices, "total_volumes": volumes}


def test_from_coingecko_basic():
    df = from_coingecko(SAMPLE_COINGECKO)
    assert "Close" in df.columns
    assert "Volume" in df.columns
    assert "Open" not in df.columns
    assert len(df) == 5


def test_from_coingecko_with_ticker():
    df = from_coingecko(SAMPLE_COINGECKO, ticker="bitcoin")
    assert df.attrs["ticker"] == "bitcoin"


def test_from_coingecko_without_volumes():
    data = {"prices": SAMPLE_COINGECKO["prices"]}
    df = from_coingecko(data)
    assert "Close" in df.columns
    assert "Volume" not in df.columns


def test_from_coingecko_empty_raises():
    with pytest.raises(Exception, match="prices"):
        from_coingecko({})


def test_from_coingecko_narrate_integration():
    data = _make_coingecko_data(60)
    df = from_coingecko(data, ticker="BTC")
    text = narrate(df)
    assert "BTC" in text
    # Patterns section silently omitted (no OHLC)
    assert "Patterns" not in text


# ---------------------------------------------------------------------------
# Close-only mode
# ---------------------------------------------------------------------------


def test_narrate_close_only():
    """narrate() works with just a Close column."""
    dates = pd.date_range("2025-01-01", periods=60, freq="D")
    rng = np.random.default_rng(42)
    df = pd.DataFrame(
        {"Close": np.linspace(100, 120, 60) + rng.normal(0, 1, 60)},
        index=dates,
    )
    text = narrate(df)
    assert "Close" in text
    assert "RSI(14):" in text


def test_narrate_close_volume_only():
    """narrate() works with Close + Volume (no Open/High/Low)."""
    dates = pd.date_range("2025-01-01", periods=60, freq="D")
    rng = np.random.default_rng(42)
    df = pd.DataFrame(
        {
            "Close": np.linspace(100, 120, 60) + rng.normal(0, 1, 60),
            "Volume": rng.integers(1000, 5000, 60),
        },
        index=dates,
    )
    text = narrate(df)
    assert "Volume:" in text


def test_narrate_close_only_patterns_omitted():
    """Patterns section silently omitted for close-only input."""
    dates = pd.date_range("2025-01-01", periods=120, freq="D")
    rng = np.random.default_rng(42)
    df = pd.DataFrame(
        {"Close": np.linspace(100, 130, 120) + rng.normal(0, 1, 120)},
        index=dates,
    )
    text = narrate(df)
    assert "Patterns" not in text
    assert "Candlestick" not in text
