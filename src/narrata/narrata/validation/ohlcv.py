"""Validation routines for OHLCV time-series DataFrames."""

from collections.abc import Sequence

import pandas as pd

from narrata.exceptions import ValidationError

REQUIRED_OHLCV_COLUMNS: tuple[str, ...] = ("Open", "High", "Low", "Close", "Volume")
REQUIRED_OHLC_COLUMNS: tuple[str, ...] = ("Open", "High", "Low", "Close")

# Lowercase lookup → canonical name.  "adj close" variants map to Close and
# take priority over a raw "close" column when both exist.
_CANONICAL: dict[str, str] = {
    "open": "Open",
    "high": "High",
    "low": "Low",
    "close": "Close",
    "volume": "Volume",
}
_ADJ_CLOSE_VARIANTS: set[str] = {"adj close", "adj_close", "adjusted close"}

_FREQUENCY_LABELS = {
    "B": "business-daily",
    "C": "business-daily",
    "D": "daily",
    "h": "hourly",
    "H": "hourly",
    "W": "weekly",
    "ME": "monthly",
    "MS": "monthly",
    "QE": "quarterly",
    "QS": "quarterly",
    "YE": "yearly",
    "YS": "yearly",
    "min": "minutely",
    "T": "minutely",
}

# Frequencies considered intraday (sub-daily).
INTRADAY_FREQUENCIES: frozenset[str] = frozenset({"1min", "5min", "15min", "30min", "hourly", "minutely"})

# All recognized frequency labels (for validation of user-supplied values).
VALID_FREQUENCIES: frozenset[str] = frozenset(
    {
        "1min",
        "5min",
        "15min",
        "30min",
        "minutely",
        "hourly",
        "daily",
        "business-daily",
        "weekly",
        "monthly",
        "quarterly",
        "yearly",
        "irregular",
    }
)

# Frequencies that should use generic "bar" units instead of "day".
BAR_UNIT_FREQUENCIES: frozenset[str] = INTRADAY_FREQUENCIES | {"irregular"}


_VALIDATED_ATTR = "_narrata_validated"


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns to canonical OHLCV names in-place where possible.

    * Case-insensitive: ``open`` → ``Open``, ``volume`` → ``Volume``, etc.
    * ``Adj Close`` / ``Adj_Close`` / ``Adjusted Close`` → ``Close``
      (takes priority over a raw ``close`` column when both exist).
    * Unrecognized columns are left untouched.

    :param df: Input DataFrame (modified in-place via ``rename``).
    :return: The same DataFrame with canonical column names.
    """
    rename_map: dict[str, str] = {}
    has_adj_close = False

    for col in df.columns:
        lower = col.lower().strip()
        if lower in _ADJ_CLOSE_VARIANTS:
            rename_map[col] = "Close"
            has_adj_close = True
        elif lower in _CANONICAL:
            rename_map[col] = _CANONICAL[lower]

    # If adj close exists alongside a raw close, drop the raw close first.
    if has_adj_close:
        raw_close_cols = [
            c for c, target in rename_map.items() if target == "Close" and c.lower().strip() not in _ADJ_CLOSE_VARIANTS
        ]
        if raw_close_cols:
            df = df.drop(columns=raw_close_cols)
            for col in raw_close_cols:
                del rename_map[col]

    df = df.rename(columns=rename_map)
    return df


def validate_ohlcv_frame(df: pd.DataFrame, required_columns: Sequence[str] = REQUIRED_OHLC_COLUMNS) -> None:
    """Validate basic OHLCV and index contracts expected by narrata.

    Columns are normalized first (case-insensitive, adj-close handling).
    Only OHLC columns are required; Volume is optional.

    :param df: Input DataFrame to validate.
    :param required_columns: Required columns (default: OHLC only).
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


def is_intraday(frequency: str) -> bool:
    """Return True if the frequency label represents sub-daily bars."""
    return frequency in INTRADAY_FREQUENCIES


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
        # Handle sub-hourly pandas codes like "5min", "15min", "min".
        if key.endswith("min"):
            prefix = key[: -len("min")]
            if prefix == "" or prefix == "1":
                return "1min"
            return f"{prefix}min"
        if key.endswith("T"):
            prefix = key[:-1]
            if prefix == "" or prefix == "1":
                return "1min"
            return f"{prefix}min"
        return _FREQUENCY_LABELS.get(key, key.lower())

    deltas = index.to_series().diff().dropna()
    if deltas.empty:
        return "irregular"

    median_seconds = float(deltas.dt.total_seconds().median())

    if median_seconds <= 120:
        return "1min"
    if median_seconds <= 600:
        return "5min"
    if median_seconds <= 1200:
        return "15min"
    if median_seconds <= 2400:
        return "30min"
    if median_seconds <= 3600:
        return "hourly"
    if median_seconds <= 86_400:
        return "daily"
    if median_seconds <= 86_400 * 7:
        return "weekly"
    if median_seconds <= 86_400 * 31:
        return "monthly"
    return "irregular"
