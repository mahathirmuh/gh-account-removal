# 07 — Mining dense block

Fase 3

## Tujuan

Menghasilkan fitur dense-block lintas jenis event untuk RQ5, tanpa label.

## Input

Tabel `events`.

## Output

`data/processed/dense_blocks/window=*/part.parquet`

## Modul `src`

- `ghremoval/features/dense_blocks.py`: `build_tensor(events, window_min)`, `peel_blocks(tensor, k)`, `block_features(blocks, tensor, top_k)`, `mine_hour(...)`.

## Langkah

1. Untuk tiap jam dan `w`, bangun tensor `actor_id × repo_id × event_type × minute`, nilai = jumlah event.
2. Jalankan greedy peeling (implementasi proyek, gaya M-Zoom): buang nilai atribut bermassa slice terkecil, pilih kondisi dengan densitas aritmetika tertinggi, keluarkan tuple blok, ulangi hingga `top_k_blocks` blok.
3. Hitung fitur `docs/05`.

Implementasi sendiri dipakai karena sistem izin memblokir eksekusi JAR M-Zoom yang diunduh dari luar.

Blok dihitung per jam dan per jendela, sehingga tidak ada event setelah cutoff yang terpakai. Jam `w3` ikut diproses karena tidak memakai label.

## Cek

Q13. Laporkan waktu proses, jumlah akun di dalam blok per jam, dan distribusi densitas.

## Test

Tensor sintetis dengan blok padat yang disuntikkan harus ditemukan. `block_features` menghasilkan nilai yang benar pada contoh kecil.
