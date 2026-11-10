"""Unduh GH Archive dan nilai kualitas tiap jam."""

from __future__ import annotations

import gzip
import hashlib
import json
import statistics
import time
from collections import Counter
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import orjson
import requests

from ghremoval.config import Context


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_manifest(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    entries = (json.loads(line) for line in path.read_text(encoding="utf8").splitlines() if line.strip())
    return {entry["path"]: entry for entry in entries}


def download_hour(ctx: Context, hour_id: str, retries: int = 5) -> dict:
    """Unduh satu jam bila belum ada, lalu catat di manifest. File yang sudah cocok dilewati."""
    url = f"{ctx.p.data['base_url']}/{hour_id}.json.gz"
    dest = ctx.paths.raw / f"{hour_id}.json.gz"
    key = str(dest.relative_to(ctx.paths.root))
    known = read_manifest(ctx.paths.manifest).get(key)
    if dest.exists() and known and sha256_file(dest) == known["sha256"]:
        return known
    if dest.exists():
        raise RuntimeError(f"{key} ada tetapi tidak cocok dengan manifest; raw bersifat immutable, periksa manual")
    tmp = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(retries):
        try:
            with requests.get(url, stream=True, timeout=120, headers={"User-Agent": ctx.p.project["user_agent"]}) as response:
                response.raise_for_status()
                expected = int(response.headers.get("Content-Length", 0))
                with open(tmp, "wb") as handle:
                    for chunk in response.iter_content(1 << 20):
                        handle.write(chunk)
            if expected and tmp.stat().st_size != expected:
                raise IOError(f"ukuran tidak cocok untuk {hour_id}")
            break
        except (requests.RequestException, IOError):
            if attempt == retries - 1:
                raise
            time.sleep(10 * 2**attempt)
    tmp.rename(dest)
    entry = {"url": url, "path": key, "downloaded_at_utc": datetime.now(UTC).isoformat(timespec="seconds"), "sha256": sha256_file(dest),
             "bytes": dest.stat().st_size, "content_length_header": expected}
    with open(ctx.paths.manifest, "a", encoding="utf8") as handle:
        handle.write(json.dumps(entry) + "\n")
    return entry


def iter_events(path: Path) -> Iterator[dict | None]:
    """Menghasilkan event; baris rusak menghasilkan None supaya bisa dihitung."""
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rb") as handle:
        for line in handle:
            try:
                yield orjson.loads(line)
            except orjson.JSONDecodeError:
                yield None


def minute_counts(events) -> Counter:
    return Counter(int(event["created_at"][14:16]) for event in events if event is not None)


def hour_quality(path: Path) -> dict:
    lines = bad = 0
    minutes: Counter = Counter()
    first, last = None, None
    for event in iter_events(path):
        lines += 1
        if event is None:
            bad += 1
            continue
        stamp = event["created_at"]
        minutes[int(stamp[14:16])] += 1
        first = stamp if first is None or stamp < first else first
        last = stamp if last is None or stamp > last else last
    values = [minutes.get(m, 0) for m in range(60)]
    median = statistics.median(values)
    return {"n_lines": lines, "n_bad": bad, "n_minutes": sum(1 for v in values if v), "minute_min": min(values), "minute_median": median,
            "minute_max": max(values), "minutes_below_half_median": sum(1 for v in values if v < 0.5 * median), "first_created_at": first, "last_created_at": last}


def compare_with_local(gz_path: Path, local_path: Path) -> dict:
    """Bandingkan file unduhan dengan file lokal pengguna, baca-saja."""
    gz = hour_quality(gz_path)
    local = hour_quality(local_path)
    keys = ("n_lines", "first_created_at", "last_created_at")
    return {"match": all(gz[k] == local[k] for k in keys), **{f"gz_{k}": gz[k] for k in keys}, **{f"local_{k}": local[k] for k in keys}}
