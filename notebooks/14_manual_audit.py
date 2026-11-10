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
mode = "sample"

# %% [markdown]
# # 14 — Audit manual
#
# **Tujuan:** memperkirakan arti substantif dari akun hilang dan akun skor tinggi, sesuai `docs/04`.
#
# Mode `sample` menyiapkan file untuk anotator. Mode `evaluate` membaca hasil anotasi dua manusia.
# Kolom anotasi tidak pernah diisi oleh kode.

# %%
import json

import polars as pl

from ghremoval.analysis import hour_order, seeds
from ghremoval.audit import attach_pseudo, cohen_kappa, draw_sample, render_summaries, write_summaries
from ghremoval.config import load_context
from ghremoval.models.fit import fit_predict, load_stage
from ghremoval.quality import Checks, wilson
from ghremoval.report import save_table, write_numbers
from ghremoval.runlog import RunLog
from ghremoval.secrets import load_hmac_key

ctx = load_context(config_path)
run = RunLog(f"14_manual_audit_{mode}", ctx.paths.run_log, ctx.paths.root)
checks = Checks()
cfg = ctx.p.annotation
folder = ctx.paths.annotation

# %%
if mode == "sample":
    best = json.loads((ctx.paths.results / "best_params.json").read_text())
    data = load_stage(ctx, "dev", 60)
    assert set(data.test["week"].unique()) == {"w2"}
    score = fit_predict("xgb", best["xgb"], "M_behav", data.train, [data.test], hour_order(ctx), seeds(ctx))[0]
    sample, key = draw_sample(attach_pseudo(ctx, data.test), score, cfg["audit_sample_top"], cfg["audit_sample_low"], ctx.p.project["seed"])
    write_summaries(render_summaries(ctx, sample, load_hmac_key(ctx).reveal().encode()), folder / "audit_sample.jsonl")
    sample.select("audit_id", "actor_pseudo", "stratum").write_csv(folder / "audit_sample.csv")
    key.write_csv(folder / "audit_key_do_not_open.csv")
    template = sample.select("audit_id").with_columns(pl.lit("").alias("category"), pl.lit("").alias("notes"))
    for name in ("A", "B"):
        template.write_csv(folder / f"audit_annotator_{name}.csv")
    print("sampel:", sample.height, "ringkasan ditulis ke data/annotation/audit_sample.jsonl")
    checks.add("Q17", set(data.test["week"].unique()) == {"w2"}, "sampel dari w2, tanpa w3")

# %%
if mode == "evaluate":
    a, b = (pl.read_csv(folder / f"audit_annotator_{name}.csv").filter(pl.col("category") != "") for name in ("A", "B"))
    joined = a.join(b, on="audit_id", suffix="_b")
    kappa = cohen_kappa(joined["category"].to_list(), joined["category_b"].to_list())
    print("kappa:", round(kappa, 3), "n:", joined.height)
    final = pl.read_csv(folder / "audit_adjudication.csv")
    key = pl.read_csv(folder / "audit_key_do_not_open.csv")
    merged = final.join(key, on="audit_id")
    n_group = merged.group_by("score_group").len().rename({"len": "n_group"})
    table = merged.group_by(["score_group", "final_category"]).len().join(n_group, on="score_group").with_columns((pl.col("len") / pl.col("n_group")).alias("share")).sort(["score_group", "final_category"])
    table = table.with_columns(pl.struct("len", "n_group").map_elements(lambda r: list(wilson(r["len"], r["n_group"])), return_dtype=pl.List(pl.Float64)).alias("ci"))
    save_table(table.with_columns(pl.col("ci").list.get(0).alias("ci_low"), pl.col("ci").list.get(1).alias("ci_high")).drop("ci"), "tab_audit_results", "Manual audit categories per score group")
    write_numbers({"kappa_audit": kappa})
    checks.add("kappa", kappa >= cfg["min_kappa"], f"{kappa:.3f}")

# %% [markdown]
# ## Ringkasan & cek

# %%
checks.raise_if_failed()
print(run.finish(mode=mode))
