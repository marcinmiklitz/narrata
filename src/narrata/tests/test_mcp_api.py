from __future__ import annotations

import pandas as pd
import pytest

from narrata.exceptions import ValidationError
from narrata.mcp_api import (
    astride_from_records,
    compare_from_records,
    indicators_from_records,
    levels_from_records,
    narrate_from_records,
    ohlcv_records_to_frame,
    patterns_from_records,
    regime_from_records,
    sax_from_records,
    summary_from_records,
)


def _records_from_frame(df: pd.DataFrame) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for ts, row in df.iterrows():
        records.append(
            {
                "timestamp": ts.isoformat(),
                "open": row["Open"],
                "high": row["High"],
                "low": row["Low"],
                "close": row["Close"],
                "volume": row["Volume"],
            }
        )
    return records


def test_ohlcv_records_to_frame_handles_patchy_and_deduplicates(sample_ohlcv_df: pd.DataFrame) -> None:
    records = _records_from_frame(sample_ohlcv_df.head(12))
    # Add duplicate timestamp and patchy values in different fields.
    duplicate = dict(records[3])
    duplicate["close"] = None
    duplicate["volume"] = None
    records.append(duplicate)

    frame = ohlcv_records_to_frame(records, ticker="AAPL")
    assert isinstance(frame.index, pd.DatetimeIndex)
    assert frame.index.is_monotonic_increasing
    assert not frame.index.has_duplicates
    assert "Close" in frame.columns
    assert "Volume" in frame.columns
    assert frame.attrs["ticker"] == "AAPL"


def test_narrate_from_records_returns_default_text(sample_ohlcv_df: pd.DataFrame) -> None:
    records = _records_from_frame(sample_ohlcv_df)
    text = narrate_from_records(records, ticker="AAPL")
    assert text.startswith("AAPL (")
    assert "Date range:" in text
    assert "Regime:" in text
    assert "Support:" in text


def test_ohlcv_records_to_frame_allows_close_only_records() -> None:
    records = [
        {"timestamp": "2024-01-01T00:00:00", "close": 100.0},
        {"timestamp": "2024-01-02T00:00:00", "close": 101.0},
    ]

    frame = ohlcv_records_to_frame(records, ticker="BTC")

    assert list(frame.columns) == ["Close"]
    assert frame.attrs["ticker"] == "BTC"


def test_narrate_from_records_allows_close_only_records() -> None:
    records = [{"timestamp": f"2024-01-{day:02d}T00:00:00", "close": 100.0 + day} for day in range(1, 25)]

    text = narrate_from_records(records, ticker="BTC", include_patterns=True)

    assert text.startswith("BTC (")
    assert "Date range:" in text
    assert "Support:" in text
    assert "Candlestick:" not in text


def test_summary_from_records_returns_structured_and_text(sample_ohlcv_df: pd.DataFrame) -> None:
    records = _records_from_frame(sample_ohlcv_df)
    payload = summary_from_records(records, ticker="AAPL")
    assert "summary" in payload
    assert "text" in payload
    summary = payload["summary"]
    assert isinstance(summary, dict)
    assert isinstance(summary["start_date"], str)
    assert isinstance(summary["end_date"], str)
    assert str(payload["text"]).startswith("AAPL (")


def test_indicators_from_records_handles_patchy_inputs(sample_ohlcv_df: pd.DataFrame) -> None:
    frame = sample_ohlcv_df.copy()
    frame.loc[frame.index[::13], "Close"] = pd.NA
    frame.loc[frame.index[::17], "Volume"] = pd.NA
    records = _records_from_frame(frame)

    payload = indicators_from_records(records)
    assert "indicators" in payload
    assert "text" in payload
    assert "RSI(14):" in str(payload["text"])


def test_regime_from_records(sample_ohlcv_df: pd.DataFrame) -> None:
    records = _records_from_frame(sample_ohlcv_df)
    payload = regime_from_records(records, ticker="AAPL")
    assert "regime" in payload
    assert "text" in payload
    assert "Regime:" in payload["text"]


def test_sax_from_records(sample_ohlcv_df: pd.DataFrame) -> None:
    records = _records_from_frame(sample_ohlcv_df)
    payload = sax_from_records(records)
    assert "symbolic" in payload
    assert "text" in payload
    assert "SAX(" in payload["text"]


def test_astride_from_records(sample_ohlcv_df: pd.DataFrame) -> None:
    records = _records_from_frame(sample_ohlcv_df)
    payload = astride_from_records(records)
    assert "symbolic" in payload
    assert "text" in payload
    assert "ASTRIDE(" in payload["text"]


def test_patterns_from_records(sample_ohlcv_df: pd.DataFrame) -> None:
    records = _records_from_frame(sample_ohlcv_df)
    payload = patterns_from_records(records)
    assert "patterns" in payload
    assert "chart_text" in payload
    assert "candlestick_text" in payload


def test_levels_from_records(sample_ohlcv_df: pd.DataFrame) -> None:
    records = _records_from_frame(sample_ohlcv_df)
    payload = levels_from_records(records)
    assert "levels" in payload
    assert "text" in payload
    assert "Support:" in payload["text"]


def test_compare_from_records(sample_ohlcv_df: pd.DataFrame) -> None:
    mid = len(sample_ohlcv_df) // 2
    records_before = _records_from_frame(sample_ohlcv_df.iloc[:mid])
    records_after = _records_from_frame(sample_ohlcv_df.iloc[mid:])
    text = compare_from_records(records_before, records_after, ticker="AAPL")
    assert "AAPL:" in text
    assert "→" in text


def test_ohlcv_records_to_frame_rejects_empty() -> None:
    with pytest.raises(ValidationError, match="At least one"):
        ohlcv_records_to_frame([])


def test_ohlcv_records_to_frame_rejects_unparseable_timestamps() -> None:
    records = [{"timestamp": "not-a-date", "close": 100.0}]
    with pytest.raises(ValidationError, match="no parseable datetime"):
        ohlcv_records_to_frame(records)


def test_ohlcv_records_to_frame_rejects_missing_close() -> None:
    records = [{"timestamp": "2024-01-01", "open": 100.0}]
    with pytest.raises(ValidationError, match="missing required.*Close"):
        ohlcv_records_to_frame(records)


def test_ohlcv_records_to_frame_resolves_alternate_timestamp_field() -> None:
    records = [
        {"datetime": "2024-01-01", "close": 100.0},
        {"datetime": "2024-01-02", "close": 101.0},
    ]
    frame = ohlcv_records_to_frame(records, timestamp_field="datetime")
    assert len(frame) == 2


def test_ohlcv_records_to_frame_fallback_timestamp_columns() -> None:
    records = [
        {"date": "2024-01-01", "close": 100.0},
        {"date": "2024-01-02", "close": 101.0},
    ]
    frame = ohlcv_records_to_frame(records)
    assert len(frame) == 2


def test_ohlcv_records_to_frame_no_timestamp_column() -> None:
    records = [{"price": 100.0, "close": 100.0}]
    with pytest.raises(ValidationError, match="timestamp column"):
        ohlcv_records_to_frame(records)
