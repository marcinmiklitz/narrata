"""Verify shared content between root and package READMEs stays in sync.

The root README has logo, badges, demo gif, and centered intro as HTML blocks.
The package README has the intro as plain markdown and a ``# narrata`` heading.
Everything from ``## Installation`` onward must be identical.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
ROOT_README = REPO_ROOT / "README.md"
PKG_README = REPO_ROOT / "src" / "narrata" / "README.md"

INTRO_LINE_1 = "narrata turns price series into short text that an LLM can reason about quickly."
INTRO_LINE_2 = (
    "It is designed for situations where a chart is easy for a human to read,"
    " but you need an agent to consume the same information as text."
)


def _from_installation(text: str) -> str:
    """Return everything from ## Installation onward."""
    match = re.search(r"^## Installation", text, re.MULTILINE)
    assert match, "## Installation section not found"
    return text[match.start() :].strip()


def _normalize_html(text: str) -> str:
    """Strip HTML tags, backticks, and collapse whitespace."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("`", "")
    return re.sub(r"\s+", " ", text).strip()


def test_intro_present_in_both() -> None:
    for path in [ROOT_README, PKG_README]:
        norm = _normalize_html(path.read_text())
        assert INTRO_LINE_1 in norm, f"{path.name} missing intro line 1"
        assert INTRO_LINE_2 in norm, f"{path.name} missing intro line 2"


def test_body_matches() -> None:
    """From ## Installation onward, both READMEs must be identical."""
    root_body = _from_installation(ROOT_README.read_text())
    pkg_body = _from_installation(PKG_README.read_text())
    assert root_body == pkg_body, "Root and package READMEs have diverged after ## Installation. Keep them in sync."


def _extract_sections(text: str) -> set[str]:
    """Extract ## section headers."""
    return set(re.findall(r"^## (.+)$", text, re.MULTILINE))


def test_same_sections() -> None:
    root_sections = _extract_sections(ROOT_README.read_text())
    pkg_sections = _extract_sections(PKG_README.read_text())
    assert root_sections == pkg_sections, (
        f"Section mismatch.\n"
        f"  Only in root: {root_sections - pkg_sections}\n"
        f"  Only in pkg:  {pkg_sections - root_sections}"
    )
