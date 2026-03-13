import pandas as pd
import pytest

import narrata.analysis.patterns as patterns
from narrata.analysis.patterns import (
    describe_candlestick,
    describe_patterns,
    detect_candlestick_pattern,
    detect_chart_pattern,
    detect_patterns,
)
from narrata.exceptions import ValidationError
from narrata.types import PatternStats


def test_detect_chart_pattern_returns_tuple(sample_ohlcv_df: pd.DataFrame) -> None:
    pattern, since = detect_chart_pattern(sample_ohlcv_df, lookback=60)
    assert pattern in {"Ascending triangle", None}
    if pattern is None:
        assert since is None


def test_detect_candlestick_pattern_detects_bullish_engulfing() -> None:
    dates = pd.date_range("2025-01-01", periods=5, freq="D")
    df = pd.DataFrame(
        {
            "Open": [10.0, 11.0, 12.0, 13.0, 11.0],
            "High": [11.0, 12.0, 13.0, 13.5, 14.5],
            "Low": [9.5, 10.5, 11.5, 11.0, 11.0],
            "Close": [10.5, 11.5, 12.5, 11.2, 14.4],
            "Volume": [1000, 1100, 1200, 1300, 1400],
        },
        index=dates,
    )
    name, when = detect_candlestick_pattern(df)
    assert name == "Bullish Engulfing"
    assert when == dates[-1].date()


def test_detect_patterns_composes_stats(sample_ohlcv_df: pd.DataFrame) -> None:
    stats = detect_patterns(sample_ohlcv_df)
    assert hasattr(stats, "chart_pattern")
    assert hasattr(stats, "candlestick_pattern")


def test_describe_pattern_lines(sample_ohlcv_df: pd.DataFrame) -> None:
    stats = detect_patterns(sample_ohlcv_df)
    assert describe_patterns(stats).startswith("Patterns:")
    assert describe_candlestick(stats).startswith("Candlestick:")


def test_detect_candlestick_pattern_uses_pandas_ta_when_available(monkeypatch, sample_ohlcv_df: pd.DataFrame) -> None:
    class FakeTA:
        Imports = {"talib": False}

        @staticmethod
        def cdl_pattern(open_, high, low, close, name):
            return pd.DataFrame(
                {
                    "CDL_DOJI_10_0.1": [0.0, 100.0],
                    "CDL_INSIDE": [0.0, 0.0],
                },
                index=close.index[-2:],
            )

    def should_not_be_called(*_args, **_kwargs):
        raise AssertionError("In-house fallback should not run when pandas_ta detected a pattern.")

    monkeypatch.setattr(patterns, "ta", FakeTA())
    monkeypatch.setattr(patterns, "_detect_candlestick_inhouse", should_not_be_called)

    name, when = patterns.detect_candlestick_pattern(sample_ohlcv_df)
    assert name == "Doji"
    assert when == sample_ohlcv_df.index[-1].date()


def test_detect_candlestick_pattern_falls_back_when_pandas_ta_returns_none(
    monkeypatch,
) -> None:
    dates = pd.date_range("2025-01-01", periods=5, freq="D")
    df = pd.DataFrame(
        {
            "Open": [10.0, 11.0, 12.0, 13.0, 11.0],
            "High": [11.0, 12.0, 13.0, 13.5, 14.5],
            "Low": [9.5, 10.5, 11.5, 11.0, 11.0],
            "Close": [10.5, 11.5, 12.5, 11.2, 14.4],
            "Volume": [1000, 1100, 1200, 1300, 1400],
        },
        index=dates,
    )

    class FakeTA:
        Imports = {"talib": False}

        @staticmethod
        def cdl_pattern(open_, high, low, close, name):
            return pd.DataFrame(
                {
                    "CDL_DOJI_10_0.1": [0.0, 0.0],
                    "CDL_INSIDE": [0.0, 0.0],
                },
                index=close.index[-2:],
            )

    monkeypatch.setattr(patterns, "ta", FakeTA())
    name, when = patterns.detect_candlestick_pattern(df)
    assert name == "Bullish Engulfing"
    assert when == dates[-1].date()


def test_detect_candlestick_pattern_inhouse_detects_doji(monkeypatch) -> None:
    monkeypatch.setattr(patterns, "ta", None)
    dates = pd.date_range("2025-01-01", periods=4, freq="D")
    df = pd.DataFrame(
        {
            "Open": [10.0, 10.4, 10.8, 11.0],
            "High": [10.5, 10.9, 11.2, 11.6],
            "Low": [9.8, 10.0, 10.6, 10.2],
            "Close": [10.3, 10.8, 11.1, 11.02],
            "Volume": [1000, 1100, 1200, 1300],
        },
        index=dates,
    )
    name, when = patterns.detect_candlestick_pattern(df)
    assert name == "Doji"
    assert when == dates[-1].date()


def test_detect_candlestick_pattern_inhouse_detects_inside_bar(monkeypatch) -> None:
    monkeypatch.setattr(patterns, "ta", None)
    dates = pd.date_range("2025-01-01", periods=4, freq="D")
    df = pd.DataFrame(
        {
            "Open": [10.0, 10.3, 10.8, 10.9],
            "High": [11.0, 11.4, 11.8, 11.2],
            "Low": [9.4, 9.8, 10.1, 10.4],
            "Close": [10.5, 10.9, 11.1, 10.8],
            "Volume": [1000, 1100, 1200, 1300],
        },
        index=dates,
    )
    name, when = patterns.detect_candlestick_pattern(df)
    assert name == "Inside Bar"
    assert when == dates[-1].date()


def test_detect_patterns_rejects_small_lookback(sample_ohlcv_df: pd.DataFrame) -> None:
    with pytest.raises(ValidationError, match="lookback must be >= 10"):
        detect_patterns(sample_ohlcv_df, lookback=5)


def test_detect_chart_pattern_missing_columns() -> None:
    dates = pd.date_range("2025-01-01", periods=5, freq="D")
    df = pd.DataFrame({"Close": [1.0] * 5}, index=dates)
    with pytest.raises(ValidationError, match="High, Low and Close"):
        detect_chart_pattern(df)


def test_detect_candlestick_too_few_rows() -> None:
    dates = pd.date_range("2025-01-01", periods=1, freq="D")
    df = pd.DataFrame(
        {"Open": [10.0], "High": [11.0], "Low": [9.0], "Close": [10.5], "Volume": [100]},
        index=dates,
    )
    name, when = detect_candlestick_pattern(df)
    assert name is None
    assert when is None


def test_describe_patterns_none_when_no_pattern() -> None:
    stats = PatternStats(
        chart_pattern=None,
        chart_pattern_since=None,
        candlestick_pattern=None,
        candlestick_date=None,
    )
    assert describe_patterns(stats) is None
    assert describe_candlestick(stats) is None


def test_detect_candlestick_inhouse_bearish_engulfing(monkeypatch) -> None:
    monkeypatch.setattr(patterns, "ta", None)
    dates = pd.date_range("2025-01-01", periods=5, freq="D")
    # prev: open=11.0, close=13.5 (bullish, close > open)
    # curr: open=13.5, close=11.0 (bearish, close < open, engulfs prev body)
    df = pd.DataFrame(
        {
            "Open": [10.0, 10.3, 10.8, 11.0, 13.5],
            "High": [11.0, 11.2, 11.8, 14.0, 14.0],
            "Low": [9.5, 9.8, 10.1, 10.8, 10.5],
            "Close": [10.5, 10.9, 11.5, 13.5, 11.0],
            "Volume": [1000, 1100, 1200, 1300, 1400],
        },
        index=dates,
    )
    name, when = detect_candlestick_pattern(df)
    assert name == "Bearish Engulfing"
    assert when == dates[-1].date()


def test_detect_chart_pattern_no_pattern_when_too_few_points() -> None:
    dates = pd.date_range("2025-01-01", periods=3, freq="D")
    df = pd.DataFrame(
        {
            "Open": [10.0, 11.0, 12.0],
            "High": [11.0, 12.0, 13.0],
            "Low": [9.0, 10.0, 11.0],
            "Close": [10.5, 11.5, 12.5],
            "Volume": [100, 100, 100],
        },
        index=dates,
    )
    pattern, since = detect_chart_pattern(df, lookback=60)
    assert pattern is None
    assert since is None
