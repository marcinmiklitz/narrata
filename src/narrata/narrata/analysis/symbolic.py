"""Symbolic time-series encodings.

Implements SAX and ASTRIDE-style symbolization.

Uses tslearn's SAX implementation when available, and falls back to an in-house
SAX implementation otherwise.  ASTRIDE uses ruptures for change-point-based
adaptive segmentation.

References:
    [SAX] Lin et al., "Experiencing SAX", DMKD 2007.
    [ASTRIDE] Combettes et al., "An Adaptive Symbolization for Time Series",
    EUSIPCO 2024. arXiv:2302.04097.
"""

import warnings
from statistics import NormalDist
from typing import Any

import numpy as np
import pandas as pd

from narrata.exceptions import ValidationError
from narrata.types import SymbolicStats
from narrata.validation import validate_ohlcv_frame

try:
    import ruptures as _rpt
except ImportError:  # pragma: no cover - optional dependency path
    _rpt = None

rpt: Any | None = _rpt

SymbolicAggregateApproximation: Any | None
with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore",
        message="h5py not installed, hdf5 features will not be supported.",
        category=UserWarning,
    )
    try:
        from tslearn.piecewise import SymbolicAggregateApproximation as _sax_cls
    except ImportError:  # pragma: no cover - optional dependency path
        _sax_cls = None

SymbolicAggregateApproximation = _sax_cls


def sax_encode(df: pd.DataFrame, column: str = "Close", word_size: int = 16, alphabet_size: int = 8) -> SymbolicStats:
    """Encode a series with SAX-style symbolization.

    :param df: OHLCV DataFrame.
    :param column: Price column to encode.
    :param word_size: Number of PAA segments.
    :param alphabet_size: Number of symbols in alphabet.
    :return: Structured symbolic encoding result.
    """
    validate_ohlcv_frame(df)
    if column not in df.columns:
        raise ValidationError(f"Column '{column}' does not exist in DataFrame.")
    if word_size < 2:
        raise ValidationError("word_size must be >= 2.")
    if alphabet_size < 2 or alphabet_size > 26:
        raise ValidationError("alphabet_size must be between 2 and 26.")

    values = pd.to_numeric(df[column], errors="coerce").dropna().to_numpy(dtype=float)
    if values.size < word_size:
        raise ValidationError("Not enough data points for requested word_size.")

    if SymbolicAggregateApproximation is not None:
        symbols = _sax_encode_with_tslearn(
            values=values,
            word_size=word_size,
            alphabet_size=alphabet_size,
            sax_cls=SymbolicAggregateApproximation,
        )
    else:
        symbols = _sax_encode_inhouse(values=values, word_size=word_size, alphabet_size=alphabet_size)

    return SymbolicStats(
        method="SAX",
        word_size=word_size,
        alphabet_size=alphabet_size,
        symbols=symbols,
    )


def describe_sax(stats: SymbolicStats) -> str:
    """Render symbolic encoding as one line.

    :param stats: Symbolic encoding result.
    :return: Human-readable symbolic description.
    """
    return f"SAX({stats.word_size}): {stats.symbols}"


def _sax_encode_with_tslearn(values: np.ndarray, word_size: int, alphabet_size: int, sax_cls: Any) -> str:
    model = sax_cls(
        n_segments=word_size,
        alphabet_size_avg=alphabet_size,
        scale=True,
    )
    transformed = model.fit_transform(values.reshape(1, -1, 1))
    symbol_indices = transformed.reshape(-1).astype(int)
    return "".join(chr(ord("a") + int(index)) for index in symbol_indices)


def _sax_encode_inhouse(values: np.ndarray, word_size: int, alphabet_size: int) -> str:
    normalized = _z_normalize(values)
    paa = _piecewise_aggregate(normalized, segments=word_size)
    breakpoints = _gaussian_breakpoints(alphabet_size)
    symbol_indices = np.searchsorted(breakpoints, paa, side="right")
    return "".join(chr(ord("a") + int(index)) for index in symbol_indices)


def _z_normalize(values: np.ndarray) -> np.ndarray:
    mean = float(values.mean())
    std = float(values.std(ddof=0))
    if np.isclose(std, 0.0):
        return np.zeros_like(values)
    return (values - mean) / std


def _piecewise_aggregate(values: np.ndarray, segments: int) -> np.ndarray:
    chunks = np.array_split(values, segments)
    return np.asarray([float(chunk.mean()) for chunk in chunks], dtype=float)


def _gaussian_breakpoints(alphabet_size: int) -> np.ndarray:
    dist = NormalDist()
    points = [dist.inv_cdf(i / alphabet_size) for i in range(1, alphabet_size)]
    return np.asarray(points, dtype=float)


def astride_encode(
    df: pd.DataFrame,
    column: str = "Close",
    n_segments: int = 16,
    alphabet_size: int = 8,
    penalty: float = 3.0,
) -> SymbolicStats:
    """Encode a series with ASTRIDE-style adaptive symbolization.

    Uses change-point detection (ruptures) to find segment boundaries that
    align with regime changes, then quantizes segment means into symbols.
    Unlike SAX, segments have variable length.

    :param df: OHLCV DataFrame.
    :param column: Price column to encode.
    :param n_segments: Approximate number of segments.
    :param alphabet_size: Number of symbols in alphabet.
    :param penalty: Ruptures PELT penalty parameter.
    :return: Structured symbolic encoding result.
    """
    validate_ohlcv_frame(df)
    if column not in df.columns:
        raise ValidationError(f"Column '{column}' does not exist in DataFrame.")
    if n_segments < 2:
        raise ValidationError("n_segments must be >= 2.")
    if alphabet_size < 2 or alphabet_size > 26:
        raise ValidationError("alphabet_size must be between 2 and 26.")
    if rpt is None:
        raise ValidationError(
            "ASTRIDE encoding requires the 'ruptures' package. Install with: pip install narrata[symbolic]"
        )

    values = pd.to_numeric(df[column], errors="coerce").dropna().to_numpy(dtype=float)
    if values.size < n_segments:
        raise ValidationError("Not enough data points for requested n_segments.")

    normalized = _z_normalize(values)
    symbols = _astride_encode_core(normalized, n_segments=n_segments, alphabet_size=alphabet_size, penalty=penalty)

    return SymbolicStats(
        method="ASTRIDE",
        word_size=len(symbols),
        alphabet_size=alphabet_size,
        symbols=symbols,
    )


def describe_astride(stats: SymbolicStats) -> str:
    """Render ASTRIDE symbolic encoding as one line.

    :param stats: Symbolic encoding result.
    :return: Human-readable symbolic description.
    """
    return f"ASTRIDE({stats.word_size}): {stats.symbols}"


def _astride_encode_core(values: np.ndarray, n_segments: int, alphabet_size: int, penalty: float) -> str:
    algo = rpt.Pelt(model="rbf", min_size=max(2, values.size // (n_segments * 2))).fit(values.reshape(-1, 1))  # type: ignore[union-attr]
    bkpts = algo.predict(pen=penalty)

    starts = [0] + bkpts[:-1]
    ends = bkpts
    segment_means = np.asarray(
        [float(values[s:e].mean()) for s, e in zip(starts, ends, strict=True)],
        dtype=float,
    )

    if segment_means.size < 2:
        return "a" * max(1, len(segment_means))

    quantile_boundaries = np.quantile(segment_means, np.linspace(0, 1, alphabet_size + 1))
    bins = quantile_boundaries[1:-1]
    symbol_indices = np.searchsorted(bins, segment_means, side="right")
    return "".join(chr(ord("a") + min(int(idx), alphabet_size - 1)) for idx in symbol_indices)
