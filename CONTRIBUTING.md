# Contributing

## Local setup

```bash
uv sync --dev
```

## Quality checks

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

## Standards

- Keep modules focused by domain responsibility.
- Add tests for every public method.
- Keep public APIs typed and documented.
