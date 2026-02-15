import pandas as pd
import pytest

import narrata.analysis.indicators as indicators
from narrata.analysis.indicators import analyze_indicators, compute_macd, compute_rsi, describe_indicators


def test_compute_rsi_returns_bounded_value(sample_ohlcv_df: pd.DataFrame) -> None:
    value = compute_rsi(sample_ohlcv_df["Close"])
    assert 0.0 <= value <= 100.0


def test_compute_macd_returns_three_values(sample_ohlcv_df: pd.DataFrame) -> None:
    macd, signal, hist = compute_macd(sample_ohlcv_df["Close"])
    assert isinstance(macd, float)
    assert isinstance(signal, float)
    assert isinstance(hist, float)


def test_analyze_indicators_has_states(sample_ohlcv_df: pd.DataFrame) -> None:
    stats = analyze_indicators(sample_ohlcv_df)
    assert stats.rsi_state in {"overbought", "oversold", "neutral-bullish", "neutral-bearish"}
    assert stats.macd_state


def test_describe_indicators_format(sample_ohlcv_df: pd.DataFrame) -> None:
    text = describe_indicators(analyze_indicators(sample_ohlcv_df))
    assert "RSI(14):" in text
    assert "MACD:" in text


def test_analyze_indicators_fallback_without_pandas_ta(monkeypatch, sample_ohlcv_df: pd.DataFrame) -> None:
    monkeypatch.setattr(indicators, "ta", None)
    monkeypatch.setattr(indicators, "compute_rsi", lambda _series, period=14: 55.5)
    monkeypatch.setattr(indicators, "compute_macd", lambda _series: (1.1, 0.9, 0.2))

    stats = indicators.analyze_indicators(sample_ohlcv_df)
    assert stats.rsi_value == 55.5
    assert stats.macd_value == 1.1
    assert stats.macd_signal == 0.9
    assert stats.macd_histogram == 0.2


def test_analyze_indicators_uses_pandas_ta_when_available(monkeypatch, sample_ohlcv_df: pd.DataFrame) -> None:
    class FakeTA:
        @staticmethod
        def rsi(values: pd.Series, length: int) -> pd.Series:
            assert length == 14
            return pd.Series([float("nan"), 61.2], index=values.index[:2])

        @staticmethod
        def macd(values: pd.Series, fast: int, slow: int, signal: int) -> pd.DataFrame:
            assert (fast, slow, signal) == (12, 26, 9)
            return pd.DataFrame(
                {
                    "MACD_12_26_9": [0.8],
                    "MACDs_12_26_9": [0.5],
                    "MACDh_12_26_9": [0.3],
                }
            )

    def should_not_be_called(*_args, **_kwargs):
        raise AssertionError("Fallback implementation should not be used when pandas_ta is available.")

    monkeypatch.setattr(indicators, "ta", FakeTA())
    monkeypatch.setattr(indicators, "compute_rsi", should_not_be_called)
    monkeypatch.setattr(indicators, "compute_macd", should_not_be_called)

    stats = indicators.analyze_indicators(sample_ohlcv_df)
    assert stats.rsi_value == 61.2
    assert stats.macd_value == 0.8
    assert stats.macd_signal == 0.5
    assert stats.macd_histogram == 0.3


def test_analyze_indicators_uses_pandas_ta_macd_lines_for_state(monkeypatch, sample_ohlcv_df: pd.DataFrame) -> None:
    class FakeTA:
        @staticmethod
        def rsi(values: pd.Series, length: int) -> pd.Series:
            return pd.Series([55.0, 56.0], index=values.index[:2])

        @staticmethod
        def macd(values: pd.Series, fast: int, slow: int, signal: int) -> pd.DataFrame:
            idx = values.index[:4]
            return pd.DataFrame(
                {
                    "MACD_12_26_9": [-1.0, -0.2, 0.1, 0.4],
                    "MACDs_12_26_9": [0.0, 0.0, 0.0, 0.0],
                    "MACDh_12_26_9": [-1.0, -0.2, 0.1, 0.4],
                },
                index=idx,
            )

    def should_not_be_called(*_args, **_kwargs):
        raise AssertionError("In-house MACD classifier should not be used when pandas_ta data is available.")

    monkeypatch.setattr(indicators, "ta", FakeTA())
    monkeypatch.setattr(indicators, "_classify_macd", should_not_be_called)

    stats = indicators.analyze_indicators(sample_ohlcv_df)
    assert stats.macd_state == "bullish"
    assert stats.crossover_days_ago == 1


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (1.0, "1st"),
        (2.0, "2nd"),
        (3.0, "3rd"),
        (4.0, "4th"),
        (11.0, "11th"),
        (12.0, "12th"),
        (13.0, "13th"),
        (21.0, "21st"),
        (22.0, "22nd"),
        (23.0, "23rd"),
    ],
)
def test_format_ordinal(value: float, expected: str) -> None:
    assert indicators._format_ordinal(value) == expected
