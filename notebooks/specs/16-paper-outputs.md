# 16 — Luaran paper

Fase 7

## Tujuan

Menghasilkan figur, tabel, dan angka final untuk naskah.

## Input

`results/`, `docs/08`, `docs/00`.

## Output

- `results/figures/*`, `results/tables/*`
- `results/numbers.json`, `results/macros.tex`
- `results/release/` (opsional, setelah pengguna setuju): tabel fitur dan label terpseudonimisasi

## Langkah

1. Pastikan semua nama pada `docs/08` ada.
2. Bangun `macros.tex` dari `numbers.json`.
3. Tulis draf bagian Hasil dalam Bahasa Indonesia: keputusan tiap hipotesis, tanpa melebih-lebihkan. Sertakan hasil yang tidak mendukung.
4. Terapkan bahasa klaim `docs/00` dan aturan emas 12.
5. Rilis dataset hanya jika diminta: hapus login, email, `actor_id` mentah, dan pseudonim yang bisa ditautkan.

## Cek

Q20. Semua angka dalam teks berasal dari `numbers.json`. Tidak ada kata "pertama", "belum pernah", "abuse detection", atau "real-time" yang dipakai sebagai klaim.

## Test

`write_numbers` menggabungkan kunci tanpa menimpa kunci lain.
