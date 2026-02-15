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
AAPL (251 pts, daily): ▅▄▃▁▂▁▁▂▂▂▄▄▆▇▇██▆▆▆
Date range: 2025-02-14 to 2026-02-13
Range: [$171.67, $285.92]  Mean: $235.06  Std: $28.36
Start: $243.54  End: $255.78  Change: +5.03%
Regime: Uptrend since 2025-05-07 (low volatility)
RSI(14): 39.6 (neutral-bearish)  MACD: bearish crossover 0 days ago
BB: lower half
SMA 50/200: golden cross
Volume: 0.94x 20-day avg (average)
Volatility: 84th percentile (high)
SAX(16): ecabbabbdegghhhg
Patterns: none detected
Candlestick: Inside Bar on 2026-02-10
Support: $201.77 (26 touches), $208.38 (23 touches)  Resistance: $270.88 (24 touches), $257.57 (22 touches)
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

Reproduce this comparison:

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

## Fallback vs extras (same input)

<!-- BACKEND_COMPARISON:START -->
Using the same static real-market MSFT dataset (251 daily points, yfinance fixture):

Use separate clean virtual environments when comparing fallback vs extras.

Fallback-only (`pip install narrata`):

```text
MSFT (251 pts, daily): ▂▁▁▁▃▄▅▇▇█▇███▇▆▅▆▆▂
Date range: 2025-02-14 to 2026-02-13
Range: [$354.56, $542.07]  Mean: $466.98  Std: $49.62
Start: $408.43  End: $401.32  Change: -1.74%
Regime: Downtrend since 2026-01-29 (high volatility)
RSI(14): 32.4 (neutral-bearish)  MACD: bearish crossover 11 days ago
BB: lower half
SMA 50/200: death cross 17 days ago
Volume: 0.74x 20-day avg (below average)
Volatility: 94th percentile (extremely high)
SAX(16): aaabdfggggggffdb
Patterns: none detected
Candlestick: Inside Bar on 2026-02-13
Support: $393.67 (15 touches), $378.77 (8 touches)  Resistance: $510.83 (34 touches), $481.63 (21 touches)
```

With extras (`pip install "narrata[all]"`):

```text
MSFT (251 pts, daily): ▂▁▁▁▃▄▅▇▇█▇███▇▆▅▆▆▂
Date range: 2025-02-14 to 2026-02-13
Range: [$354.56, $542.07]  Mean: $466.98  Std: $49.62
Start: $408.43  End: $401.32  Change: -1.74%
Regime: Ranging since 2025-02-18 (low volatility)
RSI(14): 32.4 (neutral-bearish)  MACD: bearish crossover 11 days ago
BB: lower half
SMA 50/200: death cross 17 days ago
Volume: 0.74x 20-day avg (below average)
Volatility: 94th percentile (extremely high)
SAX(16): aaabdefggggggfed
Patterns: none detected
Candlestick: Inside Bar on 2026-02-13
Support: $393.67 (15 touches), $378.77 (8 touches)  Resistance: $510.83 (34 touches), $481.63 (21 touches)
```

Main differences in this run:
- `Regime` changed: `Regime: Downtrend since 2026-01-29 (high volatility)` -> `Regime: Ranging since 2025-02-18 (low volatility)`
- `SAX(16)` changed: `SAX(16): aaabdfggggggffdb` -> `SAX(16): aaabdefggggggfed`
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
