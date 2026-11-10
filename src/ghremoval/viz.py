"""Gaya figur tunggal untuk seluruh paper."""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

from ghremoval.config import load_context

OKABE_ITO = {"blue": "#0072B2", "vermillion": "#D55E00", "green": "#009E73", "orange": "#E69F00", "sky": "#56B4E9", "purple": "#CC79A7", "black": "#000000"}
SINGLE_COLUMN_IN, DOUBLE_COLUMN_IN = 3.5, 7.2


def apply_style() -> None:
    mpl.rcParams.update({"font.family": "sans-serif", "font.size": 8, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                         "grid.color": "#E6E6E6", "grid.linewidth": 0.5, "axes.axisbelow": True, "legend.frameon": False, "figure.dpi": 110, "savefig.bbox": "tight"})


def new_figure(width: float = SINGLE_COLUMN_IN, height: float = 2.4, **kwargs):
    apply_style()
    return plt.subplots(figsize=(width, height), **kwargs)


def save_figure(fig, name: str, *, figures_dir: Path | None = None) -> list[Path]:
    ctx = load_context()
    out = figures_dir or ctx.paths.figures
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for fmt in ctx.p.reporting["figure_formats"]:
        path = out / f"{name}.{fmt}"
        fig.savefig(path, dpi=ctx.p.reporting["figure_dpi"])
        paths.append(path)
    return paths
