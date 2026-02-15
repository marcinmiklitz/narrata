"""Unicode sparkline rendering for compact trend visualization."""

from collections.abc import Sequence

import numpy as np

BARS = "▁▂▃▄▅▆▇█"


def downsample_evenly(values: Sequence[float], width: int) -> list[float]:
    """Reduce a sequence to an evenly sampled representation.

    :param values: Input numeric sequence.
    :param width: Output width.
    :return: Evenly sampled values.
    """
    if width < 1:
        raise ValueError("width must be >= 1")

    array = np.asarray(values, dtype=float)
    if array.size == 0:
        return []

    if array.size <= width:
        return [float(value) for value in array.tolist()]

    indices = np.linspace(0, array.size - 1, num=width)
    sampled = array[np.round(indices).astype(int)]
    return [float(value) for value in sampled.tolist()]


def normalize_to_bins(values: Sequence[float], bins: int) -> list[int]:
    """Map numeric values to integer bins in [0, bins - 1].

    :param values: Input numeric sequence.
    :param bins: Number of target bins.
    :return: Bin indices.
    """
    if bins < 2:
        raise ValueError("bins must be >= 2")

    array = np.asarray(values, dtype=float)
    if array.size == 0:
        return []

    if not np.isfinite(array).all():
        raise ValueError("values must be finite numbers")

    low = float(array.min())
    high = float(array.max())

    if high == low:
        return [bins // 2] * int(array.size)

    scaled = (array - low) / (high - low)
    mapped = np.clip(np.rint(scaled * (bins - 1)).astype(int), 0, bins - 1)
    return [int(value) for value in mapped.tolist()]


def make_sparkline(values: Sequence[float], width: int = 20, bars: str = BARS) -> str:
    """Create a single-line Unicode sparkline.

    :param values: Input numeric sequence.
    :param width: Max number of output glyphs.
    :param bars: Glyph palette from low to high.
    :return: Sparkline string.
    """
    if len(bars) < 2:
        raise ValueError("bars must have at least two characters")

    sampled = downsample_evenly(values, width=width)
    if not sampled:
        return ""

    bins = normalize_to_bins(sampled, bins=len(bars))
    return "".join(bars[index] for index in bins)
