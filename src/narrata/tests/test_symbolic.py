import numpy as np
import pandas as pd

import narrata.analysis.symbolic as symbolic
from narrata.analysis.symbolic import describe_sax, sax_encode


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
