# 03 — Model data

Format Parquet, dibaca lewat Polars atau view DuckDB `data/processed/ghremoval.duckdb`. Nama kolom snake_case.

## `data/manifest.jsonl`

Satu baris per unduhan: `url`, `path`, `downloaded_at_utc`, `sha256`, `bytes`, `content_length_header`.

## `events`

Path `data/interim/events/hour_id=*/part.parquet`. Grain: satu event. Kunci: `event_id`.

| Kolom | Tipe | Keterangan |
| --- | --- | --- |
| `event_id` | str | `id` asli |
| `hour_id` | str | `YYYY-MM-DD-H` |
| `week` | str | `dev`, `w0`, `w1`, `w2`, `w3` |
| `created_at` | datetime | UTC |
| `second_of_hour` | int | 0–3599 |
| `event_type` | str | Salah satu dari 15 tipe di `docs/02` |
| `action` | str? | `payload.action` |
| `actor_id` | i64 | ID numerik, tetap privat |
| `actor_pseudo` | str | HMAC-SHA256 login, 16 heksadesimal |
| `is_app_bot` | bool | Login berakhiran `[bot]` |
| `repo_id` | i64 | |
| `repo_owner_pseudo` | str | HMAC-SHA256 owner, huruf kecil |
| `repo_owner_is_actor` | bool | Owner sama dengan login aktor, tanpa beda huruf |
| `repo_short_hash` | str | Hash nama repo pendek dalam huruf kecil |
| `repo_short_len` | int | |
| `repo_short_has_digit` | bool | |
| `has_org` | bool | Ada `org` |
| `ref_type` | str? | Create dan Delete |
| `push_size` | int? | `payload.size` |
| `push_distinct_size` | int? | `payload.distinct_size` |
| `pr_author_none` | bool? | PullRequestEvent `opened` dengan `author_association = NONE` |

Tidak ada login, email, nama repo, judul, atau pesan commit mentah di tabel ini.

## `commit_msgs`

Path `data/interim/commit_msgs/hour_id=*/part.parquet`. Grain: satu commit dalam payload PushEvent.

| Kolom | Tipe | Keterangan |
| --- | --- | --- |
| `event_id` | str | |
| `actor_id` | i64 | |
| `hour_id` | str | |
| `second_of_hour` | int | |
| `msg_hash` | str | BLAKE2b 8 byte atas pesan setelah `strip()` |
| `msg_len` | int | Panjang pesan setelah `strip()` |
| `author_is_noreply` | bool | Email mengandung `noreply`; email dibuang setelah ini |
| `is_distinct` | bool | `commits[].distinct` |

## `account_dim`

Path `data/processed/account_dim.parquet`. Grain: satu `actor_id`.

Kolom: `actor_id`, `actor_pseudo`, `is_app_bot`, `login_len`, `login_digit_ratio`, `login_hyphen_count`, `first_hour_id`, `n_hours_seen`. Tiga kolom `login_*` hanya dipakai baseline heuristik nama, dan dihitung saat parse sebelum login dibuang.

## `account_hour`

Path `data/processed/account_hour.parquet`. Grain: `(actor_id, hour_id)`.

| Kolom | Tipe | Keterangan |
| --- | --- | --- |
| `actor_id` | i64 | |
| `hour_id`, `week` | str | |
| `n_events` | int | Dalam 60 menit |
| `first_second`, `last_second` | int | |
| `stratum` | str | `1`, `2-4`, `5-19`, `20+` |
| `in_fixed_cohort` | bool | `n_events ≥ fixed_min_events` dan bukan `[bot]` |
| `max_id_in_hour` | i64 | ID aktor terbesar pada jam itu |
| `id_recency` | i64 | `max_id_in_hour − actor_id` |
| `is_first_in_period` | bool | Kemunculan pertama akun dalam himpunan `dev`, `w0–w2`, atau `w3` |

## `labels`

Path `data/processed/labels.parquet`. Grain: `(snapshot_id, actor_id)`.

| Kolom | Tipe | Keterangan |
| --- | --- | --- |
| `snapshot_id` | str | `s1`, `s2` |
| `actor_id` | i64 | |
| `status` | str | `present`, `gone`, `error` |
| `node_type` | str? | `User`, `Organization`, null |
| `is_gone` | bool | `status == gone` |
| `created_at_api` | datetime? | `createdAt`, bila ada |
| `source` | str | `graphql`, `rest` |
| `checked_at` | datetime | UTC |

**Guard:** semua pembacaan label lewat `ghremoval.labels.load_labels(scope)`. `scope` adalah `dev`, `train`, `val`, atau `holdout`. Selama `holdout_open: false`, permintaan yang menyertakan akun yang hanya muncul di `w3` memicu `HoldoutLockedError`.

## `features`

Path `data/processed/features/window=*/part.parquet`. Grain: `(actor_id, hour_id, window_min)`. Kolom di `docs/05`.

## `dense_blocks`

Path `data/processed/dense_blocks/window=*/part.parquet`. Grain: `(actor_id, hour_id, window_min)`. Kolom di `docs/05`.

## `splits`

- `data/processed/splits/cv_groups.parquet`: `actor_id`, `arm`, `group_id`, `fold`, `seed`.
- `data/processed/splits/forward_sets.parquet`: `actor_id`, `hour_id`, `arm`, `role` (`train`, `calib`, `val`, `test`), `excluded_reason`.
- `data/processed/splits/group_diagnostics.parquet`: `arm`, `n_groups`, `largest_group`, `largest_group_pos_share`, `max_fold_pos_share`, `is_degenerate`.

Lengan: `A1_random`, `A2_artifact`, `A3_idblock_{W}`, `A3s_signature`, `F1_forward`, `F2_forward_new_accounts`, `F3_forward_batch_excluded`.

## `predictions`

Path `data/processed/predictions/{model}__{arm}__w{window}.parquet`. Kolom: `actor_id`, `hour_id`, `score`, `fold`, `seed`.

## `results`

- `results/run_log.jsonl`, `results/numbers.json`.
- `results/tables/`, `results/figures/`.

## Anotasi (di-gitignore)

- `data/annotation/audit_sample.csv`: `audit_id`, `actor_pseudo`, `score_group`, ringkasan event.
- `data/annotation/audit_annotator_A.csv`, `audit_annotator_B.csv`: `audit_id`, `category`, `notes`.
- `data/annotation/audit_adjudication.csv`: `audit_id`, `final_category`.

Sampel audit ditulis dari raw untuk akun terpilih saja. Boleh memuat nama repo pendek dan pesan commit, tetapi login diganti pseudonim.
