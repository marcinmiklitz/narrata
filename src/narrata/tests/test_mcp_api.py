from __future__ import annotations

import pandas as pd

from narrata.mcp_api import (
    indicators_from_records,
    narrate_from_records,
    ohlcv_records_to_frame,
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
