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
# # 00 — Pemeriksaan environment
#
# **Tujuan:** memastikan environment, kredensial, dan koneksi siap sebelum data diunduh.
# Token dan kunci HMAC tidak pernah ditampilkan.

# %%
import platform
import shutil
import subprocess

import polars
import requests
import sklearn
import torch
import xgboost

from ghremoval.config import load_context
from ghremoval.quality import Checks
from ghremoval.runlog import RunLog
from ghremoval.secrets import ensure_hmac_key, load_token, token_file_ok

ctx = load_context(config_path)
ctx.paths.ensure()
run = RunLog("00_environment_check", ctx.paths.run_log, ctx.paths.root)
checks = Checks()

# %% [markdown]
# ## 1. Versi perangkat lunak

# %%
java = subprocess.run(["java", "-version"], capture_output=True, text=True).stderr.splitlines()[0]
versions = {"python": platform.python_version(), "polars": polars.__version__, "sklearn": sklearn.__version__, "xgboost": xgboost.__version__, "torch": torch.__version__, "java": java}
print(versions)
checks.add("cuda", torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else "tidak ada")

# %% [markdown]
# ## 2. Disk, token, dan koneksi

# %%
free_gb = shutil.disk_usage(ctx.paths.root).free / 1e9
checks.add("disk", free_gb >= 40, f"{free_gb:.0f} GB kosong")
checks.add("token_file", token_file_ok(ctx), "file token ada dan mode 600")
headers = {"Authorization": "Bearer " + load_token(ctx).reveal(), "User-Agent": ctx.p.project["user_agent"]}
response = requests.get("https://api.github.com/rate_limit", headers=headers, timeout=30)
limits = response.json()["resources"]
print({k: (limits[k]["limit"], limits[k]["remaining"]) for k in ("core", "graphql")})
checks.add("token_valid", response.status_code == 200, f"HTTP {response.status_code}")
checks.add("token_no_scope", response.headers.get("X-OAuth-Scopes", "") == "", "scope kosong")
head = requests.head(f"{ctx.p.data['base_url']}/{ctx.p.data['dev_hour']}.json.gz", timeout=30, headers={"User-Agent": ctx.p.project["user_agent"]})
checks.add("gharchive", head.status_code == 200, f"HTTP {head.status_code}")

# %% [markdown]
# ## 3. Kunci HMAC dan gitignore

# %%
print("kunci HMAC baru dibuat:", ensure_hmac_key(ctx))
ignore = (ctx.paths.root / ".gitignore").read_text()
checks.add("gitignore", all(item in ignore for item in ("/data/", "/tools/", "/mlruns/", "/2024-04-01-15.json/")), "pola wajib ada")

# %% [markdown]
# ## Ringkasan & cek

# %%
checks.raise_if_failed()
(ctx.paths.results / "environment.txt").write_text(str(versions) + "\n")
print(run.finish(checks=len(checks.results)))
