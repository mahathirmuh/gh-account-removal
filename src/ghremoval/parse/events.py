"""Mengubah raw GH Archive menjadi tabel tanpa data pribadi mentah (docs/03)."""

from __future__ import annotations

import hashlib
import hmac
from pathlib import Path

import polars as pl

from ghremoval.ingest.gharchive import iter_events

EVENT_SCHEMA = {
    "event_id": pl.String, "hour_id": pl.String, "week": pl.String, "created_at": pl.String, "second_of_hour": pl.Int32, "event_type": pl.String,
    "action": pl.String, "actor_id": pl.Int64, "actor_pseudo": pl.String, "is_app_bot": pl.Boolean, "repo_id": pl.Int64, "repo_owner_pseudo": pl.String,
    "repo_owner_is_actor": pl.Boolean, "repo_short_hash": pl.String, "repo_short_len": pl.Int32, "repo_short_has_digit": pl.Boolean, "has_org": pl.Boolean,
    "ref_type": pl.String, "push_size": pl.Int32, "push_distinct_size": pl.Int32, "pr_author_none": pl.Boolean,
}
COMMIT_SCHEMA = {"event_id": pl.String, "actor_id": pl.Int64, "hour_id": pl.String, "second_of_hour": pl.Int32, "msg_hash": pl.String, "msg_len": pl.Int32,
                 "author_is_noreply": pl.Boolean, "is_distinct": pl.Boolean}
ACTOR_SCHEMA = {"actor_id": pl.Int64, "actor_pseudo": pl.String, "is_app_bot": pl.Boolean, "login_len": pl.Int32, "login_digit_ratio": pl.Float64, "login_hyphen_count": pl.Int32}


def pseudo(value: str, key: bytes) -> str:
    return hmac.new(key, value.encode("utf8"), hashlib.sha256).hexdigest()[:16]


def normalize_short(name: str) -> str:
    return name.lower()


def short_hash(text: str) -> str:
    return hashlib.blake2b(text.encode("utf-8", "ignore"), digest_size=8).hexdigest()


def hash_msg(text: str) -> str:
    return short_hash(text)


def parse_event(raw: dict, key: bytes, hour_id: str, week: str, cache: dict[str, str]) -> tuple[tuple, list[tuple], tuple]:
    """Satu event raw menjadi baris event, baris commit, dan baris aktor."""
    def p(value: str) -> str:
        if value not in cache:
            cache[value] = pseudo(value, key)
        return cache[value]

    actor, repo, payload = raw["actor"], raw["repo"], raw.get("payload") or {}
    login, event_type, stamp = actor["login"], raw["type"], raw["created_at"]
    second = int(stamp[14:16]) * 60 + int(stamp[17:19])
    owner, short = repo["name"].split("/", 1) if "/" in repo["name"] else ("", repo["name"])
    is_bot = login.endswith("[bot]")
    pseudo_login = p(login)
    pr_none = None
    if event_type == "PullRequestEvent" and payload.get("action") == "opened":
        pr_none = (payload.get("pull_request") or {}).get("author_association") == "NONE"
    is_push = event_type == "PushEvent"
    event_row = (raw["id"], hour_id, week, stamp, second, event_type, payload.get("action"), actor["id"], pseudo_login, is_bot, repo["id"], p(owner.lower()),
                 owner.lower() == login.lower(), short_hash(normalize_short(short)), len(short), any(ch.isdigit() for ch in short), "org" in raw,
                 payload.get("ref_type"), payload.get("size") if is_push else None, payload.get("distinct_size") if is_push else None, pr_none)
    commit_rows = []
    if is_push:
        for commit in payload.get("commits") or []:
            message = (commit.get("message") or "").strip()
            noreply = "noreply" in ((commit.get("author") or {}).get("email") or "")
            commit_rows.append((raw["id"], actor["id"], hour_id, second, hash_msg(message), len(message), noreply, bool(commit.get("distinct", True))))
    digits = sum(ch.isdigit() for ch in login)
    actor_row = (actor["id"], pseudo_login, is_bot, len(login), digits / max(len(login), 1), login.count("-"))
    return event_row, commit_rows, actor_row


def _write(rows, schema, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(rows, schema=schema, orient="row").write_parquet(path)


def build_hour(raw_path: Path, interim: Path, key: bytes, hour_id: str, week: str) -> dict:
    """Parse satu jam lalu tulis tiga tabel interim. Mengembalikan statistik jam itu."""
    events, commits, actors, cache, seen = [], [], {}, {}, set()
    bad = truncated = duplicates = 0
    for raw in iter_events(raw_path):
        if raw is None:
            bad += 1
            continue
        if raw["id"] in seen:
            duplicates += 1
            continue
        seen.add(raw["id"])
        event_row, commit_rows, actor_row = parse_event(raw, key, hour_id, week, cache)
        events.append(event_row)
        commits.extend(commit_rows)
        actors[actor_row[0]] = actor_row
        if raw["type"] == "PushEvent" and raw["payload"].get("size", 0) > len(raw["payload"].get("commits") or []):
            truncated += 1
    _write(events, EVENT_SCHEMA, interim / f"events/hour_id={hour_id}/part.parquet")
    _write(commits, COMMIT_SCHEMA, interim / f"commit_msgs/hour_id={hour_id}/part.parquet")
    _write(list(actors.values()), ACTOR_SCHEMA, interim / f"actor_login_features/hour_id={hour_id}/part.parquet")
    return {"hour_id": hour_id, "week": week, "n_events": len(events), "n_commits": len(commits), "n_actors": len(actors), "n_bad": bad, "n_duplicates": duplicates, "n_push_truncated": truncated}
