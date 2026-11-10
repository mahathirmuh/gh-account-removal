# 06 — Metode analisis

## Tangga model

Semua model dilatih dan dievaluasi pada akun non-`[bot]`, dan dilaporkan per stratum.

| Kode | Fitur | Model | Peran |
| --- | --- | --- | --- |
| `B0` | `n_events` | Peringkat tanpa fitting | Falsifikasi volume |
| `B1` | `age_bin12` | XGBoost dangkal | Porsi yang dijelaskan usia |
| `B2` | `n_events_coarse` + `age_bin12` | XGBoost dangkal (`max_depth` 3) dan LR | **Lawan utama** |
| `B3` | Baseline literatur (`docs/05`) | Sesuai aslinya | Posisi terhadap SOTA, opsional |
| `M_behav` | `B2` + 48 perilaku | XGBoost (utama), LR, MLP one-hot | Model utama |
| `M_robust` | `B2` + 28 perilaku | XGBoost | Sensitivitas |
| `M_proxy` | `M_behav` + 10 proksi koordinasi | XGBoost | Ablasi |
| `M_coord` | `M_proxy` + fitur dense-block | XGBoost | RQ5 |

Model yang lebih mahal dari XGBoost dipertahankan hanya jika CI paired positif dan selisih AP ≥ `min_delta_ap` efektif.

## Tuning

Mengikuti pola mata kuliah: Optuna TPE dengan penyimpanan SQLite, `optuna_trials` per keluarga per sampler seed, MLflow untuk pencatatan.

| Keluarga | Domain | Resource |
| --- | --- | --- |
| LR | `C` 0,001–10 log | `max_iter` 4000 |
| XGBoost | `max_depth` 3–8; `learning_rate` 0,01–0,2 log; `min_child_weight` 1–20 log; `subsample` 0,6–1; `colsample_bytree` 0,5–1; `reg_lambda` 0,1–10 log | Early stopping pada 20% terakhir jam train, patience 50, maksimum 2.000 ronde |
| MLP one-hot | `hidden` 64/128/256/512; `dropout` 0–0,5; `lr` 0,0001–0,003 log; `weight_decay` 1e-6–1e-2 log; `batch` 256/512 | Early stopping sama, patience 10, maksimum 80 epoch, GPU |

Objective: AP stratum 5–19 pada lengan `F2` tahap pengembangan (train `w0–w1`, evaluasi `w2`). Preprocessing di-fit hanya pada train. Laporkan seluruh trial, waktu, dan device.

## Audit desain split (RQ2)

### Lengan validasi silang

Dijalankan pada kemunculan pertama akun di `w0–w2`, tanpa menyentuh `w3`.

| Lengan | Grup |
| --- | --- |
| `A1_random` | Tiap akun satu grup, stratifikasi pada `s` |
| `A2_artifact` | Akun yang berbagi repo atau `msg_hash` yang dipakai 2 sampai `artifact_max_accounts` akun |
| `A3_idblock_{W}` | `actor_id // W`, untuk tiap `W` di `id_block_widths` |
| `A3s_signature` | `(n_events, n_repos, n_active_minutes)` sama, untuk `n_events ≥ signature_min_events`; lainnya tunggal |

Pakai `StratifiedGroupKFold`, `n_folds` lipatan, untuk tiap seed di `cv_seeds`.

**Larangan perantaian.** Jangan menggabungkan grup artefak dengan blok ID, dan jangan merantai ID berdekatan. Pilot menunjukkan skema itu runtuh menjadi satu grup raksasa (4.457 akun memuat 425 dari 519 positif), sehingga satu lipatan memegang sebagian besar positif dan hasilnya tidak bisa ditafsirkan.

**Diagnostik wajib.** Untuk tiap lengan, laporkan jumlah grup, grup terbesar, porsi positif pada grup terbesar, dan porsi positif per lipatan. Lengan ditandai `is_degenerate` bila grup terbesar memuat lebih dari `max_group_pos_share` positif. Lengan degeneratif dilaporkan tanpa estimasi performa.

### Pemilihan lebar blok

Prosedur berikut dikunci, dan nilainya diisi sekali oleh nb09 ke `derived.primary_id_block_width`.

1. Pada `w0–w1`, hitung residual out-of-fold `s − p` dari `B2` dengan `A1_random`.
2. Bangun korelogram residual terhadap jarak ID, dengan bin jarak log.
3. Pilih `W` terkecil di `id_block_widths` yang jarak autokorelasinya, yaitu titik pertama korelasi residual < 0,05, tidak melebihi `W`. Jika tidak ada, pakai `W` terbesar.

### Lengan forward

| Lengan | Isi test |
| --- | --- |
| `F1_forward` | Semua akun di minggu test |
| `F2_forward_new_accounts` | Akun yang tidak muncul di minggu train |
| `F3_forward_batch_excluded` | `F2`, dikurangi akun di blok ID (`primary_id_block_width`) yang memuat minimal satu positif train |

Sensitivitas `F3`: mengecualikan blok yang memuat akun train apa pun. Laporkan juga performa pada bagian test yang tidak bertetangga dengan train, supaya memorisasi bisa dibedakan dari generalisasi.

Tahap pengembangan: train `w0–w1`, test `w2`. Tahap final (nb15): train `w0–w2`, test `w3`.

**Penafsiran wajib.** Penurunan di bawah pengecualian batch menggabungkan leakage dan pergeseran distribusi yang nyata.

## Analisis terkontrol (RQ1)

- AP per stratum, selalu berdampingan dengan base rate.
- AUC di dalam sel `n_events_coarse × age_bin12`, dibobot jumlah positif, hanya untuk sel yang memuat positif dan negatif.
- `ΔAP` per pasangan model bertingkat pada lengan yang sama.

## Metrik

| Metrik | Catatan |
| --- | --- |
| AP per stratum | Utama. AP gabungan didominasi stratum ≥ 20, jadi tidak boleh dilaporkan sendirian |
| Precision@k, Recall@k | k = 50, 100, 500 |
| AUC dalam sel | Lihat di atas |
| AUROC | Pelengkap |
| Brier, ECE | Setelah kalibrasi |

Tangani skor sama secara deterministik, terutama `B0`. Setiap tabel menyebut bahwa metrik dihitung terhadap label teramati `s`.

## PU (RQ3)

Bagian ini eksploratif. Target laten `y` adalah akun kelak hilang kapan pun.

| Metode | Asumsi | Catatan |
| --- | --- | --- |
| Naive | Unlabeled = negatif | Pembanding wajib; kadang mengalahkan metode SCAR |
| Elkan–Noto | SCAR | Estimasi `c` dari positif pada set kalibrasi |
| PU bagging | SCAR longgar | XGBoost sebagai base learner |
| SAR-EM | SAR | Propensity pada atribut aktivitas dan usia; karena keduanya juga prediktor kuat, identifikasinya lemah, jadi perlakukan sebagai analisis sensitivitas atas beberapa spesifikasi propensity |

Laporkan prior sebagai rentang per stratum dari beberapa estimator. Metode dua sampel seperti nnPU tidak dipakai tanpa penyesuaian, karena data ini satu sampel.

**Uji semi-sintetis.** Sembunyikan 50% positif train dengan propensity logistik pada `n_events_coarse` dan `age_bin12`, ulangi 5 kali. Evaluasi AP untuk memulihkan positif tersembunyi di antara unlabeled.

**Validasi prospektif (bila ada `s2`).** Late removal adalah positif tersembunyi yang nyata. Bandingkan AP metode PU dan naive dalam mengurutkan late removal di antara akun yang masih ada pada `s1`.

## Latensi (RQ4, K4)

Untuk tiap `w` di `windows_minutes`, latih `B2` dan `M_behav` pada fitur jendela `w`. Hiperparameter berasal dari nb10 tanpa tuning tambahan. Laporkan AP per stratum pada kohort tetap dan deployable. Pada kohort tetap, akun yang belum muncul pada jendela `w` diberi skor terendah, supaya penyebut sama antarjendela. Metrik ERDE dan F_latency tidak dipakai sebagai metrik utama.

## Kebijakan penandaan dini adaptif (RQ4, K6)

### Definisi

Checkpoint `c` ∈ `windows_minutes`. Pada tiap checkpoint, `f_c` menghasilkan skor untuk akun yang sudah muncul dan memenuhi syarat kohort.

1. **Kalibrasi.** Skor `f_c` dikalibrasi isotonic pada set kalibrasi, satu kalibrator per checkpoint. Kalau set kalibrasi memuat kurang dari 30 positif pada suatu checkpoint, pakai Platt scaling.
2. **Aturan first-cross.** Akun ditandai pada checkpoint pertama dengan `p_c ≥ θ_c`, dengan `θ_c = min(1, q · (1 + κ · (60 − c) / 60))`. `κ` menuntut bukti lebih kuat pada checkpoint awal.
3. **Pemilihan parameter.** Pada set kalibrasi, untuk tiap `κ` di `kappa_grid`, cari `q` terkecil pada kisi `q_grid_size` titik sehingga precision seluruh kebijakan ≥ target. Pilih pasangan `(q, κ)` dengan AURT tertinggi. Karena precision dihitung atas seluruh kebijakan, efek banyak kali melihat sudah tercakup.

Jendela tetap pembanding memakai cara pemilihan ambang yang sama, pada satu checkpoint saja.

### Pembagian waktu

| Tahap | Latih | Kalibrasi dan pilih `(q, κ)` | Evaluasi |
| --- | --- | --- | --- |
| Pengembangan (nb12) | `w0` | `w1` | `w2` |
| Final (nb15) | `w0–w1` | `w2` | `w3`, lengan F3 |

### Metrik

Misal `P` himpunan positif pada kohort evaluasi, dan `R(t)` porsi `P` yang sudah ditandai sampai menit `t`.

- **AURT** = `(1/T) ∫₀ᵀ R(t) dt`, dengan `T = aurt_horizon_minutes`. Horizon lebih panjang dari 60 menit supaya penandaan pada menit 60 tetap bernilai. Untuk jendela tetap `c`, `AURT = R(c) · (T − c) / T`.
- Precision yang tercapai terhadap `s`, recall akhir, median waktu penandaan pada true positive.
- Kurva AMOC: waktu penandaan rata-rata terhadap false positive rate, untuk tiap `q`.

Pembanding: tiap jendela tetap dengan `M_behav`, dan kebijakan first-cross memakai skor `B2`. Perbandingan terakhir menunjukkan berapa banyak yang berasal dari fitur perilaku. Sensitivitas: `T` di `aurt_horizon_sensitivity`, dan perbandingan pada precision teramati yang disamakan.

### Batas klaim

Waktu penandaan berjangkar pada awal jam, jadi akun yang baru muncul pada menit 40 paling cepat ditandai pada menit 60. Hasil adalah simulasi atas data arsip, bukan sistem real-time.

## Koordinasi (RQ5, K5)

Bandingkan `M_behav`, `M_proxy`, dan `M_coord` pada lengan yang sama, berpasangan. Laporkan jumlah positif di dalam blok supaya daya uji terlihat. Hasil nol adalah hasil yang sah.

## Statistik

- **Paired cluster bootstrap:** sampel ulang blok ID (`primary_id_block_width`) dengan pengembalian, pertahankan semua akun di dalam blok, hitung metrik kedua model pada sampel ulang yang sama, bentuk interval persentil pada selisih. `bootstrap_reps` replikasi.
- Validasi langsung bootstrap ini untuk AP pada data klaster tidak ditemukan dalam pencarian yang dilakukan, jadi tuliskan sebagai ekstrapolasi.
- Laporkan jumlah klaster yang memuat positif dan sensitivitas saat klaster terbesar dibuang.
- Uji Demšar hanya bila jam diperlakukan sebagai replikasi independen. Skor antar-seed dirata-ratakan sebelum bootstrap.
- p satu sisi = porsi replikasi bootstrap dengan selisih ≤ 0. Koreksi Holm pada keluarga konfirmatori (H1a, H2a, H4a, H5).

## Pelaporan

Bekukan rancangan sebelum Gerbang B. Buka holdout sekali. Semua hasil eksplorasi diberi label eksploratif. Hasil yang tidak mendukung hipotesis tetap dilaporkan.
