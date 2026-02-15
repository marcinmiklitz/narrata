"""Numerical analysis primitives for narrata."""

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

__all__ = [
    "astride_encode",
    "analyze_indicators",
    "analyze_regime",
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
    "find_support_resistance",
    "sax_encode",
]
