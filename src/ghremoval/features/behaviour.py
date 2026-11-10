"""Fitur per akun dan per jendela (docs/05). Definisi mengikuti scripts/pilot/pilot_signal.py."""

from __future__ import annotations

import math
from collections import Counter
from pathlib import Path

import polars as pl

TYPES = ["PushEvent", "CreateEvent", "PullRequestEvent", "DeleteEvent", "WatchEvent", "IssueCommentEvent", "PullRequestReviewEvent", "IssuesEvent",
         "PullRequestReviewCommentEvent", "ForkEvent", "ReleaseEvent", "PublicEvent", "MemberEvent", "GollumEvent", "CommitCommentEvent"]
FAMILIES = {
    "type_mix": [f"share_{t}" for t in TYPES] + ["n_event_types"],
    "temporal": ["n_active_minutes", "gap_mean", "gap_std", "gap_cv", "burstiness", "gap_min", "share_zero_gap", "share_modal_gap", "span_seconds", "minute_entropy", "max_events_per_minute"],
    "repo": ["n_repos", "repos_per_event", "repo_entropy", "top_repo_share", "share_own_repo", "share_org_events"],
    "push": ["push_size_mean", "push_size_max", "push_size_sum", "push_distinct_ratio"],
    "commit_msg": ["n_commit_msgs", "msg_unique_ratio", "msg_len_mean", "msg_top_share"],
    "create_pr": ["n_new_repos", "n_new_branches", "n_new_tags", "pr_author_none_ratio"],
    "repo_names": ["repo_short_len_mean", "repo_short_digit_share", "repo_short_unique_per_event"],
}
BEHAVIOUR_COLUMNS = [name for family in FAMILIES.values() for name in family]
PROXY_COLUMNS = ["msg_others_max", "msg_others_log_mean", "msg_any_shared", "msg_share_1_50", "repo_others_max", "repo_others_log_mean", "repo_any_shared",
                 "short_others_max", "short_others_log_mean", "short_any_shared"]
EPS = 1e-9


def entropy(values) -> float:
    total = sum(values)
    return -sum((v / total) * math.log(v / total) for v in values if v)


def account_behaviour(seconds: list[int], types: list[str], repos: list[int], own: list[bool], org: list[bool], short_len: list[int], short_digit: list[bool],
                      short_hash: list[str], refs: list[str | None], push_size: list[int | None], push_distinct: list[int | None], pr_none: list[bool | None],
                      msgs: list[tuple[str, int]]) -> list[float]:
    """Fitur 48 kolom untuk satu akun. `seconds` harus sudah terurut."""
    n = len(seconds)
    type_counts = Counter(types)
    gaps = [float(b - a) for a, b in zip(seconds, seconds[1:])] or [0.0]
    m = len(gaps)
    mu = sum(gaps) / m
    sd = math.sqrt(sum((g - mu) ** 2 for g in gaps) / m)
    minutes = Counter(s // 60 for s in seconds)
    gap_counts = Counter(gaps)
    repo_counts = Counter(repos)
    pushes = [v for v in push_size if v is not None] or [0]
    distinct = [v for v in push_distinct if v is not None] or [0]
    new_repo = new_branch = new_tag = 0
    for t, ref in zip(types, refs):
        if t == "CreateEvent":
            new_repo += ref == "repository"
            new_branch += ref == "branch"
            new_tag += ref == "tag"
    opened = [v for v in pr_none if v is not None]
    n_msgs = len(msgs)
    msg_counts = Counter(h for h, _ in msgs)
    return [type_counts[t] / n for t in TYPES] + [
        len(type_counts), len(minutes), mu, sd, sd / (mu + EPS), (sd - mu) / (sd + mu + EPS), min(gaps), gap_counts[0.0] / m, max(gap_counts.values()) / m,
        float(seconds[-1] - seconds[0]), entropy(list(minutes.values())), max(minutes.values()),
        len(repo_counts), len(repo_counts) / n, entropy(list(repo_counts.values())), max(repo_counts.values()) / n, sum(own) / n, sum(org) / n,
        sum(pushes) / len(pushes), max(pushes), sum(pushes), sum(distinct) / (sum(pushes) + EPS),
        n_msgs, len(msg_counts) / (n_msgs + EPS), (sum(length for _, length in msgs) / n_msgs if n_msgs else 0.0), (max(msg_counts.values()) / n_msgs if n_msgs else 0.0),
        new_repo, new_branch, new_tag, (sum(opened) / len(opened) if opened else -1.0),
        sum(short_len) / n, sum(short_digit) / n, len(set(short_hash)) / n,
    ]


def _shared_counts(df: pl.DataFrame, key: str) -> pl.DataFrame:
    """Baris unik (akun, kunci) dengan banyaknya akun lain yang memakai kunci itu."""
    unique = df.select("actor_id", key).unique()
    return unique.with_columns((pl.len().over(key) - 1).alias("others"))


def coordination_proxies(events: pl.DataFrame, commits: pl.DataFrame) -> pl.DataFrame:
    """Sepuluh proksi koordinasi per akun, dihitung atas semua akun non-bot pada jendela yang sama."""
    log1p = pl.col("others").log1p()
    msg = _shared_counts(commits, "msg_hash").group_by("actor_id").agg(pl.col("others").max().cast(pl.Float64).alias("msg_others_max"), log1p.mean().alias("msg_others_log_mean"),
                                                                     (pl.col("others") >= 1).mean().alias("msg_any_shared"), pl.col("others").is_between(1, 50).mean().alias("msg_share_1_50"))
    repo = _shared_counts(events, "repo_id").group_by("actor_id").agg(pl.col("others").max().cast(pl.Float64).alias("repo_others_max"), log1p.mean().alias("repo_others_log_mean"), (pl.col("others") >= 1).mean().alias("repo_any_shared"))
    short = _shared_counts(events, "repo_short_hash").group_by("actor_id").agg(pl.col("others").max().cast(pl.Float64).alias("short_others_max"), log1p.mean().alias("short_others_log_mean"), (pl.col("others") >= 1).mean().alias("short_any_shared"))
    accounts = events.select("actor_id").unique()
    out = accounts.join(msg, on="actor_id", how="left").join(repo, on="actor_id", how="left").join(short, on="actor_id", how="left")
    return out.with_columns(pl.col(PROXY_COLUMNS[:4]).fill_null(-1.0))


def window_features(events: pl.DataFrame, commits: pl.DataFrame, window_min: int, keep: pl.DataFrame | None = None) -> pl.DataFrame:
    """Fitur 48 + 10 untuk akun non-bot pada jendela `window_min`, hanya dari event sebelum cutoff.

    `keep` (kolom actor_id) membatasi akun yang ditulis; akun lain tetap dihitung untuk proksi koordinasi.
    """
    cutoff = 60 * window_min
    ev = events.filter((pl.col("second_of_hour") < cutoff) & ~pl.col("is_app_bot")).sort(["actor_id", "second_of_hour"])
    cm = commits.filter(pl.col("second_of_hour") < cutoff).join(ev.select("actor_id").unique(), on="actor_id", how="semi")
    proxies = coordination_proxies(ev, cm)
    target = ev if keep is None else ev.join(keep, on="actor_id", how="semi")
    grouped = target.group_by("actor_id", maintain_order=True).agg("second_of_hour", "event_type", "repo_id", "repo_owner_is_actor", "has_org", "repo_short_len", "repo_short_has_digit",
                                                                   "repo_short_hash", "ref_type", "push_size", "push_distinct_size", "pr_author_none")
    msgs = {row[0]: list(zip(row[1], row[2])) for row in cm.group_by("actor_id").agg("msg_hash", "msg_len").iter_rows()}
    ids, n_events, rows = [], [], []
    for r in grouped.iter_rows():
        ids.append(r[0])
        n_events.append(len(r[1]))
        rows.append(account_behaviour(r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11], r[12], msgs.get(r[0], [])))
    frame = pl.DataFrame(rows, schema={c: pl.Float64 for c in BEHAVIOUR_COLUMNS}, orient="row") if rows else pl.DataFrame(schema={c: pl.Float64 for c in BEHAVIOUR_COLUMNS})
    out = pl.DataFrame({"actor_id": ids, "n_events_w": n_events}, schema={"actor_id": pl.Int64, "n_events_w": pl.Int32}).hstack(frame)
    return out.join(proxies, on="actor_id", how="left").with_columns(pl.lit(window_min).cast(pl.Int32).alias("window_min"))


def build_hour_features(interim: Path, processed: Path, hour_id: str, windows: list[int], deployable_min: int) -> dict:
    """Menulis fitur satu jam untuk semua jendela."""
    columns = ["actor_id", "is_app_bot", "second_of_hour", "event_type", "repo_id", "repo_owner_is_actor", "has_org", "repo_short_len", "repo_short_has_digit", "repo_short_hash", "ref_type",
               "push_size", "push_distinct_size", "pr_author_none"]
    events = pl.read_parquet(interim / f"events/hour_id={hour_id}/part.parquet", columns=columns)
    commits = pl.read_parquet(interim / f"commit_msgs/hour_id={hour_id}/part.parquet", columns=["actor_id", "second_of_hour", "msg_hash", "msg_len"])
    hours = pl.read_parquet(processed / "account_hour.parquet", columns=["actor_id", "hour_id", "in_fixed_cohort"]).filter(pl.col("hour_id") == hour_id)
    fixed = hours.filter(pl.col("in_fixed_cohort")).select("actor_id")
    stats = {"hour_id": hour_id}
    for w in windows:
        cutoff = 60 * w
        counts = events.filter((pl.col("second_of_hour") < cutoff) & ~pl.col("is_app_bot")).group_by("actor_id").len()
        keep = None if w == 60 else pl.concat([counts.filter(pl.col("len") >= deployable_min).select("actor_id"), fixed.join(counts, on="actor_id", how="semi")]).unique()
        frame = window_features(events, commits, w, keep).with_columns(pl.lit(hour_id).alias("hour_id"))
        path = processed / f"features_by_hour/window={w}/{hour_id}.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.write_parquet(path)
        stats[f"w{w}"] = frame.height
    return stats


def merge_windows(processed: Path, windows: list[int]) -> None:
    for w in windows:
        out = processed / f"features/window={w}/part.parquet"
        out.parent.mkdir(parents=True, exist_ok=True)
        pl.scan_parquet(str(processed / f"features_by_hour/window={w}/*.parquet")).sink_parquet(out)
