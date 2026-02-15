# narrata-mcp

`narrata-mcp` is a FastMCP server exposing narrata's high-level APIs.

## Install (recommended)

From PyPI:

```bash
pip install narrata-mcp
```

`narrata` is installed automatically as a dependency.

## Run (stdio)

```bash
narrata-mcp
```

Alternative without installing globally:

```bash
uvx narrata-mcp
```

## Local development in this monorepo

```bash
uv sync --dev
uv run narrata-mcp
```

## Exposed tools

- `narrata_narrate_ohlcv`
- `narrata_summary_ohlcv`
- `narrata_regime_ohlcv`
- `narrata_indicators_ohlcv`
- `narrata_symbolic_sax_ohlcv`
- `narrata_symbolic_astride_ohlcv`
- `narrata_patterns_ohlcv`
- `narrata_levels_ohlcv`
