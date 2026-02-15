# Tutorial: From OHLCV to LLM Prompt

This tutorial shows a complete flow you can copy-paste.

## 1. Prepare data

```python
import numpy as np
import pandas as pd

n = 120
dates = pd.date_range("2025-01-01", periods=n, freq="D")
rng = np.random.default_rng(7)
close = np.linspace(140.0, 175.0, n) + rng.normal(0.0, 1.0, n)
open_ = close + rng.normal(0.0, 0.6, n)
high = np.maximum(open_, close) + np.abs(rng.normal(0.7, 0.2, n))
low = np.minimum(open_, close) - np.abs(rng.normal(0.7, 0.2, n))
volume = rng.integers(900_000, 2_100_000, n)

df = pd.DataFrame(
    {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume},
    index=dates,
)
```

## 2. Generate narration

```python
from narrata import narrate

text = narrate(df, ticker="AAPL")
print(text)
```

Representative output:

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
This comparison uses the same deterministic dataset (same random seed and same 252 business-day range).

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

### Extras-enabled environment

Install optional backends:

```bash
pip install "narrata[all]"
```

Detected optional backends:

- `{'pandas_ta': True, 'ruptures': True, 'tslearn': True}`

Representative output:

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

### Why the outputs differ
- `Regime` line changed
  fallback: `Regime: Uptrend since 2024-12-10 (low volatility)`
  extras: `Regime: Uptrend since 2024-10-02 (low volatility)`
- `SAX(16)` line changed
  fallback: `SAX(16): aaabbcdeefggghhh`
  extras: `SAX(16): aaabbbcddefggghh`
- `Candlestick` line changed
  fallback: `Candlestick: Bullish Engulfing on 2024-12-17`
  extras: `Candlestick: Doji on 2024-12-11`

### Why some lines stay the same

- Sparkline, summary statistics, chart pattern (`Ascending triangle`), and support/resistance are deterministic in-house logic.
- RSI/MACD values are often numerically close between in-house and `pandas_ta` for the same input series.
<!-- BACKEND_COMPARISON_TUTORIAL:END -->
