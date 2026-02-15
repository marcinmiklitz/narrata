"""Import boundary tests for standalone packaging guarantees."""

from __future__ import annotations

import ast
from pathlib import Path

FORBIDDEN_TOP_LEVEL_MODULES = {
    "backtesting",
    "brain",
    "data_sources",
    "local_store",
    "market_explorer",
    "stock_analysis",
}


def _package_python_files() -> list[Path]:
    package_root = Path(__file__).resolve().parents[1] / "narrata"
    return sorted(path for path in package_root.rglob("*.py") if "__pycache__" not in path.parts)


def test_no_relative_imports_in_package() -> None:
    for path in _package_python_files():
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level > 0:
                raise AssertionError(f"Relative import found in {path}:{node.lineno}")


def test_no_cross_workspace_imports() -> None:
    for path in _package_python_files():
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_level = alias.name.split(".", maxsplit=1)[0]
                    assert top_level not in FORBIDDEN_TOP_LEVEL_MODULES, (
                        f"Forbidden import in {path}:{node.lineno}: {alias.name}"
                    )
            elif isinstance(node, ast.ImportFrom) and node.module:
                top_level = node.module.split(".", maxsplit=1)[0]
                assert top_level not in FORBIDDEN_TOP_LEVEL_MODULES, (
                    f"Forbidden import in {path}:{node.lineno}: {node.module}"
                )
