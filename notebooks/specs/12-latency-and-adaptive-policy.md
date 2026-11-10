# 12 — Latensi dan kebijakan adaptif

Fase 4 · RQ4, K4 dan K6

## Tujuan

Mengukur kurva performa per jendela dan mengembangkan kebijakan penandaan dini adaptif pada tahap pengembangan.

## Input

Fitur semua jendela, hiperparameter nb10, label scope `train` dan `val`.

## Output

- `results/tables/tab_policy.*` (tahap pengembangan)
- `results/figures/fig_latency_curves.*`, `fig_recall_time.*`, `fig_amoc.*`
- `results/policy_dev.json`: `(q, κ)` terpilih per target precision

## Modul `src`

- `ghremoval/policy.py`: `fit_checkpoint_models(...)`, `calibrate(...)`, `thresholds(q, kappa, checkpoints)`, `first_cross(scores_by_ckpt, thresholds)`, `select_q_kappa(...)`, `fixed_window_policy(...)`, `aurt(flag_times, y, horizon)`, `amoc_curve(...)`.

## Langkah

1. **Kurva latensi.** Untuk tiap `w`, latih `B2` dan `M_behav`, evaluasi AP per stratum pada kohort tetap dan deployable. Lengan F2.
2. **Latih per checkpoint** pada `w0`.
3. **Kalibrasi dan pilih `(q, κ)`** pada `w1`, untuk tiap target precision.
4. **Evaluasi** pada `w2`, lengan F2 dan F3: precision teramati, recall akhir, AURT, median waktu penandaan pada true positive.
5. **Pembanding:** tiap jendela tetap dengan `M_behav`, dan first-cross dengan skor `B2`.
6. Kurva AMOC dan `R(t)`.
7. Sensitivitas horizon dan perbandingan pada precision teramati yang disamakan.

Parameter kebijakan final dipilih ulang di nb15 dengan pembagian waktu final. Hasil notebook ini tidak boleh dipakai untuk mengubah definisi kebijakan setelah holdout dibuka.

## Cek

Q18, Q10, Q17. Precision dihitung atas seluruh kebijakan.

## Test

`first_cross`: akun tidak ditandai sebelum muncul; penandaan terjadi pada checkpoint pertama yang lolos. `aurt` untuk jendela tetap sama dengan `R(c)·(T−c)/T`. `select_q_kappa` menolak kombinasi yang tidak mencapai target. `thresholds` monoton terhadap `κ`.
