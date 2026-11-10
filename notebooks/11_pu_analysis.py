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
# # 11 — Analisis PU (eksploratif)
#
# **Tujuan:** menguji apakah formulasi positive-unlabeled memperbaiki peringkat dibanding model naive.
#
# `s` adalah label teramati (hilang pada snapshot). `y` laten berarti akun kelak hilang kapan pun.
# Bila `y` dimaknai sebagai akun bermasalah, asumsi p(s=1|y=0)=0 bisa gagal, karena akun bisa dihapus sendiri.
# Semua hasil di notebook ini bersifat eksploratif.

# %%
import json

import numpy as np
import pandas as pd
import polars as pl
from scipy import stats as scipy_stats
from sklearn.metrics import average_precision_score

from ghremoval.analysis import score_row
from ghremoval.config import load_context
from ghremoval.data import xy
from ghremoval.models.fit import arm_mask, load_stage, predict
from ghremoval.pu import bagging_score, elkan_noto_fit, hide_positives, naive_fit, pu_bagging_fit, sar_em_fit
from ghremoval.quality import Checks
from ghremoval.report import save_table
from ghremoval.runlog import RunLog

ctx = load_context(config_path)
run = RunLog("11_pu_analysis", ctx.paths.run_log, ctx.paths.root)
checks = Checks()
data = load_stage(ctx, "dev", 60)
X, s = xy(data.train, "M_behav")
X_test, y_test = xy(data.test, "M_behav")
propensity = {"activity": data.train.select("n_events_coarse").to_numpy(), "age": data.train.select("age_bin12").to_numpy(), "activity+age": data.train.select("n_events_coarse", "age_bin12").to_numpy()}
mask = arm_mask(data.train, data.test, "F2_forward_new_accounts", ctx)
strata = data.test["stratum"].to_numpy()
SEED = ctx.p.project["seed"]

# %% [markdown]
# ## 1. Metode pada label teramati

# %%
naive = naive_fit(X, s, SEED)
en_model, c_mean = elkan_noto_fit(X, s, SEED)
bags = pu_bagging_fit(X, s, SEED)
sar = {name: sar_em_fit(X, s, features, SEED)[0] for name, features in propensity.items()}
methods = {"naive": predict(naive, X_test), "elkan_noto": predict(en_model, X_test), "pu_bagging": bagging_score(bags, X_test), **{f"sar_em_{name}": predict(model, X_test) for name, model in sar.items()}}
observed = pd.DataFrame([{"method": name, **score_row(y_test, score, strata, mask)} for name, score in methods.items()])
observed[["method", "n", "n_pos", "ap_all", "ap_5-19", "ap_20+", "p_at_100"]]

# %% [markdown]
# ## 2. Prior per stratum, sebagai rentang
#
# `c` diperkirakan dari positif pada data latih yang disisihkan. Rentang datang dari beberapa estimator sederhana.
# Karena pustaka estimator prior khusus tidak dipasang, rentang ini hanya memberi gambaran kasar.

# %%
rng = np.random.default_rng(SEED)
held = rng.random(len(s)) < 0.2
clf = naive_fit(X[~held], s[~held], SEED)
held_positive_scores = predict(clf, X[held & (s == 1)])
estimators = {"c_mean": float(held_positive_scores.mean()), "c_median": float(np.median(held_positive_scores)), "c_q90": float(np.quantile(held_positive_scores, 0.9))}
train_strata = data.train["stratum"].to_numpy()
prior_rows = []
for stratum in ("5-19", "20+"):
    observed_rate = float(s[train_strata == stratum].mean())
    prior_rows.append({"stratum": stratum, "observed_s_rate": observed_rate, **{f"prior_{k}": min(1.0, observed_rate / v) for k, v in estimators.items()}})
priors = pd.DataFrame(prior_rows)
print(estimators, "Elkan-Noto c:", round(c_mean, 4))
priors

# %% [markdown]
# ## 3. Uji semi-sintetis
#
# 50% positif train disembunyikan, peluangnya bergantung pada aktivitas dan usia. Tiap metode dilatih pada label yang sudah disembunyikan.

# %%
def recovery_ap(score: np.ndarray, hidden: np.ndarray, s_hidden: np.ndarray) -> float:
    unlabeled = s_hidden == 0
    return float(average_precision_score(hidden[unlabeled], score[unlabeled]))


records = []
for repeat in range(5):
    hidden = hide_positives(s, propensity["activity+age"], 0.5, SEED + repeat)
    s_hidden = s & ~hidden
    scores = {"naive": predict(naive_fit(X, s_hidden, SEED + repeat), X), "elkan_noto": predict(elkan_noto_fit(X, s_hidden, SEED + repeat)[0], X), "pu_bagging": bagging_score(pu_bagging_fit(X, s_hidden, SEED + repeat), X)}
    for name, features in propensity.items():
        scores[f"sar_em_{name}"] = predict(sar_em_fit(X, s_hidden, features, SEED + repeat)[0], X)
    records.append({name: recovery_ap(score, hidden, s_hidden) for name, score in scores.items()})
semi = pd.DataFrame(records)
print(semi.mean().round(4).to_dict())
best_pu = semi.drop(columns=["naive"]).mean().idxmax()
delta = semi[best_pu] - semi["naive"]
t = scipy_stats.t.ppf(0.975, len(delta) - 1)
ci = (float(delta.mean() - t * delta.std(ddof=1) / np.sqrt(len(delta))), float(delta.mean() + t * delta.std(ddof=1) / np.sqrt(len(delta))))
print("metode PU terbaik:", best_pu, "selisih rata-rata:", round(delta.mean(), 4), "CI 95%:", np.round(ci, 4))

# %% [markdown]
# ## Ringkasan & cek

# %%
semi_summary = semi.agg(["mean", "std"]).T.reset_index(names="method")
report = observed.merge(semi_summary.rename(columns={"mean": "semi_synth_ap_mean", "std": "semi_synth_ap_std"}), on="method", how="left")
save_table(report, "tab_pu_methods", "Exploratory PU analysis (observed label and semi-synthetic recovery)")
save_table(priors, "tab_pu_priors", "Exploratory class-prior ranges")
checks.add("Q17", "w3" not in set(data.test["week"].unique()), "tanpa w3")
checks.raise_if_failed()
h3 = {"best_pu": best_pu, "delta": float(delta.mean()), "ci": ci, "h3_supported": bool(ci[0] > 0)}
(ctx.paths.results / "pu_dev.json").write_text(json.dumps(h3, indent=2) + "\n")
print(h3)
print(run.finish(n_train=len(s)))
