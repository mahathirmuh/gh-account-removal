#!/usr/bin/env python
"""Jalankan notebook berurutan dan berhenti di gerbang yang belum lewat."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_notebook import run  # noqa: E402

from ghremoval.config import load_context  # noqa: E402
from ghremoval.gates import gate_passed  # noqa: E402

PIPELINE = [("00", ""), ("01", ""), ("02", ""), ("03", ""), ("04", "s1"), ("05", ""), "A", ("06", ""), ("07", ""), ("08", ""), "B",
            ("09", ""), ("10", ""), ("11", ""), ("12", ""), ("13", ""), ("14", "sample"), "D", ("15", ""), ("16", "")]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from", dest="start", default="00", help="Lewati notebook sebelum nomor ini. Semua gerbang tetap diperiksa.")
    start = parser.parse_args().start.zfill(2)
    if start not in {step[0] for step in PIPELINE if not isinstance(step, str)}:
        raise SystemExit(f"Notebook {start} tidak ada di pipeline.")
    ctx = load_context()
    started = False
    for step in PIPELINE:
        if isinstance(step, str):
            if not gate_passed(ctx, step):
                print(f"Berhenti di Gerbang {step}: belum lewat.", flush=True)
                return 0
            continue
        started = started or step[0] == start
        if not started:
            continue
        print(f"\n=== Notebook {step[0]} {step[1]} ===", flush=True)
        run(*step)
    print("Pipeline selesai.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
