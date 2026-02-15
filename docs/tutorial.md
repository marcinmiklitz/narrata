# Tutorial: From OHLCV to LLM Prompt

This tutorial shows a complete flow you can copy-paste.

## 1. Prepare data

```python
import yfinance as yf

df = yf.download("AAPL", period="1y", multi_level_index=False)
```

## 2. Generate narration

```python
from narrata import narrate

text = narrate(df, ticker="AAPL")
print(text)
```

Representative output:

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

## 3. Use in a prompt

```python
prompt = f"""
You are a market analysis assistant.
Given this time-series context:

{text}

Provide a concise trend interpretation and key risk caveats.
"""
```

## 4. Optional: markdown key-value output

```python
markdown_text = narrate(df, output_format="markdown_kv")
print(markdown_text)
```

## 5. Public imports

All public methods are available from top-level `narrata` imports.

```python
from narrata import (
    narrate,
    analyze_summary,
    analyze_regime,
    analyze_indicators,
    sax_encode,
    astride_encode,
    detect_patterns,
    find_support_resistance,
    make_sparkline,
    digit_tokenize,
    to_plain,
    to_markdown_kv,
    to_toon,
)
```

If you prefer module-scoped imports, use `narrata.analysis.*`, `narrata.rendering.*`, and `narrata.formatting.*`.

For the full public export list at your installed version:

```python
import narrata
print(narrata.__all__)
```

## 6. Compare fallback-only vs extras-enabled output

<!-- BACKEND_COMPARISON_TUTORIAL:START -->
This comparison uses the same static real-market MSFT fixture (251 daily points from yfinance).

Use separate clean virtual environments when comparing fallback vs extras.

### Fallback-only environment

Install only the core package:

```bash
pip install narrata
```

Detected optional backends:

- `{'pandas_ta': False, 'ruptures': False, 'tslearn': False}`

Representative output:

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

### Extras-enabled environment

Install optional backends:

```bash
pip install "narrata[all]"
```

Detected optional backends:

- `{'pandas_ta': True, 'ruptures': True, 'tslearn': True}`

Representative output:

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

### Why the outputs differ
- `Regime` line changed
  fallback: `Regime: Downtrend since 2026-01-29 (high volatility)`
  extras: `Regime: Ranging since 2025-02-18 (low volatility)`
- `SAX(16)` line changed
  fallback: `SAX(16): aaabdfggggggffdb`
  extras: `SAX(16): aaabdefggggggfed`

### Why some lines stay the same

- Sparkline, summary statistics, support/resistance, and many pattern labels come from deterministic in-house logic.
- RSI/MACD values are often numerically close between in-house and `pandas_ta` for the same input series.
<!-- BACKEND_COMPARISON_TUTORIAL:END -->

## 7. Practical notes

### Choosing output format

- Use `plain` when the text goes directly into a prompt.
- Use `markdown_kv` when you want highly scannable sections.
- Use `toon` when you optimize for compact structured serialization.

### Choosing sparkline width

- `8-12` chars for very tight token budgets
- `16-24` chars for better visual shape

### When to enable digit-level tokenization

Use `digit_level=True` only when you are explicitly optimizing number tokenization behavior in your LLM pipeline. For general usage, leave it off for readability.
