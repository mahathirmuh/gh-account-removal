# 01 — Desain riset dan pra-registrasi

## Latar belakang (untuk sanity check, bukan untuk dikutip)

Pilot pada satu jam pengembangan (2024-04-01 15:00–15:59 UTC, tidak dipraregistrasi) memberi arah berikut:

- Tingkat hilang naik tajam dengan aktivitas: 2,44% pada 5–19 event dan 38,9% pada ≥ 20 event.
- ID numerik, sebagai proksi usia, sangat informatif. Baseline aktivitas kasar + 12 bin usia mencapai AP 0,690 pada akun ≥ 5 event.
- Di stratum 5–19 event, fitur perilaku menambah AP +0,161 pada split acak dan +0,112 pada blok ID lebar 100.000.
- Proksi koordinasi sederhana tidak memberi tambahan terukur.

Paper hanya memakai angka hasil pipeline pada jam studi. Angka di atas dipakai di `docs/07` sebagai sanity check.

## Pertanyaan riset dan hipotesis

### RQ1 — Sinyal di luar aktivitas dan usia (K1, K3)

Di antara akun dengan aktivitas dan usia setara, apakah fitur perilaku dari jendela event publik mengurutkan akun yang kelak hilang lebih baik daripada baseline?

- **H1a:** pada holdout forward dengan pengecualian batch, stratum 5–19 event, AP `M_behav` lebih tinggi daripada AP `B2`.
- **H1b:** AUC di dalam sel aktivitas dan usia pada holdout lebih besar dari 0,5.

### RQ2 — Audit desain split (K2)

Seberapa besar desain split mengubah performa terukur, dan desain mana yang paling dekat dengan performa forward?

- **H2a:** split acak melebih-lebihkan tambahan AP fitur perilaku di atas baseline dibanding split blok ID, pada stratum 5–19.
- **H2b:** galat absolut estimasi AP terhadap holdout forward lebih besar pada split acak daripada split blok ID.

### RQ3 — Formulasi PU (eksploratif)

Apakah memperlakukan akun yang masih ada sebagai unlabeled memperbaiki peringkat dibanding model naive?

- **H3:** pada uji semi-sintetis, metode PU terbaik mengungguli naive dalam memulihkan positif yang disembunyikan.

### RQ4 — Latensi dan kebijakan adaptif (K4, K6)

Seberapa turun performa dari 60 ke 5 menit, dan apakah kebijakan adaptif menandai akun lebih cepat pada precision yang sama?

- **H4a:** AURT kebijakan adaptif lebih tinggi daripada AURT jendela tetap terbaik, pada `primary_target_precision`, pada holdout.
- **H4b (deskriptif):** kurva AP per jendela pada kohort tetap dan deployable.

### RQ5 — Koordinasi (K5, boleh gagal)

- **H5:** fitur dense-block lintas jenis event menambah AP di atas `M_behav` pada holdout. Hasil nol tetap dilaporkan sebagai temuan.

## Definisi operasional

| Konstruk | Definisi operasional | Kolom | Detail |
| --- | --- | --- | --- |
| Akun hilang (`s`) | ID numerik aktor tidak ter-resolve pada snapshot utama | `labels.is_gone` | `docs/04` |
| Label laten (`y`) | Akun kelak hilang kapan pun. Hanya dipakai di RQ3 | tidak teramati | Di bawah |
| Bot terdeklarasi | Login berakhiran `[bot]`. Dikeluarkan dari kohort dan dilaporkan terpisah | `is_app_bot` | `docs/03` |
| Stratum aktivitas | Jumlah event dalam jam: 1, 2–4, 5–19, ≥ 20 | `stratum` | `docs/05` |
| Usia akun (proksi) | `id_recency = max_id_jam − actor_id`, di-bin menjadi 12 kuantil dari data train | `age_bin12` | `docs/05` |
| Sel | Aktivitas kasar `floor(log2(n_events))` × `age_bin12` | `cell_id` | `docs/05` |
| Kohort tetap | Akun ≥ 5 event dalam 60 menit | `in_fixed_cohort` | `docs/05` |
| Kohort deployable | Akun ≥ `deployable_min_events` event dalam `w` menit pertama | dihitung per jendela | `docs/05` |

### Target `s` dan label laten `y`

`s` adalah satu-satunya label yang teramati, dan semua metrik utama dihitung terhadap `s`. `y` berarti akun kelak hilang kapan pun. Akun yang masih ada pada snapshot tidak pasti negatif untuk `y`, sehingga RQ3 memperlakukannya sebagai unlabeled. Kerangka survival dengan censoring adalah pesaing alami dan disebut di ancaman validitas. Tingkat hilang yang dilaporkan adalah p(s=1), bukan prevalensi `y`. Hindari kata "deleted", "suspended", dan "abuse".

### Himpunan waktu

| Peran | Minggu | Jam | Status |
| --- | --- | --- | --- |
| Dev | — | `2024-04-01-15` | Hanya pengembangan dan sanity check, tidak pernah masuk train, val, atau holdout |
| Train | `w0`, `w1` | 12 jam | Dipakai sejak Gerbang B |
| Val | `w2` | 6 jam | Tuning, kalibrasi, pemilihan ambang |
| Holdout | `w3` | 6 jam | Dibuka satu kali di nb15, setelah Gerbang D |

Semua jam berada dalam empat minggu, sehingga selisih follow-up antarjam paling banyak 25 hari dari sekitar 31 bulan. Sensitivitas terhadap selisih ini dilaporkan.

Akun yang muncul di beberapa jam dipakai satu kali per himpunan, yaitu pada jam pertama kemunculannya. Lengan forward F2 dan F3 menguji hanya akun yang belum pernah terlihat di train.

## Spesifikasi utama (pra-registrasi)

- Label: snapshot utama (`docs/04`).
- Kohort utama: kohort tetap, dilaporkan per stratum.
- Stratum kunci untuk RQ1: 5–19 event, karena stratum ≥ 20 sudah hampir tertangkap baseline.
- Metrik utama: AP per stratum berdampingan dengan base rate.
- Baseline lawan: `B2` (aktivitas kasar + 12 bin usia).
- Evaluasi konfirmatori: holdout forward lengan F3.
- Interval: paired cluster bootstrap per blok ID (`primary_id_block_width`).

## Aturan keputusan

| Hipotesis | Didukung jika |
| --- | --- |
| H1a | Selisih AP (`M_behav` − `B2`) pada F3 stratum 5–19: batas bawah CI 95% > 0 dan selisih ≥ `min_delta_ap` |
| H1b | AUC dalam sel pada F3: batas bawah CI 95% > 0,5 |
| H2a | Rasio tambahan AP (A1 / A3) pada stratum 5–19: batas bawah CI 95% > 1 |
| H2b | Selisih galat absolut (A1 − A3) terhadap F2 pada stratum 5–19: batas bawah CI 95% > 0 |
| H3 | Pada uji semi-sintetis, selisih AP positif tersembunyi (PU terbaik − naive): batas bawah CI 95% > 0 |
| H4a | Selisih AURT (adaptif − jendela tetap terbaik) pada `primary_target_precision`, kohort tetap, F3: batas bawah CI 95% > 0 |
| H5 | Selisih AP (`M_coord` − `M_behav`) pada F3, stratum 5–19: batas bawah CI 95% > 0 dan selisih ≥ `min_delta_ap` |

`min_delta_ap` efektif = `max(min_delta_ap, 2 × std seed terbesar)`, sesuai aturan yang dipakai pada mata kuliah. H1a, H2a, H4a, dan H5 adalah keluarga konfirmatori; p bootstrap satu sisi dikoreksi Holm.

Kalau stratum holdout memuat kurang dari `min_positives_per_stratum` positif, hipotesis dilaporkan sebagai "tidak dapat diuji", bukan "tidak didukung".

## Parameter pra-registrasi

Claude Code membuat `config/params.yaml` persis dari blok ini. Bagian `locked` tidak boleh berubah setelah tag `prereg-v1`.

```yaml
project:
  name: gh-account-removal
  seed: 20261110
  user_agent: "dm-git-research/0.1"

paths:
  token_env_file: "~/.dm-git.env"
  hmac_key_file: "~/.dm-git-hmac.key"
  local_dev_file: "2024-04-01-15.json/2024-04-01-15.json"

data:
  base_url: "https://data.gharchive.org"
  dev_hour: "2024-04-01-15"
  study_hours:
    w0: ["2024-04-09-3", "2024-04-09-15", "2024-04-11-3", "2024-04-11-15", "2024-04-13-3", "2024-04-13-15"]
    w1: ["2024-04-16-3", "2024-04-16-15", "2024-04-18-3", "2024-04-18-15", "2024-04-20-3", "2024-04-20-15"]
    w2: ["2024-04-23-3", "2024-04-23-15", "2024-04-25-3", "2024-04-25-15", "2024-04-27-3", "2024-04-27-15"]
    w3: ["2024-04-30-3", "2024-04-30-15", "2024-05-02-3", "2024-05-02-15", "2024-05-04-3", "2024-05-04-15"]

holdout_open: false

label:
  snapshot_date: null             # diisi otomatis oleh nb04 saat snapshot pertama, lalu jangan diubah
  min_events_to_label: 1
  fallback_min_events: 5          # jika GraphQL legacy ID berhenti berfungsi
  graphql_batch_size: 100
  second_snapshot_min_days: 30

annotation:
  audit_sample_top: 100
  audit_sample_low: 100
  double_annotation_fraction: 1.0  # minimum 0.2
  min_kappa: 0.60

web_crosscheck:
  n_gone: 200
  n_present: 500
  sleep_seconds: 1.2

locked:
  cohorts:
    fixed_min_events: 5
    deployable_min_events: 3
    strata: [[1, 1], [2, 4], [5, 19], [20, null]]
  windows_minutes: [5, 10, 15, 30, 60]
  features:
    age_bins: 12
    drop_families_robust: ["temporal", "repo", "repo_names"]
  splits:
    train_weeks: [w0, w1]
    val_weeks: [w2]
    holdout_weeks: [w3]
    n_folds: 5
    cv_seeds: [42, 43, 44]
    id_block_widths: [5000, 20000, 100000]
    signature_min_events: 10
    artifact_max_accounts: 30
    max_group_pos_share: 0.25
    batch_exclusion: train_positive_block
  models:
    optuna_trials: 24
    optuna_sampler_seeds: [42, 123, 2026]
    final_model_seeds: [42, 43, 44]
  dense_blocks:
    tool: greedy_peeling
    density: arithmetic
    top_k_blocks: 20
  policy:
    target_precisions: [0.5, 0.7, 0.9]
    primary_target_precision: 0.7
    kappa_grid: [0.0, 0.1, 0.25, 0.5]
    q_grid_size: 199
    aurt_horizon_minutes: 75
    aurt_horizon_sensitivity: [65, 90]
  decision:
    min_delta_ap: 0.01
    min_positives_per_stratum: 30
    bootstrap_reps: 2000
    ci_level: 0.95

# Prosedurnya dikunci di docs/06; nilainya diisi sekali oleh nb09 dari data train+val, sebelum holdout dibuka.
derived:
  primary_id_block_width: null

reporting:
  figure_dpi: 300
  figure_formats: [pdf, png]
  notebook_language: id
  figure_language: en
```

## Peta analisis

| RQ | Metode | Notebook | Output utama |
| --- | --- | --- | --- |
| RQ1 | Model bertingkat, AP per stratum, AUC dalam sel | nb10, nb15 | `tab_models_by_stratum`, `fig_within_cell` |
| RQ2 | Lengan split A1–A3 dan F1–F3, korelogram residual | nb09, nb15 | `tab_split_audit`, `fig_split_bias` |
| RQ3 | Naive, Elkan–Noto, PU bagging, SAR-EM, uji semi-sintetis | nb11 | `tab_pu_methods` |
| RQ4 | Kurva latensi, kebijakan adaptif, AURT, AMOC | nb12, nb15 | `fig_latency_curves`, `fig_recall_time`, `tab_policy` |
| RQ5 | Ablasi dense-block | nb07, nb13, nb15 | `tab_coord_ablation` |
