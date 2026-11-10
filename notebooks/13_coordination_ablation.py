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
# # 13 — Ablasi koordinasi
#
# **Tujuan:** menguji apakah fitur koordinasi menambah nilai di atas `M_behav` (RQ5), tahap pengembangan.
# Hasil nol adalah hasil yang sah, dan fitur tidak diubah untuk mengejar hasil positif.

# %%
import json

import pandas as pd

from ghremoval.analysis import bootstrap_gain, coordination_ladder
from ghremoval.config import load_context
from ghremoval.quality import Checks
from ghremoval.report import save_table
from ghremoval.runlog import RunLog
from ghremoval.viz import new_figure, save_figure

ctx = load_context(config_path)
run = RunLog("13_coordination_ablation", ctx.paths.run_log, ctx.paths.root)
checks = Checks()
best = json.loads((ctx.paths.results / "best_params.json").read_text())

# %%
result = coordination_ladder(ctx, "dev", best)
table = pd.DataFrame(result["rows"])
save_table(table, "tab_coord_ablation", "Coordination feature ablation, development stage (observed label)")
table[["model", "arm", "n", "n_pos", "ap_all", "ap_5-19", "ap_20+", "n_pos_in_blocks"]]

# %% [markdown]
# ## Selisih berpasangan

# %%
data, scores = result["data"], result["scores"]
pairs = {"M_proxy - M_behav": ("M_proxy", "M_behav"), "M_coord - M_behav": ("M_coord", "M_behav"), "M_coord - M_proxy": ("M_coord", "M_proxy")}
gains = {}
for name, (a, b) in pairs.items():
    for arm in ("F2_forward_new_accounts", "F3_forward_batch_excluded"):
        gains[f"{name} | {arm}"] = bootstrap_gain(ctx, data, scores[a], scores[b], arm, "5-19")
gain_table = pd.DataFrame(gains).T.reset_index(names="comparison")
(ctx.paths.results / "coord_dev.json").write_text(json.dumps(gains, indent=2, default=float) + "\n")
fig, ax = new_figure()
subset = gain_table[gain_table.comparison.str.contains("F3")]
ax.errorbar(subset["delta"].astype(float), range(len(subset)), xerr=[subset["delta"].astype(float) - subset["low"].astype(float), subset["high"].astype(float) - subset["delta"].astype(float)], fmt="o", ms=3, color="#0072B2", lw=1)
ax.set_yticks(range(len(subset))); ax.set_yticklabels([c.split(" | ")[0] for c in subset["comparison"]]); ax.axvline(0, color="#6E6E6E", lw=0.8)
ax.set_xlabel("AP difference, 5-19 events")
save_figure(fig, "fig_coord_ablation")
gain_table[["comparison", "delta", "low", "high", "p_one_sided", "n_clusters_with_pos"]]

# %% [markdown]
# ## Ringkasan & cek

# %%
checks.add("Q17", "w3" not in set(data.test["week"].unique()), "tanpa w3")
checks.raise_if_failed()
print(run.finish(n_test=data.test.height))
