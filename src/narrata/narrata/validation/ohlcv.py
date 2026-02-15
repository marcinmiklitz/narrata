"""Validation routines for OHLCV time-series DataFrames."""

from collections.abc import Sequence

import pandas as pd

from narrata.exceptions import ValidationError

REQUIRED_OHLCV_COLUMNS: tuple[str, ...] = ("Open", "High", "Low", "Close", "Volume")

_FREQUENCY_LABELS = {
    "B": "business-daily",
    "C": "business-daily",
    "D": "daily",
    "H": "hourly",
    "W": "weekly",
    "ME": "monthly",
    "MS": "monthly",
    "QE": "quarterly",
    "QS": "quarterly",
    "YE": "yearly",
    "YS": "yearly",
}


_VALIDATED_ATTR = "_narrata_validated"


def validate_ohlcv_frame(df: pd.DataFrame, required_columns: Sequence[str] = REQUIRED_OHLCV_COLUMNS) -> None:
    """Validate basic OHLCV and index contracts expected by narrata.

    :param df: Input DataFrame to validate.
    :param required_columns: Required OHLCV columns.
    :return: ``None`` if validation passes.
    """
    if isinstance(df, pd.DataFrame) and df.attrs.get(_VALIDATED_ATTR):
        return

    if not isinstance(df, pd.DataFrame):
        raise ValidationError("Input must be a pandas DataFrame.")

    if df.empty:
        raise ValidationError("Input DataFrame must not be empty.")

    if isinstance(df.index, pd.MultiIndex):
        raise ValidationError(
            "MultiIndex input is not supported. For stacked multi-ticker data, "
            "split by ticker and call narrate per symbol."
        )

    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValidationError("DataFrame index must be a pandas DatetimeIndex.")

    if df.index.has_duplicates:
        raise ValidationError("DataFrame index must not contain duplicate timestamps.")

    if not df.index.is_monotonic_increasing:
        raise ValidationError("DataFrame index must be sorted in ascending order.")

    missing_columns = [name for name in required_columns if name not in df.columns]
    if missing_columns:
        joined = ", ".join(missing_columns)
        raise ValidationError(f"DataFrame is missing required columns: {joined}.")

    df.attrs[_VALIDATED_ATTR] = True


def infer_frequency_label(index: pd.DatetimeIndex) -> str:
    """Infer a user-facing frequency label from a DatetimeIndex.

    :param index: Datetime index.
    :return: Inferred frequency label.
    """
    if len(index) < 2:
        return "irregular"

    inferred = pd.infer_freq(index)
    if inferred:
        key = str(inferred).split("-")[0]
        return _FREQUENCY_LABELS.get(key, key.lower())

    deltas = index.to_series().diff().dropna()
    if deltas.empty:
        return "irregular"

    median_seconds = float(deltas.dt.total_seconds().median())

    if median_seconds <= 3600:
        return "hourly"
    if median_seconds <= 86_400:
        return "daily"
    if median_seconds <= 86_400 * 7:
        return "weekly"
    if median_seconds <= 86_400 * 31:
        return "monthly"
    return "irregular"
