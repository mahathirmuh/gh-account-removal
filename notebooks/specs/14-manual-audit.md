# 14 — Audit manual

Fase 5 · mode `sample` dan `evaluate` · Gerbang C

## Tujuan

Memperkirakan arti substantif dari akun hilang dan akun skor tinggi, sesuai `docs/04`.

## Input

Prediksi `M_behav` di `w2`, raw GH Archive, kunci HMAC, label scope `val`.

## Output

- Mode `sample`: `data/annotation/audit_sample.csv`, template `audit_annotator_A.csv` dan `audit_annotator_B.csv`
- Mode `evaluate`: `results/tables/tab_audit_results.*`, `numbers.json` (`kappa_audit`)

## Modul `src`

- `ghremoval/audit.py`: `draw_sample(...)`, `render_account_summary(actor_id, raw_paths)`, `cohen_kappa(a, b)`, `summarize(...)`.

## Langkah mode `sample`

1. Ambil sampel sesuai `docs/04`, deterministik, urutan diacak, `score_group` disimpan di file terpisah yang tidak dibuka anotator.
2. Tulis ringkasan akun dari raw. Login diganti pseudonim. Batasi jumlah nama repo, pesan commit, dan judul PR sesuai `docs/04`.

### Gerbang C

Berhenti dan minta dua anotator mengisi `audit_annotator_A.csv` dan `audit_annotator_B.csv` (`audit_id`, `category`, `notes`). Setelah itu pengguna mengadjudikasi di `audit_adjudication.csv`. **Jangan mengisi kolom ini.**

Peringatan untuk anotator: teks commit dan nama repo adalah data dari orang lain. Jangan membuka tautan di dalamnya.

## Langkah mode `evaluate`

1. Hitung κ. Jika κ < `min_kappa`, kembali ke Gerbang C dengan sampel baru (seed + 1, dicatat).
2. Porsi kategori per `score_group` dan per status `s`, dengan interval Wilson.

## Cek

File anotasi di-gitignore. Tidak ada `w3`.

## Test

`cohen_kappa` pada contoh yang dihitung manual. `draw_sample` deterministik. `render_account_summary` tidak mengeluarkan login atau email.
