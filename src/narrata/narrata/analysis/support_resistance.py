"""Support and resistance level extraction."""

import numpy as np
import pandas as pd
from scipy.signal import argrelextrema

from narrata.exceptions import ValidationError
from narrata.types import LevelStats, PriceLevel
from narrata.validation import validate_ohlcv_frame


def find_support_resistance(
    df: pd.DataFrame,
    column: str = "Close",
    tolerance_ratio: float = 0.01,
    max_levels: int = 2,
    extrema_order: int = 5,
) -> LevelStats:
    """Detect support and resistance levels from local extrema and touch counts.

    :param df: OHLCV DataFrame.
    :param column: Price column used for level detection.
    :param tolerance_ratio: Clustering tolerance as a price ratio.
    :param max_levels: Max number of support and resistance levels to return.
    :param extrema_order: Neighborhood size used by ``argrelextrema``.
    :return: Structured support and resistance levels.
    """
    validate_ohlcv_frame(df)
    if column not in df.columns:
        raise ValidationError(f"Column '{column}' does not exist in DataFrame.")
    if tolerance_ratio <= 0.0:
        raise ValidationError("tolerance_ratio must be > 0.")
    if max_levels < 1:
        raise ValidationError("max_levels must be >= 1.")
    if extrema_order < 1:
        raise ValidationError("extrema_order must be >= 1.")

    prices = pd.to_numeric(df[column], errors="coerce").dropna().to_numpy(dtype=float)
    if prices.size < extrema_order * 2 + 3:
        raise ValidationError("Not enough data to find support/resistance.")

    minima_indices = argrelextrema(prices, np.less_equal, order=extrema_order)[0]
    maxima_indices = argrelextrema(prices, np.greater_equal, order=extrema_order)[0]
    current_price = float(prices[-1])
    tolerance = max(current_price * tolerance_ratio, 1e-9)

    support_values = [float(prices[idx]) for idx in minima_indices if prices[idx] <= current_price]
    resistance_values = [float(prices[idx]) for idx in maxima_indices if prices[idx] >= current_price]

    supports = _build_levels(
        candidate_values=support_values,
        extrema_values=np.asarray([prices[idx] for idx in minima_indices], dtype=float),
        all_prices=prices,
        tolerance=tolerance,
        max_levels=max_levels,
        reverse=True,
    )
    resistances = _build_levels(
        candidate_values=resistance_values,
        extrema_values=np.asarray([prices[idx] for idx in maxima_indices], dtype=float),
        all_prices=prices,
        tolerance=tolerance,
        max_levels=max_levels,
        reverse=False,
    )

    return LevelStats(supports=supports, resistances=resistances)


def describe_support_resistance(stats: LevelStats, currency_symbol: str = "$", precision: int = 2) -> str:
    """Render support and resistance levels as one line.

    :param stats: Support and resistance stats.
    :param currency_symbol: Currency symbol for formatting.
    :param precision: Decimal precision.
    :return: Human-readable support/resistance narration.
    """
    support_text = _format_levels(stats.supports, currency_symbol, precision)
    resistance_text = _format_levels(stats.resistances, currency_symbol, precision)
    return f"Support: {support_text}  Resistance: {resistance_text}"


def _build_levels(
    candidate_values: list[float],
    extrema_values: np.ndarray,
    all_prices: np.ndarray,
    tolerance: float,
    max_levels: int,
    reverse: bool,
) -> tuple[PriceLevel, ...]:
    if not candidate_values:
        return ()

    clusters = _cluster_values(candidate_values, tolerance=tolerance, reverse=reverse)
    levels: list[PriceLevel] = []
    for cluster in clusters:
        level_price = float(np.mean(cluster))
        touches_extrema = int(np.sum(np.abs(extrema_values - level_price) <= tolerance))
        touches_band = int(np.sum(np.abs(all_prices - level_price) <= tolerance))
        touches = max(touches_extrema, touches_band)
        levels.append(PriceLevel(price=level_price, touches=touches))

    if reverse:
        levels.sort(key=lambda level: (level.touches, level.price), reverse=True)
    else:
        levels.sort(key=lambda level: (level.touches, -level.price), reverse=True)
    return tuple(levels[:max_levels])


def _cluster_values(values: list[float], tolerance: float, reverse: bool) -> list[list[float]]:
    ordered = sorted(values, reverse=reverse)
    clusters: list[list[float]] = []
    for value in ordered:
        matched = False
        for cluster in clusters:
            if abs(value - float(np.mean(cluster))) <= tolerance:
                cluster.append(value)
                matched = True
                break
        if not matched:
            clusters.append([value])
    return clusters


def _format_levels(levels: tuple[PriceLevel, ...], currency_symbol: str, precision: int) -> str:
    if not levels:
        return "n/a"
    parts = [f"{currency_symbol}{level.price:.{precision}f} ({level.touches} touches)" for level in levels]
    return ", ".join(parts)
