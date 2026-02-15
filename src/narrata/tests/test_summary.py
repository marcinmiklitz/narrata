import math

import pandas as pd
import pytest

from narrata.analysis.summary import analyze_summary, describe_summary
from narrata.exceptions import ValidationError


def test_analyze_summary_computes_expected_values(sample_ohlcv_df: pd.DataFrame) -> None:
    stats = analyze_summary(sample_ohlcv_df)
    assert stats.ticker == "AAPL"
    assert stats.points == len(sample_ohlcv_df)
    assert stats.frequency == "daily"
    close = sample_ohlcv_df["Close"].astype(float)
    assert stats.start_date == sample_ohlcv_df.index[0].date()
    assert stats.end_date == sample_ohlcv_df.index[-1].date()
    assert stats.start == pytest.approx(float(close.iloc[0]))
    assert stats.end == pytest.approx(float(close.iloc[-1]))
    assert stats.minimum == pytest.approx(float(close.min()))
    assert stats.maximum == pytest.approx(float(close.max()))
    assert stats.mean == pytest.approx(float(close.mean()))
    assert stats.std == pytest.approx(float(close.std(ddof=0)))


def test_analyze_summary_prefers_explicit_ticker(sample_ohlcv_df: pd.DataFrame) -> None:
    stats = analyze_summary(sample_ohlcv_df, ticker="MSFT")
    assert stats.ticker == "MSFT"


def test_analyze_summary_rejects_missing_column(sample_ohlcv_df: pd.DataFrame) -> None:
    with pytest.raises(ValidationError, match="does not exist"):
        analyze_summary(sample_ohlcv_df, column="AdjustedClose")


def test_describe_summary_formats_compact_text(sample_ohlcv_df: pd.DataFrame) -> None:
    stats = analyze_summary(sample_ohlcv_df)
    text = describe_summary(stats)
    assert f"AAPL ({len(sample_ohlcv_df)} pts, daily)" in text
    assert "Range: [$" in text
    assert "Change:" in text


def test_describe_summary_handles_nan_change(sample_ohlcv_df: pd.DataFrame) -> None:
    modified = sample_ohlcv_df.copy().astype({"Close": float})
    modified.loc[:, "Close"] = [0.0] + [float(i) for i in range(1, len(modified))]
    text = describe_summary(analyze_summary(modified))
    assert "Change: n/a" in text
    assert math.isnan(analyze_summary(modified).change_pct)


def test_describe_summary_without_header(sample_ohlcv_df: pd.DataFrame) -> None:
    text = describe_summary(analyze_summary(sample_ohlcv_df), include_header=False)
    assert text.startswith("Range:")
