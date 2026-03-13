import pandas as pd
import pytest

from narrata.composition.narrate import narrate
from narrata.exceptions import ValidationError


def test_narrate_with_real_aapl_data(real_aapl_df: pd.DataFrame) -> None:
    text = narrate(real_aapl_df, ticker="AAPL")
    assert "AAPL" in text
    assert "Date range:" in text
    assert "Range:" in text
    assert "Regime:" in text
    assert "RSI(14):" in text
    assert "SAX(16):" in text
    assert "Support:" in text


def test_narrate_plain_includes_summary_and_sparkline(sample_ohlcv_df: pd.DataFrame) -> None:
    text = narrate(sample_ohlcv_df)
    assert f"AAPL ({len(sample_ohlcv_df)} pts, daily):" in text
    assert "Date range:" in text
    assert "Range:" in text
    assert "Regime:" in text
    assert "RSI(14):" in text
    assert "SAX(16):" in text
    assert "Support:" in text
    assert "Candlestick:" in text


def test_narrate_markdown_kv_uses_key_value_format(sample_ohlcv_df: pd.DataFrame) -> None:
    text = narrate(sample_ohlcv_df, output_format="markdown_kv")
    assert "**overview**:" in text
    assert "**regime**:" in text
    assert "**indicators**:" in text


def test_narrate_digit_level_tokenizes_output(sample_ohlcv_df: pd.DataFrame) -> None:
    text = narrate(sample_ohlcv_df, include_sparkline=False, digit_level=True, include_patterns=False)
    assert text.startswith("<digits-split>")
    assert "1 2 0" in text
    assert "RSI( 1 4 ):" in text


def test_narrate_requires_at_least_one_component(sample_ohlcv_df: pd.DataFrame) -> None:
    with pytest.raises(ValidationError, match="At least one"):
        narrate(
            sample_ohlcv_df,
            include_summary=False,
            include_sparkline=False,
            include_regime=False,
            include_indicators=False,
            include_symbolic=False,
            include_patterns=False,
            include_support_resistance=False,
        )


def test_narrate_rejects_missing_column(sample_ohlcv_df: pd.DataFrame) -> None:
    with pytest.raises(ValidationError, match="does not exist"):
        narrate(sample_ohlcv_df, column="AdjustedClose")


def test_narrate_handles_patchy_misaligned_data(sample_ohlcv_df: pd.DataFrame) -> None:
    patchy = sample_ohlcv_df.copy()
    patchy.loc[patchy.index[::10], "Close"] = pd.NA
    patchy.loc[patchy.index[1::15], "Open"] = pd.NA
    patchy.loc[patchy.index[2::16], "High"] = pd.NA
    patchy.loc[patchy.index[3::17], "Low"] = pd.NA
    patchy.loc[patchy.index[4::18], "Volume"] = pd.NA
    patchy = patchy.drop(index=patchy.index[[7, 24, 40]])

    text = narrate(patchy)
    assert "Date range:" in text
    assert "Regime:" in text
    assert "RSI(14):" in text
    assert "SAX(16):" in text
    assert "Support:" in text


def test_narrate_intraday_series_is_labeled_intraday() -> None:
    index = pd.date_range("2025-01-01 09:30:00", periods=180, freq="15min")
    close = pd.Series(range(180), index=index, dtype=float) * 0.1 + 100.0
    frame = pd.DataFrame(
        {
            "Open": close - 0.2,
            "High": close + 0.5,
            "Low": close - 0.5,
            "Close": close,
            "Volume": 1_000,
        },
        index=index,
    )
    frame.attrs["ticker"] = "AAPL"

    text = narrate(
        frame,
        include_regime=False,
        include_indicators=False,
        include_symbolic=False,
        include_patterns=False,
        include_support_resistance=False,
    )
    assert "AAPL (180 pts, 15min):" in text


def test_narrate_weekly_series_is_labeled_weekly() -> None:
    index = pd.date_range("2024-01-05", periods=120, freq="W-FRI")
    close = pd.Series(range(120), index=index, dtype=float) * 0.5 + 100.0
    frame = pd.DataFrame(
        {
            "Open": close - 0.3,
            "High": close + 0.7,
            "Low": close - 0.8,
            "Close": close,
            "Volume": 2_000,
        },
        index=index,
    )
    frame.attrs["ticker"] = "AAPL"

    text = narrate(
        frame,
        include_regime=False,
        include_indicators=False,
        include_symbolic=False,
        include_patterns=False,
        include_support_resistance=False,
    )
    assert "AAPL (120 pts, weekly):" in text


def test_narrate_short_series_reports_insufficient_data_in_sensitive_sections() -> None:
    index = pd.date_range("2025-01-01", periods=8, freq="D")
    close = pd.Series(range(8), index=index, dtype=float) * 0.5 + 100.0
    frame = pd.DataFrame(
        {
            "Open": close - 0.2,
            "High": close + 0.4,
            "Low": close - 0.5,
            "Close": close,
            "Volume": 1_000,
        },
        index=index,
    )

    text = narrate(frame, ticker="AAPL")
    assert "Date range:" in text
    # Insufficient-data sections are silently omitted
    assert "Regime" not in text
    assert "RSI" not in text
    assert "SAX" not in text
    assert "Support" not in text


def test_narrate_one_month_series_does_not_raise_and_marks_indicators_insufficient() -> None:
    index = pd.date_range("2025-01-01", periods=22, freq="B")
    close = pd.Series(range(22), index=index, dtype=float) * 0.4 + 150.0
    frame = pd.DataFrame(
        {
            "Open": close - 0.1,
            "High": close + 0.5,
            "Low": close - 0.6,
            "Close": close,
            "Volume": 1_250,
        },
        index=index,
    )

    text = narrate(frame, ticker="AAPL")
    assert "AAPL (22 pts, business-daily):" in text
    # Indicators section silently omitted for short series
    assert "RSI" not in text


def test_narrate_json_output(sample_ohlcv_df: pd.DataFrame) -> None:
    import json

    text = narrate(sample_ohlcv_df, ticker="AAPL", output_format="json")
    data = json.loads(text)
    assert "overview" in data
    assert "AAPL" in data["overview"]


def test_narrate_precision_zero(sample_ohlcv_df: pd.DataFrame) -> None:
    text = narrate(sample_ohlcv_df, ticker="AAPL", precision=0)
    assert "Range: [" in text
    # No decimal points in the Range line
    range_line = [line for line in text.splitlines() if line.startswith("Range:")][0]
    assert "." not in range_line


def test_narrate_currency_symbol(sample_ohlcv_df: pd.DataFrame) -> None:
    text = narrate(sample_ohlcv_df, ticker="AAPL", currency_symbol="£")
    assert "£" in text


def test_narrate_astride_method(sample_ohlcv_df: pd.DataFrame) -> None:
    text = narrate(sample_ohlcv_df, symbolic_method="astride")
    assert "ASTRIDE(" in text
    assert "SAX(" not in text
