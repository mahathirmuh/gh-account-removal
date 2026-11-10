"""Sampel audit manual (docs/04). Kolom validasi manusia tidak pernah diisi oleh kode."""

from __future__ import annotations

import json
from collections import Counter

import numpy as np
import polars as pl

from ghremoval.config import Context
from ghremoval.ingest.gharchive import iter_events
from ghremoval.parse.events import pseudo

AUDIT_CATEGORIES = ("promotion_or_spam", "bulk_automation", "ordinary_development", "unclear")
RARE_CATEGORIES = ("promotion_or_spam", "bulk_automation")


def read_annotations(path) -> pl.DataFrame:
    """Baris anotasi yang sudah terisi."""
    return pl.read_csv(path, schema_overrides={"category": pl.String, "notes": pl.String}).filter(pl.col("category").is_not_null() & (pl.col("category") != ""))


def draw_validation_sample(llm: pl.DataFrame, fraction: float, seed: int) -> pl.DataFrame:
    """Akun untuk validasi manusia. Sampel acak dipakai untuk κ; label jarang dan keyakinan rendah ditambahkan untuk koreksi."""
    llm = llm.sort("audit_id")
    rng = np.random.default_rng(seed)
    random_ids = rng.choice(llm["audit_id"].to_numpy(), int(np.ceil(llm.height * fraction)), replace=False).tolist()
    targeted = llm.filter((pl.col("category").is_in(RARE_CATEGORIES) | (pl.col("confidence") == "rendah")) & ~pl.col("audit_id").is_in(random_ids))["audit_id"].to_list()
    rows = [(i, "random") for i in random_ids] + [(i, "targeted") for i in targeted]
    return pl.DataFrame([rows[i] for i in rng.permutation(len(rows))], schema={"audit_id": pl.Int64, "validation_set": pl.String}, orient="row")


def render_validation_sheet(rows: list[dict], audit_ids: list[int]) -> str:
    """Ringkasan akun untuk validator, dalam blok kode supaya tautan di dalam teks tidak aktif."""
    by_id = {row["audit_id"]: row for row in rows}
    parts = ["# Data validasi\n"]
    for audit_id in audit_ids:
        row = by_id[audit_id]
        lines = ["event_counts: " + ", ".join(f"{k}={v}" for k, v in row["event_counts"].items())]
        for field in ("repo_names", "commit_messages", "pr_titles"):
            lines.append(f"{field}:")
            lines += [f"  - {' '.join(str(value).split())}" for value in row[field]] or ["  (kosong)"]
        parts.append(f"## audit_id {audit_id}\n\n```text\n" + "\n".join(lines).replace("```", "'''") + "\n```\n")
    return "\n".join(parts)


def build_adjudication(llm: pl.DataFrame, human: pl.DataFrame) -> pl.DataFrame:
    """File keputusan. `final_category` terisi bila akun tidak divalidasi atau kedua penilaian sama, dan kosong bila berbeda."""
    joined = llm.select("audit_id", pl.col("category").alias("llm_category")).join(human.select("audit_id", pl.col("category").alias("human_category")), on="audit_id", how="left")
    same = pl.col("human_category") == pl.col("llm_category")
    missing = pl.col("human_category").is_null()
    return joined.with_columns(
        pl.when(missing | same).then(pl.col("llm_category")).otherwise(pl.lit(None, dtype=pl.String)).alias("final_category"),
        pl.when(missing).then(pl.lit("llm")).when(same).then(pl.lit("setuju")).otherwise(pl.lit("berbeda")).alias("status"),
    ).sort("audit_id")


def cohen_kappa(a: list[str], b: list[str]) -> float:
    """Cohen's κ untuk dua anotator."""
    n = len(a)
    labels = sorted(set(a) | set(b))
    observed = sum(x == y for x, y in zip(a, b)) / n
    count_a, count_b = Counter(a), Counter(b)
    expected = sum(count_a[label] * count_b[label] for label in labels) / (n * n)
    return (observed - expected) / (1 - expected) if expected < 1 else float("nan")


def attach_pseudo(ctx: Context, frame: pl.DataFrame) -> pl.DataFrame:
    """Menambahkan pseudonim akun, dengan urutan baris tetap."""
    dim = pl.read_parquet(ctx.paths.processed / "account_dim.parquet", columns=["actor_id", "actor_pseudo"])
    return frame.join(dim, on="actor_id", how="left", maintain_order="left")


def draw_sample(frame: pl.DataFrame, score: np.ndarray, n_top: int, n_low: int, seed: int) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Sampel skor tinggi dan skor rendah dengan distribusi stratum sama. Mengembalikan (sampel acak, kunci kelompok)."""
    rng = np.random.default_rng(seed)
    data = frame.select("actor_id", "hour_id", "stratum", "actor_pseudo").with_columns(pl.Series("score", score))
    top = data.sort("score", descending=True).head(n_top).with_columns(pl.lit("top").alias("score_group"))
    below = data.sort("score", descending=True).slice(n_top, None).filter(pl.col("score") < pl.col("score").median().over("stratum"))
    wanted = top.group_by("stratum").len().to_dicts()
    parts = [below.filter(pl.col("stratum") == row["stratum"]).sample(n=min(row["len"], below.filter(pl.col("stratum") == row["stratum"]).height), seed=seed) for row in wanted]
    low = pl.concat(parts).with_columns(pl.lit("low").alias("score_group")).head(n_low)
    sample = pl.concat([top, low])
    sample = sample[rng.permutation(sample.height)].with_row_index("audit_id")
    return sample.select("audit_id", "actor_id", "hour_id", "stratum", "actor_pseudo"), sample.select("audit_id", "score_group", "score")


def render_summaries(ctx: Context, sample: pl.DataFrame, key: bytes) -> list[dict]:
    """Ringkasan publik tiap akun dari raw, dengan login diganti pseudonim dan tanpa email."""
    wanted = {(row["actor_id"], row["hour_id"]): row["audit_id"] for row in sample.iter_rows(named=True)}
    by_hour: dict[str, set[int]] = {}
    for (actor_id, hour) in wanted:
        by_hour.setdefault(hour, set()).add(actor_id)
    data: dict[int, dict] = {audit: {"audit_id": audit, "event_counts": Counter(), "repo_names": [], "commit_messages": [], "pr_titles": []} for audit in wanted.values()}
    for hour, actors in by_hour.items():
        for raw in iter_events(ctx.paths.raw / f"{hour}.json.gz"):
            if raw is None or raw["actor"]["id"] not in actors:
                continue
            entry = data[wanted[(raw["actor"]["id"], hour)]]
            login = raw["actor"]["login"]
            mask = lambda text: text.replace(login, pseudo(login, key)[:8])  # noqa: E731
            entry["event_counts"][raw["type"]] += 1
            name = mask(raw["repo"]["name"].split("/", 1)[-1])
            if name not in entry["repo_names"] and len(entry["repo_names"]) < 20:
                entry["repo_names"].append(name)
            payload = raw.get("payload") or {}
            for commit in payload.get("commits") or []:
                if len(entry["commit_messages"]) < 20:
                    entry["commit_messages"].append(mask((commit.get("message") or "")[:200]))
            if raw["type"] == "PullRequestEvent" and len(entry["pr_titles"]) < 10:
                entry["pr_titles"].append(mask(((payload.get("pull_request") or {}).get("title") or "")[:200]))
    return [{**entry, "event_counts": dict(entry["event_counts"])} for entry in data.values()]


def write_summaries(rows: list[dict], path) -> None:
    with open(path, "w", encoding="utf8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
