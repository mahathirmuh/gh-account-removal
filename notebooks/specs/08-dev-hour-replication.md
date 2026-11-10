# 08 — Replikasi pilot pada jam dev

Fase 3 · Gerbang B

## Tujuan

Membuktikan pipeline mereproduksi angka pilot pada jam dev, sebelum parameter dikunci.

## Input

Fitur, label scope `dev`, `scripts/pilot/` sebagai referensi.

## Output

- `results/tables/tab_dev_replication.*`
- Tag git `prereg-v1`, setelah Gerbang B

## Modul `src`

- `ghremoval/models/pilot.py`: konfigurasi HistGradientBoosting pilot.
- `ghremoval/splits.py`: `stratified_group_folds(...)`, `id_block_groups(ids, width)`.

## Langkah

1. Bandingkan jumlah akun dan akun hilang dengan tabel `docs/07`.
2. Pada akun ≥ 5 event, jalankan baseline dan `+ 48 perilaku` untuk split acak dan blok ID 20.000 serta 100.000, dengan konfigurasi `docs/07`.
3. Tulis `tab_dev_replication`: nilai pilot, nilai pipeline, selisih, status toleransi.
4. Kalau ada selisih di luar toleransi, cari penyebabnya sebelum melapor. Bandingkan definisi fitur dengan `scripts/pilot/pilot_signal.py`.

### Gerbang B

Berhenti dan minta pengguna:

1. Mengonfirmasi hasil replikasi.
2. Mengisi keputusan terbuka di `README.md` yang memengaruhi parameter.

Setelah itu commit `config/params.yaml` dan buat tag `prereg-v1`.

## Cek

Q14. Jam dev tidak dipakai lagi setelah notebook ini, kecuali sebagai sanity check.

## Test

`id_block_groups` tidak merantai blok. Hasil lipatan deterministik untuk seed yang sama.
