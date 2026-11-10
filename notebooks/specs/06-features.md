# 06 — Fitur per jendela

Fase 3

## Tujuan

Menghitung fitur `docs/05` untuk tiap jendela dan jam, tanpa label.

## Input

`events`, `commit_msgs`, `account_hour`.

## Output

`data/processed/features/window=*/part.parquet`

## Modul `src`

- `ghremoval/features/behaviour.py`: `behaviour_features(events, window_min)`. Mengembalikan 48 kolom dengan nama sesuai `docs/05`.
- `ghremoval/features/basic.py`: `basic_features(...)`, `fit_age_bins(train)`, `apply_age_bins(df, edges)`.
- `ghremoval/features/coordination.py`: `coordination_proxies(events, commit_msgs, window_min)`.

## Langkah

1. Untuk tiap jam dan `w`, batasi event pada `second_of_hour < 60·w`.
2. Hitung fitur untuk akun yang memenuhi: kohort tetap, atau kohort deployable pada `w`. Pada `w = 60`, sertakan juga strata 1 dan 2–4.
3. Hitung proksi koordinasi atas semua akun yang aktif pada jendela itu.
4. `age_bin12` tidak dihitung di sini, melainkan saat split, dari data train.
5. Tulis per jendela.

Pakai Polars. Hindari loop Python per event bila memungkinkan, dan jaga pemakaian memori di bawah 25 GB.

## Cek

Q11. Rentang nilai tiap fitur masuk akal. Jumlah akun per jendela dilaporkan.

## Test

Keempat uji kebocoran di `docs/05`. Nilai fitur pada akun sintetis yang dihitung manual, termasuk akun satu event (`g = [0]`).
