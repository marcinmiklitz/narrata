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

`narrate(...)` takes a pandas OHLCV DataFrame with a datetime index.

```python
import yfinance as yf
from narrata import narrate

df = yf.download("AAPL", period="1y", multi_level_index=False)
print(narrate(df, ticker="AAPL"))
```

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

## Fallback vs extras (same input)

Using the same static real-market MSFT dataset (251 daily points, yfinance fixture):

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

## Digit Splitting for LLM Robustness

`digit_tokenize(...)` can help when your downstream model is sensitive to dense numeric strings.

Use it when you have many prices, percentages, or long decimals in prompt context.

```python
from narrata import digit_tokenize

print(digit_tokenize("Price 171.24, move +3.2%"))
# <digits-split>
# Price 1 7 1 . 2 4 , move + 3 . 2 %
```

## Features

- Input validation for OHLCV DataFrames
- Summary analysis with date range context
- Regime classification (`Uptrend` / `Downtrend` / `Ranging`)
- RSI and MACD interpretation
- Bollinger Band and moving average crossover descriptions
- Volatility and volume context
- SAX symbolic encoding
- ASTRIDE adaptive symbolic encoding (with `ruptures`)
- Pattern and candlestick detection
- Support/resistance extraction
- Sparkline generation
- Output formatting (`plain`, `markdown_kv`, `toon`)

## FAQ

### Is narrata redundant if I already use OpenBB, yfinance, or another data SDK?

No. `narrata` is complementary. It sits on top of your data access layer and converts OHLCV data into concise, LLM-ready narrative text.

### Does narrata call an LLM or provide LLM endpoints?

No. `narrata` is a pure Python library with deterministic, programmatic analysis and narration. It does not call LLM APIs.

## Citation

If you use `narrata` in research or public projects, cite this package using `CITATION.cff`.
