# 11 — Analisis PU

Fase 4 · RQ3, eksploratif

## Tujuan

Menguji apakah formulasi PU memperbaiki peringkat dibanding model naive, sesuai `docs/06`.

## Input

Fitur jendela 60, `forward_sets`, label scope `train` dan `val`. Label `s2` bila ada.

## Output

`results/tables/tab_pu_methods.*`

## Modul `src`

- `ghremoval/pu.py`: `naive_fit`, `elkan_noto_fit`, `pu_bagging_fit`, `sar_em_fit`, `estimate_prior_range`, `hide_positives(df, propensity, seed)`.

## Langkah

1. Definisikan secara eksplisit di notebook: `s` teramati, `y` laten, dan bahwa asumsi p(s=1|y=0)=0 bisa gagal bila `y` dimaknai sebagai akun bermasalah.
2. Latih naive, Elkan–Noto, dan PU bagging dengan XGBoost, pada train `w0–w1`.
3. SAR-EM dengan beberapa spesifikasi propensity: `n_events_coarse`, `age_bin12`, dan keduanya.
4. Prior per stratum dari beberapa estimator, dilaporkan sebagai rentang. Jika pustaka estimator tidak tersedia, pakai estimasi `c` Elkan–Noto dan nyatakan keterbatasannya.
5. Uji semi-sintetis sesuai `docs/06`, 5 pengulangan.
6. Evaluasi pada `w2` terhadap label teramati.
7. Bila ada `s2`: AP dalam mengurutkan late removal.

## Cek

Q10, Q17. Semua hasil diberi label eksploratif.

## Test

`hide_positives` deterministik dan memenuhi proporsi target. `elkan_noto_fit` pada data sintetis dengan `c` diketahui memberi estimasi mendekati nilai sebenarnya. `sar_em_fit` konvergen pada contoh kecil.
