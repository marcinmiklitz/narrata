import numpy as np
import pandas as pd
import pytest

import narrata.analysis.symbolic as symbolic
from narrata.analysis.symbolic import astride_encode, describe_astride, describe_sax, sax_encode
from narrata.exceptions import ValidationError

requires_ruptures = pytest.mark.skipif(
    __import__("importlib").util.find_spec("ruptures") is None,
    reason="ruptures not installed (unavailable on Python 3.14+)",
)


def test_sax_encode_returns_symbolic_stats(sample_ohlcv_df: pd.DataFrame) -> None:
    stats = sax_encode(sample_ohlcv_df, word_size=16, alphabet_size=8)
    assert stats.method == "SAX"
    assert len(stats.symbols) == 16
    assert set(stats.symbols).issubset(set("abcdefgh"))


def test_describe_sax_format(sample_ohlcv_df: pd.DataFrame) -> None:
    text = describe_sax(sax_encode(sample_ohlcv_df, word_size=12, alphabet_size=6))
    assert text.startswith("SAX(12): ")


def test_sax_encode_prefers_tslearn_when_available(monkeypatch, sample_ohlcv_df: pd.DataFrame) -> None:
    class FakeSAX:
        def __init__(self, n_segments: int, alphabet_size_avg: int, scale: bool) -> None:
            assert n_segments == 4
            assert alphabet_size_avg == 4
            assert scale is True

        def fit_transform(self, values):
            assert values.shape[0] == 1
            return np.asarray([[[0], [1], [2], [3]]], dtype=int)

    def should_not_be_called(*_args, **_kwargs):
        raise AssertionError("In-house fallback should not be used when tslearn is available.")

    monkeypatch.setattr(symbolic, "SymbolicAggregateApproximation", FakeSAX)
    monkeypatch.setattr(symbolic, "_sax_encode_inhouse", should_not_be_called)

    stats = symbolic.sax_encode(sample_ohlcv_df, word_size=4, alphabet_size=4)
    assert stats.symbols == "abcd"


def test_sax_encode_falls_back_when_tslearn_missing(monkeypatch, sample_ohlcv_df: pd.DataFrame) -> None:
    monkeypatch.setattr(symbolic, "SymbolicAggregateApproximation", None)
    monkeypatch.setattr(symbolic, "_sax_encode_inhouse", lambda **_kwargs: "zzzz")

    stats = symbolic.sax_encode(sample_ohlcv_df, word_size=4, alphabet_size=4)
    assert stats.symbols == "zzzz"


def test_sax_rejects_small_word_size(sample_ohlcv_df: pd.DataFrame) -> None:
    with pytest.raises(ValidationError, match="word_size must be >= 2"):
        sax_encode(sample_ohlcv_df, word_size=1)


def test_sax_rejects_bad_alphabet_size(sample_ohlcv_df: pd.DataFrame) -> None:
    with pytest.raises(ValidationError, match="alphabet_size must be between"):
        sax_encode(sample_ohlcv_df, alphabet_size=1)
    with pytest.raises(ValidationError, match="alphabet_size must be between"):
        sax_encode(sample_ohlcv_df, alphabet_size=27)


def test_sax_rejects_missing_column(sample_ohlcv_df: pd.DataFrame) -> None:
    with pytest.raises(ValidationError, match="does not exist"):
        sax_encode(sample_ohlcv_df, column="NonExistent")


@requires_ruptures
def test_astride_encode_returns_symbolic_stats(sample_ohlcv_df: pd.DataFrame) -> None:
    stats = astride_encode(sample_ohlcv_df, n_segments=8, alphabet_size=4)
    assert stats.method == "ASTRIDE"
    assert len(stats.symbols) > 0
    assert set(stats.symbols).issubset(set("abcdefghijklmnopqrstuvwxyz"))


@requires_ruptures
def test_describe_astride_format(sample_ohlcv_df: pd.DataFrame) -> None:
    stats = astride_encode(sample_ohlcv_df, n_segments=8, alphabet_size=4)
    text = describe_astride(stats)
    assert text.startswith("ASTRIDE(")


def test_astride_rejects_small_n_segments(sample_ohlcv_df: pd.DataFrame) -> None:
    with pytest.raises(ValidationError, match="n_segments must be >= 2"):
        astride_encode(sample_ohlcv_df, n_segments=1)


def test_astride_rejects_bad_alphabet(sample_ohlcv_df: pd.DataFrame) -> None:
    with pytest.raises(ValidationError, match="alphabet_size must be between"):
        astride_encode(sample_ohlcv_df, alphabet_size=1)


def test_astride_rejects_missing_column(sample_ohlcv_df: pd.DataFrame) -> None:
    with pytest.raises(ValidationError, match="does not exist"):
        astride_encode(sample_ohlcv_df, column="NonExistent")


def test_astride_rejects_when_ruptures_missing(monkeypatch, sample_ohlcv_df: pd.DataFrame) -> None:
    monkeypatch.setattr(symbolic, "rpt", None)
    with pytest.raises(ValidationError, match="ruptures"):
        astride_encode(sample_ohlcv_df)


def test_sax_rejects_insufficient_data() -> None:
    index = pd.date_range("2025-01-01", periods=5, freq="D")
    df = pd.DataFrame({"Close": [100.0, 101.0, 102.0, 103.0, 104.0]}, index=index)
    with pytest.raises(ValidationError, match="Not enough data"):
        sax_encode(df, word_size=16)


@requires_ruptures
def test_astride_rejects_insufficient_data() -> None:
    index = pd.date_range("2025-01-01", periods=5, freq="D")
    df = pd.DataFrame({"Close": [100.0, 101.0, 102.0, 103.0, 104.0]}, index=index)
    with pytest.raises(ValidationError, match="Not enough data"):
        astride_encode(df, n_segments=16)
