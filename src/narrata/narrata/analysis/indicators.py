"""Technical indicator analysis and narration."""

import importlib
from typing import Any

import numpy as np
import pandas as pd

from narrata.exceptions import ValidationError
from narrata.types import IndicatorStats
from narrata.validation import validate_ohlcv_frame

ta: Any | None
try:
    importlib.import_module("importlib.metadata")
    import pandas_ta as ta
except ImportError:  # pragma: no cover - optional dependency path
    ta = None


def compute_rsi(series: pd.Series, period: int = 14) -> float:
    """Compute RSI using Wilder-style exponential smoothing.

    :param series: Price series.
    :param period: RSI period length.
    :return: Latest RSI value.
    """
    if period < 2:
        raise ValidationError("RSI period must be >= 2.")

    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.size < period + 1:
        raise ValidationError("Not enough data to compute RSI.")

    delta = values.diff()
    gains = delta.clip(lower=0.0)
    losses = -delta.clip(upper=0.0)
    avg_gain = gains.ewm(alpha=1.0 / period, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1.0 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))

    latest = float(rsi.iloc[-1]) if not np.isnan(rsi.iloc[-1]) else 100.0
    return max(0.0, min(100.0, latest))


def compute_macd(
    series: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9
) -> tuple[float, float, float]:
    """Compute MACD values for the latest sample.

    :param series: Price series.
    :param fast_period: Fast EMA period.
    :param slow_period: Slow EMA period.
    :param signal_period: Signal EMA period.
    :return: Tuple of (macd_line, signal_line, histogram).
    """
    if fast_period >= slow_period:
        raise ValidationError("fast_period must be smaller than slow_period.")

    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.size < slow_period + signal_period:
        raise ValidationError("Not enough data to compute MACD.")

    fast_ema = values.ewm(span=fast_period, adjust=False).mean()
    slow_ema = values.ewm(span=slow_period, adjust=False).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line

    return float(macd_line.iloc[-1]), float(signal_line.iloc[-1]), float(histogram.iloc[-1])


def compute_bollinger(series: pd.Series, period: int = 20, num_std: float = 2.0) -> tuple[str, bool]:
    """Compute Bollinger Band position and squeeze state.

    :param series: Price series.
    :param period: Bollinger Band period.
    :param num_std: Number of standard deviations for band width.
    :return: Tuple of (position label, squeeze detected).
    """
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.size < period:
        raise ValidationError("Not enough data to compute Bollinger Bands.")

    sma = values.rolling(window=period).mean()
    std = values.rolling(window=period).std(ddof=0)
    upper = sma + num_std * std
    lower = sma - num_std * std
    bandwidth = ((upper - lower) / sma).dropna()

    latest_price = float(values.iloc[-1])
    latest_upper = float(upper.iloc[-1])
    latest_lower = float(lower.iloc[-1])
    latest_sma = float(sma.iloc[-1])

    if latest_upper == latest_lower:
        position = "at midline"
    else:
        pct = (latest_price - latest_lower) / (latest_upper - latest_lower)
        if pct >= 0.95:
            position = "above upper band"
        elif pct >= 0.80:
            position = "near upper band"
        elif pct <= 0.05:
            position = "below lower band"
        elif pct <= 0.20:
            position = "near lower band"
        elif latest_price > latest_sma:
            position = "upper half"
        else:
            position = "lower half"

    squeeze = False
    if bandwidth.size >= period:
        recent_bw = float(bandwidth.iloc[-1])
        lookback_bw = float(bandwidth.iloc[-period:].quantile(0.20))
        squeeze = recent_bw <= lookback_bw

    return position, squeeze


def compute_ma_crossover(
    series: pd.Series, fast_period: int = 50, slow_period: int = 200
) -> tuple[str | None, int | None]:
    """Detect moving average crossover (golden/death cross).

    :param series: Price series.
    :param fast_period: Fast SMA period.
    :param slow_period: Slow SMA period.
    :return: Tuple of (cross type or None, days since cross or None).
    """
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.size < slow_period + 1:
        return None, None

    fast_sma = values.rolling(window=fast_period).mean()
    slow_sma = values.rolling(window=slow_period).mean()
    diff = (fast_sma - slow_sma).dropna()
    if diff.size < 2:
        return None, None

    signs = np.sign(diff.to_numpy())
    current = "golden cross" if signs[-1] >= 0.0 else "death cross"

    for idx in range(signs.size - 1, 0, -1):
        if signs[idx] != signs[idx - 1] and signs[idx] != 0.0 and signs[idx - 1] != 0.0:
            days_ago = signs.size - 1 - idx
            return current, days_ago

    return current, None


def compute_volume_state(df: pd.DataFrame, lookback: int = 20) -> tuple[float, str]:
    """Compute volume ratio to N-day moving average and classify.

    :param df: OHLCV DataFrame with Volume column.
    :param lookback: Moving average lookback period.
    :return: Tuple of (ratio to average, state label).
    """
    if "Volume" not in df.columns:
        raise ValidationError("DataFrame must contain Volume column.")

    volume = pd.to_numeric(df["Volume"], errors="coerce").dropna()
    if volume.size < lookback + 1:
        raise ValidationError("Not enough data to compute volume state.")

    avg = float(volume.rolling(window=lookback).mean().iloc[-1])
    if avg <= 0.0:
        return 1.0, "average"

    latest = float(volume.iloc[-1])
    ratio = latest / avg

    if ratio >= 2.0:
        state = "unusually high"
    elif ratio >= 1.5:
        state = "above average"
    elif ratio <= 0.5:
        state = "unusually low"
    elif ratio <= 0.75:
        state = "below average"
    else:
        state = "average"

    return round(ratio, 2), state


def compute_volatility_percentile(series: pd.Series, window: int = 20, lookback: int = 252) -> tuple[float, str]:
    """Compute historical volatility percentile rank.

    :param series: Price series.
    :param window: Rolling window for volatility calculation.
    :param lookback: Lookback period for percentile ranking.
    :return: Tuple of (percentile 0-100, state label).
    """
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.size < window + 2:
        raise ValidationError("Not enough data to compute volatility percentile.")

    returns = values.pct_change().dropna()
    rolling_vol = returns.rolling(window=window).std(ddof=0).dropna()
    if rolling_vol.empty:
        raise ValidationError("Not enough data to compute volatility percentile.")

    current_vol = float(rolling_vol.iloc[-1])
    rank_window = rolling_vol.tail(min(lookback, rolling_vol.size))
    percentile = float((rank_window <= current_vol).sum() / rank_window.size * 100.0)
    percentile = round(percentile, 0)

    if percentile <= 10:
        state = "extremely low"
    elif percentile <= 25:
        state = "low"
    elif percentile >= 90:
        state = "extremely high"
    elif percentile >= 75:
        state = "high"
    else:
        state = "moderate"

    return percentile, state


def analyze_indicators(df: pd.DataFrame, column: str = "Close", rsi_period: int = 14) -> IndicatorStats:
    """Analyze RSI, MACD, Bollinger Bands, MA crossovers, volume, and volatility.

    :param df: OHLCV DataFrame.
    :param column: Price column to analyze.
    :param rsi_period: RSI period.
    :return: Structured indicator statistics.
    """
    validate_ohlcv_frame(df)
    if column not in df.columns:
        raise ValidationError(f"Column '{column}' does not exist in DataFrame.")

    values = pd.to_numeric(df[column], errors="coerce").dropna()
    if ta is None:
        rsi_value = compute_rsi(values, period=rsi_period)
        macd_value, signal_value, histogram = compute_macd(values)
        macd_state, crossover_days = _classify_macd(values)
    else:
        rsi_value = _compute_rsi_with_pandas_ta(values, period=rsi_period)
        macd_value, signal_value, histogram, macd_state, crossover_days = _compute_macd_with_pandas_ta(values)

    rsi_state = _classify_rsi(values, rsi_value)

    bb_position: str | None = None
    bb_squeeze: bool | None = None
    try:
        bb_position, bb_squeeze = compute_bollinger(values)
    except ValidationError:
        pass

    ma_cross: str | None = None
    ma_cross_days: int | None = None
    try:
        ma_cross, ma_cross_days = compute_ma_crossover(values)
    except ValidationError:
        pass

    volume_ratio: float | None = None
    volume_state: str | None = None
    try:
        volume_ratio, volume_state = compute_volume_state(df)
    except ValidationError:
        pass

    vol_pct: float | None = None
    vol_state: str | None = None
    try:
        vol_pct, vol_state = compute_volatility_percentile(values)
    except ValidationError:
        pass

    return IndicatorStats(
        rsi_period=rsi_period,
        rsi_value=rsi_value,
        rsi_state=rsi_state,
        macd_value=macd_value,
        macd_signal=signal_value,
        macd_histogram=histogram,
        macd_state=macd_state,
        crossover_days_ago=crossover_days,
        bb_position=bb_position,
        bb_squeeze=bb_squeeze,
        ma_cross=ma_cross,
        ma_cross_days_ago=ma_cross_days,
        volume_ratio=volume_ratio,
        volume_state=volume_state,
        volatility_percentile=vol_pct,
        volatility_state=vol_state,
    )


def describe_indicators(stats: IndicatorStats) -> str:
    """Render indicator statistics as concise narration lines.

    :param stats: Indicator statistics.
    :return: Human-readable indicator narration.
    """
    rsi_part = f"RSI({stats.rsi_period}): {stats.rsi_value:.1f} ({stats.rsi_state})"

    if stats.crossover_days_ago is None:
        macd_part = f"MACD: {stats.macd_state}"
    else:
        unit = "day" if stats.crossover_days_ago == 1 else "days"
        macd_part = f"MACD: {stats.macd_state} crossover {stats.crossover_days_ago} {unit} ago"

    parts = [f"{rsi_part}  {macd_part}"]

    if stats.bb_position is not None:
        bb_text = f"BB: {stats.bb_position}"
        if stats.bb_squeeze:
            bb_text += " (squeeze)"
        parts.append(bb_text)

    if stats.ma_cross is not None:
        if stats.ma_cross_days_ago is not None:
            unit = "day" if stats.ma_cross_days_ago == 1 else "days"
            parts.append(f"SMA 50/200: {stats.ma_cross} {stats.ma_cross_days_ago} {unit} ago")
        else:
            parts.append(f"SMA 50/200: {stats.ma_cross}")

    if stats.volume_ratio is not None and stats.volume_state is not None:
        parts.append(f"Volume: {stats.volume_ratio}x 20-day avg ({stats.volume_state})")

    if stats.volatility_percentile is not None and stats.volatility_state is not None:
        percentile = _format_ordinal(stats.volatility_percentile)
        parts.append(f"Volatility: {percentile} percentile ({stats.volatility_state})")

    return "\n".join(parts)


def _classify_rsi(values: pd.Series, rsi_value: float) -> str:
    if rsi_value >= 70.0:
        return "overbought"
    if rsi_value <= 30.0:
        return "oversold"

    recent = values.tail(4)
    if recent.size >= 2 and float(recent.iloc[-1]) >= float(recent.iloc[0]):
        return "neutral-bullish"
    return "neutral-bearish"


def _classify_macd(values: pd.Series) -> tuple[str, int | None]:
    fast_ema = values.ewm(span=12, adjust=False).mean()
    slow_ema = values.ewm(span=26, adjust=False).mean()
    return _classify_macd_lines(fast_ema - slow_ema, (fast_ema - slow_ema).ewm(span=9, adjust=False).mean())


def _classify_macd_lines(macd_line: pd.Series, signal_line: pd.Series) -> tuple[str, int | None]:
    aligned = pd.concat(
        [
            pd.to_numeric(macd_line, errors="coerce"),
            pd.to_numeric(signal_line, errors="coerce"),
        ],
        axis=1,
    ).dropna()
    if aligned.empty:
        return "neutral", None

    diff = aligned.iloc[:, 0] - aligned.iloc[:, 1]

    direction = "bullish" if float(diff.iloc[-1]) >= 0.0 else "bearish"

    signs = np.sign(diff.to_numpy())
    for idx in range(signs.size - 1, 0, -1):
        if signs[idx] == 0.0:
            continue
        if signs[idx - 1] == 0.0:
            continue
        if signs[idx] != signs[idx - 1]:
            days_ago = signs.size - 1 - idx
            return direction, days_ago

    widening = abs(float(diff.iloc[-1])) >= abs(float(diff.iloc[-2])) if diff.size >= 2 else True
    suffix = "widening" if widening else "narrowing"
    return f"{direction}, {suffix}", None


def _compute_rsi_with_pandas_ta(values: pd.Series, period: int) -> float:
    if ta is None:  # pragma: no cover
        return compute_rsi(values, period=period)

    rsi = ta.rsi(values, length=period)
    if rsi is None:
        return compute_rsi(values, period=period)
    rsi_numeric = pd.to_numeric(rsi, errors="coerce").dropna()
    if rsi_numeric.empty:
        return compute_rsi(values, period=period)
    return float(rsi_numeric.iloc[-1])


def _macd_fallback(values: pd.Series) -> tuple[float, float, float, str, int | None]:
    macd_value, signal_value, histogram = compute_macd(values)
    macd_state, crossover_days = _classify_macd(values)
    return macd_value, signal_value, histogram, macd_state, crossover_days


def _compute_macd_with_pandas_ta(values: pd.Series) -> tuple[float, float, float, str, int | None]:
    if ta is None:  # pragma: no cover
        return _macd_fallback(values)

    macd_frame = ta.macd(values, fast=12, slow=26, signal=9)
    if macd_frame is None or macd_frame.empty:
        return _macd_fallback(values)

    macd_col = next((name for name in macd_frame.columns if name.startswith("MACD_")), None)
    signal_col = next((name for name in macd_frame.columns if name.startswith("MACDs_")), None)
    hist_col = next((name for name in macd_frame.columns if name.startswith("MACDh_")), None)

    if macd_col is None or signal_col is None or hist_col is None:
        return _macd_fallback(values)

    macd_series = pd.to_numeric(macd_frame[macd_col], errors="coerce").dropna()
    signal_series = pd.to_numeric(macd_frame[signal_col], errors="coerce").dropna()
    hist_series = pd.to_numeric(macd_frame[hist_col], errors="coerce").dropna()
    if macd_series.empty or signal_series.empty or hist_series.empty:
        return _macd_fallback(values)

    macd_state, crossover_days = _classify_macd_lines(macd_series, signal_series)
    return (
        float(macd_series.iloc[-1]),
        float(signal_series.iloc[-1]),
        float(hist_series.iloc[-1]),
        macd_state,
        crossover_days,
    )


def _format_ordinal(value: float) -> str:
    number = int(round(value))
    remainder_100 = number % 100
    if 11 <= remainder_100 <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"
