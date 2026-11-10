# 01 — Unduh GH Archive

Fase 1

## Tujuan

Mengunduh 25 jam GH Archive secara immutable dan menilai kualitas tangkapan tiap jam.

## Input

`params.yaml` (`data.base_url`, `data.dev_hour`, `data.study_hours`, `paths.local_dev_file`).

## Output

- `data/raw/gharchive/{hour_id}.json.gz`
- `data/manifest.jsonl`
- `results/tables/tab_hour_quality.*`

## Modul `src`

- `ghremoval/ingest/gharchive.py`: `download_hour(hour_id, dest)`, `iter_events(path)`, `hour_quality(path) -> dict`, `compare_with_local(gz_path, local_path)`.

## Langkah

1. Unduh tiap jam dengan retry dan backoff. Lewati file yang sudah ada dan sha256-nya cocok dengan manifest.
2. Catat manifest.
3. Untuk tiap jam, stream event dan hitung: jumlah baris, baris rusak, menit berbeda, hitungan per menit (min, median, maks), rentang `created_at`.
4. Bandingkan jam dev dengan file lokal pengguna, baca-saja.
5. Tulis `tab_hour_quality`, tandai jam yang melanggar Q02.

## Cek

Q01–Q03. Kalau sebuah jam melanggar Q02, jangan membuangnya diam-diam. Laporkan dan tanya.

## Test

`iter_events` pada fixture gzip sintetis, termasuk baris rusak. `hour_quality` menghitung menit dengan benar.
