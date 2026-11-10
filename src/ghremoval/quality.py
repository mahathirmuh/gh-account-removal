"""Assertion kualitas data (docs/07)."""

from __future__ import annotations

from dataclasses import dataclass, field

FORBIDDEN_COLUMN_MARKERS = ("login", "email", "message", "repo_name", "title", "body")
ALLOWED_DERIVED = {"login_len", "login_digit_ratio", "login_hyphen_count"}


@dataclass
class Checks:
    results: list[tuple[str, bool, str]] = field(default_factory=list)

    def add(self, check_id: str, passed: bool, detail: str = "") -> None:
        self.results.append((check_id, bool(passed), detail))
        print(f"[{'LULUS' if passed else 'GAGAL'}] {check_id}: {detail}")

    def raise_if_failed(self) -> None:
        failed = [item for item in self.results if not item[1]]
        if failed:
            raise AssertionError(f"Cek gagal: {failed}")


def pii_columns(columns: list[str]) -> list[str]:
    """Nama kolom yang menyerupai data pribadi mentah."""
    return [c for c in columns if c not in ALLOWED_DERIVED and any(marker in c.lower() for marker in FORBIDDEN_COLUMN_MARKERS)]


def wilson(k: float, n: float, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    m = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return c - m, c + m
