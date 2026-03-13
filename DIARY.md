
## 2026-03-13 – compare() feature

Added `compare(df_before, df_after)` for side-by-side period diff narratives.
- Core: `src/narrata/narrata/composition/compare.py`
- MCP API: `compare_from_records()` in `mcp_api.py`
- MCP tool: `narrata_compare_ohlcv` in server
- CLI: `narrata compare before.csv after.csv --ticker AAPL`
- Tests: 9 unit tests in `test_compare.py`, 3 MCP tests
- Docs: README, module README, tutorial, SKILL.md updated
- 127 tests passing (105 core + 22 MCP)

