import pandas as pd
import pytest

import narrata.analysis.indicators as indicators
from narrata.analysis.indicators import (
    analyze_indicators,
    compute_bollinger,
    compute_ma_crossover,
    compute_macd,
    compute_rsi,
    compute_volatility_percentile,
    compute_volume_state,
    describe_indicators,
)
from narrata.exceptions import ValidationError


def test_compute_rsi_returns_bounded_value(sample_ohlcv_df: pd.DataFrame) -> None:
    value = compute_rsi(sample_ohlcv_df["Close"])
    assert 0.0 <= value <= 100.0


def test_compute_rsi_flat_series_is_neutral() -> None:
    series = pd.Series([100.0] * 20)
    assert compute_rsi(series) == pytest.approx(50.0)


def test_compute_macd_returns_three_values(sample_ohlcv_df: pd.DataFrame) -> None:
    macd, signal, hist = compute_macd(sample_ohlcv_df["Close"])
    assert isinstance(macd, float)
    assert isinstance(signal, float)
    assert isinstance(hist, float)


def test_analyze_indicators_has_states(sample_ohlcv_df: pd.DataFrame) -> None:
    stats = analyze_indicators(sample_ohlcv_df)
    assert stats.rsi_state in {"overbought", "oversold", "neutral-bullish", "neutral-bearish"}
    assert stats.macd_state


def test_analyze_indicators_flat_series_does_not_report_extreme_rsi_or_volatility() -> None:
    index = pd.date_range("2025-01-01", periods=40, freq="D")
    frame = pd.DataFrame({"Close": 100.0}, index=index)

    stats = analyze_indicators(frame)

    assert stats.rsi_value == pytest.approx(50.0)
    assert stats.rsi_state == "neutral-bullish"
    assert stats.volatility_percentile == pytest.approx(50.0)
    assert stats.volatility_state == "moderate"


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


def test_compute_rsi_rejects_small_period() -> None:
    with pytest.raises(ValidationError, match="period must be >= 2"):
        compute_rsi(pd.Series([1.0, 2.0, 3.0]), period=1)


def test_compute_rsi_rejects_insufficient_data() -> None:
    with pytest.raises(ValidationError, match="Not enough data"):
        compute_rsi(pd.Series([1.0, 2.0, 3.0]), period=14)


def test_compute_rsi_fully_rising() -> None:
    series = pd.Series([float(i) for i in range(50)])
    value = compute_rsi(series)
    assert value == pytest.approx(100.0)


def test_compute_macd_rejects_bad_periods() -> None:
    with pytest.raises(ValidationError, match="fast_period must be smaller"):
        compute_macd(pd.Series([1.0] * 100), fast_period=26, slow_period=12)


def test_compute_macd_rejects_insufficient_data() -> None:
    with pytest.raises(ValidationError, match="Not enough data"):
        compute_macd(pd.Series([1.0] * 10))


def test_compute_bollinger_rejects_insufficient_data() -> None:
    with pytest.raises(ValidationError, match="Not enough data"):
        compute_bollinger(pd.Series([1.0] * 5), period=20)


def test_compute_bollinger_flat_series() -> None:
    series = pd.Series([100.0] * 30)
    position, squeeze = compute_bollinger(series)
    assert position == "at midline"


def test_compute_ma_crossover_insufficient_data() -> None:
    cross, days = compute_ma_crossover(pd.Series([1.0] * 50))
    assert cross is None
    assert days is None


def test_compute_volume_state_missing_column() -> None:
    df = pd.DataFrame({"Close": [1.0] * 30}, index=pd.date_range("2025-01-01", periods=30))
    with pytest.raises(ValidationError, match="Volume column"):
        compute_volume_state(df)


def test_compute_volume_state_insufficient_data() -> None:
    df = pd.DataFrame(
        {"Volume": [1000.0] * 5},
        index=pd.date_range("2025-01-01", periods=5),
    )
    with pytest.raises(ValidationError, match="Not enough data"):
        compute_volume_state(df)


def test_compute_volatility_percentile_insufficient_data() -> None:
    with pytest.raises(ValidationError, match="Not enough data"):
        compute_volatility_percentile(pd.Series([1.0] * 10))


def test_analyze_indicators_rejects_missing_column(sample_ohlcv_df: pd.DataFrame) -> None:
    with pytest.raises(ValidationError, match="does not exist"):
        analyze_indicators(sample_ohlcv_df, column="NonExistent")


def test_describe_indicators_with_intraday_bar_units(sample_ohlcv_df: pd.DataFrame) -> None:
    stats = analyze_indicators(sample_ohlcv_df, frequency="15min")
    text = describe_indicators(stats)
    assert "bar" in text.lower()
