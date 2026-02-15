"""High-level narration composition for LLM-ready text."""

import pandas as pd

from narrata.analysis.indicators import analyze_indicators, describe_indicators
from narrata.analysis.patterns import describe_candlestick, describe_patterns, detect_patterns
from narrata.analysis.regimes import analyze_regime, describe_regime
from narrata.analysis.summary import analyze_summary, describe_summary
from narrata.analysis.support_resistance import describe_support_resistance, find_support_resistance
from narrata.analysis.symbolic import describe_sax, sax_encode
from narrata.compression.digits import digit_tokenize
from narrata.exceptions import ValidationError
from narrata.formatting.serializers import format_sections
from narrata.rendering.sparkline import make_sparkline
from narrata.types import OutputFormat
from narrata.validation.ohlcv import validate_ohlcv_frame


def narrate(
    df: pd.DataFrame,
    *,
    column: str = "Close",
    ticker: str | None = None,
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
    output_format: OutputFormat = "plain",
) -> str:
    """Compose selected narration components into one final text output.

    :param df: OHLCV DataFrame.
    :param column: Price column used across modules.
    :param ticker: Optional ticker override.
    :param include_summary: Include summary lines.
    :param include_sparkline: Include sparkline in overview line.
    :param include_regime: Include regime classification line.
    :param include_indicators: Include indicators line.
    :param include_symbolic: Include SAX line.
    :param include_patterns: Include chart and candlestick pattern lines.
    :param include_support_resistance: Include support/resistance line.
    :param sparkline_width: Sparkline width.
    :param symbolic_word_size: SAX word size.
    :param symbolic_alphabet_size: SAX alphabet size.
    :param digit_level: Apply digit-level tokenization to final text.
    :param output_format: Output format.
    :return: Composed narration text.
    """
    validate_ohlcv_frame(df)

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
    summary = analyze_summary(df, column=column, ticker=ticker)

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
        summary_lines = describe_summary(summary, include_header=False).splitlines()
        sections["range"] = summary_lines[0]
        sections["change"] = summary_lines[1]

    if include_regime:
        sections["regime"] = describe_regime(analyze_regime(df, column=column))

    if include_indicators:
        sections["indicators"] = describe_indicators(analyze_indicators(df, column=column))

    if include_symbolic:
        symbolic = sax_encode(df, column=column, word_size=symbolic_word_size, alphabet_size=symbolic_alphabet_size)
        sections["symbolic"] = describe_sax(symbolic)

    if include_patterns:
        pattern_stats = detect_patterns(df)
        sections["patterns"] = describe_patterns(pattern_stats)
        sections["candlestick"] = describe_candlestick(pattern_stats)

    if include_support_resistance:
        levels = find_support_resistance(df, column=column)
        sections["levels"] = describe_support_resistance(levels)

    rendered = format_sections(sections, output_format=output_format)
    if digit_level:
        return digit_tokenize(rendered)

    return rendered
