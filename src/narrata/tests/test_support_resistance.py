import pandas as pd
import pytest

from narrata.analysis.support_resistance import describe_support_resistance, find_support_resistance
from narrata.exceptions import ValidationError


def test_find_support_resistance_returns_levels(sample_ohlcv_df: pd.DataFrame) -> None:
    stats = find_support_resistance(sample_ohlcv_df)
    assert isinstance(stats.supports, tuple)
    assert isinstance(stats.resistances, tuple)


def test_describe_support_resistance_format(sample_ohlcv_df: pd.DataFrame) -> None:
    text = describe_support_resistance(find_support_resistance(sample_ohlcv_df))
    assert text.startswith("Support:")
    assert "Resistance:" in text


def test_find_support_resistance_rejects_missing_column(sample_ohlcv_df: pd.DataFrame) -> None:
    with pytest.raises(ValidationError, match="does not exist"):
        find_support_resistance(sample_ohlcv_df, column="NonExistent")


def test_find_support_resistance_rejects_bad_tolerance(sample_ohlcv_df: pd.DataFrame) -> None:
    with pytest.raises(ValidationError, match="tolerance_ratio must be > 0"):
        find_support_resistance(sample_ohlcv_df, tolerance_ratio=0.0)


def test_find_support_resistance_rejects_bad_max_levels(sample_ohlcv_df: pd.DataFrame) -> None:
    with pytest.raises(ValidationError, match="max_levels must be >= 1"):
        find_support_resistance(sample_ohlcv_df, max_levels=0)


def test_find_support_resistance_rejects_bad_extrema_order(sample_ohlcv_df: pd.DataFrame) -> None:
    with pytest.raises(ValidationError, match="extrema_order must be >= 1"):
        find_support_resistance(sample_ohlcv_df, extrema_order=0)


def test_find_support_resistance_insufficient_data() -> None:
    index = pd.date_range("2025-01-01", periods=5, freq="D")
    df = pd.DataFrame({"Close": [100.0, 101.0, 102.0, 103.0, 104.0]}, index=index)
    with pytest.raises(ValidationError, match="Not enough data"):
        find_support_resistance(df)
