#!/usr/bin/env python3
"""Generate fallback-only and extras-enabled narrate outputs for docs."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NARRATA_PROJECT = ROOT / "src" / "narrata"
UV_CACHE_DIR = str(ROOT / ".uv-cache")


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["UV_CACHE_DIR"] = UV_CACHE_DIR
    return subprocess.run(
        cmd,
        cwd=ROOT,
        env=env,
        check=True,
        text=True,
        capture_output=True,
    )


def _narrate_for_mode(mode: str, install_target: str) -> dict[str, object]:
    fixture_path = ROOT / "src" / "narrata" / "tests" / "assets" / "msft_1y.csv"

    with tempfile.TemporaryDirectory(prefix=f"narrata-{mode}-") as tmp_dir:
        venv_dir = Path(tmp_dir) / ".venv"
        _run(["uv", "venv", str(venv_dir)])

        python_bin = venv_dir / "bin" / "python"
        if not python_bin.exists():
            raise RuntimeError(f"Expected virtualenv python at {python_bin}, but it was not found.")

        _run(["uv", "pip", "install", "--python", str(python_bin), install_target])

        code = textwrap.dedent(
            f"""
            import importlib.util
            import json
            import pandas as pd
            from narrata.composition.narrate import narrate

            mods = {{m: (importlib.util.find_spec(m) is not None) for m in ('pandas_ta', 'ruptures', 'tslearn')}}

            df = pd.read_csv({str(fixture_path)!r}, index_col='Date', parse_dates=True)

            payload = {{
                'mode': {mode!r},
                'deps': mods,
                'text': narrate(df, ticker='MSFT', digit_level=False),
            }}
            print(json.dumps(payload, ensure_ascii=False))
            """
        )
        result = _run([str(python_bin), "-c", code])
        return json.loads(result.stdout.strip().splitlines()[-1])


def _diff_lines(fallback_text: str, extras_text: str) -> list[dict[str, str]]:
    fallback_lines = fallback_text.splitlines()
    extras_lines = extras_text.splitlines()
    max_len = max(len(fallback_lines), len(extras_lines))

    diffs: list[dict[str, str]] = []
    for idx in range(max_len):
        fb = fallback_lines[idx] if idx < len(fallback_lines) else ""
        ex = extras_lines[idx] if idx < len(extras_lines) else ""
        if fb == ex:
            continue
        label = ex.split(":", maxsplit=1)[0] if ":" in ex else f"line {idx + 1}"
        diffs.append(
            {
                "label": label,
                "fallback": fb,
                "extras": ex,
            }
        )
    return diffs


def generate() -> dict[str, object]:
    fallback = _narrate_for_mode("fallback_only", str(NARRATA_PROJECT))
    extras = _narrate_for_mode("external_enabled", f"{NARRATA_PROJECT}[all]")

    return {
        "fallback": fallback,
        "extras": extras,
        "differences": _diff_lines(str(fallback["text"]), str(extras["text"])),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON payload")
    args = parser.parse_args()

    payload = generate()
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
        return

    print("MODE=fallback_only")
    print(f"deps={payload['fallback']['deps']}")
    print(payload["fallback"]["text"])
    print()
    print("MODE=external_enabled")
    print(f"deps={payload['extras']['deps']}")
    print(payload["extras"]["text"])
    print()
    print("DIFFERENCES")
    for item in payload["differences"]:
        print(f"- {item['label']}")
        print(f"  fallback: {item['fallback']}")
        print(f"  extras:   {item['extras']}")


if __name__ == "__main__":
    main()
