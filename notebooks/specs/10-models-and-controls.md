# 10 — Model dan analisis terkontrol

Fase 4 · RQ1

## Tujuan

Melatih tangga model, melakukan tuning, dan menguji sinyal di dalam sel aktivitas dan usia pada tahap pengembangan.

## Input

Fitur jendela 60, `forward_sets`, label scope `train` dan `val`.

## Output

- `data/processed/predictions/*`
- `mlruns/`, `results/optuna/*.sqlite3`
- `results/tables/tab_models_by_stratum.*`, `tab_tuning_trials.*`
- `results/figures/fig_within_cell.*`

## Modul `src`

- `ghremoval/models/fit.py`: `fit_xgb`, `fit_lr`, `fit_mlp`, `predict`.
- `ghremoval/models/tune.py`: `run_study(family, sampler_seed, ...)`.
- `ghremoval/evaluate.py`: `ap_by_stratum`, `precision_at_k`, `within_cell_auc`, `paired_cluster_bootstrap`.
- `ghremoval/baselines.py`: `rank_events`, `du_interval_features`, `starscout_low_activity`, `name_heuristic`, `rabbit_offline`.

## Langkah

1. Tuning sesuai `docs/06`. Objective: AP stratum 5–19 pada lengan F2 tahap pengembangan. Catat semua trial ke MLflow.
2. Latih `B0`, `B1`, `B2`, `M_behav`, `M_robust` dengan `final_model_seeds`.
3. Bandingkan XGBoost, LR, dan MLP one-hot, memakai aturan keputusan mata kuliah.
4. Hitung AP per stratum, Precision@k, Recall@k, AUC dalam sel, dan bootstrap selisih pada lengan F2 dan F3.
5. Baseline literatur `B3`: batasi waktu. RABBIT-ng dipasang terpisah. Kalau gagal dipasang atau format event tidak cocok, catat sebagai "tidak dijalankan" beserta alasannya. Jangan menghabiskan lebih dari setengah hari pada langkah ini.

## Cek

Q17, Q10. `M_behav` dan `B2` dievaluasi pada akun yang sama.

## Test

`within_cell_auc` pada contoh kecil yang dihitung manual. `paired_cluster_bootstrap` mempertahankan seluruh akun per klaster. `ap_by_stratum` deterministik untuk skor sama.
