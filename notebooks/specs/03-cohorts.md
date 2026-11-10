# 03 — Akun dan kohort

Fase 1

## Tujuan

Membangun dimensi akun dan tabel akun-jam, termasuk stratum dan kohort. Belum ada label.

## Input

Tabel interim nb02, `params.yaml`.

## Output

- `data/processed/account_dim.parquet`
- `data/processed/account_hour.parquet`
- `results/tables/tab_dataset_overview.*`
- `numbers.json`: `n_events_study`, `n_accounts_study`, `n_fixed_cohort`

## Modul `src`

- `ghremoval/build/accounts.py`: `build_account_dim(...)`, `build_account_hour(...)`, `assign_stratum(n, strata)`, `mark_first_in_period(df)`.

## Langkah

1. Agregasi event per `(actor_id, hour_id)`.
2. Isi `stratum`, `in_fixed_cohort`, `max_id_in_hour`, `id_recency`. `max_id_in_hour` dihitung dari semua aktor pada jam itu.
3. `is_first_in_period` per himpunan: `dev`, `w0–w2`, `w3`. Akun di `w3` yang sudah muncul di `w0–w2` tetap punya baris, tetapi akan dikeluarkan oleh lengan F2.
4. `tab_dataset_overview`: event, akun, kohort, dan strata per minggu. Tanpa label.

## Cek

Q06, Q07. Angka jam dev pada `docs/07`.

## Test

`assign_stratum` pada batas. `mark_first_in_period` pada akun yang muncul di beberapa jam. `id_recency` selalu ≥ 0.
