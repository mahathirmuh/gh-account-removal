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
# # 16 — Luaran paper
#
# **Tujuan:** memeriksa kelengkapan figur dan tabel, membangun `macros.tex`, dan memastikan luaran bebas login serta nama repo.

# %%
import json
import re
from pathlib import Path

import pandas as pd

from ghremoval.config import load_context
from ghremoval.quality import Checks, pii_columns
from ghremoval.report import write_macros, write_numbers
from ghremoval.runlog import RunLog

ctx = load_context(config_path)
run = RunLog("16_paper_outputs", ctx.paths.run_log, ctx.paths.root)
checks = Checks()

# %% [markdown]
# ## 1. Kelengkapan

# %%
listing = (ctx.paths.root / "docs/08-figures-and-tables.md").read_text(encoding="utf8")
names = sorted(set(re.findall(r"`((?:tab|fig)_[a-z0-9_]+)`", listing)))
existing = {p.stem for folder in (ctx.paths.tables, ctx.paths.figures) for p in folder.iterdir()}
missing = [n for n in names if n not in existing]
print("luaran terdaftar:", len(names), "tidak ada:", missing)

# %% [markdown]
# ## 2. Angka dan makro

# %%
write_numbers({"snapshot_date": ctx.p.label["snapshot_date"]})
numbers = json.loads(ctx.paths.numbers.read_text())
write_macros(numbers, ctx.paths.results / "macros.tex")
print(json.dumps(numbers, indent=1)[:1500])

# %% [markdown]
# ## 3. Cek privasi pada tabel

# %%
bad = {}
for path in ctx.paths.tables.glob("*.csv"):
    columns = list(pd.read_csv(path, nrows=1).columns)
    found = pii_columns(columns)
    if found:
        bad[path.name] = found
checks.add("Q20", not bad, f"kolom mencurigakan: {bad}")
checks.add("kelengkapan_luaran", not missing or set(missing) <= {"tab_audit_results"}, f"tidak ada: {missing}")
checks.raise_if_failed()
print(run.finish(n_outputs=len(existing)))
