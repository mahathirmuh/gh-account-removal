"""Kredensial. Nilainya tidak pernah boleh muncul lewat repr, str, atau log."""

from __future__ import annotations

import os
import secrets as stdlib_secrets
from pathlib import Path

from ghremoval.config import Context


class Secret:
    """Pembungkus nilai rahasia; akses nilainya hanya lewat `reveal()`."""

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        self._value = value

    def reveal(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return "Secret(***)"

    __str__ = __repr__


def _expand(path: str) -> Path:
    return Path(os.path.expanduser(path))


def token_file_ok(ctx: Context) -> bool:
    path = _expand(ctx.p.paths["token_env_file"])
    return path.exists() and (path.stat().st_mode & 0o777) == 0o600


def load_token(ctx: Context) -> Secret:
    for line in _expand(ctx.p.paths["token_env_file"]).read_text(encoding="utf8").splitlines():
        if line.startswith("GITHUB_TOKEN="):
            return Secret(line.split("=", 1)[1].strip())
    raise RuntimeError("GITHUB_TOKEN tidak ditemukan di file token")


def ensure_hmac_key(ctx: Context) -> bool:
    """Membuat kunci HMAC bila belum ada. Mengembalikan True bila kunci baru dibuat."""
    path = _expand(ctx.p.paths["hmac_key_file"])
    if path.exists():
        return False
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as handle:
        handle.write(stdlib_secrets.token_hex(32))
    return True


def load_hmac_key(ctx: Context) -> Secret:
    return Secret(_expand(ctx.p.paths["hmac_key_file"]).read_text(encoding="utf8").strip())
