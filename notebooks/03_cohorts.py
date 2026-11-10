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
# # 03 — Akun dan kohort
#
# **Tujuan:** membangun dimensi akun dan tabel akun-jam, termasuk stratum dan kohort. Belum ada label.

# %%
import polars as pl

from ghremoval.build.accounts import build_account_dim, build_account_hour
from ghremoval.config import load_context
from ghremoval.quality import Checks
from ghremoval.report import save_table, write_numbers
from ghremoval.runlog import RunLog

ctx = load_context(config_path)
run = RunLog("03_cohorts", ctx.paths.run_log, ctx.paths.root)
checks = Checks()

# %%
account_hour = build_account_hour(ctx)
account_dim = build_account_dim(ctx, account_hour)
account_hour.write_parquet(ctx.paths.processed / "account_hour.parquet")
account_dim.write_parquet(ctx.paths.processed / "account_dim.parquet")
print(account_hour.shape, account_dim.shape)

# %% [markdown]
# ## Gambaran data, tanpa label

# %%
overview = (account_hour.group_by("week").agg(pl.col("hour_id").n_unique().alias("n_hours"), pl.col("n_events").sum().alias("n_events"), pl.col("actor_id").n_unique().alias("n_accounts"),
                                              pl.col("is_app_bot").sum().alias("n_bot_rows"), pl.col("in_fixed_cohort").sum().alias("n_fixed_cohort_rows")).sort("week"))
save_table(overview, "tab_dataset_overview", "Accounts and cohorts per week")
overview

# %%
strata = account_hour.filter(~pl.col("is_app_bot")).group_by(["week", "stratum"]).agg(pl.len().alias("n")).sort(["week", "stratum"]).pivot(on="stratum", index="week", values="n")
strata

# %% [markdown]
# ## Ringkasan & cek

# %%
dev = account_hour.filter(pl.col("week") == "dev")
nonbot = dev.filter(~pl.col("is_app_bot"))
n = nonbot["n_events"]
checks.add("Q06a", account_hour.select(pl.struct("actor_id", "hour_id").is_unique().all()).item(), "(actor_id, hour_id) unik")
checks.add("Q06b", not account_hour.filter(pl.col("is_app_bot") & pl.col("in_fixed_cohort")).height, "akun [bot] tidak masuk kohort")
firsts = account_hour.filter(pl.col("is_first_in_period")).with_columns(pl.col("week").replace({"w1": "w0", "w2": "w0"}).alias("p")).group_by(["actor_id", "p"]).len()
checks.add("Q07", firsts["len"].max() == 1, "satu baris kemunculan pertama per periode")
sanity = {"actor_id unik": (dev["actor_id"].n_unique(), 64864), "akun [bot]": (dev["is_app_bot"].sum(), 315), "non-bot": (nonbot.height, 64549), "median": (int(n.median()), 1),
          "p90": (int(n.quantile(0.9, "lower")), 5), "p99": (int(n.quantile(0.99, "lower")), 26), "maks": (int(n.max()), 6774), "kohort": (nonbot["in_fixed_cohort"].sum(), 8434),
          "5-19": (nonbot.filter(pl.col("stratum") == "5-19").height, 7576), "20+": (nonbot.filter(pl.col("stratum") == "20+").height, 858)}
for name, (got, want) in sanity.items():
    checks.add(f"sanity_{name}", got == want, f"{got} vs {want}")
share_one = (n == 1).mean()
checks.add("sanity_satu_event", abs(share_one - 0.525) < 0.001, f"{share_one:.4f}")
study = account_hour.filter(pl.col("week") != "dev")
write_numbers({"n_events_study": int(study["n_events"].sum()), "n_accounts_study": int(study["actor_id"].n_unique()), "n_fixed_cohort": int(study["in_fixed_cohort"].sum())})
checks.raise_if_failed()
print(run.finish(n_account_hour=account_hour.height, n_accounts=account_dim.height))
