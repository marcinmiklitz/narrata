"""Adapters for converting external data formats into narrata DataFrames."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pandas as pd

from narrata.exceptions import ValidationError


def from_ccxt(
    ohlcv: Sequence[Sequence[float | int]],
    *,
    ticker: str | None = None,
) -> pd.DataFrame:
    """Convert ccxt OHLCV data into a narrata-ready DataFrame.

    ccxt's ``exchange.fetch_ohlcv()`` returns a list of lists::

        [[timestamp_ms, open, high, low, close, volume], ...]

    This function converts that into a pandas DataFrame with a
    DatetimeIndex and canonical OHLCV column names.

    :param ohlcv: List of ``[timestamp_ms, open, high, low, close, volume]`` rows.
    :param ticker: Optional ticker symbol attached to ``DataFrame.attrs["ticker"]``.
    :return: OHLCV DataFrame ready for ``narrate()``.
    """
    if not ohlcv:
        raise ValidationError("ohlcv must contain at least one row.")

    first = ohlcv[0]
    if len(first) < 6:
        raise ValidationError(f"Each row must have at least 6 elements [timestamp, O, H, L, C, V], got {len(first)}.")

    df = pd.DataFrame(
        list(ohlcv),
        columns=["timestamp", "Open", "High", "Low", "Close", "Volume"],
    )
    df.index = pd.DatetimeIndex(pd.to_datetime(df["timestamp"], unit="ms", utc=True))
    df = df.drop(columns="timestamp")
    df = df.sort_index()

    for col in ("Open", "High", "Low", "Close", "Volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if ticker:
        df.attrs["ticker"] = ticker

    return df


def from_coingecko(
    data: dict[str, list[list[float | int]]],
    *,
    ticker: str | None = None,
) -> pd.DataFrame:
    """Convert CoinGecko market chart data into a narrata-ready DataFrame.

    CoinGecko's ``/coins/{id}/market_chart`` returns::

        {
            "prices": [[timestamp_ms, price], ...],
            "total_volumes": [[timestamp_ms, volume], ...],  # optional
        }

    This produces a Close-only (or Close+Volume) DataFrame suitable
    for ``narrate()``.  Open, High, and Low are not available from
    CoinGecko; sections that require them (patterns, candlestick)
    will be silently omitted.

    :param data: CoinGecko market chart response dict.
    :param ticker: Optional ticker symbol.
    :return: DataFrame with Close (and optionally Volume) column.
    """
    prices: Any = data.get("prices")
    if not prices:
        raise ValidationError("CoinGecko data must contain a 'prices' key with at least one entry.")

    df = pd.DataFrame(prices, columns=["timestamp", "Close"])
    df.index = pd.DatetimeIndex(pd.to_datetime(df["timestamp"], unit="ms", utc=True))
    df = df.drop(columns="timestamp")
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")

    volumes: Any = data.get("total_volumes")
    if volumes:
        vol_df = pd.DataFrame(volumes, columns=["timestamp", "Volume"])
        vol_df.index = pd.DatetimeIndex(pd.to_datetime(vol_df["timestamp"], unit="ms", utc=True))
        df["Volume"] = pd.to_numeric(vol_df["Volume"], errors="coerce")

    df = df.sort_index()

    if ticker:
        df.attrs["ticker"] = ticker

    return df
