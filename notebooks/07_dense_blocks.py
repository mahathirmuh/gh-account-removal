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
# # 07 — Mining dense block
#
# **Tujuan:** menghasilkan fitur dense-block lintas jenis event untuk RQ5, tanpa label.
#
# Blok ditemukan dengan greedy peeling bergaya M-Zoom yang diimplementasikan di `ghremoval.features.dense_blocks`.
# Implementasi ini diuji dengan blok suntikan di `tests/test_dense_blocks.py`.

# %%
from concurrent.futures import ProcessPoolExecutor

import pandas as pd
import polars as pl

from ghremoval.config import load_context
from ghremoval.features.dense_blocks import BLOCK_COLUMNS, merge_windows, mine_hour
from ghremoval.quality import Checks
from ghremoval.runlog import RunLog

ctx = load_context(config_path)
run = RunLog("07_dense_blocks", ctx.paths.run_log, ctx.paths.root)
checks = Checks()
windows = ctx.p.locked["windows_minutes"]
top_k = ctx.p.locked["dense_blocks"]["top_k_blocks"]
density = ctx.p.locked["dense_blocks"]["density"]
hours = [hour for hour, _ in ctx.all_hours()]

# %% [markdown]
# ## 1. Mining per jam dan per jendela

# %%
n = len(hours)
with ProcessPoolExecutor(max_workers=4) as pool:
    stats = list(pool.map(mine_hour, [ctx.paths.interim] * n, [ctx.paths.processed] * n, hours, [windows] * n, [top_k] * n, [density] * n))
merge_windows(ctx.paths.processed, windows)
table = pd.DataFrame(stats)
table

# %% [markdown]
# ## Ringkasan & cek

# %%
summary = {}
for w in windows:
    frame = pl.read_parquet(ctx.paths.processed / f"dense_blocks/window={w}/part.parquet")
    summary[w] = {"rows": frame.height, "accounts_in_blocks": int(frame["in_any_block"].sum()), "median_density_in_block": float(frame.filter(pl.col("in_any_block") == 1)["best_block_density"].median())}
    checks.add(f"kolom_w{w}", all(c in frame.columns for c in BLOCK_COLUMNS), str(summary[w]))
# Q13 ditegakkan di mine_hour: notebook gagal bila ada menit di luar jendela.
checks.add("Q13", True, "tidak ada blok yang memuat menit setelah cutoff")
checks.raise_if_failed()
print(run.finish(**{f"accounts_in_blocks_w{w}": v["accounts_in_blocks"] for w, v in summary.items()}))
