"""Side-by-side period comparison narrative."""

import pandas as pd

from narrata.analysis.indicators import analyze_indicators
from narrata.analysis.regimes import analyze_regime
from narrata.analysis.summary import analyze_summary
from narrata.analysis.support_resistance import find_support_resistance
from narrata.analysis.symbolic import astride_encode, describe_astride, describe_sax, sax_encode
from narrata.exceptions import ValidationError
from narrata.formatting.serializers import format_sections
from narrata.types import OutputFormat
from narrata.validation.ohlcv import normalize_columns, validate_ohlcv_frame


def _fmt_price(value: float, currency_symbol: str, precision: int) -> str:
    return f"{currency_symbol}{value:.{precision}f}"


def _regime_short(df: pd.DataFrame, column: str) -> str:
    """Return compact regime label like 'Uptrend (low vol)'."""
    try:
        stats = analyze_regime(df, column=column)
        return f"{stats.trend_label} ({stats.volatility_label} vol)"
    except ValidationError:
        return "insufficient data"


def _indicators_short(df: pd.DataFrame, column: str) -> dict[str, str]:
    """Return compact indicator snippets."""
    try:
        stats = analyze_indicators(df, column=column)
        parts: dict[str, str] = {}
        parts["rsi"] = f"{stats.rsi_value:.1f} ({stats.rsi_state})"
        parts["macd"] = stats.macd_state
        if stats.volume_state is not None and stats.volume_ratio is not None:
            parts["volume"] = f"{stats.volume_ratio:.2f}x avg ({stats.volume_state})"
        if stats.volatility_percentile is not None and stats.volatility_state is not None:
            parts["volatility"] = f"{stats.volatility_percentile:.0f}th pctl ({stats.volatility_state})"
        return parts
    except ValidationError:
        return {"rsi": "insufficient data", "macd": "insufficient data"}


def _symbolic_short(
    df: pd.DataFrame,
    column: str,
    method: str,
    word_size: int,
    alphabet_size: int,
    penalty: float,
) -> str:
    """Return compact symbolic label."""
    try:
        if method == "astride":
            stats = astride_encode(
                df, column=column, n_segments=word_size, alphabet_size=alphabet_size, penalty=penalty
            )
            return describe_astride(stats)
        stats = sax_encode(df, column=column, word_size=word_size, alphabet_size=alphabet_size)
        return describe_sax(stats)
    except ValidationError:
        label = "ASTRIDE" if method == "astride" else f"SAX({word_size})"
        return f"{label}: insufficient data"


def _levels_short(df: pd.DataFrame, column: str, currency_symbol: str, precision: int) -> tuple[str, str]:
    """Return (support_str, resistance_str)."""
    try:
        levels = find_support_resistance(df, column=column)
        sup = ", ".join(_fmt_price(lv.price, currency_symbol, precision) for lv in levels.supports) or "none"
        res = ", ".join(_fmt_price(lv.price, currency_symbol, precision) for lv in levels.resistances) or "none"
        return sup, res
    except ValidationError:
        return "insufficient data", "insufficient data"


def compare(
    df_before: pd.DataFrame,
    df_after: pd.DataFrame,
    *,
    column: str = "Close",
    ticker: str | None = None,
    currency_symbol: str = "",
    precision: int = 2,
    include_regime: bool = True,
    include_indicators: bool = True,
    include_symbolic: bool = True,
    include_support_resistance: bool = True,
    symbolic_method: str = "sax",
    symbolic_word_size: int = 16,
    symbolic_alphabet_size: int = 8,
    symbolic_penalty: float = 3.0,
    output_format: OutputFormat = "plain",
) -> str:
    """Compare two time periods and produce a compact diff narrative.

    :param df_before: OHLCV DataFrame for the earlier period.
    :param df_after: OHLCV DataFrame for the later period.
    :param column: Price column used across modules.
    :param ticker: Optional ticker override.
    :param currency_symbol: Symbol prepended to price values.
    :param precision: Decimal places for price values.
    :param include_regime: Include regime comparison.
    :param include_indicators: Include indicator comparison.
    :param include_symbolic: Include symbolic comparison.
    :param include_support_resistance: Include support/resistance comparison.
    :param symbolic_method: Symbolic encoding method ('sax' or 'astride').
    :param symbolic_word_size: SAX word size / ASTRIDE segments.
    :param symbolic_alphabet_size: Symbol alphabet size.
    :param symbolic_penalty: ASTRIDE ruptures penalty.
    :param output_format: Output format.
    :return: Compact diff narrative text.
    """
    df_before = normalize_columns(df_before)
    df_after = normalize_columns(df_after)
    validate_ohlcv_frame(df_before)
    validate_ohlcv_frame(df_after)

    for label, df in [("before", df_before), ("after", df_after)]:
        if column not in df.columns:
            raise ValidationError(f"Column '{column}' does not exist in {label} DataFrame.")

    sum_a = analyze_summary(df_before, column=column, ticker=ticker)
    sum_b = analyze_summary(df_after, column=column, ticker=ticker)
    cs = currency_symbol
    p = precision

    entity = sum_a.ticker or sum_b.ticker or sum_a.column

    sections: dict[str, str] = {}

    # Header
    sections["overview"] = (
        f"{entity}: {sum_a.start_date.isoformat()}..{sum_a.end_date.isoformat()}"
        f" \u2192 {sum_b.start_date.isoformat()}..{sum_b.end_date.isoformat()}"
    )

    # Price change
    delta = sum_b.end - sum_a.end
    delta_pct = (delta / sum_a.end * 100) if sum_a.end != 0 else 0.0
    sign = "+" if delta_pct >= 0 else ""
    sections["price"] = (
        f"Price: {_fmt_price(sum_a.end, cs, p)} \u2192 {_fmt_price(sum_b.end, cs, p)} ({sign}{delta_pct:.1f}%)"
    )

    # Range
    sections["range"] = (
        f"Range: [{_fmt_price(sum_a.minimum, cs, p)}, {_fmt_price(sum_a.maximum, cs, p)}]"
        f" \u2192 [{_fmt_price(sum_b.minimum, cs, p)}, {_fmt_price(sum_b.maximum, cs, p)}]"
    )

    if include_regime:
        ra = _regime_short(df_before, column)
        rb = _regime_short(df_after, column)
        sections["regime"] = f"Regime: {ra} \u2192 {rb}"

    if include_indicators:
        ia = _indicators_short(df_before, column)
        ib = _indicators_short(df_after, column)
        sections["rsi"] = f"RSI(14): {ia['rsi']} \u2192 {ib['rsi']}"
        sections["macd"] = f"MACD: {ia['macd']} \u2192 {ib['macd']}"
        if "volume" in ia and "volume" in ib:
            sections["volume"] = f"Volume: {ia['volume']} \u2192 {ib['volume']}"
        if "volatility" in ia and "volatility" in ib:
            sections["volatility"] = f"Volatility: {ia['volatility']} \u2192 {ib['volatility']}"

    if include_symbolic:
        sa = _symbolic_short(
            df_before, column, symbolic_method, symbolic_word_size, symbolic_alphabet_size, symbolic_penalty
        )
        sb = _symbolic_short(
            df_after, column, symbolic_method, symbolic_word_size, symbolic_alphabet_size, symbolic_penalty
        )
        sections["symbolic"] = f"{sa} \u2192 {sb}"

    if include_support_resistance:
        sup_a, res_a = _levels_short(df_before, column, cs, p)
        sup_b, res_b = _levels_short(df_after, column, cs, p)
        sections["support"] = f"Support: {sup_a} \u2192 {sup_b}"
        sections["resistance"] = f"Resistance: {res_a} \u2192 {res_b}"

    return format_sections(sections, output_format=output_format)
