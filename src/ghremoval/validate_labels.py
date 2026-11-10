"""Validasi arti label (docs/04). Login hanya berada di memori selama pemeriksaan."""

from __future__ import annotations

import time
from collections import Counter

import numpy as np
import polars as pl
import requests
from scipy.stats import spearmanr

from ghremoval.config import Context
from ghremoval.github_client import API_PREFIX, GitHubClient
from ghremoval.ingest.gharchive import iter_events

LOGIN_QUERY = "query($ids:[ID!]!){nodes(ids:$ids){... on User{login} ... on Organization{login}}}"
OBJECT_PREFIX = API_PREFIX + "repos/"


def raw_scan(ctx: Context, hours: list[str], actor_ids: set[int]) -> tuple[dict[int, str], dict[int, list[str]]]:
    """Login pada event dan URL objek di repo orang lain, untuk akun terpilih."""
    logins: dict[int, str] = {}
    objects: dict[int, list[str]] = {}
    for hour in hours:
        for raw in iter_events(ctx.paths.raw / f"{hour}.json.gz"):
            if raw is None or raw["actor"]["id"] not in actor_ids:
                continue
            actor, payload, event_type = raw["actor"], raw.get("payload") or {}, raw["type"]
            logins.setdefault(actor["id"], actor["login"])
            url = None
            if event_type in ("IssueCommentEvent", "PullRequestReviewCommentEvent", "CommitCommentEvent"):
                url = (payload.get("comment") or {}).get("url")
            elif event_type == "IssuesEvent" and payload.get("action") == "opened":
                url = (payload.get("issue") or {}).get("url")
            elif event_type == "PullRequestEvent" and payload.get("action") == "opened":
                url = (payload.get("pull_request") or {}).get("url")
            if url and url.startswith(OBJECT_PREFIX) and raw["repo"]["name"].split("/")[0].lower() != actor["login"].lower():
                objects.setdefault(actor["id"], []).append(url)
    return logins, objects


def current_logins(client: GitHubClient, ids: list[int], legacy_id) -> dict[int, str]:
    out: dict[int, str] = {}
    for k in range(0, len(ids), 100):
        batch = ids[k:k + 100]
        response = client.graphql(LOGIN_QUERY, {"ids": [legacy_id(i) for i in batch]})
        for actor_id, node in zip(batch, (response.get("data") or {}).get("nodes", [])):
            if node and node.get("login"):
                out[actor_id] = node["login"]
    return out


class WebChecker:
    """HEAD ke halaman profil publik tanpa token, tanpa mengikuti redirect."""

    def __init__(self, user_agent: str, sleep_seconds: float) -> None:
        self.session = requests.Session()
        self.session.headers["User-Agent"] = user_agent
        self.sleep_seconds, self.limited = sleep_seconds, 0

    def status(self, login: str) -> int | str:
        if self.limited >= 3:
            return "dihentikan_429"
        try:
            response = self.session.head(f"https://github.com/{login}", allow_redirects=False, timeout=30)
        except requests.RequestException as error:
            return type(error).__name__
        if response.status_code == 429:
            self.limited += 1
            time.sleep(min(int(response.headers.get("Retry-After") or 60), 120))
        time.sleep(self.sleep_seconds)
        return response.status_code


def web_crosscheck(checker: WebChecker, gone: dict[int, str], present: dict[int, str]) -> dict[str, dict]:
    table = {"api_gone": Counter(), "api_present": Counter()}
    for name, group in (("api_gone", gone), ("api_present", present)):
        for login in group.values():
            table[name][checker.status(login)] += 1
    return {k: {str(a): b for a, b in v.items()} for k, v in table.items()}


def id_age_check(actor_ids: np.ndarray, created: pl.Series) -> dict:
    """Korelasi peringkat ID dan waktu pembuatan, serta monotonisitas per desil."""
    epoch = created.str.to_datetime("%Y-%m-%dT%H:%M:%SZ", strict=False).dt.epoch("s").to_numpy()
    valid = ~np.isnan(epoch.astype(float))
    ids, seconds = actor_ids[valid], epoch[valid].astype(float)
    rho = float(spearmanr(ids, seconds).statistic)
    deciles = np.quantile(ids, np.linspace(0, 1, 11))
    medians = [float(np.median(seconds[(ids >= low) & (ids <= high)])) for low, high in zip(deciles[:-1], deciles[1:])]
    return {"n": int(valid.sum()), "spearman": rho, "monotone_deciles": bool(all(b > a for a, b in zip(medians, medians[1:])))}


def ghost_probe(client: GitHubClient, accounts: dict[int, list[str]], rng: np.random.Generator, per_account: int = 3) -> dict:
    """Atribusi objek milik akun di repo orang lain."""
    by_account: Counter = Counter()
    by_object: Counter = Counter()
    for actor_id, urls in accounts.items():
        picked = list(rng.permutation(urls)[:per_account])
        results: Counter = Counter()
        for url in picked:
            status, body = client.get(url)
            if status == 200:
                author = (body or {}).get("user") or {}
                results["ghost" if author.get("login") == "ghost" else ("attributed" if author.get("id") == actor_id else "other_author")] += 1
            else:
                results[f"http_{status}"] += 1
        by_object.update(results)
        by_account["ghost" if results["ghost"] else "attributed" if results["attributed"] else "other_author" if results["other_author"] else "object_unavailable"] += 1
    return {"accounts": dict(by_account), "objects": dict(by_object), "n_accounts": len(accounts)}
