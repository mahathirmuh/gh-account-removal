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
# # 10 — Model dan analisis terkontrol
#
# **Tujuan:** tuning, tangga model, dan analisis di dalam sel aktivitas dan usia (RQ1), tahap pengembangan: train `w0–w1`, test `w2`.

# %%
import json
import os

os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")  # mlruns/ tetap dipakai sebagai folder lokal

import mlflow
import numpy as np
import pandas as pd
import polars as pl

from ghremoval.analysis import bootstrap_gain, cells_of, du_name_baselines, hour_order, ladder, seeds
from ghremoval.config import load_context
from ghremoval.data import xy
from ghremoval.evaluate import within_cell_auc
from ghremoval.models.fit import arm_mask, fit_predict, load_stage, time_holdback
from ghremoval.models.tune import run_study
from ghremoval.quality import Checks
from ghremoval.report import save_table
from ghremoval.runlog import RunLog
from ghremoval.viz import new_figure, save_figure

ctx = load_context(config_path)
run = RunLog("10_models_and_controls", ctx.paths.run_log, ctx.paths.root)
checks = Checks()
models_cfg = ctx.p.locked["models"]
data = load_stage(ctx, "dev", 60)
assert set(data.train["week"].unique()) <= {"w0", "w1"} and set(data.test["week"].unique()) == {"w2"}
order = hour_order(ctx)
print("train:", data.train.height, "test:", data.test.height)

# %% [markdown]
# ## 1. Tuning
#
# Objective: AP stratum 5–19 pada lengan F2. Early stopping memakai 20% jam terakhir train.

# %%
X, y = xy(data.train, "M_behav")
X_test, y_test = xy(data.test, "M_behav")
es = time_holdback(data.train, order)
tune_mask = arm_mask(data.train, data.test, "F2_forward_new_accounts", ctx) & (data.test["stratum"].to_numpy() == "5-19")
mlflow.set_tracking_uri(f"file:{ctx.paths.root}/mlruns")
mlflow.set_experiment("nb10_tuning")
storage = ctx.paths.results / "optuna"
studies = []
for family in ("xgb", "lr", "mlp"):
    for sampler_seed in models_cfg["optuna_sampler_seeds"]:
        result = run_study(family, sampler_seed, X, y, es, X_test, y_test, tune_mask, storage, models_cfg["optuna_trials"])
        studies.append(result)
        with mlflow.start_run(run_name=f"{family}_{sampler_seed}"):
            mlflow.log_params({"family": family, "sampler_seed": sampler_seed})
            mlflow.log_metrics({"best_ap_5_19": result["best_value"], "seconds": result["seconds"]})
        print(family, sampler_seed, round(result["best_value"], 4), round(result["seconds"]), "s", flush=True)
tuning = pd.DataFrame(studies)
save_table(tuning.drop(columns=["best_params"]).assign(best_params=tuning["best_params"].map(json.dumps)), "tab_tuning_trials", "Hyperparameter search: best value per family and sampler seed")
best = {family: tuning[tuning.family == family].sort_values("best_value", ascending=False).iloc[0]["best_params"] for family in ("xgb", "lr", "mlp")}
(ctx.paths.results / "best_params.json").write_text(json.dumps(best, indent=2) + "\n")
tuning[["family", "sampler_seed", "best_value", "n_trials", "seconds"]]

# %% [markdown]
# ## 2. Tangga model

# %%
result = ladder(ctx, "dev", data, best)
table = pd.DataFrame(result["rows"])
table = pd.concat([table, pd.DataFrame(du_name_baselines(ctx, data))], ignore_index=True)
save_table(table, "tab_models_by_stratum", "Model ladder per stratum, development stage (observed label)")
view = table[table.arm == "F2_forward_new_accounts"][["model", "n", "n_pos", "base_5-19", "ap_all", "ap_5-19", "ap_20+", "within_cell_auc", "p_at_100"]]
view

# %% [markdown]
# ## 3. Keputusan keluarga model
#
# Model yang lebih mahal dari XGBoost dipertahankan hanya jika CI paired-nya positif dan selisih AP melewati ambang.

# %%
scores = {name: value[0] for name, value in result["models"].items()}
per_seed = [fit_predict("xgb", best["xgb"], "M_behav", data.train, [data.test], order, [seed])[0] for seed in seeds(ctx)]
mask = arm_mask(data.train, data.test, "F2_forward_new_accounts", ctx) & (data.test["stratum"].to_numpy() == "5-19")
from sklearn.metrics import average_precision_score  # noqa: E402

seed_ap = [average_precision_score(y_test[mask], s[mask]) for s in per_seed]
effective_delta = max(ctx.p.locked["decision"]["min_delta_ap"], 2 * float(np.std(seed_ap)))
print("AP per seed:", np.round(seed_ap, 4), "ambang efektif:", round(effective_delta, 4))
comparisons = {"M_behav_xgb - B2_xgb": ("M_behav_xgb", "B2_xgb"), "M_behav_mlp - M_behav_xgb": ("M_behav_mlp", "M_behav_xgb"), "M_behav_lr - M_behav_xgb": ("M_behav_lr", "M_behav_xgb")}
decisions = {}
for name, (a, b) in comparisons.items():
    for arm in ("F2_forward_new_accounts", "F3_forward_batch_excluded"):
        decisions[f"{name} | {arm}"] = bootstrap_gain(ctx, data, scores[a], scores[b], arm, "5-19")
decision_table = pd.DataFrame(decisions).T
save_table(decision_table.reset_index(names="comparison"), "tab_model_decisions_dev", "Paired AP differences, 5-19 events, development stage")
(ctx.paths.results / "model_decisions_dev.json").write_text(json.dumps({"effective_delta": effective_delta, "seed_ap": seed_ap, "decisions": decisions}, indent=2, default=float) + "\n")
decision_table[["delta", "low", "high", "p_one_sided", "n_clusters_with_pos", "delta_without_largest_cluster"]]

# %% [markdown]
# ## 4. Peringkat di dalam sel aktivitas dan usia

# %%
cells = cells_of(data.test)
f2 = arm_mask(data.train, data.test, "F2_forward_new_accounts", ctx)
inside = {name: within_cell_auc(y_test[f2], scores[name][f2], cells[f2]) for name in ("B2_xgb", "M_behav_xgb", "M_robust_xgb")}
print(inside)
fig, ax = new_figure()
ax.bar(list(inside), list(inside.values()), color="#0072B2")
ax.axhline(0.5, color="#D55E00", lw=0.8, ls="--")
ax.set_ylabel("Within-cell AUC")
ax.tick_params(axis="x", labelrotation=20)
save_figure(fig, "fig_within_cell")

# %% [markdown]
# ## Ringkasan & cek

# %%
checks.add("Q17", "w3" not in set(data.train["week"].unique()) | set(data.test["week"].unique()), "tanpa w3")
checks.add("kelengkapan", len(studies) == 9, f"{len(studies)} studi")
checks.raise_if_failed()
print(run.finish(n_train=data.train.height, n_test=data.test.height))
