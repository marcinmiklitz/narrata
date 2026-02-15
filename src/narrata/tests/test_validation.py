import pandas as pd
import pytest

from narrata.exceptions import ValidationError
from narrata.validation.ohlcv import infer_frequency_label, validate_ohlcv_frame


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
