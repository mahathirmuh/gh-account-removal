# 04 — Snapshot status akun

Fase 2 · mode `s1` dan `s2`

## Tujuan

Mengambil status semua akun target sekali waktu, sesuai `docs/04`.

## Input

`account_hour`, `account_dim`, token, `params.yaml`.

## Output

- `data/processed/labels.parquet`
- `data/processed/label_checkpoint/` (sementara, per batch)
- `config/params.yaml`: `label.snapshot_date`, hanya saat mode `s1` pertama kali

## Modul `src`

- `ghremoval/labels.py`: `legacy_node_id(actor_id)`, `fetch_batch(ids, client)`, `run_snapshot(ids, snapshot_id, ...)`, `verify_rest(sample)`, `load_labels(scope, snapshot_id)`, `HoldoutLockedError`.
- `ghremoval/github_client.py`: klien dengan retry, backoff, dan rate limit. Menolak URL di luar `https://api.github.com/`.

## Langkah

1. Susun daftar ID: akun non-`[bot]` dengan `n_events ≥ min_events_to_label`, pada jam dev dan studi.
2. Perkirakan waktu dari jumlah ID, cetak, lalu lanjut.
3. Query per batch, tulis checkpoint. Boleh dilanjutkan bila terputus.
4. Hitung peringatan `DEPRECATION`, galat `NOT_FOUND`, galat lain.
5. Verifikasi sampel dengan REST.
6. Gabungkan ke `labels.parquet`.
7. Jika GraphQL menolak ID lama: **berhenti dan tanya**.

Jangan menampilkan tingkat hilang jam studi di notebook ini. Tampilkan hanya jumlah status per himpunan `dev`, dan jumlah keseluruhan tanpa pemisahan minggu.

Mode `s2`: akun `present` pada `s1`, minimal `second_snapshot_min_days` setelahnya.

## Cek

Q08–Q10.

## Test

`legacy_node_id` untuk ID contoh (26939949 menjadi `MDQ6VXNlcjI2OTM5OTQ5`). `fetch_batch` dengan respons tiruan: node ada, `null`, `Organization`, galat jaringan. Token tidak muncul di log. `load_labels` menolak holdout.
