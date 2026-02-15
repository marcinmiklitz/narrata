# How narrata builds text

Think of `narrata` as a 4-step pipeline:

1. Validate incoming data (`validation`)
2. Extract key numeric signals (`analysis`)
3. Render compact text pieces (`rendering`)
4. Assemble final output (`formatting` + `composition`)

If you only want the final result, call `narrate(df)`.

If you want control, call each step directly and keep only the pieces that matter for your prompt budget.

## Why this split matters

- You can test each step independently
- You can swap formatting without changing analysis logic
- You can reuse only one function (for example just sparklines) in other projects
