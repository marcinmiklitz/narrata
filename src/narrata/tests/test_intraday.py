"""Tests for intraday frequency detection and indicator parameter scaling."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from narrata import narrate
from narrata.analysis.indicators import (
    _intraday_defaults,
    analyze_indicators,
    describe_indicators,
)
from narrata.validation.ohlcv import infer_frequency_label, is_intraday, normalize_columns

ASSETS_DIR = Path(__file__).parent / "assets"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def intraday_15m_1d() -> pd.DataFrame:
    """1 day of AAPL 15-minute bars."""
    df = pd.read_csv(ASSETS_DIR / "aapl_15m_1d.csv", index_col="Datetime", parse_dates=True)
    df = normalize_columns(df)
    df.attrs["ticker"] = "AAPL"
    return df


@pytest.fixture
def intraday_15m_5d() -> pd.DataFrame:
    """5 days of AAPL 15-minute bars."""
    df = pd.read_csv(ASSETS_DIR / "aapl_15m_5d.csv", index_col="Datetime", parse_dates=True)
    df = normalize_columns(df)
    df.attrs["ticker"] = "AAPL"
    return df


@pytest.fixture
def intraday_5m() -> pd.DataFrame:
    """Synthetic 5-min OHLCV for 1 trading day (78 bars)."""
    dates = pd.date_range("2025-06-01 09:30", periods=78, freq="5min")
    rng = np.random.default_rng(99)
    close = np.linspace(150.0, 152.0, 78) + rng.normal(0, 0.2, 78)
    return pd.DataFrame(
        {
            "Open": close + rng.normal(0, 0.1, 78),
            "High": close + abs(rng.normal(0.1, 0.05, 78)),
            "Low": close - abs(rng.normal(0.1, 0.05, 78)),
            "Close": close,
            "Volume": rng.integers(1000, 5000, 78),
        },
        index=dates,
    )


# ---------------------------------------------------------------------------
# Frequency detection
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("freq_str", "expected"),
    [
        ("1min", "1min"),
        ("5min", "5min"),
        ("15min", "15min"),
        ("30min", "30min"),
        ("h", "hourly"),
        ("D", "daily"),
    ],
)
def test_infer_frequency_sub_hourly(freq_str, expected):
    idx = pd.date_range("2025-01-01", periods=50, freq=freq_str)
    assert infer_frequency_label(idx) == expected


def test_infer_frequency_from_real_15m(intraday_15m_1d):
    label = infer_frequency_label(intraday_15m_1d.index)
    assert label == "15min"


def test_is_intraday_true():
    for freq in ("1min", "5min", "15min", "30min", "hourly"):
        assert is_intraday(freq), f"{freq} should be intraday"


def test_is_intraday_false():
    for freq in ("daily", "weekly", "monthly", "business-daily"):
        assert not is_intraday(freq), f"{freq} should not be intraday"


# ---------------------------------------------------------------------------
# Parameter scaling
# ---------------------------------------------------------------------------


def test_daily_defaults_unchanged():
    d = _intraday_defaults("daily")
    assert d["ma_fast"] == 50
    assert d["ma_slow"] == 200
    assert d["volume_lookback"] == 20
    assert d["vol_lookback"] == 252


def test_15min_defaults_scaled():
    d = _intraday_defaults("15min")
    assert d["ma_fast"] == 10
    assert d["ma_slow"] == 40
    assert d["volume_lookback"] == 26  # 1 trading day of 15m bars
    assert d["vol_lookback"] == 520  # 20 * 26 bars


def test_5min_defaults_scaled():
    d = _intraday_defaults("5min")
    assert d["ma_fast"] == 30  # 10 * 78 // 26
    assert d["ma_slow"] == 120  # 40 * 78 // 26
    assert d["volume_lookback"] == 78


def test_1min_defaults_scaled():
    d = _intraday_defaults("1min")
    assert d["ma_fast"] == 150  # 10 * 390 // 26
    assert d["ma_slow"] == 600  # 40 * 390 // 26
    assert d["volume_lookback"] == 390


# ---------------------------------------------------------------------------
# analyze_indicators with frequency
# ---------------------------------------------------------------------------


def test_analyze_indicators_stores_frequency(intraday_15m_5d):
    stats = analyze_indicators(intraday_15m_5d, frequency="15min")
    assert stats.frequency == "15min"
    assert stats.ma_fast_period == 10
    assert stats.ma_slow_period == 40
    assert stats.volume_lookback == 26


def test_analyze_indicators_daily_defaults(sample_ohlcv_df):
    stats = analyze_indicators(sample_ohlcv_df, frequency="daily")
    assert stats.ma_fast_period == 50
    assert stats.ma_slow_period == 200
    assert stats.frequency == "daily"


# ---------------------------------------------------------------------------
# describe_indicators labels
# ---------------------------------------------------------------------------


def test_describe_uses_actual_ma_periods(intraday_15m_5d):
    stats = analyze_indicators(intraday_15m_5d, frequency="15min")
    text = describe_indicators(stats)
    assert "SMA 10/40" in text or "SMA 10/40" in text
    assert "SMA 50/200" not in text


def test_describe_uses_bar_unit_for_intraday(intraday_15m_5d):
    stats = analyze_indicators(intraday_15m_5d, frequency="15min")
    text = describe_indicators(stats)
    if stats.volume_state is not None:
        assert "26-bar avg" in text
        assert "20-day avg" not in text


def test_describe_uses_day_unit_for_daily(sample_ohlcv_df):
    stats = analyze_indicators(sample_ohlcv_df, frequency="daily")
    text = describe_indicators(stats)
    if stats.volume_state is not None:
        assert "20-day avg" in text


# ---------------------------------------------------------------------------
# narrate() end-to-end with intraday data
# ---------------------------------------------------------------------------


def test_narrate_intraday_detects_frequency(intraday_15m_5d):
    text = narrate(intraday_15m_5d)
    assert "15min" in text  # frequency label in overview


def test_narrate_intraday_uses_scaled_sma(intraday_15m_5d):
    text = narrate(intraday_15m_5d)
    assert "SMA 50/200" not in text
    # Should use SMA 10/40 or not appear at all (insufficient data)
    if "SMA" in text:
        assert "SMA 10/40" in text


def test_narrate_intraday_1d_runs(intraday_15m_1d):
    text = narrate(intraday_15m_1d)
    assert "AAPL" in text
    assert "15min" in text


def test_narrate_explicit_frequency_override(sample_ohlcv_df):
    """Daily data forced to '15min' uses intraday scaling."""
    text = narrate(sample_ohlcv_df, frequency="15min")
    assert "15min" in text
    if "SMA" in text:
        assert "SMA 10/40" in text


def test_narrate_invalid_frequency_raises(sample_ohlcv_df):
    with pytest.raises(Exception, match="Unknown frequency"):
        narrate(sample_ohlcv_df, frequency="bogus")


def test_narrate_irregular_frequency_uses_bar_units(sample_ohlcv_df):
    text = narrate(sample_ohlcv_df, frequency="irregular")
    assert "irregular" in text
    if "Volume" in text:
        assert "bar avg" in text
        assert "day avg" not in text


@pytest.fixture
def sample_ohlcv_df():
    """Standard daily fixture matching conftest pattern."""
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
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=dates,
    )
    df.attrs["ticker"] = "AAPL"
    return df
