"""Statistical summary analysis and textual description for one series."""

import math

import pandas as pd

from narrata.exceptions import ValidationError
from narrata.types import SummaryStats
from narrata.validation.ohlcv import infer_frequency_label, validate_ohlcv_frame


def analyze_summary(df: pd.DataFrame, column: str = "Close", ticker: str | None = None) -> SummaryStats:
    """Compute summary statistics for a selected numeric column.

    :param df: OHLCV DataFrame.
    :param column: Numeric column to summarize.
    :param ticker: Optional ticker override.
    :return: Structured summary statistics.
    """
    validate_ohlcv_frame(df)

    if column not in df.columns:
        raise ValidationError(f"Column '{column}' does not exist in DataFrame.")

    series = pd.to_numeric(df[column], errors="coerce").dropna()
    if series.empty:
        raise ValidationError(f"Column '{column}' contains no numeric values.")

    start = float(series.iloc[0])
    end = float(series.iloc[-1])

    if start == 0.0:
        change_pct = math.nan
    else:
        change_pct = ((end - start) / abs(start)) * 100.0

    return SummaryStats(
        ticker=_resolve_ticker(df, ticker),
        column=column,
        points=int(series.size),
        frequency=infer_frequency_label(df.index),
        start_date=df.index[0].date(),
        end_date=df.index[-1].date(),
        start=start,
        end=end,
        minimum=float(series.min()),
        maximum=float(series.max()),
        mean=float(series.mean()),
        std=float(series.std(ddof=0)),
        change_pct=change_pct,
    )


def describe_summary(
    summary: SummaryStats, currency_symbol: str = "$", precision: int = 2, include_header: bool = True
) -> str:
    """Render summary statistics as text.

    :param summary: Summary statistics.
    :param currency_symbol: Symbol for currency formatting.
    :param precision: Decimal precision for numeric values.
    :param include_header: Include ticker/points/frequency prefix.
    :return: Summary narration.
    """
    entity_name = summary.ticker or summary.column
    prefix = f"{entity_name} ({summary.points} pts, {summary.frequency}): " if include_header else ""

    line_1 = (
        f"{prefix}Range: [{_format_currency(summary.minimum, currency_symbol, precision)}, "
        f"{_format_currency(summary.maximum, currency_symbol, precision)}]  "
        f"Mean: {_format_currency(summary.mean, currency_symbol, precision)}  "
        f"Std: {_format_currency(summary.std, currency_symbol, precision)}"
    )
    line_2 = (
        f"Start: {_format_currency(summary.start, currency_symbol, precision)}  "
        f"End: {_format_currency(summary.end, currency_symbol, precision)}  "
        f"Change: {_format_change(summary.change_pct, precision)}"
    )

    return f"{line_1}\n{line_2}"


def _resolve_ticker(df: pd.DataFrame, ticker: str | None) -> str | None:
    if ticker:
        return ticker

    attr_ticker = df.attrs.get("ticker")
    if isinstance(attr_ticker, str) and attr_ticker.strip():
        return attr_ticker.strip()

    frame_name = getattr(df, "name", None)
    if isinstance(frame_name, str) and frame_name.strip():
        return frame_name.strip()

    return None


def _format_currency(value: float, currency_symbol: str, precision: int) -> str:
    return f"{currency_symbol}{value:.{precision}f}"


def _format_change(change_pct: float, precision: int) -> str:
    if math.isnan(change_pct):
        return "n/a"
    return f"{change_pct:+.{precision}f}%"
