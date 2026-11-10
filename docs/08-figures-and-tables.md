# 08 — Daftar figur dan tabel

Versi holdout dari nb15 memakai akhiran `_final`, misalnya `tab_policy_final`. Figur lewat `ghremoval.viz.save_figure`, tabel lewat `ghremoval.report.save_table`. Label figur dan tabel dalam bahasa Inggris. Semua luaran tanpa login atau nama repo.

## Tabel

| Nama file | Isi | Notebook |
| --- | --- | --- |
| `tab_dataset_overview` | Event, akun, kohort per minggu | nb03 |
| `tab_hour_quality` | Kualitas tangkapan per jam | nb01 |
| `tab_label_validation` | Tabel silang API × web, ID vs usia, probe `ghost` | nb05 |
| `tab_base_rate_by_stratum` | Tingkat hilang per stratum, jam dev dan train | nb05 |
| `tab_dev_replication` | Angka jam dev dibanding pilot | nb08 |
| `tab_group_diagnostics` | Ukuran grup dan porsi positif per lengan | nb09 |
| `tab_split_audit` | AP dan tambahan AP per lengan | nb09, nb15 |
| `tab_models_by_stratum` | Tangga model per stratum | nb10, nb15 |
| `tab_tuning_trials` | Search space, trial, waktu, device | nb10 |
| `tab_pu_methods` | Metode PU, prior, uji semi-sintetis | nb11 |
| `tab_policy` | Precision, recall, AURT, median waktu per kebijakan | nb12, nb15 |
| `tab_coord_ablation` | `M_behav`, `M_proxy`, `M_coord` | nb13, nb15 |
| `tab_audit_results` | Kategori audit per kelompok, κ | nb14 |
| `tab_holdout_summary` | Keputusan H1a–H5 | nb15 |

## Figur

| Nama file | Isi | Notebook |
| --- | --- | --- |
| `fig_rate_by_stratum_age` | Tingkat hilang menurut aktivitas dan usia | nb05 |
| `fig_id_vs_created` | `actor_id` terhadap `createdAt` | nb05 |
| `fig_correlogram` | Korelasi residual terhadap jarak ID | nb09 |
| `fig_split_bias` | Tambahan AP per lengan | nb09, nb15 |
| `fig_within_cell` | AUC dalam sel | nb10, nb15 |
| `fig_latency_curves` | AP per jendela, kohort tetap dan deployable | nb12, nb15 |
| `fig_recall_time` | `R(t)` adaptif dibanding jendela tetap | nb12, nb15 |
| `fig_amoc` | Waktu penandaan terhadap false positive rate | nb12, nb15 |
| `fig_coord_ablation` | Selisih AP berpasangan | nb13, nb15 |

## `results/numbers.json`

Kunci minimal: `n_events_study`, `n_accounts_study`, `n_fixed_cohort`, `base_rate_5_19`, `base_rate_20p`, `delta_ap_h1a`, `ratio_h2a`, `aurt_delta_h4a`, `delta_ap_h5`, `kappa_audit`, `primary_id_block_width`, `snapshot_date`.
