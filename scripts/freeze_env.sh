#!/usr/bin/env bash
# Simpan versi paket dan daftar data ke results/environment.txt.
set -euo pipefail
UV="${1:-uv}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/results/environment.txt"
{
  echo "# Dibuat oleh make freeze pada $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  "$UV" --version
  "$UV" run --project "$ROOT" python --version
  echo; echo "[packages]"
  "$UV" pip freeze --project "$ROOT"
  echo; echo "[data_manifest]"
  [ -f "$ROOT/data/manifest.jsonl" ] && cat "$ROOT/data/manifest.jsonl" || true
} > "$OUT"
echo "Ditulis: $OUT"
