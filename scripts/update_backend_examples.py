#!/usr/bin/env python3
"""Update README and tutorial backend-comparison sections from generated outputs."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN_SCRIPT = ROOT / "scripts" / "generate_backend_examples.py"

README_PATH = ROOT / "README.md"
TUTORIAL_PATH = ROOT / "docs" / "tutorial.md"

README_START = "<!-- BACKEND_COMPARISON:START -->"
README_END = "<!-- BACKEND_COMPARISON:END -->"
TUTORIAL_START = "<!-- BACKEND_COMPARISON_TUTORIAL:START -->"
TUTORIAL_END = "<!-- BACKEND_COMPARISON_TUTORIAL:END -->"


def _load_payload() -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, str(GEN_SCRIPT), "--json"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(result.stdout.strip().splitlines()[-1])


def _replace_between_markers(path: Path, start: str, end: str, replacement_body: str) -> None:
    content = path.read_text()
    if start not in content or end not in content:
        raise RuntimeError(f"Markers not found in {path}")

    before, remainder = content.split(start, maxsplit=1)
    _, after = remainder.split(end, maxsplit=1)

    updated = f"{before}{start}\n{replacement_body.rstrip()}\n{end}{after}"
    path.write_text(updated)


def _render_readme(payload: dict[str, object]) -> str:
    fallback = payload["fallback"]
    extras = payload["extras"]
    differences = payload["differences"]

    lines = [
        "Using the same deterministic 252-point dataset:",
        "",
        "Use separate clean virtual environments when comparing fallback vs extras.",
        "",
        "Fallback-only (`pip install narrata`):",
        "",
        "```text",
        str(fallback["text"]),
        "```",
        "",
        'With extras (`pip install "narrata[all]"`):',
        "",
        "```text",
        str(extras["text"]),
        "```",
        "",
        "Main differences in this run:",
    ]

    for diff in differences:
        lines.append(f"- `{diff['label']}` changed: `{diff['fallback']}` -> `{diff['extras']}`")

    return "\n".join(lines)


def _render_tutorial(payload: dict[str, object]) -> str:
    fallback = payload["fallback"]
    extras = payload["extras"]
    differences = payload["differences"]

    lines = [
        "This comparison uses the same deterministic dataset (same random seed and same 252 business-day range).",
        "",
        "Use separate clean virtual environments when comparing fallback vs extras.",
        "",
        "### Fallback-only environment",
        "",
        "Install only the core package:",
        "",
        "```bash",
        "pip install narrata",
        "```",
        "",
        "Detected optional backends:",
        "",
        f"- `{fallback['deps']}`",
        "",
        "Representative output:",
        "",
        "```text",
        str(fallback["text"]),
        "```",
        "",
        "### Extras-enabled environment",
        "",
        "Install optional backends:",
        "",
        "```bash",
        'pip install "narrata[all]"',
        "```",
        "",
        "Detected optional backends:",
        "",
        f"- `{extras['deps']}`",
        "",
        "Representative output:",
        "",
        "```text",
        str(extras["text"]),
        "```",
        "",
        "### Why the outputs differ",
    ]

    for diff in differences:
        lines.append(f"- `{diff['label']}` line changed")
        lines.append(f"  fallback: `{diff['fallback']}`")
        lines.append(f"  extras: `{diff['extras']}`")

    lines.extend(
        [
            "",
            "### Why some lines stay the same",
            "",
            "- Sparkline, summary statistics, chart pattern (`Ascending triangle`), "
            "and support/resistance are deterministic in-house logic.",
            "- RSI/MACD values are often numerically close between in-house and `pandas_ta` for the same input series.",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    payload = _load_payload()
    _replace_between_markers(README_PATH, README_START, README_END, _render_readme(payload))
    _replace_between_markers(TUTORIAL_PATH, TUTORIAL_START, TUTORIAL_END, _render_tutorial(payload))
    print("Updated README.md and docs/tutorial.md backend comparison blocks.")


if __name__ == "__main__":
    main()
