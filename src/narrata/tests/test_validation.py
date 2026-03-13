import pandas as pd
import pytest

from narrata.exceptions import ValidationError
from narrata.validation.ohlcv import infer_frequency_label, normalize_columns, validate_ohlcv_frame


def test_validate_ohlcv_frame_accepts_valid_input(sample_ohlcv_df: pd.DataFrame) -> None:
    validate_ohlcv_frame(sample_ohlcv_df)


def test_validate_ohlcv_frame_rejects_missing_columns(sample_ohlcv_df: pd.DataFrame) -> None:
    missing_close = sample_ohlcv_df.drop(columns=["Close"])
    with pytest.raises(ValidationError, match="missing required columns"):
        validate_ohlcv_frame(missing_close)


def test_validate_ohlcv_frame_rejects_non_datetime_index(sample_ohlcv_df: pd.DataFrame) -> None:
    bad = sample_ohlcv_df.copy()
    bad.index = range(len(bad))
    with pytest.raises(ValidationError, match="DatetimeIndex"):
        validate_ohlcv_frame(bad)


def test_validate_ohlcv_frame_rejects_multiindex_panel(sample_ohlcv_df: pd.DataFrame) -> None:
    panel = sample_ohlcv_df.copy()
    panel.index = pd.MultiIndex.from_arrays(
        [["AAPL"] * len(panel), panel.index],
        names=["Ticker", "Timestamp"],
    )
    with pytest.raises(ValidationError, match="MultiIndex input is not supported"):
        validate_ohlcv_frame(panel)


def test_validate_ohlcv_frame_accepts_patchy_misaligned_values(sample_ohlcv_df: pd.DataFrame) -> None:
    patchy = sample_ohlcv_df.copy()
    patchy.loc[patchy.index[::11], "Close"] = pd.NA
    patchy.loc[patchy.index[1::17], "Open"] = pd.NA
    patchy.loc[patchy.index[2::19], "High"] = pd.NA
    patchy.loc[patchy.index[3::23], "Low"] = pd.NA
    patchy.loc[patchy.index[4::29], "Volume"] = pd.NA

    validate_ohlcv_frame(patchy)


def test_validate_ohlcv_frame_accepts_irregular_gaps(sample_ohlcv_df: pd.DataFrame) -> None:
    gapped = sample_ohlcv_df.drop(index=sample_ohlcv_df.index[[5, 6, 18, 41, 76]])
    validate_ohlcv_frame(gapped)


def test_infer_frequency_label_daily(sample_ohlcv_df: pd.DataFrame) -> None:
    assert infer_frequency_label(sample_ohlcv_df.index) == "daily"


def test_infer_frequency_label_intraday_15min() -> None:
    index = pd.date_range("2025-01-01", periods=16, freq="15min")
    assert infer_frequency_label(index) == "15min"


def test_infer_frequency_label_weekly() -> None:
    index = pd.date_range("2025-01-03", periods=10, freq="W-FRI")
    assert infer_frequency_label(index) == "weekly"


def test_infer_frequency_label_irregular_for_short_index() -> None:
    index = pd.DatetimeIndex([pd.Timestamp("2025-01-01")])
    assert infer_frequency_label(index) == "irregular"


def test_normalize_columns_lowercased(sample_ohlcv_df: pd.DataFrame) -> None:
    lower = sample_ohlcv_df.rename(columns=str.lower)
    result = normalize_columns(lower)
    assert list(result.columns) == ["Open", "High", "Low", "Close", "Volume"]


def test_normalize_columns_adj_close_replaces_close(sample_ohlcv_df: pd.DataFrame) -> None:
    df = sample_ohlcv_df.copy()
    df["Adj Close"] = df["Close"] * 0.98
    result = normalize_columns(df)
    assert "Adj Close" not in result.columns
    assert "Close" in result.columns
    # Adj Close values should have won
    assert result["Close"].iloc[0] == pytest.approx(sample_ohlcv_df["Close"].iloc[0] * 0.98)


def test_normalize_columns_adj_close_only_no_raw_close(sample_ohlcv_df: pd.DataFrame) -> None:
    df = sample_ohlcv_df.drop(columns=["Close"])
    df["adj_close"] = sample_ohlcv_df["Close"]
    result = normalize_columns(df)
    assert "Close" in result.columns


def test_validate_accepts_without_volume(sample_ohlcv_df: pd.DataFrame) -> None:
    no_vol = sample_ohlcv_df.drop(columns=["Volume"])
    validate_ohlcv_frame(no_vol)


def test_narrate_works_without_volume(sample_ohlcv_df: pd.DataFrame) -> None:
    from narrata.composition.narrate import narrate

    no_vol = sample_ohlcv_df.drop(columns=["Volume"])
    text = narrate(no_vol, ticker="TEST")
    assert "TEST" in text


def test_narrate_works_with_lowercase_columns(sample_ohlcv_df: pd.DataFrame) -> None:
    from narrata.composition.narrate import narrate

    lower = sample_ohlcv_df.rename(columns=str.lower)
    text = narrate(lower, ticker="TEST")
    assert "TEST" in text


def test_validate_rejects_non_dataframe() -> None:
    with pytest.raises(ValidationError, match="pandas DataFrame"):
        validate_ohlcv_frame("not a dataframe")  # type: ignore[arg-type]


def test_validate_rejects_empty_dataframe() -> None:
    df = pd.DataFrame(columns=["Open", "High", "Low", "Close"], dtype=float)
    df.index = pd.DatetimeIndex([])
    with pytest.raises(ValidationError, match="must not be empty"):
        validate_ohlcv_frame(df)


def test_validate_rejects_duplicate_timestamps(sample_ohlcv_df: pd.DataFrame) -> None:
    dup = pd.concat([sample_ohlcv_df.head(5), sample_ohlcv_df.head(5)])
    with pytest.raises(ValidationError, match="duplicate timestamps"):
        validate_ohlcv_frame(dup)


def test_validate_rejects_unsorted_index(sample_ohlcv_df: pd.DataFrame) -> None:
    rev = sample_ohlcv_df.iloc[::-1]
    with pytest.raises(ValidationError, match="ascending order"):
        validate_ohlcv_frame(rev)


def test_validate_caches_validated_attr(sample_ohlcv_df: pd.DataFrame) -> None:
    validate_ohlcv_frame(sample_ohlcv_df)
    assert sample_ohlcv_df.attrs.get("_narrata_validated") is True
    # Second call should short-circuit
    validate_ohlcv_frame(sample_ohlcv_df)


def test_infer_frequency_5min() -> None:
    index = pd.date_range("2025-01-01 09:30", periods=20, freq="5min")
    assert infer_frequency_label(index) == "5min"


def test_infer_frequency_1min() -> None:
    index = pd.date_range("2025-01-01 09:30", periods=20, freq="1min")
    assert infer_frequency_label(index) == "1min"


def test_infer_frequency_30min() -> None:
    index = pd.date_range("2025-01-01 09:30", periods=20, freq="30min")
    assert infer_frequency_label(index) == "30min"


def test_infer_frequency_hourly() -> None:
    index = pd.date_range("2025-01-01 09:00", periods=20, freq="h")
    assert infer_frequency_label(index) == "hourly"


def test_infer_frequency_monthly() -> None:
    index = pd.date_range("2024-01-01", periods=10, freq="MS")
    assert infer_frequency_label(index) == "monthly"


def test_infer_frequency_business_daily() -> None:
    index = pd.date_range("2025-01-01", periods=30, freq="B")
    assert infer_frequency_label(index) == "business-daily"


def test_infer_frequency_fallback_median_daily() -> None:
    # Irregular timestamps but ~daily spacing, pandas can't infer freq
    import numpy as np

    rng = np.random.default_rng(42)
    base = pd.date_range("2025-01-01", periods=30, freq="D")
    # Add small random jitter so pd.infer_freq returns None
    jittered = base + pd.to_timedelta(rng.integers(0, 3600, 30), unit="s")
    assert infer_frequency_label(pd.DatetimeIndex(jittered)) == "daily"


def test_infer_frequency_fallback_weekly() -> None:
    # Irregular weekly spacing
    timestamps = pd.to_datetime(["2025-01-01", "2025-01-08", "2025-01-16", "2025-01-22", "2025-01-29"])
    result = infer_frequency_label(pd.DatetimeIndex(timestamps))
    assert result == "weekly"
