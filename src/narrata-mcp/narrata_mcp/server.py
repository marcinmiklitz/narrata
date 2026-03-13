"""FastMCP server exposing narrata high-level tools."""

from __future__ import annotations

from typing import Any, Literal

from fastmcp import FastMCP
from narrata.exceptions import NarrataError
from narrata.mcp_api import (
    astride_from_records,
    compare_from_records,
    indicators_from_records,
    levels_from_records,
    narrate_from_records,
    patterns_from_records,
    regime_from_records,
    sax_from_records,
    summary_from_records,
)
from pydantic import BaseModel, ConfigDict, Field, field_validator

OutputFormat = Literal["plain", "markdown_kv", "toon", "json"]

mcp = FastMCP("narrata_mcp")


class OhlcvPoint(BaseModel):
    """One OHLCV point."""

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True, extra="forbid")

    timestamp: str = Field(description="Timestamp for this row, ISO 8601 string (for example '2025-01-02T15:30:00').")
    open: float | None = Field(default=None, alias="Open", description="Open price.")
    high: float | None = Field(default=None, alias="High", description="High price.")
    low: float | None = Field(default=None, alias="Low", description="Low price.")
    close: float | None = Field(default=None, alias="Close", description="Close price.")
    volume: float | None = Field(default=None, alias="Volume", description="Traded volume.")


class OhlcvPayload(BaseModel):
    """Common OHLCV payload for narrata tools."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    points: list[OhlcvPoint] = Field(
        min_length=2,
        description="Ordered or unordered OHLCV points. Duplicate timestamps are supported.",
    )
    ticker: str | None = Field(default=None, description="Optional ticker symbol (for example AAPL).")
    timestamp_field: str = Field(default="timestamp", description="Timestamp key name in each point.")
    deduplicate_timestamps: bool = Field(
        default=True,
        description="When true, keep only the latest row for duplicate timestamps.",
    )
    sort_index: bool = Field(default=True, description="When true, sort points by timestamp ascending.")

    @field_validator("timestamp_field", mode="before")
    @classmethod
    def validate_timestamp_field(cls, value: Any) -> Any:
        """Validate timestamp field name."""
        if isinstance(value, str) and value.strip():
            return value
        raise ValueError("timestamp_field must be a non-empty string.")


class NarrateInput(OhlcvPayload):
    """Input for full narrate output."""

    column: str = Field(default="Close", description="Price column to analyze.")
    frequency: str | None = Field(
        default=None,
        description="Explicit frequency (e.g. '15min', '5min', 'daily', 'irregular'). Auto-detected when omitted.",
    )
    include_summary: bool = Field(default=True)
    include_sparkline: bool = Field(default=True)
    include_regime: bool = Field(default=True)
    include_indicators: bool = Field(default=True)
    include_symbolic: bool = Field(default=True)
    include_patterns: bool = Field(default=True)
    include_support_resistance: bool = Field(default=True)
    sparkline_width: int = Field(default=20, ge=4, le=80)
    symbolic_method: Literal["sax", "astride"] = Field(default="sax", description="Symbolic encoding method.")
    symbolic_word_size: int = Field(default=16, ge=2, le=64)
    symbolic_alphabet_size: int = Field(default=8, ge=2, le=26)
    symbolic_penalty: float = Field(default=3.0, gt=0.0, le=100.0, description="ASTRIDE ruptures penalty.")
    digit_level: bool = Field(default=False)
    currency_symbol: str = Field(default="", description="Symbol prepended to price values (e.g. '$', '£').")
    precision: int = Field(default=2, ge=0, le=10, description="Decimal places for price values.")
    output_format: OutputFormat = Field(default="plain")
    verbose: bool = Field(default=False, description="Show all sections, including empty or insufficient data.")


class ColumnInput(OhlcvPayload):
    """Input with configurable price column."""

    column: str = Field(default="Close", description="Price column to analyze.")


class IndicatorsInput(ColumnInput):
    """Input for indicator analysis."""

    rsi_period: int = Field(default=14, ge=2, le=200)
    frequency: str | None = Field(
        default=None,
        description="Explicit frequency (e.g. '15min', '5min', 'daily', 'irregular'). Auto-detected when omitted.",
    )


class RegimeInput(ColumnInput):
    """Input for regime analysis."""

    window: int = Field(default=20, ge=5, le=500)
    penalty: float = Field(default=3.0, gt=0.0, le=100.0)
    trend_threshold: float = Field(default=0.0005, ge=0.0, le=1.0)


class SaxInput(ColumnInput):
    """Input for SAX encoding."""

    word_size: int = Field(default=16, ge=2, le=64)
    alphabet_size: int = Field(default=8, ge=2, le=26)


class AstrideInput(ColumnInput):
    """Input for ASTRIDE encoding."""

    n_segments: int = Field(default=16, ge=2, le=128)
    alphabet_size: int = Field(default=8, ge=2, le=26)
    penalty: float = Field(default=3.0, gt=0.0, le=100.0)


class PatternsInput(OhlcvPayload):
    """Input for pattern detection."""

    lookback: int = Field(default=60, ge=10, le=1000)


class LevelsInput(ColumnInput):
    """Input for support/resistance detection."""

    tolerance_ratio: float = Field(default=0.01, gt=0.0, le=0.25)
    max_levels: int = Field(default=2, ge=1, le=10)
    extrema_order: int = Field(default=5, ge=1, le=50)


class CompareInput(BaseModel):
    """Input for comparing two OHLCV periods."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    points_before: list[OhlcvPoint] = Field(min_length=2, description="OHLCV points for the earlier period.")
    points_after: list[OhlcvPoint] = Field(min_length=2, description="OHLCV points for the later period.")
    ticker: str | None = Field(default=None, description="Optional ticker symbol.")
    timestamp_field: str = Field(default="timestamp", description="Timestamp key name in each point.")
    deduplicate_timestamps: bool = Field(default=True)
    sort_index: bool = Field(default=True)
    column: str = Field(default="Close", description="Price column to analyze.")
    frequency: str | None = Field(
        default=None,
        description="Explicit frequency (e.g. '15min', '5min', 'daily', 'irregular'). Auto-detected when omitted.",
    )
    currency_symbol: str = Field(default="", description="Symbol prepended to price values.")
    precision: int = Field(default=2, ge=0, le=10, description="Decimal places for price values.")
    include_regime: bool = Field(default=True)
    include_indicators: bool = Field(default=True)
    include_symbolic: bool = Field(default=True)
    include_support_resistance: bool = Field(default=True)
    symbolic_method: Literal["sax", "astride"] = Field(default="sax")
    symbolic_word_size: int = Field(default=16, ge=2, le=64)
    symbolic_alphabet_size: int = Field(default=8, ge=2, le=26)
    symbolic_penalty: float = Field(default=3.0, gt=0.0, le=100.0)
    output_format: OutputFormat = Field(default="plain")
    verbose: bool = Field(default=False, description="Show all sections, including empty or insufficient data.")

    @field_validator("timestamp_field", mode="before")
    @classmethod
    def validate_timestamp_field(cls, value: Any) -> Any:
        if isinstance(value, str) and value.strip():
            return value
        raise ValueError("timestamp_field must be a non-empty string.")


@mcp.tool(
    name="narrata_compare_ohlcv",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def narrata_compare_ohlcv(params: CompareInput) -> dict[str, Any]:
    """Compare two OHLCV periods and produce a compact diff narrative.

    Useful for answering questions like "how did AAPL change between Q1 and Q2?"

    :param params: Two sets of OHLCV points and comparison settings.
    :return: Dict with one field: ``text``.
    """
    try:
        return {
            "text": compare_from_records(
                _records(params.points_before),
                _records(params.points_after),
                ticker=params.ticker,
                timestamp_field=params.timestamp_field,
                deduplicate_timestamps=params.deduplicate_timestamps,
                sort_index=params.sort_index,
                column=params.column,
                frequency=params.frequency,
                currency_symbol=params.currency_symbol,
                precision=params.precision,
                include_regime=params.include_regime,
                include_indicators=params.include_indicators,
                include_symbolic=params.include_symbolic,
                include_support_resistance=params.include_support_resistance,
                symbolic_method=params.symbolic_method,
                symbolic_word_size=params.symbolic_word_size,
                symbolic_alphabet_size=params.symbolic_alphabet_size,
                symbolic_penalty=params.symbolic_penalty,
                output_format=params.output_format,
                verbose=params.verbose,
            )
        }
    except NarrataError as exc:
        raise ValueError(str(exc)) from exc


@mcp.tool(
    name="narrata_narrate_ohlcv",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def narrata_narrate_ohlcv(params: NarrateInput) -> dict[str, Any]:
    """Generate the full narrata text from OHLCV points.

    Use this as the default entry point when you want one concise, LLM-ready
    narrative string.

    :param params: Narration input parameters and OHLCV points.
    :return: Dict with one field: ``text``.
    """
    try:
        return {
            "text": narrate_from_records(
                _records(params.points),
                ticker=params.ticker,
                timestamp_field=params.timestamp_field,
                deduplicate_timestamps=params.deduplicate_timestamps,
                sort_index=params.sort_index,
                column=params.column,
                frequency=params.frequency,
                include_summary=params.include_summary,
                include_sparkline=params.include_sparkline,
                include_regime=params.include_regime,
                include_indicators=params.include_indicators,
                include_symbolic=params.include_symbolic,
                include_patterns=params.include_patterns,
                include_support_resistance=params.include_support_resistance,
                sparkline_width=params.sparkline_width,
                symbolic_method=params.symbolic_method,
                symbolic_word_size=params.symbolic_word_size,
                symbolic_alphabet_size=params.symbolic_alphabet_size,
                symbolic_penalty=params.symbolic_penalty,
                digit_level=params.digit_level,
                currency_symbol=params.currency_symbol,
                precision=params.precision,
                output_format=params.output_format,
            )
        }
    except NarrataError as exc:
        raise ValueError(str(exc)) from exc


@mcp.tool(
    name="narrata_summary_ohlcv",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def narrata_summary_ohlcv(params: ColumnInput) -> dict[str, Any]:
    """Compute summary stats and summary text from OHLCV points.

    :param params: OHLCV input and summary settings.
    :return: Dict with ``summary`` and ``text``.
    """
    try:
        return summary_from_records(
            _records(params.points),
            ticker=params.ticker,
            timestamp_field=params.timestamp_field,
            deduplicate_timestamps=params.deduplicate_timestamps,
            sort_index=params.sort_index,
            column=params.column,
        )
    except NarrataError as exc:
        raise ValueError(str(exc)) from exc


@mcp.tool(
    name="narrata_regime_ohlcv",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def narrata_regime_ohlcv(params: RegimeInput) -> dict[str, Any]:
    """Compute current regime (trend + volatility) from OHLCV points.

    :param params: OHLCV input and regime settings.
    :return: Dict with ``regime`` and ``text``.
    """
    try:
        return regime_from_records(
            _records(params.points),
            ticker=params.ticker,
            timestamp_field=params.timestamp_field,
            deduplicate_timestamps=params.deduplicate_timestamps,
            sort_index=params.sort_index,
            column=params.column,
            window=params.window,
            penalty=params.penalty,
            trend_threshold=params.trend_threshold,
        )
    except NarrataError as exc:
        raise ValueError(str(exc)) from exc


@mcp.tool(
    name="narrata_indicators_ohlcv",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def narrata_indicators_ohlcv(params: IndicatorsInput) -> dict[str, Any]:
    """Compute indicator stats and indicator narration from OHLCV points.

    :param params: OHLCV input and indicator settings.
    :return: Dict with ``indicators`` and ``text``.
    """
    try:
        return indicators_from_records(
            _records(params.points),
            ticker=params.ticker,
            timestamp_field=params.timestamp_field,
            deduplicate_timestamps=params.deduplicate_timestamps,
            sort_index=params.sort_index,
            column=params.column,
            rsi_period=params.rsi_period,
            frequency=params.frequency,
        )
    except NarrataError as exc:
        raise ValueError(str(exc)) from exc


@mcp.tool(
    name="narrata_symbolic_sax_ohlcv",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def narrata_symbolic_sax_ohlcv(params: SaxInput) -> dict[str, Any]:
    """Compute SAX encoding and SAX narration from OHLCV points.

    :param params: OHLCV input and SAX settings.
    :return: Dict with ``symbolic`` and ``text``.
    """
    try:
        return sax_from_records(
            _records(params.points),
            ticker=params.ticker,
            timestamp_field=params.timestamp_field,
            deduplicate_timestamps=params.deduplicate_timestamps,
            sort_index=params.sort_index,
            column=params.column,
            word_size=params.word_size,
            alphabet_size=params.alphabet_size,
        )
    except NarrataError as exc:
        raise ValueError(str(exc)) from exc


@mcp.tool(
    name="narrata_symbolic_astride_ohlcv",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def narrata_symbolic_astride_ohlcv(params: AstrideInput) -> dict[str, Any]:
    """Compute ASTRIDE encoding and narration from OHLCV points.

    Requires ``ruptures`` support in the runtime environment.

    :param params: OHLCV input and ASTRIDE settings.
    :return: Dict with ``symbolic`` and ``text``.
    """
    try:
        return astride_from_records(
            _records(params.points),
            ticker=params.ticker,
            timestamp_field=params.timestamp_field,
            deduplicate_timestamps=params.deduplicate_timestamps,
            sort_index=params.sort_index,
            column=params.column,
            n_segments=params.n_segments,
            alphabet_size=params.alphabet_size,
            penalty=params.penalty,
        )
    except NarrataError as exc:
        raise ValueError(str(exc)) from exc


@mcp.tool(
    name="narrata_patterns_ohlcv",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def narrata_patterns_ohlcv(params: PatternsInput) -> dict[str, Any]:
    """Detect chart and candlestick patterns from OHLCV points.

    :param params: OHLCV input and lookback settings.
    :return: Dict with ``patterns``, ``chart_text``, and ``candlestick_text``.
    """
    try:
        return patterns_from_records(
            _records(params.points),
            ticker=params.ticker,
            timestamp_field=params.timestamp_field,
            deduplicate_timestamps=params.deduplicate_timestamps,
            sort_index=params.sort_index,
            lookback=params.lookback,
        )
    except NarrataError as exc:
        raise ValueError(str(exc)) from exc


@mcp.tool(
    name="narrata_levels_ohlcv",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def narrata_levels_ohlcv(params: LevelsInput) -> dict[str, Any]:
    """Compute support/resistance levels from OHLCV points.

    :param params: OHLCV input and level settings.
    :return: Dict with ``levels`` and ``text``.
    """
    try:
        return levels_from_records(
            _records(params.points),
            ticker=params.ticker,
            timestamp_field=params.timestamp_field,
            deduplicate_timestamps=params.deduplicate_timestamps,
            sort_index=params.sort_index,
            column=params.column,
            tolerance_ratio=params.tolerance_ratio,
            max_levels=params.max_levels,
            extrema_order=params.extrema_order,
        )
    except NarrataError as exc:
        raise ValueError(str(exc)) from exc


def _records(points: list[OhlcvPoint]) -> list[dict[str, Any]]:
    return [point.model_dump(by_alias=False) for point in points]


def main() -> None:
    """Run the FastMCP server over stdio transport."""
    mcp.run(show_banner=False)


if __name__ == "__main__":
    main()
