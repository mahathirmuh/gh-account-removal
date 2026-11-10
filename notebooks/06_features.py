# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% tags=["parameters"]
config_path = "config/params.yaml"
mode = "default"

# %% [markdown]
# # 06 — Fitur per jendela
#
# **Tujuan:** menghitung fitur `docs/05` untuk tiap jendela dan jam, tanpa label.

# %%
from concurrent.futures import ProcessPoolExecutor

import pandas as pd
import polars as pl

from ghremoval.config import load_context
from ghremoval.features.behaviour import BEHAVIOUR_COLUMNS, PROXY_COLUMNS, build_hour_features, merge_windows
from ghremoval.quality import Checks
from ghremoval.runlog import RunLog

ctx = load_context(config_path)
run = RunLog("06_features", ctx.paths.run_log, ctx.paths.root)
checks = Checks()
windows = ctx.p.locked["windows_minutes"]
deployable = ctx.p.locked["cohorts"]["deployable_min_events"]
hours = [hour for hour, _ in ctx.all_hours()]

# %% [markdown]
# ## 1. Hitung per jam, paralel

# %%
n = len(hours)
with ProcessPoolExecutor(max_workers=4) as pool:
    stats = list(pool.map(build_hour_features, [ctx.paths.interim] * n, [ctx.paths.processed] * n, hours, [windows] * n, [deployable] * n))
merge_windows(ctx.paths.processed, windows)
table = pd.DataFrame(stats)
table

# %% [markdown]
# ## Ringkasan & cek

# %%
per_window = {}
for w in windows:
    frame = pl.scan_parquet(ctx.paths.processed / f"features/window={w}/part.parquet")
    summary = frame.select(pl.len().alias("n"), pl.sum_horizontal(pl.col(BEHAVIOUR_COLUMNS).is_null().sum()).alias("behaviour_null"), pl.sum_horizontal(pl.col(PROXY_COLUMNS).is_null().sum()).alias("proxy_null"),
                           pl.sum_horizontal(pl.col(BEHAVIOUR_COLUMNS + PROXY_COLUMNS).is_nan().sum()).alias("nan")).collect().row(0, named=True)
    per_window[w] = summary
    checks.add(f"Q11_w{w}", summary["behaviour_null"] == 0 and summary["proxy_null"] == 0 and summary["nan"] == 0, str(summary))
checks.raise_if_failed()
print(run.finish(**{f"rows_w{w}": v["n"] for w, v in per_window.items()}))
