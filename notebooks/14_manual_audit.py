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
# Mode `sample` menyiapkan sampel. Anotasi awal dikerjakan LLM dan divalidasi manusia (`docs/DEVIATIONS.md`).
# Mode `validation` memilih akun untuk validator, `adjudicate` menyiapkan file keputusan, dan `evaluate` membaca hasilnya.
# Kolom validasi manusia tidak pernah diisi oleh kode.

# %%
import json

import polars as pl

from ghremoval.analysis import hour_order, seeds
from ghremoval.audit import AUDIT_CATEGORIES, attach_pseudo, build_adjudication, cohen_kappa, draw_sample, draw_validation_sample, read_annotations, render_summaries, render_validation_sheet, write_summaries
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
if mode == "validation":
    human_path = folder / "audit_validation_human.csv"
    if human_path.exists():
        raise RuntimeError("Lembar validasi sudah ada. Hapus manual bila memang ingin mengulang.")
    llm = read_annotations(folder / "audit_annotator_LLM.csv")
    checks.add("llm_lengkap", llm.height == cfg["audit_sample_top"] + cfg["audit_sample_low"] and set(llm["category"]) <= set(AUDIT_CATEGORIES), f"{llm.height} baris")
    checks.raise_if_failed()
    validation = draw_validation_sample(llm, cfg["double_annotation_fraction"], ctx.p.project["seed"])
    validation.write_csv(folder / "audit_validation_key.csv")
    validation.select("audit_id").with_columns(pl.lit("").alias("category"), pl.lit("").alias("notes")).write_csv(human_path)
    rows = [json.loads(line) for line in (folder / "audit_sample.jsonl").read_text(encoding="utf8").splitlines()]
    (folder / "audit_validation_sample.md").write_text(render_validation_sheet(rows, validation["audit_id"].to_list()), encoding="utf8")
    print(validation.group_by("validation_set").len().sort("validation_set"))

# %%
if mode == "adjudicate":
    adjudication_path = folder / "audit_adjudication.csv"
    if adjudication_path.exists():
        raise RuntimeError("File keputusan sudah ada. Hapus manual bila memang ingin mengulang.")
    human = read_annotations(folder / "audit_validation_human.csv")
    expected = pl.read_csv(folder / "audit_validation_key.csv").height
    checks.add("validasi_lengkap", human.height == expected, f"{human.height} dari {expected}")
    checks.add("kategori_sah", set(human["category"].to_list()) <= set(AUDIT_CATEGORIES), "kategori sesuai panduan")
    checks.raise_if_failed()
    adjudication = build_adjudication(read_annotations(folder / "audit_annotator_LLM.csv"), human)
    adjudication.write_csv(adjudication_path)
    print(adjudication.group_by("status").len().sort("status"))

# %%
if mode == "evaluate":
    random_ids = pl.read_csv(folder / "audit_validation_key.csv").filter(pl.col("validation_set") == "random").select("audit_id")
    joined = read_annotations(folder / "audit_annotator_LLM.csv").join(read_annotations(folder / "audit_validation_human.csv"), on="audit_id", suffix="_human").join(random_ids, on="audit_id")
    kappa = cohen_kappa(joined["category"].to_list(), joined["category_human"].to_list())
    print("kappa LLM dan manusia pada sampel acak:", round(kappa, 3), "n:", joined.height)
    final = pl.read_csv(folder / "audit_adjudication.csv", schema_overrides={"final_category": pl.String})
    checks.add("adjudikasi_lengkap", final["final_category"].null_count() == 0, f"kosong: {final['final_category'].null_count()}")
    key = pl.read_csv(folder / "audit_key_do_not_open.csv")
    merged = final.join(key, on="audit_id")
    n_group = merged.group_by("score_group").len().rename({"len": "n_group"})
    table = merged.group_by(["score_group", "final_category"]).len().join(n_group, on="score_group").with_columns((pl.col("len") / pl.col("n_group")).alias("share")).sort(["score_group", "final_category"])
    table = table.with_columns(pl.struct("len", "n_group").map_elements(lambda r: list(wilson(r["len"], r["n_group"])), return_dtype=pl.List(pl.Float64)).alias("ci"))
    save_table(table.with_columns(pl.col("ci").list.get(0).alias("ci_low"), pl.col("ci").list.get(1).alias("ci_high")).drop("ci"), "tab_audit_results", "LLM annotation with human validation: categories per score group")
    write_numbers({"kappa_audit": kappa})
    checks.add("kappa", kappa >= cfg["min_kappa"], f"{kappa:.3f}")

# %% [markdown]
# ## Ringkasan & cek

# %%
checks.raise_if_failed()
print(run.finish(mode=mode))
