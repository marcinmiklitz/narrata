"""Chart pattern and candlestick pattern detection."""

import importlib
from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from narrata.exceptions import ValidationError
from narrata.types import PatternStats
from narrata.validation import validate_ohlcv_frame

ta: Any | None
try:
    importlib.import_module("importlib.metadata")
    import pandas_ta as ta
except ImportError:  # pragma: no cover - optional dependency path
    ta = None


def detect_patterns(df: pd.DataFrame, lookback: int = 60) -> PatternStats:
    """Detect chart and candlestick patterns.

    :param df: OHLCV DataFrame.
    :param lookback: Number of recent rows to inspect for chart patterns.
    :return: Pattern detection result.
    """
    validate_ohlcv_frame(df)
    if lookback < 10:
        raise ValidationError("lookback must be >= 10.")

    chart_pattern, chart_since = detect_chart_pattern(df, lookback=lookback)
    candle_pattern, candle_date = detect_candlestick_pattern(df)
    return PatternStats(
        chart_pattern=chart_pattern,
        chart_pattern_since=chart_since,
        candlestick_pattern=candle_pattern,
        candlestick_date=candle_date,
    )


def detect_chart_pattern(df: pd.DataFrame, lookback: int = 60) -> tuple[str | None, date | None]:
    """Detect simple chart patterns from highs and lows.

    :param df: OHLCV DataFrame.
    :param lookback: Number of recent rows to inspect.
    :return: Pattern name and starting timestamp if detected.
    """
    if "High" not in df.columns or "Low" not in df.columns or "Close" not in df.columns:
        raise ValidationError("DataFrame must contain High, Low and Close columns.")

    window = df.tail(lookback).copy()
    highs = pd.to_numeric(window["High"], errors="coerce").dropna()
    lows = pd.to_numeric(window["Low"], errors="coerce").dropna()
    if highs.size < 5 or lows.size < 5:
        return None, None

    resistance = highs.quantile(0.85)
    high_band = highs[(highs >= resistance * 0.99) & (highs <= resistance * 1.01)]
    if high_band.size < 2:
        return None, None

    low_x = np.arange(lows.size, dtype=float)
    slope, _ = np.polyfit(low_x, lows.to_numpy(dtype=float), 1)
    if slope <= 0:
        return None, None

    start_idx = min(high_band.index.min(), lows.index.min())
    return "Ascending triangle", pd.Timestamp(start_idx).date()


def detect_candlestick_pattern(df: pd.DataFrame) -> tuple[str | None, date | None]:
    """Detect candlestick patterns using optional backend and in-house fallback.

    :param df: OHLCV DataFrame.
    :return: Candlestick pattern name and timestamp if detected.
    """
    for column in ("Open", "Close"):
        if column not in df.columns:
            raise ValidationError("DataFrame must contain Open and Close columns.")
    if df.shape[0] < 2:
        return None, None

    if ta is not None and "High" in df.columns and "Low" in df.columns:
        detected = _detect_candlestick_with_pandas_ta(df)
        if detected[0] is not None:
            return detected

    return _detect_candlestick_inhouse(df)


def _detect_candlestick_with_pandas_ta(df: pd.DataFrame) -> tuple[str | None, date | None]:
    names: list[str] = ["doji", "inside"]
    if bool(getattr(ta, "Imports", {}).get("talib", False)):
        names.append("engulfing")

    patterns = ta.cdl_pattern(  # type: ignore[union-attr]
        pd.to_numeric(df["Open"], errors="coerce"),
        pd.to_numeric(df["High"], errors="coerce"),
        pd.to_numeric(df["Low"], errors="coerce"),
        pd.to_numeric(df["Close"], errors="coerce"),
        name=names,
    )
    if patterns is None or patterns.empty:
        return None, None

    numeric_patterns = patterns.apply(pd.to_numeric, errors="coerce").fillna(0.0)
    recent_hits = numeric_patterns[(numeric_patterns != 0.0).any(axis=1)]
    if recent_hits.empty:
        return None, None

    last_row = recent_hits.iloc[-1]
    pattern_col = next((name for name in last_row.index if float(last_row[name]) != 0.0), None)
    if pattern_col is None:
        return None, None

    score = float(last_row[pattern_col])
    pattern_name = _map_candlestick_name(pattern_col, score=score)
    pattern_date = pd.Timestamp(recent_hits.index[-1]).date()
    return pattern_name, pattern_date


def _map_candlestick_name(pattern_col: str, score: float) -> str:
    name = pattern_col.upper()
    if "ENGULFING" in name:
        return "Bullish Engulfing" if score > 0.0 else "Bearish Engulfing"
    if "DOJI" in name:
        return "Doji"
    if "INSIDE" in name:
        return "Inside Bar"
    normalized = pattern_col.replace("CDL_", "").replace("_", " ").title()
    return normalized


def _detect_candlestick_inhouse(df: pd.DataFrame) -> tuple[str | None, date | None]:
    if "High" not in df.columns or "Low" not in df.columns:
        raise ValidationError("DataFrame must contain High and Low columns for in-house candlestick detection.")
    if df.shape[0] < 2:
        return None, None

    window = df.tail(60)
    open_series = pd.to_numeric(window["Open"], errors="coerce")
    high_series = pd.to_numeric(window["High"], errors="coerce")
    low_series = pd.to_numeric(window["Low"], errors="coerce")
    close_series = pd.to_numeric(window["Close"], errors="coerce")

    doji_threshold = 0.10
    for idx in range(window.shape[0] - 1, 0, -1):
        prev_open = float(open_series.iloc[idx - 1])
        prev_high = float(high_series.iloc[idx - 1])
        prev_low = float(low_series.iloc[idx - 1])
        prev_close = float(close_series.iloc[idx - 1])

        curr_open = float(open_series.iloc[idx])
        curr_high = float(high_series.iloc[idx])
        curr_low = float(low_series.iloc[idx])
        curr_close = float(close_series.iloc[idx])

        # Engulfing patterns first - these are generally stronger signals.
        if prev_close < prev_open and curr_close > curr_open and curr_open <= prev_close and curr_close >= prev_open:
            return "Bullish Engulfing", pd.Timestamp(window.index[idx]).date()

        if prev_close > prev_open and curr_close < curr_open and curr_open >= prev_close and curr_close <= prev_open:
            return "Bearish Engulfing", pd.Timestamp(window.index[idx]).date()

        # Inside bar: current range fully within previous range.
        if curr_high <= prev_high and curr_low >= prev_low:
            return "Inside Bar", pd.Timestamp(window.index[idx]).date()

        # Doji: open and close are very close relative to candle range.
        candle_range = max(curr_high - curr_low, 1e-9)
        body = abs(curr_close - curr_open)
        if body / candle_range <= doji_threshold:
            return "Doji", pd.Timestamp(window.index[idx]).date()

    return None, None


def describe_patterns(stats: PatternStats) -> str:
    """Render chart pattern line.

    :param stats: Pattern detection results.
    :return: Human-readable chart pattern narration.
    """
    if stats.chart_pattern is None or stats.chart_pattern_since is None:
        return "Patterns: none detected"
    return f"Patterns: {stats.chart_pattern} forming since {stats.chart_pattern_since.isoformat()}"


def describe_candlestick(stats: PatternStats) -> str:
    """Render candlestick line.

    :param stats: Pattern detection results.
    :return: Human-readable candlestick narration.
    """
    if stats.candlestick_pattern is None or stats.candlestick_date is None:
        return "Candlestick: none detected"
    return f"Candlestick: {stats.candlestick_pattern} on {stats.candlestick_date.isoformat()}"
