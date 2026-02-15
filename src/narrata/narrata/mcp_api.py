"""High-level adapters for MCP tools built on top of narrata public APIs.

This module converts row-wise OHLCV records into DataFrames and exposes
high-level helper functions suitable for MCP tool handlers.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date
from typing import Any

import pandas as pd

from narrata.analysis.indicators import analyze_indicators, describe_indicators
from narrata.analysis.patterns import describe_candlestick, describe_patterns, detect_patterns
from narrata.analysis.regimes import analyze_regime, describe_regime
from narrata.analysis.summary import analyze_summary, describe_summary
from narrata.analysis.support_resistance import describe_support_resistance, find_support_resistance
from narrata.analysis.symbolic import astride_encode, describe_astride, describe_sax, sax_encode
from narrata.composition.narrate import narrate
from narrata.exceptions import ValidationError
from narrata.validation.ohlcv import REQUIRED_OHLCV_COLUMNS

_TIMESTAMP_CANDIDATES: tuple[str, ...] = ("timestamp", "datetime", "date", "time")
_COLUMN_CANDIDATES: dict[str, tuple[str, ...]] = {
    "Open": ("Open", "open", "OPEN"),
    "High": ("High", "high", "HIGH"),
    "Low": ("Low", "low", "LOW"),
    "Close": ("Close", "close", "CLOSE"),
    "Volume": ("Volume", "volume", "VOLUME"),
}


def ohlcv_records_to_frame(
    records: list[dict[str, Any]],
    *,
    ticker: str | None = None,
    timestamp_field: str = "timestamp",
    deduplicate_timestamps: bool = True,
    sort_index: bool = True,
) -> pd.DataFrame:
    """Convert OHLCV records into a narrata-ready DataFrame.

    Missing numeric values are allowed and passed through as NaN so narrata
    analytics can handle patchy data gracefully.

    :param records: List of OHLCV row dictionaries.
    :param ticker: Optional ticker symbol attached to ``DataFrame.attrs["ticker"]``.
    :param timestamp_field: Preferred timestamp field name in each record.
    :param deduplicate_timestamps: If ``True``, keep only the latest row for duplicates.
    :param sort_index: If ``True``, sort by timestamp ascending.
    :return: DataFrame indexed by timestamp with canonical OHLCV column names.
    """
    if not records:
        raise ValidationError("At least one OHLCV record is required.")

    raw = pd.DataFrame.from_records(records)
    timestamp_column = _resolve_timestamp_column(raw, preferred=timestamp_field)

    timestamp = pd.to_datetime(raw[timestamp_column], errors="coerce")
    if timestamp.isna().all():
        raise ValidationError(f"Timestamp column '{timestamp_column}' contains no parseable datetime values.")

    frame = raw.copy()
    frame.index = pd.DatetimeIndex(timestamp)
    frame = frame[~frame.index.isna()]

    if deduplicate_timestamps:
        frame = frame[~frame.index.duplicated(keep="last")]
    if sort_index:
        frame = frame.sort_index()

    canonical: dict[str, pd.Series] = {}
    for target in REQUIRED_OHLCV_COLUMNS:
        source = _resolve_ohlcv_column(frame, target)
        canonical[target] = pd.to_numeric(frame[source], errors="coerce")

    result = pd.DataFrame(canonical, index=frame.index)
    if ticker and ticker.strip():
        result.attrs["ticker"] = ticker.strip()
    return result


def narrate_from_records(
    records: list[dict[str, Any]],
    *,
    ticker: str | None = None,
    timestamp_field: str = "timestamp",
    deduplicate_timestamps: bool = True,
    sort_index: bool = True,
    column: str = "Close",
    include_summary: bool = True,
    include_sparkline: bool = True,
    include_regime: bool = True,
    include_indicators: bool = True,
    include_symbolic: bool = True,
    include_patterns: bool = True,
    include_support_resistance: bool = True,
    sparkline_width: int = 20,
    symbolic_word_size: int = 16,
    symbolic_alphabet_size: int = 8,
    digit_level: bool = False,
    output_format: str = "plain",
) -> str:
    """Generate the full narrata text from OHLCV records.

    :param records: List of OHLCV row dictionaries.
    :param ticker: Optional ticker symbol.
    :param timestamp_field: Preferred timestamp field name.
    :param deduplicate_timestamps: Keep only latest row for duplicate timestamps.
    :param sort_index: Sort by timestamp ascending.
    :param column: Price column used across analyzers.
    :param include_summary: Include summary lines.
    :param include_sparkline: Include sparkline in overview.
    :param include_regime: Include regime line.
    :param include_indicators: Include indicator lines.
    :param include_symbolic: Include SAX line.
    :param include_patterns: Include pattern lines.
    :param include_support_resistance: Include support/resistance line.
    :param sparkline_width: Sparkline width.
    :param symbolic_word_size: SAX word size.
    :param symbolic_alphabet_size: SAX alphabet size.
    :param digit_level: Enable digit tokenization in final output.
    :param output_format: Output format (plain, markdown_kv, toon).
    :return: Full narrata output text.
    """
    frame = ohlcv_records_to_frame(
        records,
        ticker=ticker,
        timestamp_field=timestamp_field,
        deduplicate_timestamps=deduplicate_timestamps,
        sort_index=sort_index,
    )
    return narrate(
        frame,
        column=column,
        include_summary=include_summary,
        include_sparkline=include_sparkline,
        include_regime=include_regime,
        include_indicators=include_indicators,
        include_symbolic=include_symbolic,
        include_patterns=include_patterns,
        include_support_resistance=include_support_resistance,
        sparkline_width=sparkline_width,
        symbolic_word_size=symbolic_word_size,
        symbolic_alphabet_size=symbolic_alphabet_size,
        digit_level=digit_level,
        output_format=output_format,  # type: ignore[arg-type]
    )


def summary_from_records(
    records: list[dict[str, Any]],
    *,
    ticker: str | None = None,
    timestamp_field: str = "timestamp",
    deduplicate_timestamps: bool = True,
    sort_index: bool = True,
    column: str = "Close",
) -> dict[str, Any]:
    """Compute summary stats and text from OHLCV records.

    :param records: List of OHLCV row dictionaries.
    :param ticker: Optional ticker symbol.
    :param timestamp_field: Preferred timestamp field name.
    :param deduplicate_timestamps: Keep only latest row for duplicate timestamps.
    :param sort_index: Sort by timestamp ascending.
    :param column: Price column to summarize.
    :return: Dict with ``summary`` (structured) and ``text`` fields.
    """
    frame = ohlcv_records_to_frame(
        records,
        ticker=ticker,
        timestamp_field=timestamp_field,
        deduplicate_timestamps=deduplicate_timestamps,
        sort_index=sort_index,
    )
    stats = analyze_summary(frame, column=column)
    return {"summary": _to_serializable(stats), "text": describe_summary(stats)}


def regime_from_records(
    records: list[dict[str, Any]],
    *,
    ticker: str | None = None,
    timestamp_field: str = "timestamp",
    deduplicate_timestamps: bool = True,
    sort_index: bool = True,
    column: str = "Close",
    window: int = 20,
    penalty: float = 3.0,
    trend_threshold: float = 0.0005,
) -> dict[str, Any]:
    """Compute current regime classification and narration.

    :param records: List of OHLCV row dictionaries.
    :param ticker: Optional ticker symbol.
    :param timestamp_field: Preferred timestamp field name.
    :param deduplicate_timestamps: Keep only latest row for duplicate timestamps.
    :param sort_index: Sort by timestamp ascending.
    :param column: Price column to analyze.
    :param window: Rolling window for fallback regime detection.
    :param penalty: Ruptures penalty parameter when available.
    :param trend_threshold: Mean-return threshold for trend labels.
    :return: Dict with ``regime`` (structured) and ``text`` fields.
    """
    frame = ohlcv_records_to_frame(
        records,
        ticker=ticker,
        timestamp_field=timestamp_field,
        deduplicate_timestamps=deduplicate_timestamps,
        sort_index=sort_index,
    )
    stats = analyze_regime(frame, column=column, window=window, penalty=penalty, trend_threshold=trend_threshold)
    return {"regime": _to_serializable(stats), "text": describe_regime(stats)}


def indicators_from_records(
    records: list[dict[str, Any]],
    *,
    ticker: str | None = None,
    timestamp_field: str = "timestamp",
    deduplicate_timestamps: bool = True,
    sort_index: bool = True,
    column: str = "Close",
    rsi_period: int = 14,
) -> dict[str, Any]:
    """Compute indicator stats and narration from OHLCV records.

    :param records: List of OHLCV row dictionaries.
    :param ticker: Optional ticker symbol.
    :param timestamp_field: Preferred timestamp field name.
    :param deduplicate_timestamps: Keep only latest row for duplicate timestamps.
    :param sort_index: Sort by timestamp ascending.
    :param column: Price column to analyze.
    :param rsi_period: RSI period.
    :return: Dict with ``indicators`` (structured) and ``text`` fields.
    """
    frame = ohlcv_records_to_frame(
        records,
        ticker=ticker,
        timestamp_field=timestamp_field,
        deduplicate_timestamps=deduplicate_timestamps,
        sort_index=sort_index,
    )
    stats = analyze_indicators(frame, column=column, rsi_period=rsi_period)
    return {"indicators": _to_serializable(stats), "text": describe_indicators(stats)}


def sax_from_records(
    records: list[dict[str, Any]],
    *,
    ticker: str | None = None,
    timestamp_field: str = "timestamp",
    deduplicate_timestamps: bool = True,
    sort_index: bool = True,
    column: str = "Close",
    word_size: int = 16,
    alphabet_size: int = 8,
) -> dict[str, Any]:
    """Compute SAX symbols and narration from OHLCV records.

    :param records: List of OHLCV row dictionaries.
    :param ticker: Optional ticker symbol.
    :param timestamp_field: Preferred timestamp field name.
    :param deduplicate_timestamps: Keep only latest row for duplicate timestamps.
    :param sort_index: Sort by timestamp ascending.
    :param column: Price column to encode.
    :param word_size: Number of SAX segments.
    :param alphabet_size: SAX alphabet size.
    :return: Dict with ``symbolic`` (structured) and ``text`` fields.
    """
    frame = ohlcv_records_to_frame(
        records,
        ticker=ticker,
        timestamp_field=timestamp_field,
        deduplicate_timestamps=deduplicate_timestamps,
        sort_index=sort_index,
    )
    stats = sax_encode(frame, column=column, word_size=word_size, alphabet_size=alphabet_size)
    return {"symbolic": _to_serializable(stats), "text": describe_sax(stats)}


def astride_from_records(
    records: list[dict[str, Any]],
    *,
    ticker: str | None = None,
    timestamp_field: str = "timestamp",
    deduplicate_timestamps: bool = True,
    sort_index: bool = True,
    column: str = "Close",
    n_segments: int = 16,
    alphabet_size: int = 8,
    penalty: float = 3.0,
) -> dict[str, Any]:
    """Compute ASTRIDE symbols and narration from OHLCV records.

    :param records: List of OHLCV row dictionaries.
    :param ticker: Optional ticker symbol.
    :param timestamp_field: Preferred timestamp field name.
    :param deduplicate_timestamps: Keep only latest row for duplicate timestamps.
    :param sort_index: Sort by timestamp ascending.
    :param column: Price column to encode.
    :param n_segments: Approximate adaptive segment count.
    :param alphabet_size: Symbol alphabet size.
    :param penalty: Ruptures penalty parameter.
    :return: Dict with ``symbolic`` (structured) and ``text`` fields.
    """
    frame = ohlcv_records_to_frame(
        records,
        ticker=ticker,
        timestamp_field=timestamp_field,
        deduplicate_timestamps=deduplicate_timestamps,
        sort_index=sort_index,
    )
    stats = astride_encode(frame, column=column, n_segments=n_segments, alphabet_size=alphabet_size, penalty=penalty)
    return {"symbolic": _to_serializable(stats), "text": describe_astride(stats)}


def patterns_from_records(
    records: list[dict[str, Any]],
    *,
    ticker: str | None = None,
    timestamp_field: str = "timestamp",
    deduplicate_timestamps: bool = True,
    sort_index: bool = True,
    lookback: int = 60,
) -> dict[str, Any]:
    """Detect chart/candlestick patterns and narration from OHLCV records.

    :param records: List of OHLCV row dictionaries.
    :param ticker: Optional ticker symbol.
    :param timestamp_field: Preferred timestamp field name.
    :param deduplicate_timestamps: Keep only latest row for duplicate timestamps.
    :param sort_index: Sort by timestamp ascending.
    :param lookback: Lookback rows for chart pattern detection.
    :return: Dict with ``patterns`` (structured) and text lines.
    """
    frame = ohlcv_records_to_frame(
        records,
        ticker=ticker,
        timestamp_field=timestamp_field,
        deduplicate_timestamps=deduplicate_timestamps,
        sort_index=sort_index,
    )
    stats = detect_patterns(frame, lookback=lookback)
    return {
        "patterns": _to_serializable(stats),
        "chart_text": describe_patterns(stats),
        "candlestick_text": describe_candlestick(stats),
    }


def levels_from_records(
    records: list[dict[str, Any]],
    *,
    ticker: str | None = None,
    timestamp_field: str = "timestamp",
    deduplicate_timestamps: bool = True,
    sort_index: bool = True,
    column: str = "Close",
    tolerance_ratio: float = 0.01,
    max_levels: int = 2,
    extrema_order: int = 5,
) -> dict[str, Any]:
    """Detect support/resistance levels and narration from OHLCV records.

    :param records: List of OHLCV row dictionaries.
    :param ticker: Optional ticker symbol.
    :param timestamp_field: Preferred timestamp field name.
    :param deduplicate_timestamps: Keep only latest row for duplicate timestamps.
    :param sort_index: Sort by timestamp ascending.
    :param column: Price column to analyze.
    :param tolerance_ratio: Price-band clustering tolerance ratio.
    :param max_levels: Max support/resistance levels to return per side.
    :param extrema_order: Neighborhood size for local extrema.
    :return: Dict with ``levels`` (structured) and ``text`` fields.
    """
    frame = ohlcv_records_to_frame(
        records,
        ticker=ticker,
        timestamp_field=timestamp_field,
        deduplicate_timestamps=deduplicate_timestamps,
        sort_index=sort_index,
    )
    stats = find_support_resistance(
        frame,
        column=column,
        tolerance_ratio=tolerance_ratio,
        max_levels=max_levels,
        extrema_order=extrema_order,
    )
    return {"levels": _to_serializable(stats), "text": describe_support_resistance(stats)}


def _resolve_timestamp_column(frame: pd.DataFrame, preferred: str) -> str:
    candidates = [preferred] + [name for name in _TIMESTAMP_CANDIDATES if name != preferred]
    for candidate in candidates:
        if candidate in frame.columns:
            return candidate
    available = ", ".join(map(str, frame.columns))
    raise ValidationError(
        f"Could not find a timestamp column. Provide '{preferred}' or one of: "
        f"{', '.join(_TIMESTAMP_CANDIDATES)}. Available columns: {available}"
    )


def _resolve_ohlcv_column(frame: pd.DataFrame, target: str) -> str:
    candidates = _COLUMN_CANDIDATES[target]
    for candidate in candidates:
        if candidate in frame.columns:
            return candidate
    raise ValidationError(f"Input records are missing required OHLCV field: '{target}'.")


def _to_serializable(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _to_serializable(asdict(value))
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _to_serializable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_to_serializable(item) for item in value]
    if isinstance(value, list):
        return [_to_serializable(item) for item in value]
    return value
