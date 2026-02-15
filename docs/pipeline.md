# Pipeline

`narrata` can be used in two ways:

1. Call one high-level function (`narrate`) and get the full text block.
2. Compose only the parts you need for your token budget.

For a full end-to-end walkthrough, see the [Tutorial](tutorial.md).

## Fast path: one call

```python
import yfinance as yf
from narrata import narrate

df = yf.download("AAPL", period="1y", multi_level_index=False)
text = narrate(df, ticker="AAPL")
print(text)
```

This returns a compact multi-line summary (sparkline, date range, regime, indicators, symbolic encoding, patterns, and levels).

## Composed path: pick only what matters

If you want tighter control over prompt size, call the public analysis/rendering helpers directly:

```python
import yfinance as yf
from narrata import (
    analyze_indicators,
    analyze_regime,
    analyze_summary,
    describe_indicators,
    describe_regime,
    describe_summary,
    describe_support_resistance,
    find_support_resistance,
    format_sections,
    make_sparkline,
)

df = yf.download("MSFT", period="1y", multi_level_index=False)

summary = analyze_summary(df, ticker="MSFT")
regime = analyze_regime(df)
indicators = analyze_indicators(df)
levels = find_support_resistance(df)

sections = {
    "overview": f"{summary.ticker} ({summary.points} pts, {summary.frequency}): "
    f"{make_sparkline(df['Close'].tolist(), width=16)}",
    "range": describe_summary(summary, include_header=False).splitlines()[0],
    "change": describe_summary(summary, include_header=False).splitlines()[1],
    "regime": describe_regime(regime),
    "indicators": describe_indicators(indicators),
    "levels": describe_support_resistance(levels),
}

print(format_sections(sections, output_format="plain"))
```

Representative output shape:

```text
MSFT (251 pts, daily): ▂▁▁▁▃▄▅▇▇█▇███▇▆▅▆
Range: [$354.56, $542.07]  Mean: $466.98  Std: $49.62
Start: $408.43  End: $401.32  Change: -1.74%
Regime: Ranging since 2025-02-18 (low volatility)
RSI(14): 32.4 (neutral-bearish)  MACD: bearish crossover 11 days ago
Support: $393.67 (15 touches), $378.77 (8 touches)  Resistance: $510.83 (34 touches), $481.63 (21 touches)
```

## Practical guidance

- Use `narrate(...)` for default usage in agents and apps.
- Use composed sections when you need strict token control.
- Keep summary + regime + indicators as a strong minimal subset for most prompts.
