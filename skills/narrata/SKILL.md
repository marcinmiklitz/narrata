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
- `analyze_summary`, `describe_summary`
- `analyze_regime`, `describe_regime`
- `analyze_indicators`, `describe_indicators`
- `sax_encode`, `describe_sax`
- `astride_encode`, `describe_astride`
- `detect_patterns`, `describe_patterns`, `describe_candlestick`
- `find_support_resistance`, `describe_support_resistance`

Avoid internal/private helpers unless explicitly requested.

## Data handling guidance

- Patchy/misaligned numeric values are valid; do not reject them by default.
- Structural issues should still fail fast:
  - missing OHLCV columns
  - non-datetime index
  - unsorted/duplicate timestamps where the caller does not want auto-fix
- For user-facing examples, use 80+ rows when demonstrating full `narrate(df)` output.

## MCP guidance

If user wants MCP integration:
- Package: `src/narrata-mcp` (`narrata_mcp`)
- Run locally via stdio:
  - `uv run --project src/narrata-mcp --no-sync narrata-mcp`
- Prefer exposed high-level tools:
  - `narrata_narrate_ohlcv`
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
