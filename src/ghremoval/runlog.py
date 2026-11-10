"""Satu baris catatan per eksekusi notebook."""

from __future__ import annotations

import json
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path


def git_commit(root: Path) -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    except subprocess.CalledProcessError:
        return "tanpa-commit"


class RunLog:
    def __init__(self, name: str, path: Path, root: Path) -> None:
        self.name, self.path, self.root = name, path, root
        self.started = time.time()

    def finish(self, **counts) -> dict:
        entry = {"notebook": self.name, "finished_at_utc": datetime.now(UTC).isoformat(timespec="seconds"), "git_commit": git_commit(self.root),
                 "duration_seconds": round(time.time() - self.started, 1), "counts": counts}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry
