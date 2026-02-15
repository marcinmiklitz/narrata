<p align="center">
  <img src="./assets/logo_narrata_github.png" alt="narrata logo" width="560" />
</p>

<p align="center">
  <a href="https://github.com/marcinmiklitz/narrata/actions/workflows/tests.yml">
    <img src="https://github.com/marcinmiklitz/narrata/actions/workflows/tests.yml/badge.svg?branch=main" alt="Tests" />
  </a>
  <a href="https://pypi.org/project/narrata/">
    <img src="https://img.shields.io/pypi/v/narrata" alt="PyPI" />
  </a>
  <a href="https://pypi.org/project/narrata-mcp/">
    <img src="https://img.shields.io/pypi/v/narrata-mcp?label=narrata-mcp" alt="narrata-mcp on PyPI" />
  </a>
  <a href="https://pypi.org/project/narrata/">
    <img src="https://img.shields.io/pypi/dm/narrata" alt="Downloads" />
  </a>
  <img src="https://img.shields.io/badge/python-3.11%2B-blue.svg" alt="Python 3.11+" />
  <a href="https://github.com/marcinmiklitz/narrata/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/marcinmiklitz/narrata" alt="License" />
  </a>
  <a href="https://marcinmiklitz.github.io/narrata/">
    <img src="https://img.shields.io/badge/docs-mkdocs-blue.svg" alt="Docs" />
  </a>
</p>

`narrata` turns price series into short text that an LLM can reason about quickly.

It is designed for situations where a chart is easy for a human to read, but you need an agent to consume the same information as text.

## Installation

From PyPI:

```bash
pip install narrata
```

With optional extras for enhanced backends:

```bash
pip install "narrata[all]"
```

## Quickstart

`narrate(...)` takes a pandas OHLCV DataFrame with a datetime index.

```python
import yfinance as yf
from narrata import narrate

df = yf.download("AAPL", period="1y", multi_level_index=False)
print(narrate(df, ticker="AAPL"))
```

Any data source works — yfinance, OpenBB, CSV, database — as long as you have a DataFrame with `Open`, `High`, `Low`, `Close`, `Volume` columns and a `DatetimeIndex`.

Example output:

```text
AAPL (120 pts, daily): ▁▁▂▂▂▃▃▄▄▄▄▅▆▆▆▆▇▇██
Date range: 2025-01-01 to 2025-04-30
Range: [$139.99, $175.68]  Mean: $157.35  Std: $10.33
Start: $140.00  End: $175.19  Change: +25.14%
Regime: Uptrend since 2025-01-02 (low volatility)
RSI(14): 65.1 (neutral-bullish)  MACD: bullish crossover 1 day ago
BB: near upper band
Volume: 0.98x 20-day avg (average)
Volatility: 23rd percentile (low)
SAX(16): aaabbccdeeffgggh
Patterns: Ascending triangle forming since 2025-03-02
Candlestick: Doji on 2025-04-29
Support: $145.13 (13 touches), $139.99 (6 touches)  Resistance: $175.68 (3 touches)
```

## Token compression

The whole point of narrata is fitting price context into an LLM prompt without wasting tokens.
On a 251-day AAPL OHLCV DataFrame:

| Representation | Tokens (gpt-4o) |
|---|---|
| `df.to_string()` | ~9,000 |
| `df.to_csv()` | ~10,700 |
| `narrate(df)` | **~260** |

That's **~35–41x compression** while preserving regime, indicators, patterns, and support/resistance.

<details>
<summary>Reproduce this comparison</summary>

```python
import tiktoken
import pandas as pd
from narrata import narrate

enc = tiktoken.encoding_for_model("gpt-4o")
# df = your OHLCV DataFrame
print(f"Raw:     {len(enc.encode(df.to_string())):,} tokens")
print(f"CSV:     {len(enc.encode(df.to_csv())):,} tokens")
print(f"narrate: {len(enc.encode(narrate(df))):,} tokens")
```

</details>

## Fallback vs extras (same input)

<!-- BACKEND_COMPARISON:START -->
Using the same deterministic 252-point dataset:

Use separate clean virtual environments when comparing fallback vs extras.

Fallback-only (`pip install narrata`):

```text
AAPL (252 pts, business-daily): ▁▂▁▂▂▃▃▃▄▄▄▅▆▆▆▆▇▇▇█
Date range: 2024-01-02 to 2024-12-18
Range: [$140.61, $201.32]  Mean: $170.44  Std: $17.52
Start: $141.05  End: $201.32  Change: +42.73%
Regime: Uptrend since 2024-12-10 (low volatility)
RSI(14): 72.9 (overbought)  MACD: bullish crossover 7 days ago
BB: above upper band
SMA 50/200: golden cross
Volume: 0.95x 20-day avg (average)
Volatility: 1st percentile (extremely low)
SAX(16): aaabbcdeefggghhh
Patterns: Ascending triangle forming since 2024-09-26
Candlestick: Bullish Engulfing on 2024-12-17
Support: $193.16 (27 touches), $156.63 (26 touches)  Resistance: $201.32 (4 touches)
```

With extras (`pip install "narrata[all]"`):

```text
AAPL (252 pts, business-daily): ▁▂▁▂▂▃▃▃▄▄▄▅▆▆▆▆▇▇▇█
Date range: 2024-01-02 to 2024-12-18
Range: [$140.61, $201.32]  Mean: $170.44  Std: $17.52
Start: $141.05  End: $201.32  Change: +42.73%
Regime: Uptrend since 2024-10-02 (low volatility)
RSI(14): 72.9 (overbought)  MACD: bullish crossover 7 days ago
BB: above upper band
SMA 50/200: golden cross
Volume: 0.95x 20-day avg (average)
Volatility: 1st percentile (extremely low)
SAX(16): aaabbbcddefggghh
Patterns: Ascending triangle forming since 2024-09-26
Candlestick: Doji on 2024-12-11
Support: $193.16 (27 touches), $156.63 (26 touches)  Resistance: $201.32 (4 touches)
```

Main differences in this run:
- `Regime` changed: `Regime: Uptrend since 2024-12-10 (low volatility)` -> `Regime: Uptrend since 2024-10-02 (low volatility)`
- `SAX(16)` changed: `SAX(16): aaabbcdeefggghhh` -> `SAX(16): aaabbbcddefggghh`
- `Candlestick` changed: `Candlestick: Bullish Engulfing on 2024-12-17` -> `Candlestick: Doji on 2024-12-11`
<!-- BACKEND_COMPARISON:END -->

## Compose your own output

Use lower-level functions when you want full control:

```python
from narrata import analyze_summary, describe_summary, make_sparkline

summary = analyze_summary(df)
text_block = describe_summary(summary)
spark = make_sparkline(df["Close"].tolist(), width=12)

print(text_block)
print(f"Close sparkline: {spark}")
```

## Output formats

You can keep the output plain, render as Markdown key-value, or serialize to TOON.

```python
from narrata import narrate

markdown_text = narrate(df, output_format="markdown_kv")
plain_text = narrate(df, output_format="plain")
```

## Digit Splitting for LLM Robustness

`digit_tokenize(...)` is useful when your downstream model struggles with long or dense numeric strings.

Why this can help:

- Some tokenizers split long numbers in inconsistent chunks.
- Smaller models can be less stable when many decimals/signs appear close together.
- Splitting digits can reduce numeric parsing ambiguity in prompts and tool outputs.

When to use it:

- Use it for numeric-heavy prompts (prices, percentages, IDs, many decimals).
- Keep it off when human readability matters more than model robustness.

Example:

```python
from narrata import digit_tokenize

print(digit_tokenize("Price 171.24, move +3.2%"))
# <digits-split>
# Price 1 7 1 . 2 4 , move + 3 . 2 %
```

## Dependencies

Optional extras:

- `indicators`: `pandas-ta-openbb` (import path remains `pandas_ta`)
- `patterns`: `pandas-ta-openbb` (candlestick pattern backend)
- `regimes`: `ruptures` (for change-point regime detection)
- `symbolic`: `tslearn`, `ruptures` (`ruptures` currently supports Python < 3.14)
- `all`: install all compatible extras for your interpreter

## Agent Integrations

### narrata Skill

A reusable skill is included at `skills/narrata/SKILL.md`.

Depending on your CLI:

- Anthropic-style skills dir: copy to `~/.agents/skills/narrata/`
- Codex-style skills dir: copy to `~/.codex/skills/narrata/`

```bash
mkdir -p ~/.agents/skills/narrata
cp skills/narrata/SKILL.md ~/.agents/skills/narrata/SKILL.md
```

### FastMCP Server

A dedicated MCP package is available on [PyPI](https://pypi.org/project/narrata-mcp/).
Full docs: [`src/narrata-mcp/README.md`](https://github.com/marcinmiklitz/narrata/blob/main/src/narrata-mcp/README.md).

```bash
pip install narrata-mcp
narrata-mcp
```

<details>
<summary>Claude Desktop configuration</summary>

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

</details>

## Features

- Input validation for OHLCV DataFrames
- Summary analysis with date range context
- Regime classification (`Uptrend` / `Downtrend` / `Ranging`)
- RSI and MACD interpretation (uses `pandas_ta` indicator lines when available)
- Volume analysis (ratio to moving average)
- Bollinger Band position and squeeze detection
- Moving average crossover detection (golden/death cross)
- Volatility percentile ranking
- SAX symbolic encoding
- ASTRIDE adaptive symbolic encoding (requires `ruptures`)
- Pattern detection plus candlestick detection (`pandas_ta` first, in-house fallback)
- Support/resistance extraction
- Compact Unicode sparklines
- Output formatting helpers (`plain`, `markdown_kv`, `toon`)
- High-level `narrate(...)` composition

## FAQ

### Is narrata redundant if I already use OpenBB, yfinance, or another data SDK?

No. `narrata` is complementary.

It sits on top of your existing data layer and turns OHLCV data into compact, LLM-ready narrative text.

Typical flow:

```text
Data source (OpenBB / yfinance / CSV / DB)
        -> pandas DataFrame (OHLCV)
        -> narrata
        -> concise narrative context for an LLM
```

`narrata` is data-source-agnostic: if you can produce a standard OHLCV DataFrame, you can use it.

### Does narrata call an LLM or provide LLM endpoints?

No. This is intentional.

`narrata` is a pure Python library with deterministic, programmatic analysis and narration. It does not make LLM API calls and does not ship model endpoints.

Use it as a pipeline component:

```text
your data -> narrata text output -> your chosen LLM/runtime
```

This keeps the library lightweight, testable, and provider-agnostic.

## Citation

If you use `narrata` in research, publications, or public projects:

```bibtex
@software{miklitz_narrata,
  author  = {Miklitz, Marcin},
  title   = {narrata},
  url     = {https://github.com/marcinmiklitz/narrata},
  license = {MIT}
}
```

You can also use the GitHub "Cite this repository" button or the metadata in `CITATION.cff`.
