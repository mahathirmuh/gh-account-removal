# 05 — Validasi label

Fase 2 · Gerbang A

## Tujuan

Menilai arti dan kualitas label sesuai `docs/04`, tanpa menggabungkan label jam studi dengan fitur.

## Input

`labels`, `account_hour`, raw GH Archive (untuk URL objek dan login sampel), token.

## Output

- `results/tables/tab_label_validation.*`, `tab_base_rate_by_stratum.*`
- `results/figures/fig_id_vs_created.*`, `fig_rate_by_stratum_age.*`

## Modul `src`

- `ghremoval/validate_labels.py`: `web_crosscheck(sample)`, `id_age_check(sample)`, `ghost_probe(accounts)`.

## Langkah

1. **Cek silang API dan web:** sampel sesuai `web_crosscheck`, HEAD tanpa token, tanpa mengikuti redirect, berhenti setelah tiga respons 429. Login hanya berada di memori.
2. **ID vs usia:** ambil `createdAt` 5.000 akun `present`. Hitung Spearman dan monotonisitas per desil.
3. **Probe `ghost`:** untuk akun `gone` pada `dev` dan `train`, ambil sampai 3 objek di repo orang lain. Kontrol: 150 akun `present` acak. Hanya URL berawalan `https://api.github.com/repos/`.
4. **Tingkat hilang:** per stratum dan per kuantil usia, hanya `dev` dan `train`, dengan interval Wilson.

### Gerbang A

Berhenti dan laporkan hasil sesuai `docs/04`. Lanjut hanya setelah pengguna menyatakan label layak dipakai. Kalau pola API 200 + web 404 muncul lebih dari 1%, tanya sebelum lanjut.

## Cek

Tidak ada login pada output. Q10.

## Test

`ghost_probe` dengan respons tiruan untuk `ghost`, atribusi tetap, dan 404. Penjaga host menolak URL di luar GitHub API.
