# MCP Server

`narrata-mcp` is a [FastMCP](https://github.com/jlowin/fastmcp) server that exposes narrata's analysis as MCP tools.
Available on [PyPI](https://pypi.org/project/narrata-mcp/).

## Install

```bash
pip install narrata-mcp
```

`narrata` is installed automatically as a dependency.

## Run

```bash
narrata-mcp
```

Or without installing globally:

```bash
uvx narrata-mcp
```

## Claude Desktop configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "narrata": {
      "command": "uvx",
      "args": ["narrata-mcp"]
    }
  }
}
```

## Exposed tools

| Tool | Description |
|---|---|
| `narrata_narrate_ohlcv` | Full narration text (default entry point) |
| `narrata_summary_ohlcv` | Summary stats and text |
| `narrata_regime_ohlcv` | Regime classification (trend + volatility) |
| `narrata_indicators_ohlcv` | RSI, MACD, Bollinger, volume, volatility |
| `narrata_symbolic_sax_ohlcv` | SAX symbolic encoding |
| `narrata_symbolic_astride_ohlcv` | ASTRIDE adaptive symbolic encoding |
| `narrata_patterns_ohlcv` | Chart and candlestick patterns |
| `narrata_levels_ohlcv` | Support and resistance levels |

## Input format

All tools accept OHLCV data as a list of points:

```json
{
  "points": [
    {"timestamp": "2025-01-02", "Open": 140.0, "High": 142.0, "Low": 139.5, "Close": 141.5, "Volume": 1000000},
    {"timestamp": "2025-01-03", "Open": 141.5, "High": 143.0, "Low": 140.0, "Close": 142.8, "Volume": 1100000}
  ],
  "ticker": "AAPL"
}
```

Common optional fields:

- `ticker` — symbol for headers (default: column name)
- `column` — price column to analyze (default: `"Close"`)
- `sort_index` — sort points by timestamp (default: `true`)
- `deduplicate_timestamps` — keep latest row for duplicates (default: `true`)

See the [API Reference](reference/narrata/mcp_api.md) for the full `narrata.mcp_api` interface.
