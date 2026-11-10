# 02 — Bangun tabel event

Fase 1

## Tujuan

Mengubah raw menjadi tabel event dan pesan commit yang bebas data pribadi mentah.

## Input

`data/raw/gharchive/*.json.gz`, kunci HMAC.

## Output

- `data/interim/events/hour_id=*/part.parquet`
- `data/interim/commit_msgs/hour_id=*/part.parquet`
- `data/interim/actor_login_features/hour_id=*/part.parquet` (`actor_id`, `actor_pseudo`, `is_app_bot`, `login_len`, `login_digit_ratio`, `login_hyphen_count`)

Skema sesuai `docs/03`.

## Modul `src`

- `ghremoval/parse/events.py`: `parse_event(raw, key, week) -> (event_row, commit_rows, actor_row)`, `pseudo(value, key)`, `normalize_short(name)`, `hash_msg(text)`.

## Langkah

1. Stream tiap jam dengan `orjson`, tulis Parquet per batch supaya memori terjaga.
2. Isi kolom sesuai `docs/03`. Field payload per tipe event ada di `docs/02`.
3. `repo_owner_is_actor` dibandingkan tanpa beda huruf, lalu nama aslinya dibuang.
4. `author_is_noreply` dihitung dari email, lalu email dibuang tanpa pernah disimpan.
5. Catat jumlah push terpotong per jam.

## Cek

Q04, Q05. Angka jam dev pada `docs/07` (event, hitungan per menit, push terpotong).

## Test

`parse_event` untuk tiap tipe event dengan payload sintetis. Output tidak memuat email, login, atau teks commit mentah. Flag `[bot]`. `normalize_short` menyamakan huruf.
