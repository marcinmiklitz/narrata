
## 2026-03-13 – compare() feature

Added `compare(df_before, df_after)` for side-by-side period diff narratives.
- Core: `src/narrata/narrata/composition/compare.py`
- MCP API: `compare_from_records()` in `mcp_api.py`
- MCP tool: `narrata_compare_ohlcv` in server
- CLI: `narrata compare before.csv after.csv --ticker AAPL`
- Tests: 9 unit tests in `test_compare.py`, 3 MCP tests
- Docs: README, module README, tutorial, SKILL.md updated
- 127 tests passing (105 core + 22 MCP)


## Intraday Awareness (2026-03-13)

**Problem**: Indicator defaults (RSI(14), SMA 50/200, 20-day volume avg) are calibrated for daily bars. On intraday data (5-min, 15-min, etc.), these defaults produce misleading signals — SMA 200 needs 200 bars (~8 days of 15m data) but semantically should span months.

**Solution**: Frequency-aware parameter scaling.

- **Frequency detection** (`validation/ohlcv.py`): Added sub-hourly labels — `1min`, `5min`, `15min`, `30min` — via both `pd.infer_freq` code parsing and median-delta fallback. Added `is_intraday()` helper and `INTRADAY_FREQUENCIES` set.
- **Parameter scaling** (`analysis/indicators.py`): `_intraday_defaults(frequency)` scales SMA crossover periods (50/200 → 10/40 for 15m), volume lookback (20 → bars-per-day), and volatility lookback (252 → 20×bars-per-day). RSI, MACD, and Bollinger keep their standard defaults — practitioners use these across timeframes.
- **IndicatorStats** (`types.py`): Added fields for actual periods used (`ma_fast_period`, `ma_slow_period`, `volume_lookback`, `bb_period`, `volatility_window`, `volatility_lookback`, `frequency`) so descriptions reflect what was actually computed.
- **Narrative labels** (`describe_indicators`): Uses "bar" instead of "day" for intraday; shows actual SMA periods instead of hardcoded "50/200".
- **Wired through**: `narrate()` and `compare()` pass detected frequency to `analyze_indicators`.
- **Test assets**: Added `aapl_15m_1d.csv` (26 bars) and `aapl_15m_5d.csv` (130 bars) from real yfinance data.
- **Tests**: 21 new tests in `test_intraday.py` covering frequency detection, parameter scaling, label output, and end-to-end narration. All 148 tests pass.

