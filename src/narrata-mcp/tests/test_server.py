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


def test_mcp_lists_expected_tools() -> None:
    async def _run() -> None:
        async with _open_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                names = {tool.name for tool in tools.tools}
                assert names == {
                    "narrata_narrate_ohlcv",
                    "narrata_summary_ohlcv",
                    "narrata_regime_ohlcv",
                    "narrata_indicators_ohlcv",
                    "narrata_symbolic_sax_ohlcv",
                    "narrata_symbolic_astride_ohlcv",
                    "narrata_patterns_ohlcv",
                    "narrata_levels_ohlcv",
                }

    anyio.run(_run)


def test_mcp_tool_calls_return_expected_shapes() -> None:
    async def _run() -> None:
        payload = {"points": _build_points(120), "ticker": "AAPL"}
        async with _open_session() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                narrate_result = await session.call_tool("narrata_narrate_ohlcv", {"params": payload})
                narrate_payload = _tool_text_payload(narrate_result)
                assert "text" in narrate_payload
                assert "AAPL (" in narrate_payload["text"]
                assert "Date range:" in narrate_payload["text"]

                summary_result = await session.call_tool("narrata_summary_ohlcv", {"params": payload})
                summary_payload = _tool_text_payload(summary_result)
                assert "summary" in summary_payload
                assert "text" in summary_payload
                assert summary_payload["summary"]["ticker"] == "AAPL"
                assert isinstance(summary_payload["summary"]["start_date"], str)

    anyio.run(_run)
