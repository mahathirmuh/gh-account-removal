# 09 — Audit desain split

Fase 4 · RQ2

## Tujuan

Mengukur seberapa besar desain split mengubah performa terukur, sesuai `docs/06`.

## Input

Fitur jendela 60, label scope `train` dan `val`.

## Output

- `data/processed/splits/*.parquet`
- `config/params.yaml`: `derived.primary_id_block_width`
- `results/tables/tab_group_diagnostics.*`, `tab_split_audit.*` (tahap pengembangan)
- `results/figures/fig_correlogram.*`, `fig_split_bias.*`

## Modul `src`

- `ghremoval/splits.py`: `artifact_groups(...)`, `signature_groups(...)`, `diagnose(groups, y)`, `forward_sets(...)`, `batch_exclusion(...)`.
- `ghremoval/correlogram.py`: `residual_correlogram(ids, residuals)`, `choose_block_width(...)`.

## Langkah

1. Bangun grup untuk `A1`, `A2`, `A3_{W}`, `A3s`. Tulis diagnostik. Tandai lengan degeneratif.
2. Jalankan korelogram pada `w0–w1`, pilih lebar blok menurut aturan `docs/06`, tulis ke `derived`.
3. Pada `w0–w2`, untuk tiap lengan non-degeneratif, jalankan set fitur `B2` dan `M_behav` memakai `HistGradientBoostingClassifier` konfigurasi pilot (`docs/07`), `cv_seeds`, supaya audit tidak bergantung pada hasil tuning.
4. Tahap pengembangan forward: train `w0–w1`, test `w2`, untuk `F1`, `F2`, `F3`.
5. Hitung per lengan: AP per stratum, tambahan AP `M_behav` − `B2`, dan rasio terhadap `A3` primer. Interval dari paired cluster bootstrap.
6. Hitung seberapa dekat tiap lengan CV dengan `F2` tahap pengembangan.

## Cek

Q15, Q16, Q10. Tidak ada `w3`.

## Test

`artifact_groups` mematuhi `artifact_max_accounts`. `diagnose` menandai grup raksasa. `batch_exclusion` hanya memakai label train. `forward_sets` tidak meloloskan akun train ke test pada F2.
