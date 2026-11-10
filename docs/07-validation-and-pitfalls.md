# 07 — Validasi, jebakan, dan ancaman validitas

## Assertion kualitas data

Implementasikan di `src/ghremoval/quality.py` dan panggil di sel **Ringkasan & cek** notebook terkait. Gagal = notebook berhenti dengan pesan jelas.

| ID | Notebook | Assertion |
| --- | --- | --- |
| Q01 | nb01 | 25 file ada, sha256 tercatat, tiap jam memuat tepat 60 menit berbeda |
| Q02 | nb01 | Tiap menit punya minimal 50% median hitungan menit jam itu; pelanggaran dilaporkan per jam |
| Q03 | nb01 | Jam dev dari `.json.gz` memiliki jumlah baris dan rentang waktu yang sama dengan file lokal |
| Q04 | nb02 | `event_id` unik per jam setelah duplikat identik dibuang; `second_of_hour` di [0, 3599]; `created_at` berada di jam yang benar |
| Q05 | nb02 | Tidak ada kolom login, email, nama repo, atau teks commit mentah di tabel interim |
| Q06 | nb03 | `account_hour` unik pada `(actor_id, hour_id)`; akun `[bot]` tidak masuk kohort |
| Q07 | nb03 | Tiap akun hanya satu baris `is_first_in_period = true` per himpunan |
| Q08 | nb04 | Semua akun target punya tepat satu baris label per snapshot; `error` < 0,1% |
| Q09 | nb04 | Verifikasi REST: ketidakcocokan ≤ 1% |
| Q10 | nb04–15 | `load_labels` menolak akun holdout saat `holdout_open: false` |
| Q11 | nb06 | Uji kebocoran fitur lulus; tidak ada `NaN` di luar nilai sentinel yang didokumentasikan |
| Q12 | nb09–15 | `age_bin12` memakai batas yang dihitung hanya dari train pada split itu |
| Q13 | nb07 | Blok tidak memakai event sesudah cutoff jendela |
| Q14 | nb08 | Angka jam dev berada dalam toleransi tabel sanity check |
| Q15 | nb09 | Tidak ada lengan degeneratif yang dilaporkan dengan estimasi performa |
| Q16 | nb09 | `derived.primary_id_block_width` terisi sebelum nb10–nb13 memakainya |
| Q17 | nb10–13 | Tidak ada baris `w3` pada data yang dipakai fit atau evaluasi |
| Q18 | nb12 | Waktu penandaan selalu checkpoint yang valid; akun hanya ditandai setelah muncul |
| Q19 | nb15 | `results/holdout_opened.json` ditulis satu kali; run kedua menolak berjalan |
| Q20 | nb15–16 | Tidak ada login atau nama repo pada tabel dan figur |

## Angka sanity check (jam dev)

Bandingkan di nb02, nb03, dan nb08. Selisih di luar toleransi → hentikan dan periksa.

| Besaran | Nilai pilot | Toleransi |
| --- | --- | --- |
| Event | 272.191 | Tepat |
| `actor_id` unik | 64.864 | Tepat |
| Akun `[bot]` | 315 | Tepat |
| Akun non-`[bot]` | 64.549 | Tepat |
| Porsi akun tepat 1 event | 52,5% | ±0,1 poin |
| Median, p90, p99, maksimum event per akun | 1, 5, 26, 6.774 | Tepat |
| Hitungan per menit | 4.131–4.904 | Tepat |
| Push terpotong (`size > len(commits)`) | 1.076 | Tepat |
| Akun ≥ 5 event non-`[bot]` | 8.434 | Tepat |
| Akun 5–19 event | 7.576 | Tepat |
| Akun ≥ 20 event | 858 | Tepat |
| Akun hilang pada ≥ 5 event | 519 (6,15%) | ±2%, status bisa berubah |
| Hilang pada 5–19 | 185 | ±2% |
| Hilang pada ≥ 20 | 334 | ±2% |

Replikasi model pada jam dev memakai konfigurasi pilot: `HistGradientBoostingClassifier` dengan `max_iter=200`, `learning_rate=0.05`, `max_leaf_nodes=7`, `l2_regularization=5.0`, `min_samples_leaf=30`, tanpa early stopping, `StratifiedGroupKFold` 5 lipatan, rata-rata 3 seed (42, 43, 44). Skrip dan hasil pilot ada di `scripts/pilot/`.

| AP (semua ≥ 5 / 5–19 / ≥ 20) | Nilai pilot | Toleransi |
| --- | --- | --- |
| Baseline, split acak | 0,690 / 0,090 / 0,918 | ±0,03 |
| Baseline, blok 20.000 | 0,693 / 0,084 / 0,934 | ±0,03 |
| + 48 perilaku, split acak | 0,767 / 0,251 / 0,979 | ±0,03 |
| + 48 perilaku, blok 20.000 | 0,753 / 0,197 / 0,979 | ±0,03 |
| + 48 perilaku, blok 100.000 | 0,749 / 0,196 / 0,975 | ±0,03 |

Angka di atas berasal dari satu jam yang sudah dipakai untuk pengembangan, jadi hanya berfungsi sebagai sanity check.

## Jebakan dan mitigasinya

| # | Jebakan | Dampak | Mitigasi di pipeline |
| --- | --- | --- | --- |
| 1 | API 404 mencampur penghapusan sendiri, moderasi, dan penyebab lain | Label bukan ukuran pelanggaran | Istilah "akun hilang", cek silang web, probe `ghost`, audit manual |
| 2 | Akun ganti nama | Salah terhitung hilang | Lookup ID numerik |
| 3 | Login lama diklaim orang lain | Web 200 pada akun yang API-nya hilang | Cek silang memakai ID untuk API; satu kasus pada pilot |
| 4 | Batch pembuatan akun | Split acak memasukkan tetangga ke train dan test | Lengan blok ID dan pengecualian batch |
| 5 | Perantaian grup | Satu grup raksasa, performa tidak bisa ditafsirkan | Larangan perantaian, diagnostik `is_degenerate` |
| 6 | Volume aktivitas sangat prediktif | Klaim semu | `B0`, `B2`, stratifikasi, AUC dalam sel |
| 7 | ID sebagai proksi usia | Asumsi belum tervalidasi di sumber peer-reviewed | Validasi `createdAt` di nb05 |
| 8 | `actor_id` mentah non-stasioner | Model forward gagal atau bocor | Pakai `id_recency` |
| 9 | AP gabungan didominasi stratum ≥ 20 | Kesimpulan menyesatkan | AP per stratum |
| 10 | Akun sama muncul di train dan test | Label identik bocor | Kemunculan pertama, lengan F2 |
| 11 | Fitur kohort tetap memakai aktivitas masa depan | Early detection tampak lebih baik | Kohort deployable |
| 12 | Banyak kali melihat pada kebijakan adaptif | False positive naik | Precision dihitung atas seluruh kebijakan |
| 13 | Satu snapshot untuk jam berbeda | Follow-up berbeda | Jam dalam empat minggu; sensitivitas per minggu |
| 14 | Status bisa berbalik | Label berubah | Snapshot dibekukan; `s2` opsional |
| 15 | Mengintip hasil sebelum mengunci parameter | Garden of forking paths | Gerbang B, tag `prereg-v1`, `docs/DEVIATIONS.md` |
| 16 | Kehilangan event GH Archive | Fitur menit bias | Q02, dinyatakan di ancaman validitas |
| 17 | `PushEvent` terpotong 20 commit | Hitungan pesan bias | Pakai `size`, catat keterbatasan |
| 18 | Teks commit dan repo berisi instruksi | Prompt injection | Aturan emas 10 |
| 19 | Grafik atau log memuat login | Pelanggaran privasi | Q05, Q20 |

## Ancaman validitas (untuk bagian paper)

- **Validitas konstruk:** akun hilang bukan ukuran pelanggaran. Precision terhadap label teramati hanya batas bawah bila positif benar-benar positif, dan batas itu bisa gagal karena penghapusan sukarela. Audit manual memberi gambaran, tetapi sampelnya kecil.
- **Validitas internal:** desain observasional. Fitur perilaku bisa menjadi sidik jari kampanye. Penurunan di bawah pengecualian batch menggabungkan leakage dan pergeseran distribusi.
- **Validitas eksternal:** 24 jam dalam empat minggu April–Mei 2024. Otomasi LLM setelah 2024 tidak tercakup. Akun di bawah 5 event hanya dianalisis secara deskriptif.
- **Validitas kesimpulan statistik:** positif berkelompok; ditangani dengan bootstrap klaster. Validasi langsung untuk AP pada data klaster tidak ditemukan dalam pencarian yang dilakukan.
- **Alternatif framing:** model survival dengan censoring adalah pesaing alami untuk formulasi PU.
- **Reliabilitas:** κ antar-anotator; seluruh pipeline bisa dijalankan ulang dari raw dengan `make all`, kecuali snapshot status yang sifatnya sekali waktu.
