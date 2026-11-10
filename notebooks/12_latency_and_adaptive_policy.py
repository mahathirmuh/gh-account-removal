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
# # 12 — Latensi dan kebijakan adaptif
#
# **Tujuan:** kurva performa per jendela dan kebijakan penandaan dini adaptif pada tahap pengembangan.
# Hasil ini simulasi atas data arsip, bukan sistem real-time. Waktu dihitung dari awal jam.

# %%
import json

import numpy as np
import pandas as pd

from ghremoval.analysis import aurt_delta_bootstrap, checkpoint_scores, latency_table, policy_results, policy_sensitivity
from ghremoval.config import load_context
from ghremoval.models.fit import load_stage
from ghremoval.policy import amoc_curve, first_cross, q_grid, thresholds
from ghremoval.quality import Checks
from ghremoval.report import save_table
from ghremoval.runlog import RunLog
from ghremoval.viz import new_figure, save_figure

ctx = load_context(config_path)
run = RunLog("12_latency_and_adaptive_policy", ctx.paths.run_log, ctx.paths.root)
checks = Checks()
best = json.loads((ctx.paths.results / "best_params.json").read_text())
cfg = ctx.p.locked["policy"]
windows = ctx.p.locked["windows_minutes"]
primary = cfg["primary_target_precision"]

# %% [markdown]
# ## 1. Kurva latensi

# %%
latency = pd.DataFrame(latency_table(ctx, "dev", best))
save_table(latency, "tab_latency_dev", "Average precision by observation window, development stage")
fig, axes = new_figure(width=7.2, height=2.5, ncols=2, sharey=False)
for ax, cohort in zip(axes, ("fixed", "deployable")):
    part = latency[latency.cohort == cohort]
    for model, color in (("B2", "#6E6E6E"), ("M_behav", "#0072B2")):
        rows = part[part.model == model]
        ax.plot(rows["window"], rows["ap_5-19"], marker="o", ms=3, color=color, label=model)
    ax.set_xlabel("Observation window (minutes)"); ax.set_title(f"{cohort} cohort, 5-19 events"); ax.set_ylabel("Average precision"); ax.legend()
save_figure(fig, "fig_latency_curves")
latency[latency.model == "M_behav"][["cohort", "window", "n", "n_pos", "ap_all", "ap_5-19", "ap_20+"]]

# %% [markdown]
# ## 2. Kebijakan adaptif

# %%
results, tables, scores_keep = {}, [], {}
data = load_stage(ctx, "dev", 60)
for cohort in ("fixed", "deployable"):
    behav = checkpoint_scores(ctx, "dev", cohort, "M_behav", best["xgb"])
    base = checkpoint_scores(ctx, "dev", cohort, "B2", None)
    scores_keep[cohort] = behav
    train_for_arm = load_stage(ctx, "dev", 60, cohort=cohort).train
    for arm in ("F2_forward_new_accounts", "F3_forward_batch_excluded"):
        adaptive = policy_results(ctx, behav, arm, train_for_arm)
        baseline = policy_results(ctx, base, arm, train_for_arm)
        results[(cohort, arm)] = (adaptive, baseline)
        for r in adaptive["rows"]:
            tables.append({"cohort": cohort, "arm": arm, "model": "M_behav", **r})
        for r in baseline["rows"]:
            if r["policy"] == "adaptive":
                tables.append({"cohort": cohort, "arm": arm, "model": "B2_first_cross", **r})
policy_table = pd.DataFrame(tables)
save_table(policy_table, "tab_policy", "Early-flagging policy comparison, development stage (observed label)")
policy_table[(policy_table.target == primary) & (policy_table.cohort == "fixed") & (policy_table.arm == "F2_forward_new_accounts")][["model", "policy", "status", "q", "kappa", "n_flagged", "precision", "recall", "aurt", "median_time_tp"]]

# %% [markdown]
# ## 3. Adaptif terhadap jendela tetap terbaik

# %%
comparisons = {}
for (cohort, arm), (adaptive, _baseline) in results.items():
    if ("adaptive", primary) in adaptive["times"] and ("best_fixed", primary) in adaptive["times"]:
        comparisons[f"{cohort}|{arm}"] = {"best_fixed_window": adaptive["best_fixed"].get(primary), **aurt_delta_bootstrap(ctx, scores_keep[cohort], adaptive["times"][("adaptive", primary)], adaptive["times"][("best_fixed", primary)], adaptive["mask"])}
    else:
        comparisons[f"{cohort}|{arm}"] = {"status": "target precision tidak tercapai"}
comparison_table = pd.DataFrame(comparisons).T.reset_index(names="setting")
(ctx.paths.results / "policy_dev.json").write_text(json.dumps(comparisons, indent=2, default=float) + "\n")
comparison_table

# %% [markdown]
# ## 3b. Sensitivitas
#
# Horizon lain dan perbandingan pada precision teramati yang disamakan. Precision yang tercapai bisa berbeda antarkebijakan walaupun targetnya sama.
# Pada perbandingan yang disamakan, `q` dipilih memakai label evaluasi untuk kedua kebijakan, jadi hasilnya bukan kinerja yang bisa dicapai saat dipakai.

# %%
sensitivity = pd.DataFrame([{"cohort": cohort, "arm": arm, **row} for (cohort, arm), (adaptive, _baseline) in results.items() for row in policy_sensitivity(ctx, scores_keep[cohort], adaptive, primary)])
save_table(sensitivity, "tab_policy_sensitivity", "Policy sensitivity, development stage: other horizons and matched observed precision (exploratory, observed label)")
sensitivity

# %% [markdown]
# ## 4. Kurva recall terhadap waktu dan AMOC

# %%
behav = scores_keep["fixed"]
adaptive = results[("fixed", "F2_forward_new_accounts")][0]
horizon = cfg["aurt_horizon_minutes"]
mask = adaptive["mask"]
y = behav["test_y"]
points = np.arange(0, horizon + 1)
fig, ax = new_figure()
if ("adaptive", primary) in adaptive["times"]:
    for key, color, label in ((("adaptive", primary), "#0072B2", "Adaptive"), (("best_fixed", primary), "#D55E00", "Best fixed window")):
        t = adaptive["times"][key][mask]
        ax.step(points, [((t <= p) & np.isfinite(t) & (y[mask] == 1)).sum() / max(y[mask].sum(), 1) for p in points], where="post", color=color, label=label)
    ax.set_xlabel("Minutes into the hour"); ax.set_ylabel("Recall on observed label"); ax.legend()
save_figure(fig, "fig_recall_time")
curve = pd.DataFrame(amoc_curve({c: v[mask] for c, v in behav["test_prob"].items()}, y[mask], 0.0, q_grid(cfg["q_grid_size"]), horizon))
fig, ax = new_figure()
ax.plot(curve["false_positive_rate"], curve["mean_delay_positive"], color="#0072B2", lw=1)
ax.set_xscale("log"); ax.set_xlabel("False positive rate"); ax.set_ylabel("Mean delay on positives (min)")
save_figure(fig, "fig_amoc")

# %% [markdown]
# ## Ringkasan & cek

# %%
valid_checkpoints = set(windows)
all_times = np.concatenate([t[np.isfinite(t)] for (_, arm), (a, _b) in results.items() for t in a["times"].values() if len(t)])
checks.add("Q18", set(np.unique(all_times)).issubset(valid_checkpoints), "waktu penandaan selalu checkpoint yang valid")
checks.add("Q17", set(data.test["week"].unique()) == {"w2"}, "evaluasi pengembangan pada w2")
checks.raise_if_failed()
print(run.finish(n_settings=len(results)))
