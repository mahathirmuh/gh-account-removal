"""Catatan keputusan gerbang manusia, disimpan di results/gates.json."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from ghremoval.config import Context


def _path(ctx: Context):
    return ctx.paths.results / "gates.json"


def read_gates(ctx: Context) -> dict:
    path = _path(ctx)
    return json.loads(path.read_text(encoding="utf8")) if path.exists() else {}


def record_gate(ctx: Context, gate: str, decided_by: str, decision: str, rationale: str) -> dict:
    gates = read_gates(ctx)
    gates[gate] = {"decided_by": decided_by, "decision": decision, "rationale": rationale, "recorded_at_utc": datetime.now(UTC).isoformat(timespec="seconds")}
    _path(ctx).write_text(json.dumps(gates, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    return gates[gate]


def gate_passed(ctx: Context, gate: str) -> bool:
    return read_gates(ctx).get(gate, {}).get("decision") == "lanjut"
