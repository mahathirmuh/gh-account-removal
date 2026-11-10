#!/usr/bin/env python
"""Generate .ipynb dari sumber jupytext lalu eksekusi dengan papermill."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = "config/params.yaml"


def find_source(nb: str) -> Path:
    matches = sorted((ROOT / "notebooks").glob(f"{nb.zfill(2)}_*.py"))
    if len(matches) != 1:
        raise SystemExit(f"Sumber notebook {nb} tidak ditemukan tepat satu: {matches}")
    return matches[0]


def run(nb: str, mode: str = "") -> None:
    source = find_source(nb)
    output = source.with_suffix(".ipynb")
    subprocess.run([sys.executable, "-m", "jupytext", "--to", "ipynb", "--output", str(output), str(source)], check=True, cwd=ROOT)
    command = [sys.executable, "-m", "papermill", str(output), str(output), "--cwd", str(ROOT), "--kernel", "python3",
               "--no-progress-bar", "-p", "config_path", CONFIG_PATH]
    if mode:
        command += ["-p", "mode", mode]
    subprocess.run(command, check=True, cwd=ROOT)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nb", required=True)
    parser.add_argument("--mode", default="")
    args = parser.parse_args()
    run(args.nb, args.mode)


if __name__ == "__main__":
    main()
