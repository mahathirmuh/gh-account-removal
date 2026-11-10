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
# # 08 — Replikasi pilot pada jam dev
#
# **Tujuan:** membuktikan pipeline mereproduksi angka pilot pada jam dev, sebelum parameter dikunci.

# %%
import numpy as np
import pandas as pl_pandas
import polars as pl

from ghremoval.config import load_context
from ghremoval.data import apply_age_bins, fit_age_edges, xy
from ghremoval.data import load_frame
from ghremoval.evaluate import ap_by_stratum
from ghremoval.models.pilot import oof_scores
from ghremoval.quality import Checks
from ghremoval.report import save_table
from ghremoval.runlog import RunLog
from ghremoval.splits import id_block_groups, stratified_group_folds

ctx = load_context(config_path)
run = RunLog("08_dev_hour_replication", ctx.paths.run_log, ctx.paths.root)
checks = Checks()
seeds = ctx.p.locked["splits"]["cv_seeds"]

# %% [markdown]
# ## 1. Jumlah akun

# %%
frame = load_frame(ctx, 60, ["dev"]).filter(pl.col("in_fixed_cohort"))
frame = apply_age_bins(frame, fit_age_edges(frame["id_recency"].to_numpy()))
y = frame["is_gone"].to_numpy().astype(int)
strata = frame["stratum"].to_numpy()
ids = frame["actor_id"].to_numpy()
counts = {"Akun >=5": (frame.height, 8434), "5-19": (int((strata == "5-19").sum()), 7576), "20+": (int((strata == "20+").sum()), 858)}
gone = {"Hilang >=5": (int(y.sum()), 519), "Hilang 5-19": (int(y[strata == "5-19"].sum()), 185), "Hilang 20+": (int(y[strata == "20+"].sum()), 334)}
for name, (got, want) in counts.items():
    checks.add(name, got == want, f"{got} vs {want}")
for name, (got, want) in gone.items():
    checks.add(name, abs(got - want) <= 0.02 * want, f"{got} vs {want}")

# %% [markdown]
# ## 2. Model dengan konfigurasi pilot

# %%
PILOT = {("B2", "random"): (0.690, 0.090, 0.918), ("B2", "blocks_w20000"): (0.693, 0.084, 0.934), ("M_behav", "random"): (0.767, 0.251, 0.979), ("M_behav", "blocks_w20000"): (0.753, 0.197, 0.979), ("M_behav", "blocks_w100000"): (0.749, 0.196, 0.975)}
rows = []
for (feature_set, split), expected in PILOT.items():
    groups = np.arange(frame.height) if split == "random" else id_block_groups(ids, int(split.split("w")[1]))
    X, _ = xy(frame, feature_set)
    score = oof_scores(X, y, {seed: stratified_group_folds(groups, y, 5, seed) for seed in seeds})
    ap = ap_by_stratum(y, score, strata)
    got = (ap["all"], ap["5-19"], ap["20+"])
    rows.append({"features": feature_set, "split": split, "pilot_all": expected[0], "pipeline_all": got[0], "pilot_5_19": expected[1], "pipeline_5_19": got[1], "pilot_20p": expected[2], "pipeline_20p": got[2], "within_tolerance": all(abs(g - e) <= 0.03 for g, e in zip(got, expected))})
table = pl_pandas.DataFrame(rows)
save_table(table, "tab_dev_replication", "Development-hour replication of the pilot")
table

# %% [markdown]
# ## Ringkasan & cek

# %%
checks.add("Q14", bool(table["within_tolerance"].all()), f"{int(table['within_tolerance'].sum())}/{len(table)} baris dalam toleransi")
checks.raise_if_failed()
print(run.finish(n_rows=frame.height, n_gone=int(y.sum())))
