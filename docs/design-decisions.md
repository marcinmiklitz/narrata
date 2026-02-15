# Practical Notes

## Choosing output format

- Use `plain` when the text goes directly into a prompt.
- Use `markdown_kv` when you want highly scannable sections.
- Use `toon` when you optimize for compact structured serialization.

## Choosing sparkline width

- `8-12` chars for very tight token budgets
- `16-24` chars for better visual shape

## When to enable digit-level tokenization

Use `digit_level=True` only when you are explicitly optimizing number tokenization behavior in your LLM pipeline. For general usage, leave it off for readability.
