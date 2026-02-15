import pytest

from narrata.rendering.sparkline import BARS, downsample_evenly, make_sparkline, normalize_to_bins


def test_downsample_evenly_returns_original_when_short() -> None:
    assert downsample_evenly([1.0, 2.0], width=5) == [1.0, 2.0]


def test_downsample_evenly_reduces_length() -> None:
    values = list(range(100))
    sampled = downsample_evenly(values, width=10)
    assert len(sampled) == 10
    assert sampled[0] == 0.0
    assert sampled[-1] == 99.0


def test_normalize_to_bins_handles_flat_series() -> None:
    assert normalize_to_bins([5.0, 5.0, 5.0], bins=8) == [4, 4, 4]


def test_make_sparkline_maps_values_to_bars() -> None:
    spark = make_sparkline([0.0, 1.0, 2.0, 3.0], width=4)
    assert len(spark) == 4
    assert all(char in BARS for char in spark)
    assert spark[0] == "▁"
    assert spark[-1] == "█"


def test_make_sparkline_returns_empty_for_empty_input() -> None:
    assert make_sparkline([], width=20) == ""


def test_make_sparkline_rejects_invalid_bars() -> None:
    with pytest.raises(ValueError, match="at least two"):
        make_sparkline([1, 2, 3], bars="x")
