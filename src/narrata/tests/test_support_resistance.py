import pandas as pd

from narrata.analysis.support_resistance import describe_support_resistance, find_support_resistance


def test_find_support_resistance_returns_levels(sample_ohlcv_df: pd.DataFrame) -> None:
    stats = find_support_resistance(sample_ohlcv_df)
    assert isinstance(stats.supports, tuple)
    assert isinstance(stats.resistances, tuple)


def test_describe_support_resistance_format(sample_ohlcv_df: pd.DataFrame) -> None:
    text = describe_support_resistance(find_support_resistance(sample_ohlcv_df))
    assert text.startswith("Support:")
    assert "Resistance:" in text
