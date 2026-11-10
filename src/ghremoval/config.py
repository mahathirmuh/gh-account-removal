"""Pemuatan konfigurasi dan lokasi folder proyek."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict
from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[2]


class Params(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project: dict[str, Any]
    paths: dict[str, str]
    data: dict[str, Any]
    holdout_open: bool
    label: dict[str, Any]
    annotation: dict[str, Any]
    web_crosscheck: dict[str, Any]
    locked: dict[str, Any]
    derived: dict[str, Any]
    reporting: dict[str, Any]


@dataclass(frozen=True)
class Paths:
    root: Path

    @property
    def raw(self) -> Path:
        return self.root / "data/raw/gharchive"

    @property
    def manifest(self) -> Path:
        return self.root / "data/manifest.jsonl"

    @property
    def interim(self) -> Path:
        return self.root / "data/interim"

    @property
    def processed(self) -> Path:
        return self.root / "data/processed"

    @property
    def annotation(self) -> Path:
        return self.root / "data/annotation"

    @property
    def results(self) -> Path:
        return self.root / "results"

    @property
    def tables(self) -> Path:
        return self.results / "tables"

    @property
    def figures(self) -> Path:
        return self.results / "figures"

    @property
    def numbers(self) -> Path:
        return self.results / "numbers.json"

    @property
    def run_log(self) -> Path:
        return self.results / "run_log.jsonl"

    @property
    def tools(self) -> Path:
        return self.root / "tools"

    def ensure(self) -> None:
        for path in (self.raw, self.interim, self.processed, self.annotation, self.tables, self.figures, self.tools):
            path.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class Context:
    params: Params
    paths: Paths
    config_path: Path

    @property
    def p(self) -> Params:
        return self.params

    def study_hours(self) -> dict[str, list[str]]:
        return dict(self.params.data["study_hours"])

    def all_hours(self) -> list[tuple[str, str]]:
        """Daftar (hour_id, week), jam dev lebih dulu."""
        hours = [(self.params.data["dev_hour"], "dev")]
        for week, items in self.study_hours().items():
            hours += [(hour, week) for hour in items]
        return hours

    def weeks_of(self, scope: str) -> list[str]:
        splits = self.params.locked["splits"]
        return {"dev": ["dev"], "train": list(splits["train_weeks"]), "val": list(splits["val_weeks"]), "holdout": list(splits["holdout_weeks"])}[scope]


def load_params(path: str | Path) -> Params:
    with open(path, encoding="utf8") as handle:
        return Params(**YAML(typ="safe").load(handle))


def load_context(config_path: str | Path = "config/params.yaml") -> Context:
    path = Path(config_path)
    if not path.is_absolute():
        path = ROOT / path
    return Context(params=load_params(path), paths=Paths(root=ROOT), config_path=path)


def update_params(ctx: Context, dotted_key: str, value: Any) -> None:
    """Menulis satu kunci di params.yaml dengan komentar tetap utuh."""
    yaml = YAML()
    yaml.preserve_quotes = True
    with open(ctx.config_path, encoding="utf8") as handle:
        document = yaml.load(handle)
    node = document
    keys = dotted_key.split(".")
    for key in keys[:-1]:
        node = node[key]
    node[keys[-1]] = value
    with open(ctx.config_path, "w", encoding="utf8") as handle:
        yaml.dump(document, handle)
