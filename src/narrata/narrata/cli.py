"""Command-line interface for narrata."""

from __future__ import annotations

import argparse
import sys

import pandas as pd

from narrata import __version__
from narrata.composition.compare import compare
from narrata.composition.narrate import narrate


def _build_narrate_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="narrata",
        description="Generate LLM-ready narration from OHLCV time series data.",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Path to CSV, TSV, or Parquet file. Use '-' or omit for stdin.",
    )
    p.add_argument(
        "--input-format",
        choices=["csv", "tsv", "parquet"],
        default=None,
        help="Input format (auto-detected from extension by default; required for stdin of non-CSV data).",
    )
    p.add_argument("--ticker", default=None, help="Ticker symbol for the header line.")
    p.add_argument("--column", default="Close", help="Price column to analyze (default: Close).")
    p.add_argument(
        "--frequency",
        default=None,
        help="Explicit frequency label (e.g. 15min, 5min, hourly, daily). Auto-detected when omitted.",
    )
    p.add_argument(
        "--format",
        dest="output_format",
        choices=["plain", "markdown_kv", "toon", "json"],
        default="plain",
        help="Output format (default: plain).",
    )
    p.add_argument("--currency", default="", help="Currency symbol for price values (e.g. '$', '£').")
    p.add_argument("--precision", type=int, default=2, help="Decimal places for price values (default: 2).")
    p.add_argument("--digit-level", action="store_true", help="Apply digit-level tokenization.")
    p.add_argument("--sparkline-width", type=int, default=20, help="Sparkline width (default: 20).")
    p.add_argument(
        "--symbolic-method",
        choices=["sax", "astride"],
        default="sax",
        help="Symbolic encoding method (default: sax).",
    )
    p.add_argument("--symbolic-word-size", type=int, default=16, help="SAX word size / ASTRIDE segments (default: 16).")
    p.add_argument("--symbolic-alphabet-size", type=int, default=8, help="Symbol alphabet size (default: 8).")
    p.add_argument("--symbolic-penalty", type=float, default=3.0, help="ASTRIDE ruptures penalty (default: 3.0).")

    for section in ("summary", "sparkline", "regime", "indicators", "symbolic", "patterns", "support-resistance"):
        p.add_argument(f"--no-{section}", action="store_true", help=f"Disable the {section} section.")

    p.add_argument("--verbose", action="store_true", help="Show all sections, including empty or insufficient data.")

    return p


def _build_compare_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="narrata compare",
        description="Compare two OHLCV periods side-by-side.",
    )
    p.add_argument("before_file", help="Path to CSV/TSV/Parquet for the earlier period.")
    p.add_argument("after_file", help="Path to CSV/TSV/Parquet for the later period.")
    p.add_argument(
        "--input-format",
        choices=["csv", "tsv", "parquet"],
        default=None,
        help="Input format (auto-detected from extension by default).",
    )
    p.add_argument("--ticker", default=None, help="Ticker symbol for the header line.")
    p.add_argument("--column", default="Close", help="Price column to analyze (default: Close).")
    p.add_argument(
        "--frequency",
        default=None,
        help="Explicit frequency label (e.g. 15min, 5min, hourly, daily). Auto-detected when omitted.",
    )
    p.add_argument(
        "--format",
        dest="output_format",
        choices=["plain", "markdown_kv", "toon", "json"],
        default="plain",
        help="Output format (default: plain).",
    )
    p.add_argument("--currency", default="", help="Currency symbol for price values (e.g. '$', '£').")
    p.add_argument("--precision", type=int, default=2, help="Decimal places for price values (default: 2).")
    p.add_argument(
        "--symbolic-method",
        choices=["sax", "astride"],
        default="sax",
        help="Symbolic encoding method (default: sax).",
    )
    p.add_argument("--symbolic-word-size", type=int, default=16, help="SAX word size / ASTRIDE segments (default: 16).")
    p.add_argument("--symbolic-alphabet-size", type=int, default=8, help="Symbol alphabet size (default: 8).")
    p.add_argument("--symbolic-penalty", type=float, default=3.0, help="ASTRIDE ruptures penalty (default: 3.0).")

    for section in ("regime", "indicators", "symbolic", "support-resistance"):
        p.add_argument(f"--no-{section}", action="store_true", help=f"Disable the {section} section.")

    p.add_argument("--verbose", action="store_true", help="Show all sections, including empty or insufficient data.")

    return p


def _detect_format(path: str, explicit: str | None) -> str:
    """Return input format from explicit flag or file extension."""
    if explicit:
        return explicit
    if path == "-":
        return "csv"
    lower = path.lower()
    if lower.endswith(".tsv"):
        return "tsv"
    if lower.endswith((".parquet", ".pq")):
        return "parquet"
    return "csv"


def _read_ohlcv(path: str, fmt: str) -> pd.DataFrame:
    """Read OHLCV data from a file path or stdin."""
    if fmt == "parquet":
        if path == "-":
            raise SystemExit("narrata: parquet format cannot be read from stdin.")
        df = pd.read_parquet(path)
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        return df

    sep = "\t" if fmt == "tsv" else ","
    source = sys.stdin if path == "-" else path
    df = pd.read_csv(source, sep=sep, parse_dates=True, index_col=0)
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    return df


def _run_compare(argv: list[str]) -> None:
    args = _build_compare_parser().parse_args(argv)
    fmt_before = _detect_format(args.before_file, args.input_format)
    fmt_after = _detect_format(args.after_file, args.input_format)
    df_before = _read_ohlcv(args.before_file, fmt_before)
    df_after = _read_ohlcv(args.after_file, fmt_after)

    text = compare(
        df_before,
        df_after,
        column=args.column,
        ticker=args.ticker,
        frequency=args.frequency,
        currency_symbol=args.currency,
        precision=args.precision,
        include_regime=not args.no_regime,
        include_indicators=not args.no_indicators,
        include_symbolic=not args.no_symbolic,
        include_support_resistance=not args.no_support_resistance,
        symbolic_method=args.symbolic_method,
        symbolic_word_size=args.symbolic_word_size,
        symbolic_alphabet_size=args.symbolic_alphabet_size,
        symbolic_penalty=args.symbolic_penalty,
        output_format=args.output_format,
        verbose=args.verbose,
    )
    print(text)


def _run_narrate(argv: list[str] | None) -> None:
    args = _build_narrate_parser().parse_args(argv)
    fmt = _detect_format(args.file, args.input_format)
    df = _read_ohlcv(args.file, fmt)

    text = narrate(
        df,
        column=args.column,
        ticker=args.ticker,
        frequency=args.frequency,
        include_summary=not args.no_summary,
        include_sparkline=not args.no_sparkline,
        include_regime=not args.no_regime,
        include_indicators=not args.no_indicators,
        include_symbolic=not args.no_symbolic,
        include_patterns=not args.no_patterns,
        include_support_resistance=not args.no_support_resistance,
        sparkline_width=args.sparkline_width,
        symbolic_method=args.symbolic_method,
        symbolic_word_size=args.symbolic_word_size,
        symbolic_alphabet_size=args.symbolic_alphabet_size,
        symbolic_penalty=args.symbolic_penalty,
        digit_level=args.digit_level,
        currency_symbol=args.currency,
        precision=args.precision,
        output_format=args.output_format,
        verbose=args.verbose,
    )
    print(text)


def main(argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == "compare":
        _run_compare(argv[1:])
    else:
        _run_narrate(argv)
