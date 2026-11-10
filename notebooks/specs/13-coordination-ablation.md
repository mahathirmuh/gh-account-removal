# 13 — Ablasi koordinasi

Fase 4 · RQ5

## Tujuan

Menguji apakah fitur koordinasi menambah nilai di atas `M_behav`, pada tahap pengembangan.

## Input

Fitur, proksi koordinasi, dense block, `forward_sets`, label scope `train` dan `val`.

## Output

- `results/tables/tab_coord_ablation.*` (tahap pengembangan)
- `results/figures/fig_coord_ablation.*`

## Langkah

1. Latih `M_behav`, `M_proxy`, dan `M_coord` dengan hiperparameter yang sama dari nb10.
2. Evaluasi pada `w2`, lengan F2 dan F3, per stratum.
3. Bootstrap selisih AP berpasangan.
4. Laporkan jumlah positif di dalam blok, supaya daya uji terlihat.
5. Tampilkan sensitivitas terhadap `density` dan `top_k_blocks` hanya sebagai eksplorasi.

Hasil nol adalah hasil yang sah. Jangan mengubah fitur sampai hasilnya positif.

## Cek

Q10, Q13, Q17.

## Test

Tidak ada fungsi baru selain pemanggilan. Pastikan penggabungan fitur tidak menggandakan baris.
