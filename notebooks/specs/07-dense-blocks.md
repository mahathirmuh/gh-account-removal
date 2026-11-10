# 07 — Mining dense block

Fase 3

## Tujuan

Menghasilkan fitur dense-block lintas jenis event untuk RQ5, tanpa label.

## Input

`events`, M-Zoom di `tools/mzoom`.

## Output

`data/processed/dense_blocks/window=*/part.parquet`

## Modul `src`

- `ghremoval/features/dense_blocks.py`: `build_tensor(events, window_min, path)`, `run_mzoom(tensor_path, k, density)`, `parse_blocks(output_dir)`, `block_features(blocks, events)`.

## Langkah

1. Clone `kijungs/mzoom` ke `tools/mzoom` (di-gitignore). Baca `user_guide.pdf` untuk format input dan argumen, jangan menebak.
2. Pastikan `MZoom-2.0.jar` berjalan di Java 8 dengan demo bawaan. Kalau gagal, **berhenti dan tanya**. Jangan memasang JDK tanpa izin.
3. Untuk tiap jam dan `w`, tulis tensor `actor_id × repo_id × event_type × minute`, nilai = jumlah event.
4. Jalankan M-Zoom dengan `top_k_blocks` blok dan densitas `dense_blocks.density`.
5. Petakan indeks kembali ke akun, lalu hitung fitur `docs/05`.

Blok dihitung per jam dan per jendela, sehingga tidak ada event setelah cutoff yang terpakai. Jam `w3` ikut diproses karena tidak memakai label.

## Cek

Q13. Laporkan waktu proses, jumlah akun di dalam blok per jam, dan distribusi densitas.

## Test

Tensor sintetis dengan blok padat yang disuntikkan harus ditemukan. `block_features` menghasilkan nilai yang benar pada contoh kecil.
