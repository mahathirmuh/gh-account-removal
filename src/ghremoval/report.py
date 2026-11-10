"""Tabel paper, numbers.json, dan macros.tex."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import orjson
import pandas as pd
import polars as pl

from ghremoval.config import load_context


def save_table(df, name: str, caption: str | None = None, *, tables_dir: Path | None = None) -> tuple[Path, Path]:
    """Simpan `<name>.csv` dan `<name>.tex` di results/tables."""
    out = tables_dir or load_context().paths.tables
    out.mkdir(parents=True, exist_ok=True)
    frame = df.to_pandas() if isinstance(df, pl.DataFrame) else df.copy()
    csv_path, tex_path = out / f"{name}.csv", out / f"{name}.tex"
    frame.to_csv(csv_path, index=False)
    frame.to_latex(tex_path, index=False, caption=caption, label=f"tab:{name}", float_format="%.4f", escape=True)
    return csv_path, tex_path


def _default(value):
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    raise TypeError(f"Tidak bisa diserialisasi: {type(value)}")


def write_numbers(values: dict, *, path: Path | None = None) -> dict:
    """Gabungkan `values` ke results/numbers.json tanpa menimpa kunci lain."""
    target = path or load_context().paths.numbers
    current = orjson.loads(target.read_bytes()) if target.exists() else {}
    current.update(values)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp")
    tmp.write_bytes(orjson.dumps(current, default=_default, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS | orjson.OPT_SERIALIZE_NUMPY))
    tmp.replace(target)
    return current


def macro_name(key: str) -> str:
    words = re.split(r"[^a-zA-Z0-9]+", key)
    digits = {"0": "Zero", "1": "One", "2": "Two", "3": "Three", "4": "Four", "5": "Five", "6": "Six", "7": "Seven", "8": "Eight", "9": "Nine"}
    joined = "".join(word[:1].upper() + word[1:] for word in words if word)
    return "".join(digits.get(ch, ch) for ch in joined)


def write_macros(numbers: dict, path: Path) -> None:
    lines = []
    for key in sorted(numbers):
        value = numbers[key]
        if isinstance(value, float) and not np.isnan(value):
            value = f"{value:.4f}"
        lines.append(f"\\newcommand{{\\{macro_name(key)}}}{{{value}}}")
    path.write_text("\n".join(lines) + "\n", encoding="utf8")
