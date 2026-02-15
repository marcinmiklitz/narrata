#!/usr/bin/env python3
"""Validate lockstep package versions for release tagging."""

from __future__ import annotations

import re
import sys
from pathlib import Path

VERSION_RE = re.compile(r"\d+\.\d+\.\d+(?:[a-zA-Z0-9\.\-\+]*)?")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: check_release_versions.py <version>")
        return 2

    version = sys.argv[1].strip()
    if not VERSION_RE.fullmatch(version):
        print(f"Invalid version string: {version}")
        return 2

    for path in [Path("src/narrata/pyproject.toml"), Path("src/narrata-mcp/pyproject.toml")]:
        content = path.read_text()
        match = re.search(r'(?m)^version\s*=\s*"([^"]+)"', content)
        if not match:
            print(f"No version field found in {path}")
            return 1
        actual = match.group(1)
        if actual != version:
            print(
                f"Version mismatch: {path} has {actual}, but tag would be {version}. "
                "Update both package versions first."
            )
            return 1

    print(f"Version check OK: {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
