# 15 — Evaluasi holdout

Fase 6 · Gerbang D

## Tujuan

Membuka minggu `w3` satu kali dan menguji semua hipotesis konfirmatori.

## Prasyarat (Gerbang D)

Berhenti dan minta pengguna menyatakan desain final. Baru setelah itu ubah `holdout_open` ke `true` lewat commit tersendiri. Notebook gagal jika `holdout_open: false`.

## Input

Semua fitur, label scope `holdout`, hiperparameter nb10, aturan `docs/06`.

## Output

- `results/holdout_opened.json`: waktu UTC dan commit, ditulis **sebelum** label holdout dibaca
- `results/tables/tab_holdout_summary.*`, serta versi final `tab_split_audit`, `tab_models_by_stratum`, `tab_policy`, `tab_coord_ablation`
- `results/figures/` versi final

## Langkah

1. Tolak berjalan bila `results/holdout_opened.json` sudah ada, kecuali pengguna memintanya secara eksplisit. Catat di `docs/DEVIATIONS.md`.
2. Latih ulang model pada `w0–w2`, tanpa tuning tambahan.
3. Bangun lengan `F1`, `F2`, `F3`, termasuk sensitivitas `F3` dan bagian test yang tidak bertetangga dengan train.
4. Evaluasi H1a, H1b.
5. **H2:** bandingkan estimasi CV nb09 dengan `F2` final.
6. **Kebijakan adaptif:** latih pada `w0–w1`, kalibrasi dan pilih `(q, κ)` pada `w2`, evaluasi pada `w3`, kohort tetap dan deployable. Evaluasi H4a.
7. Evaluasi H5.
8. Bootstrap untuk semua selisih. Koreksi Holm pada keluarga konfirmatori.
9. Terapkan aturan "tidak dapat diuji" bila positif kurang dari `min_positives_per_stratum`.
10. Tulis `tab_holdout_summary`: hipotesis, estimasi, CI, p Holm, keputusan.

Dilarang mengubah fitur, parameter, atau ambang setelah melihat hasil. Analisis lanjutan diberi label eksploratif.

## Cek

Q19, Q20. `holdout_opened.json` dibuat sebelum pembacaan label.

## Test

Penjaga gagal bila `holdout_open: false` atau file penanda sudah ada. Koreksi Holm pada contoh yang dihitung manual.
