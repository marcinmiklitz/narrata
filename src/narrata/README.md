# narrata

`narrata` turns OHLCV price series into compact, deterministic text summaries optimized for LLM context.

## Installation

```bash
pip install narrata
```

Install optional backends:

```bash
pip install "narrata[all]"
```

Requires Python 3.11+ and pandas 2.0+.

## Quickstart

```python
import numpy as np
import pandas as pd

from narrata import narrate

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
df.attrs["ticker"] = "AAPL"

print(narrate(df))
```

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

## Fallback vs extras (same input)

Using the same deterministic 252-point dataset:

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

## Public API imports

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

## FAQ

### Is narrata redundant if I already use OpenBB, yfinance, or another data SDK?

No. `narrata` is complementary. It sits on top of your data access layer and converts OHLCV data into concise, LLM-ready narrative text.

### Does narrata call an LLM or provide LLM endpoints?

No. `narrata` is a pure Python library with deterministic, programmatic analysis and narration. It does not call LLM APIs.

## Citation

If you use `narrata` in research or public projects, cite this package using `CITATION.cff`.
