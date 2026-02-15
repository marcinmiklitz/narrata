from datetime import date

import pandas as pd

import narrata.analysis.regimes as regimes
from narrata.analysis.regimes import analyze_regime, describe_regime


def test_analyze_regime_returns_expected_labels(sample_ohlcv_df: pd.DataFrame) -> None:
    stats = analyze_regime(sample_ohlcv_df)
    assert stats.trend_label in {"Uptrend", "Downtrend", "Ranging"}
    assert stats.volatility_label in {"low", "high"}


def test_describe_regime_format(sample_ohlcv_df: pd.DataFrame) -> None:
    text = describe_regime(analyze_regime(sample_ohlcv_df))
    assert text.startswith("Regime:")
    assert "since" in text


def test_analyze_regime_fallback_without_ruptures(monkeypatch, sample_ohlcv_df: pd.DataFrame) -> None:
    monkeypatch.setattr(regimes, "rpt", None)
    stats = analyze_regime(sample_ohlcv_df)
    assert stats.trend_label in {"Uptrend", "Downtrend", "Ranging"}
    assert stats.volatility_label in {"low", "high"}


def test_analyze_regime_uses_ruptures_backend_when_available(monkeypatch, sample_ohlcv_df: pd.DataFrame) -> None:
    class FakePelt:
        def __init__(self, model: str, min_size: int) -> None:
            self.model = model
            self.min_size = min_size
            self._n = 0

        def fit(self, signal):
            self._n = len(signal)
            return self

        def predict(self, pen: float):
            assert pen >= 0.1
            return [40, self._n]

    class FakeRuptures:
        Pelt = FakePelt

    def should_not_be_called(*_args, **_kwargs):
        raise AssertionError("Rolling fallback should not be used when ruptures backend is available.")

    monkeypatch.setattr(regimes, "rpt", FakeRuptures())
    monkeypatch.setattr(regimes, "_analyze_with_rolling", should_not_be_called)

    stats = analyze_regime(sample_ohlcv_df)
    expected_start = sample_ohlcv_df["Close"].pct_change().dropna().index[40].date()
    assert stats.start_date == expected_start


def test_analyze_regime_uses_rolling_when_ruptures_missing(monkeypatch, sample_ohlcv_df: pd.DataFrame) -> None:
    expected = ("Ranging", "low", date(2025, 1, 31))

    def fake_rolling(*_args, **_kwargs):
        return expected

    def should_not_be_called(*_args, **_kwargs):
        raise AssertionError("Ruptures backend should not be called when missing.")

    monkeypatch.setattr(regimes, "rpt", None)
    monkeypatch.setattr(regimes, "_analyze_with_rolling", fake_rolling)
    monkeypatch.setattr(regimes, "_analyze_with_ruptures", should_not_be_called)

    stats = analyze_regime(sample_ohlcv_df)
    assert (stats.trend_label, stats.volatility_label, stats.start_date) == expected
