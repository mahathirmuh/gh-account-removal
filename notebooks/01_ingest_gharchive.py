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
# # 01 — Unduh GH Archive
#
# **Tujuan:** mengunduh 25 jam GH Archive secara immutable dan menilai kualitas tangkapan tiap jam.

# %%
from concurrent.futures import ProcessPoolExecutor

import pandas as pd

from ghremoval.config import load_context
from ghremoval.ingest.gharchive import compare_with_local, download_hour, hour_quality
from ghremoval.quality import Checks
from ghremoval.report import save_table
from ghremoval.runlog import RunLog

ctx = load_context(config_path)
ctx.paths.ensure()
run = RunLog("01_ingest_gharchive", ctx.paths.run_log, ctx.paths.root)
checks = Checks()
hours = ctx.all_hours()

# %% [markdown]
# ## 1. Unduh

# %%
entries = [download_hour(ctx, hour) for hour, _ in hours]
print("file:", len(entries), "total GB:", round(sum(e["bytes"] for e in entries) / 1e9, 2))

# %% [markdown]
# ## 2. Kualitas tiap jam

# %%
paths = [ctx.paths.raw / f"{hour}.json.gz" for hour, _ in hours]
with ProcessPoolExecutor(max_workers=4) as pool:
    quality = list(pool.map(hour_quality, paths))
table = pd.DataFrame([{"hour_id": hour, "week": week, **q} for (hour, week), q in zip(hours, quality)])
save_table(table, "tab_hour_quality", "Capture quality per hour")
table[["hour_id", "week", "n_lines", "n_bad", "n_minutes", "minute_min", "minute_median", "minute_max", "minutes_below_half_median"]]

# %% [markdown]
# ## 3. Jam dev terhadap file lokal pengguna

# %%
comparison = compare_with_local(ctx.paths.raw / f"{ctx.p.data['dev_hour']}.json.gz", ctx.paths.root / ctx.p.paths["local_dev_file"])
print(comparison)

# %% [markdown]
# ## Ringkasan & cek

# %%
checks.add("Q01a", len(entries) == 25, f"{len(entries)} file")
checks.add("Q01b", (table["n_minutes"] == 60).all(), "tiap jam memuat 60 menit")
violations = table.loc[table["minutes_below_half_median"] > 0, ["hour_id", "minutes_below_half_median"]]
print("jam dengan menit di bawah 50% median:\n", violations.to_string(index=False) if len(violations) else "tidak ada")
checks.add("Q02", violations.empty, f"{len(violations)} jam melanggar")
checks.add("Q03", comparison["match"], "jam dev cocok dengan file lokal")
checks.raise_if_failed()
print(run.finish(n_hours=len(entries), n_events=int(table["n_lines"].sum())))
