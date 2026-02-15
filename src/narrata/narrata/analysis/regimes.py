"""Regime classification for time series.

Uses change-point detection from ruptures when available, with a robust
rolling-statistics fallback when ruptures is not installed.
"""

from datetime import date
from typing import Any

import pandas as pd

from narrata.exceptions import ValidationError
from narrata.types import RegimeStats
from narrata.validation import validate_ohlcv_frame

try:
    import ruptures as _rpt
except ImportError:  # pragma: no cover - optional dependency path
    _rpt = None

rpt: Any | None = _rpt


def analyze_regime(
    df: pd.DataFrame,
    column: str = "Close",
    window: int = 20,
    penalty: float = 3.0,
    trend_threshold: float = 0.0005,
) -> RegimeStats:
    """Classify current trend and volatility regime.

    :param df: OHLCV DataFrame.
    :param column: Price column to analyze.
    :param window: Rolling window for fallback regime metrics.
    :param penalty: Ruptures PELT penalty parameter.
    :param trend_threshold: Mean-return threshold for trend labels.
    :return: Regime classification with inferred start date.
    """
    validate_ohlcv_frame(df)
    if column not in df.columns:
        raise ValidationError(f"Column '{column}' does not exist in DataFrame.")
    if window < 5:
        raise ValidationError("window must be >= 5.")

    prices = pd.to_numeric(df[column], errors="coerce").dropna()
    returns = prices.pct_change().dropna()
    if returns.size < window:
        raise ValidationError("Not enough data to infer regime.")

    if rpt is not None and returns.size >= max(window, 40):
        trend_label, volatility_label, start_date = _analyze_with_ruptures(
            returns=returns,
            penalty=penalty,
            trend_threshold=trend_threshold,
            min_size=window,
            rpt_module=rpt,
        )
    else:
        trend_label, volatility_label, start_date = _analyze_with_rolling(
            returns=returns,
            window=window,
            trend_threshold=trend_threshold,
        )

    return RegimeStats(
        trend_label=trend_label,
        volatility_label=volatility_label,
        start_date=start_date,
    )


def describe_regime(stats: RegimeStats) -> str:
    """Render regime classification as one line.

    :param stats: Regime classification.
    :return: Human-readable regime text.
    """
    return f"Regime: {stats.trend_label} since {stats.start_date.isoformat()} ({stats.volatility_label} volatility)"


def _analyze_with_ruptures(
    returns: pd.Series,
    penalty: float,
    trend_threshold: float,
    min_size: int,
    rpt_module: Any,
) -> tuple[str, str, date]:
    signal = returns.to_numpy(dtype=float).reshape(-1, 1)
    algo = rpt_module.Pelt(model="rbf", min_size=max(10, min_size)).fit(signal)
    bkpts = algo.predict(pen=max(penalty, 0.1))

    last_start = bkpts[-2] if len(bkpts) > 1 else 0
    last_end = bkpts[-1] if bkpts else signal.shape[0]
    segment = returns.iloc[last_start:last_end]
    if segment.empty:
        segment = returns
        last_start = 0

    mean_ret = float(segment.mean())
    vol = float(segment.std(ddof=0))
    baseline_vol = float(returns.std(ddof=0))

    trend_label = _trend_label(mean_ret, trend_threshold)
    volatility_label = "high" if vol > baseline_vol else "low"
    start_ts = returns.index[last_start]
    return trend_label, volatility_label, _to_date(start_ts)


def _analyze_with_rolling(returns: pd.Series, window: int, trend_threshold: float) -> tuple[str, str, date]:
    rolling_mean = returns.rolling(window=window, min_periods=window).mean().dropna()
    rolling_std = returns.rolling(window=window, min_periods=window).std(ddof=0).dropna()
    if rolling_mean.empty or rolling_std.empty:
        raise ValidationError("Not enough data to infer regime.")

    vol_baseline = float(rolling_std.median())
    current_trend = _trend_label(float(rolling_mean.iloc[-1]), trend_threshold)
    current_volatility = "high" if float(rolling_std.iloc[-1]) > vol_baseline else "low"

    start_ts = rolling_mean.index[-1]
    for idx in range(rolling_mean.size - 1, -1, -1):
        trend = _trend_label(float(rolling_mean.iloc[idx]), trend_threshold)
        volatility = "high" if float(rolling_std.iloc[idx]) > vol_baseline else "low"
        if trend != current_trend or volatility != current_volatility:
            break
        start_ts = rolling_mean.index[idx]

    return current_trend, current_volatility, _to_date(start_ts)


def _trend_label(mean_return: float, threshold: float) -> str:
    if mean_return > threshold:
        return "Uptrend"
    if mean_return < -threshold:
        return "Downtrend"
    return "Ranging"


def _to_date(value: object) -> date:
    if isinstance(value, pd.Timestamp):
        return date.fromisoformat(value.strftime("%Y-%m-%d"))
    if isinstance(value, date):
        return value
    raise TypeError(f"Cannot convert {type(value).__name__} to date.")
