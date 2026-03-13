"""Command-line interface for narrata."""

from __future__ import annotations

import argparse
import sys

import pandas as pd

from narrata.composition.narrate import narrate


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="narrata",
        description="Generate LLM-ready narration from OHLCV time series data.",
    )
    p.add_argument(
        "file",
        nargs="?",
        default="-",
        help="CSV file path, or '-' / omit to read from stdin.",
    )
    p.add_argument("--ticker", default=None, help="Ticker symbol for the header line.")
    p.add_argument("--column", default="Close", help="Price column to analyze (default: Close).")
    p.add_argument(
        "--format",
        dest="output_format",
        choices=["plain", "markdown_kv", "toon"],
        default="plain",
        help="Output format (default: plain).",
    )
    p.add_argument("--digit-level", action="store_true", help="Apply digit-level tokenization.")
    p.add_argument("--sparkline-width", type=int, default=20, help="Sparkline width (default: 20).")
    p.add_argument("--sax-word-size", type=int, default=16, help="SAX word size (default: 16).")
    p.add_argument("--sax-alphabet-size", type=int, default=8, help="SAX alphabet size (default: 8).")

    # Section toggles — all on by default; --no-X disables.
    for section in ("summary", "sparkline", "regime", "indicators", "symbolic", "patterns", "support-resistance"):
        p.add_argument(
            f"--no-{section}",
            action="store_true",
            help=f"Disable the {section} section.",
        )

    return p


def _read_ohlcv(path: str) -> pd.DataFrame:
    """Read OHLCV CSV from a file path or stdin."""
    source = sys.stdin if path == "-" else path
    df = pd.read_csv(source, parse_dates=True, index_col=0)
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    return df


def main(argv: list[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)

    df = _read_ohlcv(args.file)

    text = narrate(
        df,
        column=args.column,
        ticker=args.ticker,
        include_summary=not args.no_summary,
        include_sparkline=not args.no_sparkline,
        include_regime=not args.no_regime,
        include_indicators=not args.no_indicators,
        include_symbolic=not args.no_symbolic,
        include_patterns=not args.no_patterns,
        include_support_resistance=not args.no_support_resistance,
        sparkline_width=args.sparkline_width,
        symbolic_word_size=args.sax_word_size,
        symbolic_alphabet_size=args.sax_alphabet_size,
        digit_level=args.digit_level,
        output_format=args.output_format,  # type: ignore[arg-type]
    )
    print(text)
