"""Shared public types for narrata."""

from dataclasses import dataclass
from datetime import date
from typing import Literal

OutputFormat = Literal["plain", "markdown_kv", "toon"]


@dataclass(frozen=True, slots=True)
class SummaryStats:
    """Structured output of summary analysis for one series."""

    ticker: str | None
    column: str
    points: int
    frequency: str
    start_date: date
    end_date: date
    start: float
    end: float
    minimum: float
    maximum: float
    mean: float
    std: float
    change_pct: float


@dataclass(frozen=True, slots=True)
class IndicatorStats:
    """Structured output for key technical indicators."""

    rsi_period: int
    rsi_value: float
    rsi_state: str
    macd_value: float
    macd_signal: float
    macd_histogram: float
    macd_state: str
    crossover_days_ago: int | None
    bb_position: str | None = None
    bb_squeeze: bool | None = None
    ma_cross: str | None = None
    ma_cross_days_ago: int | None = None
    volume_ratio: float | None = None
    volume_state: str | None = None
    volatility_percentile: float | None = None
    volatility_state: str | None = None


@dataclass(frozen=True, slots=True)
class RegimeStats:
    """Structured output for current market regime."""

    trend_label: str
    volatility_label: str
    start_date: date


@dataclass(frozen=True, slots=True)
class SymbolicStats:
    """Structured output for symbolic time-series encoding."""

    method: str
    word_size: int
    alphabet_size: int
    symbols: str


@dataclass(frozen=True, slots=True)
class PatternStats:
    """Structured output for detected chart and candlestick patterns."""

    chart_pattern: str | None
    chart_pattern_since: date | None
    candlestick_pattern: str | None
    candlestick_date: date | None


@dataclass(frozen=True, slots=True)
class PriceLevel:
    """Single support or resistance level."""

    price: float
    touches: int


@dataclass(frozen=True, slots=True)
class LevelStats:
    """Structured support and resistance output."""

    supports: tuple[PriceLevel, ...]
    resistances: tuple[PriceLevel, ...]
