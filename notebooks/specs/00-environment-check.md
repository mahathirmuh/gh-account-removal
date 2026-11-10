# 00 — Cek environment

Fase 0

## Tujuan

Memastikan environment, kredensial, dan koneksi siap sebelum data diunduh.

## Input

`config/params.yaml`, `~/.dm-git.env`.

## Output

- `results/environment.txt`
- `~/.dm-git-hmac.key` (dibuat bila belum ada, mode 600, berisi 32 byte acak dalam heksadesimal)

## Modul `src`

- `ghremoval/config.py`: `load_params(path)`, validasi dengan pydantic.
- `ghremoval/secrets.py`: `load_token()`, `load_hmac_key()`. Objek token tidak boleh punya `repr` yang menampilkan nilainya.
- `ghremoval/report.py`, `ghremoval/viz.py`, `ghremoval/runlog.py`.

## Langkah

1. Cetak versi Python, paket utama, CUDA (`torch.cuda.is_available()`), Java.
2. Pastikan disk kosong ≥ 40 GB.
3. Pastikan `~/.dm-git.env` ada dan mode-nya 600, tanpa mencetak isinya.
4. Panggil `GET https://api.github.com/rate_limit`. Tampilkan hanya batas dan sisa `core` dan `graphql`, serta apakah scope kosong.
5. HEAD `https://data.gharchive.org/2024-04-01-15.json.gz`, harus 200.
6. Buat kunci HMAC bila belum ada.
7. Pastikan `.gitignore` mengecualikan `data/`, `tools/`, `mlruns/`, `2024-04-01-15.json/`.

## Cek

Semua langkah lulus. Tidak ada token atau kunci di output notebook.

## Test

`load_params` menolak config tanpa kunci wajib. `load_token` tidak membocorkan nilai lewat `repr` atau `str`.
