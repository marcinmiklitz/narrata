"""Public API for narrata."""

from importlib.metadata import version

from narrata.analysis.indicators import (
    analyze_indicators,
    compute_bollinger,
    compute_ma_crossover,
    compute_macd,
    compute_rsi,
    compute_volatility_percentile,
    compute_volume_state,
    describe_indicators,
)
from narrata.analysis.patterns import (
    describe_candlestick,
    describe_patterns,
    detect_candlestick_pattern,
    detect_chart_pattern,
    detect_patterns,
)
from narrata.analysis.regimes import analyze_regime, describe_regime
from narrata.analysis.summary import analyze_summary, describe_summary
from narrata.analysis.support_resistance import describe_support_resistance, find_support_resistance
from narrata.analysis.symbolic import astride_encode, describe_astride, describe_sax, sax_encode
from narrata.composition.narrate import narrate
from narrata.compression.digits import digit_tokenize
from narrata.exceptions import NarrataError, UnsupportedFormatError, ValidationError
from narrata.formatting.serializers import format_sections, to_markdown_kv, to_plain, to_toon
from narrata.rendering.sparkline import make_sparkline
from narrata.types import (
    IndicatorStats,
    LevelStats,
    OutputFormat,
    PatternStats,
    PriceLevel,
    RegimeStats,
    SummaryStats,
    SymbolicStats,
)
from narrata.validation.ohlcv import infer_frequency_label, validate_ohlcv_frame

__version__ = version("narrata")

__all__ = [
    "IndicatorStats",
    "LevelStats",
    "NarrataError",
    "OutputFormat",
    "PatternStats",
    "PriceLevel",
    "RegimeStats",
    "SummaryStats",
    "SymbolicStats",
    "UnsupportedFormatError",
    "ValidationError",
    "astride_encode",
    "analyze_indicators",
    "analyze_regime",
    "__version__",
    "analyze_summary",
    "compute_bollinger",
    "compute_ma_crossover",
    "compute_macd",
    "compute_rsi",
    "compute_volatility_percentile",
    "compute_volume_state",
    "describe_astride",
    "describe_candlestick",
    "describe_indicators",
    "describe_patterns",
    "describe_regime",
    "describe_sax",
    "describe_summary",
    "describe_support_resistance",
    "detect_candlestick_pattern",
    "detect_chart_pattern",
    "detect_patterns",
    "digit_tokenize",
    "format_sections",
    "find_support_resistance",
    "infer_frequency_label",
    "make_sparkline",
    "narrate",
    "sax_encode",
    "to_markdown_kv",
    "to_plain",
    "to_toon",
    "validate_ohlcv_frame",
]
