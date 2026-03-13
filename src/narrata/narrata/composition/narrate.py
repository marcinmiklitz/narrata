"""High-level narration composition for LLM-ready text."""

import pandas as pd

from narrata.analysis.indicators import analyze_indicators, describe_indicators
from narrata.analysis.patterns import describe_candlestick, describe_patterns, detect_patterns
from narrata.analysis.regimes import analyze_regime, describe_regime
from narrata.analysis.summary import analyze_summary, describe_summary
from narrata.analysis.support_resistance import describe_support_resistance, find_support_resistance
from narrata.analysis.symbolic import astride_encode, describe_astride, describe_sax, sax_encode
from narrata.compression.digits import digit_tokenize
from narrata.exceptions import ValidationError
from narrata.formatting.serializers import format_sections
from narrata.rendering.sparkline import make_sparkline
from narrata.types import OutputFormat
from narrata.validation.ohlcv import normalize_columns, validate_ohlcv_frame


def narrate(
    df: pd.DataFrame,
    *,
    column: str = "Close",
    ticker: str | None = None,
    frequency: str | None = None,
    include_summary: bool = True,
    include_sparkline: bool = True,
    include_regime: bool = True,
    include_indicators: bool = True,
    include_symbolic: bool = True,
    include_patterns: bool = True,
    include_support_resistance: bool = True,
    sparkline_width: int = 20,
    symbolic_method: str = "sax",
    symbolic_word_size: int = 16,
    symbolic_alphabet_size: int = 8,
    symbolic_penalty: float = 3.0,
    digit_level: bool = False,
    currency_symbol: str = "",
    precision: int = 2,
    output_format: OutputFormat = "plain",
    verbose: bool = False,
) -> str:
    """Compose selected narration components into one final text output.

    :param df: OHLCV DataFrame.
    :param column: Price column used across modules.
    :param ticker: Optional ticker override.
    :param frequency: Explicit frequency label (e.g. ``"15min"``, ``"daily"``).
        When ``None``, frequency is auto-detected from the index.
    :param include_summary: Include summary lines.
    :param include_sparkline: Include sparkline in overview line.
    :param include_regime: Include regime classification line.
    :param include_indicators: Include indicators line.
    :param include_symbolic: Include SAX line.
    :param include_patterns: Include chart and candlestick pattern lines.
    :param include_support_resistance: Include support/resistance line.
    :param sparkline_width: Sparkline width.
    :param symbolic_method: Symbolic encoding method ('sax' or 'astride').
    :param symbolic_word_size: SAX word size / ASTRIDE n_segments.
    :param symbolic_alphabet_size: Symbol alphabet size.
    :param symbolic_penalty: ASTRIDE ruptures penalty (ignored for SAX).
    :param digit_level: Apply digit-level tokenization to final text.
    :param currency_symbol: Symbol prepended to price values (default: none).
    :param precision: Decimal places for price values (default: 2).
    :param output_format: Output format.
    :param verbose: Show all sections even when empty or insufficient data.
    :return: Composed narration text.
    """
    df = normalize_columns(df)
    validate_ohlcv_frame(df, required_columns=("Close",))

    if column not in df.columns:
        raise ValidationError(f"Column '{column}' does not exist in DataFrame.")

    if not any(
        [
            include_summary,
            include_sparkline,
            include_regime,
            include_indicators,
            include_symbolic,
            include_patterns,
            include_support_resistance,
        ]
    ):
        raise ValidationError("At least one narration component must be enabled.")

    sections: dict[str, str] = {}
    summary = analyze_summary(df, column=column, ticker=ticker, frequency=frequency)

    if include_summary or include_sparkline:
        entity_name = summary.ticker or summary.column
        if include_sparkline:
            values = pd.to_numeric(df[column], errors="coerce").dropna().tolist()
            if not values:
                raise ValidationError(f"Column '{column}' contains no numeric values for sparkline rendering.")
            sparkline = make_sparkline(values, width=sparkline_width)
            sections["overview"] = f"{entity_name} ({summary.points} pts, {summary.frequency}): {sparkline}"
        else:
            sections["overview"] = f"{entity_name} ({summary.points} pts, {summary.frequency})"

    if include_summary:
        sections["date_range"] = f"Date range: {summary.start_date.isoformat()} to {summary.end_date.isoformat()}"
        summary_lines = describe_summary(
            summary, currency_symbol=currency_symbol, precision=precision, include_header=False
        ).splitlines()
        sections["range"] = summary_lines[0]
        sections["change"] = summary_lines[1]

    if include_regime:
        try:
            sections["regime"] = describe_regime(analyze_regime(df, column=column))
        except ValidationError:
            if verbose:
                sections["regime"] = "Regime: insufficient data"

    if include_indicators:
        try:
            sections["indicators"] = describe_indicators(
                analyze_indicators(df, column=column, frequency=summary.frequency)
            )
        except ValidationError:
            if verbose:
                sections["indicators"] = "Indicators: insufficient data"

    if include_symbolic:
        try:
            if symbolic_method == "astride":
                try:
                    symbolic = astride_encode(
                        df,
                        column=column,
                        n_segments=symbolic_word_size,
                        alphabet_size=symbolic_alphabet_size,
                        penalty=symbolic_penalty,
                    )
                    sections["symbolic"] = describe_astride(symbolic)
                except ValidationError:
                    # Fall back to SAX when ASTRIDE unavailable (e.g. ruptures missing on 3.14+)
                    symbolic = sax_encode(
                        df,
                        column=column,
                        word_size=symbolic_word_size,
                        alphabet_size=symbolic_alphabet_size,
                    )
                    sections["symbolic"] = describe_sax(symbolic)
            else:
                symbolic = sax_encode(
                    df,
                    column=column,
                    word_size=symbolic_word_size,
                    alphabet_size=symbolic_alphabet_size,
                )
                sections["symbolic"] = describe_sax(symbolic)
        except ValidationError:
            if verbose:
                sections["symbolic"] = f"SAX({symbolic_word_size}): insufficient data"

    if include_patterns:
        try:
            pattern_stats = detect_patterns(df)
            pat = describe_patterns(pattern_stats)
            cand = describe_candlestick(pattern_stats)
            if pat is not None or verbose:
                sections["patterns"] = pat or "Patterns: none detected"
            if cand is not None or verbose:
                sections["candlestick"] = cand or "Candlestick: none detected"
        except ValidationError:
            if verbose:
                sections["patterns"] = "Patterns: insufficient data"
                sections["candlestick"] = "Candlestick: insufficient data"

    if include_support_resistance:
        try:
            levels = find_support_resistance(df, column=column)
            sections["levels"] = describe_support_resistance(
                levels, currency_symbol=currency_symbol, precision=precision
            )
        except ValidationError:
            if verbose:
                sections["levels"] = "Support: insufficient data  Resistance: insufficient data"

    rendered = format_sections(sections, output_format=output_format)
    if digit_level:
        return digit_tokenize(rendered)

    return rendered
