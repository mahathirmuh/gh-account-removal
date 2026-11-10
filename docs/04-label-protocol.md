# 04 — Protokol label

## Definisi

**Akun hilang** berarti satu hal operasional: ID numerik aktor pada jendela observasi tidak lagi ter-resolve pada snapshot utama, sekitar 31 bulan setelah jendela. Istilah ini tidak berarti akun melanggar aturan, tidak berarti akun disuspensi, dan tidak menyatakan kapan akun hilang.

## Yang diketahui dan tidak diketahui

| Pertanyaan | Yang diketahui | Yang tidak diketahui |
| --- | --- | --- |
| Arti API 404 | Dokumentasi hanya mencantumkan 200 dan 404 | Campuran penyebabnya |
| Apakah akun disuspensi menjadi API 404? | Data 2018 GitSec: akun diblokir API 200 dan web 404; akun hapus sendiri API 404 | Perilaku API 2026 tidak terdokumentasi |
| Apakah API 200 + web 404 masih ada? | Pilot: 0 dari 199 akun API-present (batas atas 95% sekitar 1,5%) | Prevalensi pada populasi |
| API-hilang di web | Pilot: 59 dari 60 web 404, 1 web 200 | Sebab satu kasus itu |
| Porsi suspensi di antara 404 | Tidak ada estimasi yang dipublikasikan | Tidak diketahui |
| Objek akun hilang | Pilot: 13 dari 519 akun hilang punya objek di repo orang lain; 7 beratribusi `ghost`, 6 tidak tersedia | 97,5% akun hilang tidak bisa diperiksa dengan cara ini |

## Snapshot status

1. nb04 mengisi `label.snapshot_date` saat dijalankan pertama kali. Setelah itu jangan diubah.
2. Daftar ID: semua akun non-`[bot]` dengan `n_events ≥ min_events_to_label` pada jam dev dan jam studi, unik, terurut.
3. Query GraphQL per `graphql_batch_size` ID, berurutan, sesuai `docs/02`.
4. Status: node ada → `present`; node `null` dengan galat `NOT_FOUND` → `gone`; kegagalan jaringan setelah retry → `error`.
5. Hasil ditulis bertahap (checkpoint per batch) supaya bisa dilanjutkan. Snapshot harus selesai dalam 48 jam. Kalau lebih, berhenti dan tanya.
6. Verifikasi: seluruh `gone` pada sampel acak 2.000 akun dicek ulang dengan REST `GET /user/{id}`. Ketidakcocokan > 1% menghentikan pipeline.
7. Tulis `labels.parquet` dengan `snapshot_id = s1`. Akun `error` tidak boleh dianggap `present`.

### Snapshot kedua (opsional)

Bila waktu mengizinkan, ulangi langkah 2–7 sebagai `s2`, minimal `second_snapshot_min_days` setelah `s1`, hanya untuk akun `present` pada `s1`. Akun yang berubah menjadi `gone` disebut **late removal**. Mereka menjadi positif tersembunyi untuk validasi prospektif di RQ3.

## Validasi label (nb05)

| Cek | Cara | Tujuan |
| --- | --- | --- |
| Cek silang API dan web | HEAD profil untuk `web_crosscheck.n_gone` akun `gone` dan `n_present` akun `present` | Mengukur kemunculan pola GitSec (API 200 + web 404) |
| ID sebagai proksi usia | Spearman `actor_id` terhadap `createdAt` pada 5.000 akun `present` acak, plus monotonisitas per desil | Validasi K3 |
| Probe `ghost` | Untuk akun `gone` dengan objek di repo orang lain, baca atribusi objek | Bukti parsial tentang penghapusan akun |
| Tingkat hilang per stratum | Hanya jam dev dan train | Sanity check terhadap pilot |

Cek silang memakai login saat ini untuk akun `present`, karena akun bisa berganti nama, dan login pada event untuk akun `gone`.

**Tidak boleh dilakukan di nb05:** menggabungkan label jam studi dengan fitur.

## Gerbang A

nb05 berhenti dan melaporkan kepada pengguna:

1. Tabel silang API × web.
2. Korelasi ID dan usia.
3. Hasil probe `ghost`.
4. Tingkat hilang per stratum dibanding pilot.
5. Rekomendasi apakah label layak dipakai.

## Audit manual (nb14, Gerbang C)

Tujuan: memperkirakan apa arti akun hilang dan akun skor tinggi secara substantif. Audit tidak boleh memakai data holdout.

### Sampel

Dari prediksi `M_behav` pada jendela 60 menit di minggu `w2`:

- `audit_sample_top` akun skor tertinggi di kohort tetap.
- `audit_sample_low` akun acak dari skor rendah, dengan distribusi stratum yang sama.
- Urutan diacak, dan `score_group` disembunyikan dari anotator.

Untuk tiap akun, tulis ringkasan dari raw: pseudonim, jumlah event per tipe, nama repo pendek (maksimum 20), contoh pesan commit (maksimum 20), judul PR (maksimum 10).

### Kategori

| Kategori | Pedoman |
| --- | --- |
| `bulk_automation` | Aktivitas massal berulang yang jelas terotomasi, tanpa tanda pengembangan perangkat lunak yang bermakna |
| `promotion_or_spam` | Repo atau konten promosi, konten curian atau game cheat, tautan unduhan mencurigakan |
| `ordinary_development` | Pengembangan perangkat lunak biasa, termasuk CI dan otomasi wajar |
| `unclear` | Bukti tidak cukup |

Anotator menilai aktivitas yang terlihat, bukan niat. Jangan membuka profil GitHub akun selama audit.

### Reliabilitas

Dua anotator mengisi secara independen. Fraksi akun yang dianotasi ganda diatur `double_annotation_fraction`. Hitung Cohen's κ. Jika κ < `min_kappa`, perbaiki pedoman dan ulangi pada sampel baru (seed + 1, dicatat). Pengguna mengadjudikasi ketidaksepakatan.

Claude Code tidak boleh mengisi kolom anotasi manusia. Sejak 2026-11-10, anotasi awal dikerjakan instance Claude di file terpisah dan divalidasi manusia, lihat `docs/DEVIATIONS.md`.

### Pelaporan

Porsi tiap kategori per `score_group` dan per status `s`, dengan interval Wilson. Precision terhadap label teramati hanya batas bawah bila positif benar-benar positif, dan batas itu bisa gagal karena penghapusan sukarela.
