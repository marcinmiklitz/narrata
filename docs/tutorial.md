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
Range: [171.67, 285.92]  Mean: 235.06  Std: 28.36
Start: 243.54  End: 255.78  Change: +5.03%
Regime: Uptrend since 2025-05-07 (low volatility)
RSI(14): 39.6 (neutral-bearish)  MACD: bearish crossover 0 days ago
BB: lower half
SMA 50/200: golden cross
Volume: 0.94x 20-day avg (average)
Volatility: 84th percentile (high)
SAX(16): ecabbabbdegghhhg
Candlestick: Inside Bar on 2026-02-10
Support: 201.77 (26 touches), 208.38 (23 touches)  Resistance: 270.88 (24 touches), 257.57 (22 touches)
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

## 4. Compare two periods

```python
from narrata import compare

df_h1 = df[:"2025-08"]
df_h2 = df["2025-08":]
print(compare(df_h1, df_h2, ticker="AAPL"))
```

This produces a compact `→` diff narrative showing how price, regime, indicators, and levels changed between the two windows. Useful for prompt context like "how did AAPL change between H1 and H2?"

## 5. Output formats

```python
# Markdown key-value (scannable sections)
print(narrate(df, output_format="markdown_kv"))

# Toon (compact structured serialization)
print(narrate(df, output_format="toon"))

# JSON (structured consumption)
print(narrate(df, output_format="json"))
```

## 6. Public imports

All public methods are available from top-level `narrata` imports.

```python
from narrata import (
    narrate,
    compare,
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
    to_json,
)
```

If you prefer module-scoped imports, use `narrata.analysis.*`, `narrata.rendering.*`, and `narrata.formatting.*`.

## 7. Crypto data

narrata includes adapters for common crypto data sources:

```python
from narrata import from_ccxt, from_coingecko, narrate

# ccxt — converts [[timestamp_ms, O, H, L, C, V], ...] to DataFrame
import ccxt
exchange = ccxt.binance()
ohlcv = exchange.fetch_ohlcv("BTC/USDT", "15m", limit=200)
df = from_ccxt(ohlcv, ticker="BTC/USDT")
print(narrate(df, currency_symbol="$", precision=0))

# CoinGecko — close + volume only (no Open/High/Low)
df = from_coingecko(cg_data, ticker="BTC")
print(narrate(df, currency_symbol="$", precision=0))
```

CoinGecko returns only close prices, so patterns and candlestick sections are silently omitted. All other sections (summary, regime, indicators, symbolic, support/resistance) work normally.

**Close-only mode** also works for any other data source that only provides closing prices — just pass a DataFrame with a `Close` column and a `DatetimeIndex`.

For the full public export list at your installed version:

```python
import narrata
print(narrata.__all__)
```

## 8. Compare fallback-only vs extras-enabled output

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
Range: [354.56, 542.07]  Mean: 466.98  Std: 49.62
Start: 408.43  End: 401.32  Change: -1.74%
Regime: Downtrend since 2026-01-29 (high volatility)
RSI(14): 32.4 (neutral-bearish)  MACD: bearish crossover 11 days ago
BB: lower half
SMA 50/200: death cross 17 days ago
Volume: 0.74x 20-day avg (below average)
Volatility: 94th percentile (extremely high)
SAX(16): aaabdfggggggffdb
Candlestick: Inside Bar on 2026-02-13
Support: 393.67 (15 touches), 378.77 (8 touches)  Resistance: 510.83 (34 touches), 481.63 (21 touches)
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
Range: [354.56, 542.07]  Mean: 466.98  Std: 49.62
Start: 408.43  End: 401.32  Change: -1.74%
Regime: Ranging since 2025-02-18 (low volatility)
RSI(14): 32.4 (neutral-bearish)  MACD: bearish crossover 11 days ago
BB: lower half
SMA 50/200: death cross 17 days ago
Volume: 0.74x 20-day avg (below average)
Volatility: 94th percentile (extremely high)
SAX(16): aaabdefggggggfed
Candlestick: Inside Bar on 2026-02-13
Support: 393.67 (15 touches), 378.77 (8 touches)  Resistance: 510.83 (34 touches), 481.63 (21 touches)
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

## 9. Intraday data

narrata auto-detects sub-daily frequencies and scales indicator defaults. No special flags needed for clean data; for patchy or unevenly-spaced data, pass `frequency` explicitly:

```python
df_intraday = yf.download("AAPL", period="5d", interval="15m", multi_level_index=False)
# Auto-detected:
print(narrate(df_intraday, ticker="AAPL", currency_symbol="$"))

# Explicit (for patchy data where auto-detection may fail):
print(narrate(df_intraday, ticker="AAPL", currency_symbol="$", frequency="15min"))

# Fully unstructured data with no fixed interval:
print(narrate(df_irregular, ticker="XYZ", frequency="irregular"))
```

Representative output:

```text
AAPL (130 pts, 15min): ▂▅▄▄▃▃▂▁▆▃▃▃▇▆▇█▇▇█▆
Date range: 2025-11-06 to 2025-11-12
Range: [$268.73, $275.55]  Mean: $271.67  Std: $2.34
Start: $268.73  End: $273.47  Change: +1.76%
Regime: Ranging since 2025-11-06 (low volatility)
RSI(14): 42.5 (neutral-bearish)  MACD: bearish crossover 6 days ago
BB: below lower band (squeeze)
SMA 10/40: golden cross 60 bars ago
Volume: 2.89x 26-bar avg (unusually high)
Volatility: 2nd percentile (extremely low)
SAX(16): dddcbacbbcfghghh
Patterns: Ascending triangle forming since 2025-11-10
Candlestick: Doji on 2025-11-12
Support: $272.02 (89 touches), $268.40 (52 touches)  Resistance: $274.96 (56 touches)
```

Key differences from daily output:
- `SMA 10/40` instead of `SMA 50/200` — crossover periods scaled to cover ~10/40 sessions
- `26-bar avg` instead of `20-day avg` — volume lookback covers ~1 trading day
- `bars ago` instead of `days ago` — unit reflects actual bar count

| Parameter | Daily | 15min | 5min |
|---|---|---|---|
| SMA crossover | 50 / 200 | 10 / 40 | 30 / 120 |
| Volume lookback | 20 days | 26 bars | 78 bars |
| Volatility lookback | 252 bars | 520 bars | 1560 bars |

## 10. Practical notes

### Choosing output format

- Use `plain` when the text goes directly into a prompt.
- Use `markdown_kv` when you want highly scannable sections.
- Use `toon` when you optimize for compact structured serialization.

### Choosing sparkline width

- `8-12` chars for very tight token budgets
- `16-24` chars for better visual shape

### When to enable digit-level tokenization

Use `digit_level=True` only when you are explicitly optimizing number tokenization behavior in your LLM pipeline. For general usage, leave it off for readability.

### Silent section skipping

By default, narrata silently omits sections that have no useful information — both insufficient-data sections (short history, missing columns) and empty results like "Patterns: none detected". This keeps output minimal and avoids wasting tokens on placeholder text.

To see all sections including empty ones, use `verbose=True` (Python) or `--verbose` (CLI):

```python
text = narrate(df, verbose=True)
```

```bash
narrata prices.csv --verbose
```
