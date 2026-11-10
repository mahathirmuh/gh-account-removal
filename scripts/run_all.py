#!/usr/bin/env python
"""Jalankan notebook berurutan dan berhenti di gerbang yang belum lewat."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_notebook import run  # noqa: E402

from ghremoval.config import load_context  # noqa: E402
from ghremoval.gates import gate_passed  # noqa: E402

PIPELINE = [("00", ""), ("01", ""), ("02", ""), ("03", ""), ("04", "s1"), ("05", ""), "A", ("06", ""), ("07", ""), ("08", ""), "B",
            ("09", ""), ("10", ""), ("11", ""), ("12", ""), ("13", ""), ("14", "sample"), "D", ("15", ""), ("16", "")]


def main() -> int:
    ctx = load_context()
    for step in PIPELINE:
        if isinstance(step, str):
            if not gate_passed(ctx, step):
                print(f"Berhenti di Gerbang {step}: belum lewat.")
                return 0
            continue
        print(f"\n=== Notebook {step[0]} {step[1]} ===", flush=True)
        run(*step)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
