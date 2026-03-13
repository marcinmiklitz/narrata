import numpy as np
import pandas as pd
import pytest

from narrata.composition.compare import compare
from narrata.exceptions import ValidationError


@pytest.fixture
def period_pair() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Two 120-point synthetic periods: downtrend then uptrend."""
    rng = np.random.default_rng(42)

    dates1 = pd.date_range("2024-07-01", periods=120, freq="D")
    base1 = np.linspace(200.0, 170.0, 120)
    close1 = base1 + rng.normal(0.0, 0.8, 120)
    df1 = pd.DataFrame(
        {
            "Open": close1 + rng.normal(0, 0.4, 120),
            "High": close1 + np.abs(rng.normal(0.8, 0.3, 120)),
            "Low": close1 - np.abs(rng.normal(0.8, 0.3, 120)),
            "Close": close1,
            "Volume": rng.integers(1000, 2000, 120),
        },
        index=dates1,
    )
    df1.attrs["ticker"] = "AAPL"

    dates2 = pd.date_range("2025-01-01", periods=120, freq="D")
    base2 = np.linspace(170.0, 210.0, 120)
    close2 = base2 + rng.normal(0.0, 0.8, 120)
    df2 = pd.DataFrame(
        {
            "Open": close2 + rng.normal(0, 0.4, 120),
            "High": close2 + np.abs(rng.normal(0.8, 0.3, 120)),
            "Low": close2 - np.abs(rng.normal(0.8, 0.3, 120)),
            "Close": close2,
            "Volume": rng.integers(1000, 2000, 120),
        },
        index=dates2,
    )
    df2.attrs["ticker"] = "AAPL"

    return df1, df2


def test_compare_plain_output(period_pair: tuple[pd.DataFrame, pd.DataFrame]) -> None:
    df1, df2 = period_pair
    text = compare(df1, df2, ticker="AAPL")
    assert "AAPL:" in text
    assert "\u2192" in text  # arrow
    assert "Price:" in text
    assert "Range:" in text
    assert "Regime:" in text
    assert "RSI(14):" in text
    assert "MACD:" in text
    assert "SAX(" in text
    assert "Support:" in text
    assert "Resistance:" in text


def test_compare_json_output(period_pair: tuple[pd.DataFrame, pd.DataFrame]) -> None:
    import json

    df1, df2 = period_pair
    text = compare(df1, df2, ticker="AAPL", output_format="json")
    data = json.loads(text)
    assert "overview" in data
    assert "price" in data
    assert "\u2192" in data["overview"]


def test_compare_markdown_kv_output(period_pair: tuple[pd.DataFrame, pd.DataFrame]) -> None:
    df1, df2 = period_pair
    text = compare(df1, df2, ticker="AAPL", output_format="markdown_kv")
    assert "**overview**:" in text
    assert "**price**:" in text


def test_compare_disable_sections(period_pair: tuple[pd.DataFrame, pd.DataFrame]) -> None:
    df1, df2 = period_pair
    text = compare(
        df1,
        df2,
        ticker="AAPL",
        include_regime=False,
        include_indicators=False,
        include_symbolic=False,
        include_support_resistance=False,
    )
    assert "Price:" in text
    assert "Range:" in text
    assert "Regime:" not in text
    assert "RSI(" not in text
    assert "SAX(" not in text
    assert "Support:" not in text


def test_compare_currency_symbol(period_pair: tuple[pd.DataFrame, pd.DataFrame]) -> None:
    df1, df2 = period_pair
    text = compare(df1, df2, ticker="AAPL", currency_symbol="$")
    assert "$" in text


def test_compare_precision_zero(period_pair: tuple[pd.DataFrame, pd.DataFrame]) -> None:
    df1, df2 = period_pair
    text = compare(df1, df2, ticker="AAPL", precision=0)
    range_line = [line for line in text.splitlines() if line.startswith("Range:")][0]
    # Prices should have no decimals; the line will contain [ and ] but no dots in prices
    # Remove the arrow portion and check each bracket group
    for bracket in range_line.split("[")[1:]:
        prices_part = bracket.split("]")[0]
        for price in prices_part.split(","):
            price = price.strip()
            assert "." not in price, f"Expected no decimal in price '{price}'"


def test_compare_rejects_missing_column(period_pair: tuple[pd.DataFrame, pd.DataFrame]) -> None:
    df1, df2 = period_pair
    with pytest.raises(ValidationError, match="does not exist"):
        compare(df1, df2, column="AdjustedClose")


def test_compare_short_series_degrades_gracefully() -> None:
    """Short data should silently omit sections, not crash."""
    index1 = pd.date_range("2025-01-01", periods=8, freq="D")
    close1 = pd.Series(range(8), index=index1, dtype=float) * 0.5 + 100.0
    df1 = pd.DataFrame(
        {"Open": close1 - 0.2, "High": close1 + 0.4, "Low": close1 - 0.5, "Close": close1, "Volume": 1000},
        index=index1,
    )

    index2 = pd.date_range("2025-02-01", periods=8, freq="D")
    close2 = pd.Series(range(8), index=index2, dtype=float) * 0.5 + 105.0
    df2 = pd.DataFrame(
        {"Open": close2 - 0.2, "High": close2 + 0.4, "Low": close2 - 0.5, "Close": close2, "Volume": 1000},
        index=index2,
    )

    text = compare(df1, df2, ticker="SHORT")
    assert "SHORT:" in text
    assert "Price:" in text
    # Insufficient-data sections are silently omitted
    assert "Regime" not in text or "insufficient" not in text


def test_compare_with_real_aapl_data(real_aapl_df: pd.DataFrame) -> None:
    """Split real data in half and compare."""
    mid = len(real_aapl_df) // 2
    df1 = real_aapl_df.iloc[:mid]
    df2 = real_aapl_df.iloc[mid:]
    text = compare(df1, df2, ticker="AAPL")
    assert "AAPL:" in text
    assert "Price:" in text
    assert "Regime:" in text
