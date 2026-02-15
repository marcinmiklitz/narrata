#!/usr/bin/env python3
"""Bump lockstep package versions for release tagging."""

from __future__ import annotations

import re
import sys
from pathlib import Path

VERSION_RE = re.compile(r"\d+\.\d+\.\d+(?:[a-zA-Z0-9\.\-\+]*)?")
VERSION_LINE_RE = re.compile(r'(?m)^version\s*=\s*"([^"]+)"')

TARGETS = [
    Path("src/narrata/pyproject.toml"),
    Path("src/narrata-mcp/pyproject.toml"),
]


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: bump_release_versions.py <version>")
        return 2

    version = sys.argv[1].strip()
    if not VERSION_RE.fullmatch(version):
        print(f"Invalid version string: {version}")
        return 2

    changed = False
    for path in TARGETS:
        content = path.read_text()
        match = VERSION_LINE_RE.search(content)
        if not match:
            print(f"No version field found in {path}")
            return 1

        current = match.group(1)
        if current == version:
            print(f"No change needed for {path} (already {version})")
            continue

        updated, count = VERSION_LINE_RE.subn(f'version = "{version}"', content, count=1)
        if count != 1:
            print(f"Could not update version in {path}")
            return 1

        path.write_text(updated)
        changed = True
        print(f"Updated {path}: {current} -> {version}")

    if not changed:
        print(f"All package versions already set to {version}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
