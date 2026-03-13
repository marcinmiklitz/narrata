---
name: narrata
description: Use when users need to turn OHLCV time series into compact, deterministic, LLM-ready narrative text (full narrate output or modular summary/regime/indicator/symbolic/pattern/levels analysis), including narrata MCP usage.
---

# narrata Skill

Use this skill for OHLCV-to-text workflows.

## Default workflow

1. Build a pandas DataFrame with:
   - Datetime index
   - `Open`, `High`, `Low`, `Close`, `Volume` columns
2. Use default narration first:
   - `from narrata import narrate`
   - `text = narrate(df)`
3. Only split into module-level APIs if the user needs custom composition.

## Public APIs to prefer

- `narrate`
- `compare`
- `analyze_summary`, `describe_summary`
- `analyze_regime`, `describe_regime`
- `analyze_indicators`, `describe_indicators`
- `sax_encode`, `describe_sax`
- `astride_encode`, `describe_astride`
- `detect_patterns`, `describe_patterns`, `describe_candlestick`
- `find_support_resistance`, `describe_support_resistance`
- `digit_tokenize`
- `from_ccxt`, `from_coingecko`
- `to_plain`, `to_markdown_kv`, `to_toon`, `to_json`

Avoid internal/private helpers unless explicitly requested.

## Intraday awareness

narrata auto-detects sub-daily frequencies (`1min`, `5min`, `15min`, `30min`, `hourly`) and scales indicator defaults (SMA crossover, volume lookback, volatility lookback) to match daily-equivalent horizons. For patchy or unevenly-spaced data, pass the frequency explicitly: `narrate(df, frequency="15min")`, `--frequency 15min` (CLI), or the `frequency` field in MCP tools. Output labels adapt automatically (`"SMA 10/40"`, `"26-bar avg"`, `"bars ago"`).

## Crypto data adapters

- `from_ccxt(ohlcv, ticker=...)` — converts ccxt's `[[ts, O, H, L, C, V], ...]` to narrata DataFrame
- `from_coingecko(data, ticker=...)` — converts CoinGecko market chart response (close-only) to DataFrame
- yfinance crypto tickers (e.g. `BTC-USD`) work directly with `narrate()`, no adapter needed

Close-only data (CoinGecko, or any DataFrame with just a `Close` column) works — patterns/candlestick sections are silently omitted, everything else runs normally.

## Silent section skipping

By default, narrata silently omits sections with insufficient data or empty results (e.g. "none detected"). This minimizes token usage. Use `verbose=True` / `--verbose` to show all sections.

## Data handling guidance

- Patchy/misaligned numeric values are valid; do not reject them by default.
- Structural issues should still fail fast:
  - missing OHLCV columns
  - non-datetime index
  - unsorted/duplicate timestamps where the caller does not want auto-fix
- For user-facing examples, use 80+ rows when demonstrating full `narrate(df)` output.

## CLI guidance

narrata ships a CLI that reads OHLCV data from CSV, TSV, or Parquet and prints narration to stdout:

```bash
# Format auto-detected from extension
narrata data.csv --ticker AAPL
narrata data.tsv --ticker AAPL
narrata data.parquet --ticker AAPL

# Stdin (defaults to CSV; use --input-format for others)
cat data.csv | narrata --ticker AAPL
cat data.tsv | narrata --input-format tsv --ticker AAPL

# Output formats: plain, markdown_kv, toon, json
narrata data.csv --format json

# Precision (default: 2; use 0 for BTC, 4 for forex)
narrata data.csv --precision 0

# ASTRIDE instead of SAX
narrata data.csv --symbolic-method astride

# Disable specific sections
narrata data.csv --no-summary --no-sparkline --no-regime
narrata data.csv --no-indicators --no-symbolic --no-patterns --no-support-resistance

# Show all sections including empty ones
narrata data.csv --verbose

# Compare two periods
narrata compare q1.csv q2.csv --ticker AAPL
```

The input must have a datetime index column and at least a `Close` column (Volume optional, column names case-insensitive). All `narrate()` parameters are exposed as flags — run `narrata --help` for the full list.

Install: `uv tool install narrata[all]` or `pip install narrata[all]`.

## MCP guidance

If user wants MCP integration:
- Package: `src/narrata-mcp` (`narrata_mcp`)
- Run locally via stdio:
  - `uv run --project src/narrata-mcp --no-sync narrata-mcp`
- Prefer exposed high-level tools:
  - `narrata_narrate_ohlcv`
  - `narrata_compare_ohlcv`
  - `narrata_summary_ohlcv`
  - `narrata_regime_ohlcv`
  - `narrata_indicators_ohlcv`
  - `narrata_symbolic_sax_ohlcv`
  - `narrata_symbolic_astride_ohlcv`
  - `narrata_patterns_ohlcv`
  - `narrata_levels_ohlcv`

## Repo docs sync

When changing narration behavior:
- refresh generated example blocks:
  - `make update-examples`
- then run:
  - `make check`
  - `make test`
