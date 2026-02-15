#!/usr/bin/env python3
"""Generate fallback-only and extras-enabled narrate outputs for docs."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
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


def _narrate_for_mode(mode: str, sync_args: list[str]) -> dict[str, object]:
    _run(["uv", "sync", "--project", str(NARRATA_PROJECT), *sync_args])

    python_bin = NARRATA_PROJECT / ".venv" / "bin" / "python"
    if not python_bin.exists():
        raise RuntimeError(
            "Expected src/narrata/.venv/bin/python after sync, but it was not found."
        )

    code = textwrap.dedent(
        f"""
        import importlib.util
        import json
        import numpy as np
        import pandas as pd
        from narrata.composition.narrate import narrate

        mods = {{m: (importlib.util.find_spec(m) is not None) for m in ('pandas_ta', 'ruptures', 'tslearn')}}

        n = 252
        dates = pd.bdate_range('2024-01-02', periods=n)
        rng = np.random.default_rng(17)
        trend = np.linspace(140.0, 201.0, n)
        seasonal = 3.0 * np.sin(np.linspace(0.0, 10.0 * np.pi, n))
        noise = rng.normal(0.0, 0.95, n)
        close = trend + seasonal + noise
        open_ = close + rng.normal(0.0, 0.7, n)
        high = np.maximum(open_, close) + np.abs(rng.normal(0.8, 0.3, n))
        low = np.minimum(open_, close) - np.abs(rng.normal(0.8, 0.3, n))
        volume = rng.integers(900_000, 2_300_000, n)

        df = pd.DataFrame(
            {{'Open': open_, 'High': high, 'Low': low, 'Close': close, 'Volume': volume}},
            index=dates,
        )
        df.attrs['ticker'] = 'AAPL'

        payload = {{
            'mode': {mode!r},
            'deps': mods,
            'text': narrate(df, digit_level=False),
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
    fallback = _narrate_for_mode("fallback_only", ["--dev"])
    extras = _narrate_for_mode("external_enabled", ["--dev", "--extra", "all"])

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
