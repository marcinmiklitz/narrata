from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from typing import Any

import anyio
import pytest

mcp = pytest.importorskip("mcp")
pytest.importorskip("fastmcp")
stdio = pytest.importorskip("mcp.client.stdio")

ClientSession = mcp.ClientSession
StdioServerParameters = stdio.StdioServerParameters
stdio_client = stdio.stdio_client


def _build_points(n: int = 120) -> list[dict[str, Any]]:
    start = datetime(2025, 1, 1)
    points: list[dict[str, Any]] = []
    for idx in range(n):
        ts = start + timedelta(days=idx)
        close = 100.0 + idx * 0.2
        points.append(
            {
                "timestamp": ts.isoformat(),
                "open": close - 0.2,
                "high": close + 0.8,
                "low": close - 0.8,
                "close": close,
                "volume": 1000 + idx,
            }
        )
    return points


def _tool_text_payload(result: Any) -> dict[str, Any]:
    assert not result.isError
    assert result.content
    first = result.content[0]
    text = getattr(first, "text", None)
    assert isinstance(text, str)
    return json.loads(text)


def _open_session() -> Any:
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "narrata_mcp"],
    )
    return stdio_client(server)


# ---------------------------------------------------------------------------
# Tool listing
# ---------------------------------------------------------------------------


def test_mcp_lists_expected_tools() -> None:
    async def _run() -> None:
        async with _open_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                names = {tool.name for tool in tools.tools}
                assert names == {
                    "narrata_narrate_ohlcv",
                    "narrata_compare_ohlcv",
                    "narrata_summary_ohlcv",
                    "narrata_regime_ohlcv",
                    "narrata_indicators_ohlcv",
                    "narrata_symbolic_sax_ohlcv",
                    "narrata_symbolic_astride_ohlcv",
                    "narrata_patterns_ohlcv",
                    "narrata_levels_ohlcv",
                }

    anyio.run(_run)


# ---------------------------------------------------------------------------
# narrata_narrate_ohlcv
# ---------------------------------------------------------------------------


def test_narrate_default() -> None:
    async def _run() -> None:
        payload = {"points": _build_points(120), "ticker": "AAPL"}
        async with _open_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("narrata_narrate_ohlcv", {"params": payload})
                data = _tool_text_payload(result)
                assert "text" in data
                text = data["text"]
                assert "AAPL (" in text
                assert "Date range:" in text
                assert "Regime:" in text
                assert "RSI(" in text
                assert "SAX(" in text
                assert "Support:" in text

    anyio.run(_run)


def test_narrate_with_currency_symbol() -> None:
    async def _run() -> None:
        payload = {"points": _build_points(120), "ticker": "AAPL", "currency_symbol": "$"}
        async with _open_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("narrata_narrate_ohlcv", {"params": payload})
                data = _tool_text_payload(result)
                assert "$" in data["text"]

    anyio.run(_run)


def test_narrate_no_currency_by_default() -> None:
    async def _run() -> None:
        payload = {"points": _build_points(120), "ticker": "AAPL"}
        async with _open_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("narrata_narrate_ohlcv", {"params": payload})
                data = _tool_text_payload(result)
                assert "$" not in data["text"]

    anyio.run(_run)


def test_narrate_section_toggles() -> None:
    async def _run() -> None:
        payload = {
            "points": _build_points(120),
            "ticker": "TEST",
            "include_regime": False,
            "include_indicators": False,
            "include_symbolic": False,
            "include_patterns": False,
            "include_support_resistance": False,
        }
        async with _open_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("narrata_narrate_ohlcv", {"params": payload})
                data = _tool_text_payload(result)
                text = data["text"]
                assert "TEST (" in text
                assert "Date range:" in text
                assert "Regime:" not in text
                assert "RSI(" not in text
                assert "SAX(" not in text
                assert "Support:" not in text

    anyio.run(_run)


def test_narrate_markdown_kv_format() -> None:
    async def _run() -> None:
        payload = {"points": _build_points(120), "output_format": "markdown_kv"}
        async with _open_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("narrata_narrate_ohlcv", {"params": payload})
                data = _tool_text_payload(result)
                assert "**" in data["text"]

    anyio.run(_run)


def test_narrate_json_format() -> None:
    async def _run() -> None:
        payload = {"points": _build_points(120), "output_format": "json"}
        async with _open_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("narrata_narrate_ohlcv", {"params": payload})
                data = _tool_text_payload(result)
                # The text itself should be valid JSON
                inner = json.loads(data["text"])
                assert "overview" in inner

    anyio.run(_run)


def test_narrate_precision() -> None:
    async def _run() -> None:
        payload = {"points": _build_points(120), "precision": 0}
        async with _open_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("narrata_narrate_ohlcv", {"params": payload})
                data = _tool_text_payload(result)
                # With precision 0, no decimal points in Range line
                assert "Range: [100, 124]" in data["text"]

    anyio.run(_run)


def test_narrate_astride_method() -> None:
    async def _run() -> None:
        payload = {"points": _build_points(120), "symbolic_method": "astride"}
        async with _open_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("narrata_narrate_ohlcv", {"params": payload})
                data = _tool_text_payload(result)
                # Falls back to SAX when ruptures unavailable (Python 3.14+)
                assert "ASTRIDE(" in data["text"] or "SAX(" in data["text"]

    anyio.run(_run)


# ---------------------------------------------------------------------------
# narrata_summary_ohlcv
# ---------------------------------------------------------------------------


def test_summary() -> None:
    async def _run() -> None:
        payload = {"points": _build_points(120), "ticker": "AAPL"}
        async with _open_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("narrata_summary_ohlcv", {"params": payload})
                data = _tool_text_payload(result)
                assert "summary" in data
                assert "text" in data
                assert data["summary"]["ticker"] == "AAPL"
                assert isinstance(data["summary"]["start_date"], str)
                assert isinstance(data["summary"]["points"], int)
                assert data["summary"]["points"] == 120

    anyio.run(_run)


# ---------------------------------------------------------------------------
# narrata_regime_ohlcv
# ---------------------------------------------------------------------------


def test_regime() -> None:
    async def _run() -> None:
        payload = {"points": _build_points(120), "ticker": "AAPL"}
        async with _open_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("narrata_regime_ohlcv", {"params": payload})
                data = _tool_text_payload(result)
                assert "regime" in data
                assert "text" in data
                assert "trend_label" in data["regime"]
                assert "volatility_label" in data["regime"]

    anyio.run(_run)


# ---------------------------------------------------------------------------
# narrata_indicators_ohlcv
# ---------------------------------------------------------------------------


def test_indicators() -> None:
    async def _run() -> None:
        payload = {"points": _build_points(120), "ticker": "AAPL"}
        async with _open_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("narrata_indicators_ohlcv", {"params": payload})
                data = _tool_text_payload(result)
                assert "indicators" in data
                assert "text" in data
                assert "rsi_value" in data["indicators"]
                assert "macd_state" in data["indicators"]

    anyio.run(_run)


# ---------------------------------------------------------------------------
# narrata_symbolic_sax_ohlcv
# ---------------------------------------------------------------------------


def test_sax() -> None:
    async def _run() -> None:
        payload = {"points": _build_points(120), "word_size": 8, "alphabet_size": 4}
        async with _open_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("narrata_symbolic_sax_ohlcv", {"params": payload})
                data = _tool_text_payload(result)
                assert "symbolic" in data
                assert "text" in data
                assert "symbols" in data["symbolic"]
                assert "word_size" in data["symbolic"]

    anyio.run(_run)


# ---------------------------------------------------------------------------
# narrata_symbolic_astride_ohlcv
# ---------------------------------------------------------------------------


def test_astride() -> None:
    async def _run() -> None:
        payload = {"points": _build_points(120)}
        async with _open_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("narrata_symbolic_astride_ohlcv", {"params": payload})
                data = _tool_text_payload(result)
                assert "symbolic" in data
                assert "text" in data

    anyio.run(_run)


# ---------------------------------------------------------------------------
# narrata_patterns_ohlcv
# ---------------------------------------------------------------------------


def test_patterns() -> None:
    async def _run() -> None:
        payload = {"points": _build_points(120)}
        async with _open_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("narrata_patterns_ohlcv", {"params": payload})
                data = _tool_text_payload(result)
                assert "patterns" in data
                assert "chart_text" in data
                assert "candlestick_text" in data

    anyio.run(_run)


# ---------------------------------------------------------------------------
# narrata_levels_ohlcv
# ---------------------------------------------------------------------------


def test_levels() -> None:
    async def _run() -> None:
        payload = {"points": _build_points(120), "ticker": "AAPL"}
        async with _open_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("narrata_levels_ohlcv", {"params": payload})
                data = _tool_text_payload(result)
                assert "levels" in data
                assert "text" in data
                assert "supports" in data["levels"]
                assert "resistances" in data["levels"]

    anyio.run(_run)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_short_series_does_not_error() -> None:
    """Short data should degrade gracefully, not crash the server."""

    async def _run() -> None:
        payload = {"points": _build_points(10), "ticker": "SHORT"}
        async with _open_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("narrata_narrate_ohlcv", {"params": payload})
                data = _tool_text_payload(result)
                assert "SHORT (" in data["text"]

    anyio.run(_run)


def test_lowercase_column_names_accepted() -> None:
    """Server should accept lowercase OHLCV field names."""

    async def _run() -> None:
        points = _build_points(120)
        payload = {"points": points, "ticker": "LC"}
        async with _open_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("narrata_summary_ohlcv", {"params": payload})
                data = _tool_text_payload(result)
                assert data["summary"]["points"] == 120

    anyio.run(_run)


# ---------------------------------------------------------------------------
# narrata_compare_ohlcv
# ---------------------------------------------------------------------------


def test_compare_default() -> None:
    async def _run() -> None:
        payload = {
            "points_before": _build_points(120),
            "points_after": _build_points(120),
            "ticker": "AAPL",
        }
        # Shift the "after" timestamps forward by 120 days
        start_after = datetime(2025, 5, 1)
        for idx, p in enumerate(payload["points_after"]):
            ts = start_after + timedelta(days=idx)
            p["timestamp"] = ts.isoformat()
            p["close"] = 120.0 + idx * 0.3  # different trajectory

        async with _open_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("narrata_compare_ohlcv", {"params": payload})
                data = _tool_text_payload(result)
                text = data["text"]
                assert "AAPL:" in text
                assert "\u2192" in text
                assert "Price:" in text
                assert "Regime:" in text

    anyio.run(_run)


def test_compare_with_toggles() -> None:
    async def _run() -> None:
        after_points = _build_points(120)
        start_after = datetime(2025, 5, 1)
        for idx, p in enumerate(after_points):
            ts = start_after + timedelta(days=idx)
            p["timestamp"] = ts.isoformat()
            p["close"] = 120.0 + idx * 0.3

        payload = {
            "points_before": _build_points(120),
            "points_after": after_points,
            "ticker": "TEST",
            "include_regime": False,
            "include_indicators": False,
            "include_symbolic": False,
            "include_support_resistance": False,
        }
        async with _open_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("narrata_compare_ohlcv", {"params": payload})
                data = _tool_text_payload(result)
                text = data["text"]
                assert "Price:" in text
                assert "Regime:" not in text
                assert "RSI(" not in text
                assert "Support:" not in text

    anyio.run(_run)


def test_compare_json_format() -> None:
    async def _run() -> None:
        after_points = _build_points(120)
        start_after = datetime(2025, 5, 1)
        for idx, p in enumerate(after_points):
            ts = start_after + timedelta(days=idx)
            p["timestamp"] = ts.isoformat()

        payload = {
            "points_before": _build_points(120),
            "points_after": after_points,
            "output_format": "json",
        }
        async with _open_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("narrata_compare_ohlcv", {"params": payload})
                data = _tool_text_payload(result)
                inner = json.loads(data["text"])
                assert "overview" in inner
                assert "price" in inner

    anyio.run(_run)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_no_volume_accepted() -> None:
    """Points without volume should still work."""

    async def _run() -> None:
        points = _build_points(120)
        for p in points:
            del p["volume"]
        payload = {"points": points, "ticker": "NOVOL"}
        async with _open_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("narrata_narrate_ohlcv", {"params": payload})
                data = _tool_text_payload(result)
                assert "NOVOL (" in data["text"]

    anyio.run(_run)
