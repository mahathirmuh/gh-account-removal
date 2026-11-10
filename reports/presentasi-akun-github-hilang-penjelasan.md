# Penjelasan Presentasi Prediksi Akun GitHub Hilang

Dokumen ini menjelaskan isi [presentasi-akun-github-hilang.pptx](presentasi-akun-github-hilang.pptx) slide demi slide, supaya bisa disampaikan dengan kata-kata sendiri dan siap menghadapi pertanyaan. Versi singkatnya sudah ada di catatan pembicara tiap slide.

PPT ini belum memuat hasil model. Hasil finalnya ada di [draf-hasil-penelitian.md](draf-hasil-penelitian.md). Semua angka data di PPT berasal dari pipeline yang sudah dijalankan.

## Ringkasan satu menit

> Penelitian ini mencoba menandai lebih awal akun GitHub yang kelak hilang, hanya dari aktivitas publiknya selama 5 sampai 60 menit. Akun dianggap hilang bila ID numeriknya menghasilkan 404 sekitar 31 bulan kemudian. Ada dua hal yang diuji secara khusus: apakah cara membagi data mengubah performa yang terukur, dan apakah kebijakan penandaan adaptif bisa menandai akun lebih cepat pada precision yang sama dibanding jendela tetap. Tidak ada algoritma baru yang diklaim. Kontribusinya ada pada evaluasi dan penerapan.

## Istilah yang perlu dikuasai

| Istilah | Arti sederhana |
| --- | --- |
| Akun hilang (label `s`) | ID numerik akun menghasilkan 404 pada snapshot status. Bisa karena dihapus sendiri, dihapus platform, atau sebab lain, jadi bukan bukti pelanggaran |
| GH Archive | Arsip event publik GitHub per jam, misalnya push, pull request, dan issue |
| Jendela | Potongan waktu sejak awal jam: 5, 10, 15, 30, atau 60 menit. Fitur hanya boleh memakai event di dalam jendela itu |
| Checkpoint | Menit saat model mengambil keputusan, yaitu menit 5, 10, 15, 30, dan 60 |
| Stratum | Kelompok akun menurut jumlah event dalam satu jam: 1, 2–4, 5–19, dan 20 ke atas. Stratum kunci adalah 5–19 |
| Kohort tetap | Akun dengan minimal 5 event dalam 60 menit. Dipakai untuk mengukur hilangnya informasi saat jendela dipendekkan |
| Kohort deployable | Akun dengan minimal 3 event dalam `w` menit. Tidak memakai informasi masa depan |
| Proksi usia | Usia akun diperkirakan dari ID numerik, karena ID makin besar untuk akun yang makin baru |
| Baseline B2 | Model pembanding yang hanya tahu aktivitas kasar dan usia akun. Ini lawan utama |
| M_behav | B2 ditambah 48 fitur perilaku |
| Split acak | Akun dibagi acak ke train dan test. Akun yang berdekatan bisa terpisah ke dua sisi |
| Split blok ID | Akun dikelompokkan per rentang ID, dan satu blok tidak boleh terbelah |
| Split forward | Latih pada minggu lebih awal, uji pada minggu sesudahnya |
| Lengan F1, F2, F3 | F1 semua akun minggu test. F2 hanya akun yang tidak muncul di train. F3 adalah F2 tanpa akun di blok ID yang memuat akun hilang di train |
| Holdout | Data minggu keempat yang dikunci dan hanya dibuka satu kali di akhir |
| AP (Average Precision) | Rangkuman precision saat recall naik. Cocok untuk kelas langka |
| Base rate | Porsi kasus positif. AP model acak kira-kira sama dengan base rate, jadi AP harus dibaca bersamanya |
| AUC di dalam sel | Kemampuan mengurutkan akun yang aktivitas dan usianya setara. Nilai 0,5 berarti setara acak |
| Kalibrasi | Mengubah skor model menjadi peluang yang bisa diberi ambang. Memakai isotonic, atau Platt bila positif kurang dari 30 |
| AURT | Luas di bawah kurva recall terhadap waktu. Makin besar berarti akun hilang makin banyak dan makin cepat ditandai |
| Kurva AMOC | Waktu penandaan rata-rata terhadap false positive rate |
| PU learning | Cara belajar saat hanya sebagian positif berlabel. Akun yang masih ada bisa saja hilang nanti, jadi diperlakukan sebagai unlabeled |
| Dense block | Sekelompok akun yang aktif bersamaan pada repo, jenis event, dan menit yang sama |
| Paired cluster bootstrap | Sampel ulang per blok ID, lalu kedua model dinilai pada sampel ulang yang sama untuk mendapat interval selisih |

## Penjelasan per slide

### Slide 1. Judul

**Pesan utama.** Penelitian ini memprediksi akun GitHub yang kelak hilang dari jendela event publik singkat, disertai audit desain split dan kebijakan penandaan dini adaptif.

**Cara menyampaikan.** Sebutkan objeknya dulu, yaitu akun GitHub yang kelak hilang. Lalu sebutkan dua hal khusus yang diuji. Kisi di sebelah kanan hanya ilustrasi: kotak terisi melambangkan aktivitas akun, dan kotak kosong melambangkan akun hilang.

**Kalau ditanya.**

- *Kenapa disebut akun hilang, bukan akun bermasalah?* Karena yang teramati hanya status 404. Status itu mencampur penghapusan sendiri, moderasi, dan penyebab lain.

### Slide 2. Latar Belakang Masalah

**Pesan utama.** Detektor yang ada butuh histori panjang, padahal keputusan perlu diambil lebih awal.

**Cara menyampaikan.** Ada empat masalah.

1. **Histori panjang.** GitSec memakai event 2015–2018, dan Du et al. 2015–2019. Prediksi dari satu jendela 60 menit atau kurang tidak ditemukan dalam pencarian yang dilakukan.
2. **Usia dan volume sudah prediktif.** Pada stratum 5–19 event di data train, desil ID terbaru hilang di atas 10%, sedangkan desil tertua di bawah 1%. Jadi model harus terbukti lebih baik dari informasi usia dan volume saja.
3. **Bias desain split.** Akun bisa dibuat berkelompok, sehingga ID yang berdekatan dapat masuk ke train dan test sekaligus. Contoh dari domain lain, studi LOBO pada bot Twitter: 97,84% pada split acak turun ke 54,88% pada kelas yang tidak terlihat saat latih.
4. **Jendela tetap menunda keputusan.** Semua akun harus menunggu sama lama, padahal sebagian mungkin sudah cukup jelas lebih awal.

Tutup dengan definisi target di kotak gelap, dan tekankan bahwa akun hilang tidak berarti melanggar aturan.

**Kalau ditanya.**

- *Kenapa tidak memakai label pelanggaran?* Label seperti itu tidak tersedia pada skala ini. Status 404 bisa diukur untuk ratusan ribu akun, tetapi artinya harus dibaca sebagai akun hilang.
- *Angka 97,84% itu hasil penelitian ini?* Bukan. Itu contoh dari studi lain untuk menunjukkan bahwa desain split bisa mengubah hasil.

### Slide 3. Novelty

**Pesan utama.** Kebaruannya ada pada kombinasi masalah, evaluasi, dan kebijakan penandaan, bukan pada algoritma baru.

**Cara menyampaikan.** Jelaskan tiga kartu, lalu tunjukkan baris "sudah ada sebelumnya". Menyebut yang tidak diklaim justru menunjukkan posisi penelitian ini jelas.

1. **Target dari jendela sangat pendek.** Yang diprediksi adalah 404 pada ID numerik sekitar 31 bulan kemudian, hanya dari satu jendela event publik.
2. **Audit desain split pada akun GitHub.** Blok ID dan signature aktivitas dipakai sebagai unit grup.
3. **Kebijakan penandaan dini adaptif.** Ini metode usulan: aturan berhenti per akun pada skor terkalibrasi, dengan kendala precision.

**Kalau ditanya.**

- *Apakah sudah ada yang mengerjakan ini?* Jawab dengan kalimat yang tertulis di slide: kombinasi ini tidak ditemukan dalam pencarian yang dilakukan, dan ketiadaan itu bukan bukti kebaruan. Pencarian memakai arXiv API, OpenAlex, WebSearch, dan penelusuran sitasi. ACM DL, IEEE Xplore, Google Scholar, dan prosiding MSR belum dicari langsung.
- *Apa bedanya dengan GitSec?* GitSec memakai histori multi-tahun dan kelas positifnya API 200 dengan web 404, sedangkan akun API 404 dibuang. Penelitian ini memakai satu jendela 60 menit atau kurang, dan targetnya justru 404 pada ID numerik.
- *Kalau tidak ada algoritma baru, apa nilainya?* Penelitian ini mengukur hal yang menentukan apakah hasil model bisa dipercaya: seberapa besar desain evaluasi mengubah angka, dan seberapa cepat penandaan bisa dilakukan pada precision yang sama.

### Slide 4. Kontribusi

**Pesan utama.** Enam kontribusi empiris dan evaluatif, dengan satu metode usulan terapan.

**Cara menyampaikan.** Mulai dari K6 karena itu metode usulan, lalu bacakan K1 sampai K5 secara singkat.

| Kode | Maksudnya | Hipotesis terkait |
| --- | --- | --- |
| K1, K3 | Apakah fitur perilaku mengalahkan baseline, termasuk di antara akun dengan aktivitas dan usia setara | H1a, H1b |
| K2 | Apakah split acak melebih-lebihkan tambahan AP dibanding split blok ID | H2a, H2b |
| K4, K6 | Seberapa turun performa dari 60 ke 5 menit, dan apakah kebijakan adaptif lebih cepat | H4a, H4b |
| K5 | Apakah fitur dense block menambah AP di atas fitur perilaku | H5 |

RQ3 tentang PU learning bersifat eksploratif, jadi tidak termasuk kontribusi utama.

**Kalau ditanya.**

- *Bagaimana kalau kebijakan adaptif tidak lebih cepat?* Hasilnya tetap dilaporkan, dan klaim K6 gugur. Judul paper juga perlu diubah.
- *Kalau fitur koordinasi tidak menambah apa-apa?* Hasil nol tetap dilaporkan sebagai temuan.

### Slide 5. Tabel Posisi Penelitian

**Pesan utama.** Karya terdekat hanya memenuhi sebagian kriteria yang digabungkan penelitian ini.

**Cara menyampaikan.** Tiap baris adalah karya terdekat, dan tiap kolom adalah kriteria. Tunjukkan beberapa contoh saja:

- GitSec dan StarScout memakai data GitHub, tetapi berbasis histori panjang.
- LOBO adalah preseden terdekat untuk audit split.
- ECTS dan eRisk punya aturan berhenti, tetapi pada deret waktu dan post pengguna.

**Kalau ditanya.**

- *Kenapa baris penelitian ini semuanya "Ya"?* Baris itu menunjukkan rancangan, bukan hasil. Kolom kosong pada karya lain bukan bukti kontribusi, dan kombinasi ini hanya bernilai kalau hasilnya mengubah kesimpulan.
- *Kenapa angkanya tidak dibandingkan langsung dengan GitSec?* Data, rasio kelas, dan definisi labelnya berbeda, jadi angkanya tidak sebanding.

### Slide 6. Dataset

**Pesan utama.** Data berasal dari 25 jam GH Archive, dengan status akun diambil sekitar 31 bulan kemudian.

**Cara menyampaikan.**

- **Sumber.** GH Archive untuk event publik, dan GitHub API untuk status akun.
- **Ukuran.** 5.291.889 event dan 885.634 akun non-bot berlabel. Sebanyak 18.068 akun hilang, atau 2,04%.
- **Pembagian waktu.** 1 jam untuk pengembangan dan 24 jam studi: train 12 jam, validasi 6 jam, holdout 6 jam.
- **Grafik.** Tingkat hilang pada data train naik di akun yang sangat aktif. Stratum 5–19 adalah stratum kunci.
- **Validasi label.** Pemeriksaan ulang lewat REST cocok 2.000 dari 2.000. Sebanyak 192 dari 200 akun hilang juga 404 di web. Korelasi ID dengan tanggal pembuatan akun 0,9995.
- **Privasi.** Login diganti pseudonim HMAC, dan email commit tidak disimpan.

**Kalau ditanya.**

- *Kenapa memakai ID numerik?* Login bisa berganti atau dipakai orang lain, sedangkan ID tetap.
- *Kenapa 8 dari 200 akun hilang masih 200 di web?* Kemungkinan login lamanya sudah dipakai orang lain. Ini belum diverifikasi per akun.
- *Kenapa hanya 24 jam?* Semua jam berada dalam empat minggu, sehingga selisih masa tunggu antarjam paling banyak 25 hari dari sekitar 31 bulan. Pilihan Selasa, Kamis, dan Sabtu pukul 03 dan 15 UTC mencakup hari kerja, akhir pekan, dan dua waktu berbeda. Ini tetap keterbatasan generalisasi.
- *Bukti apa bahwa akun hilang memang hilang?* Dari 518 akun hilang yang punya objek di repo orang lain, 237 objeknya beratribusi ghost dan 269 objeknya tidak tersedia. Pada 150 akun kontrol yang masih ada, tidak ada yang ghost.

### Slide 7. Alur Metode Penelitian

**Pesan utama.** Alurnya dari event mentah sampai holdout yang dibuka satu kali.

**Cara menyampaikan.** Langkah 1 sampai 5 menyiapkan data, dan langkah 6 sampai 10 adalah analisis.

| Langkah | Isi |
| --- | --- |
| 1–2 | Unduh arsip, catat sha256, parse event, ganti login dengan pseudonim |
| 3 | Bangun fitur untuk tiap jendela: 48 fitur perilaku, 10 proksi koordinasi, dan fitur dense block |
| 4–5 | Ambil status akun, lalu validasi label |
| 6 | Bandingkan split acak, artefak, blok ID, signature, dan forward |
| 7 | Bandingkan B2 dengan M_behav memakai XGBoost sebagai model utama, serta LR dan MLP sebagai pembanding. Hyperparameter dicari dengan Optuna TPE |
| 8 | Elkan–Noto, PU bagging, dan SAR-EM, lalu kurva performa dari 60 ke 5 menit |
| 9 | Kebijakan penandaan dini adaptif |
| 10 | Buka holdout minggu keempat satu kali, dan audit manual oleh dua anotator |

**Cara membaca rumus.** Pada tiap checkpoint, model memberi peluang akun hilang. Akun ditandai pada checkpoint paling awal yang peluangnya melewati ambang. Ambangnya lebih tinggi pada checkpoint awal. Contoh dengan `q` = 0,6 dan `κ` = 0,25 (hanya untuk ilustrasi, bukan hasil):

| Checkpoint | Ambang |
| --- | --- |
| Menit 5 | 0,74 |
| Menit 30 | 0,68 |
| Menit 60 | 0,60 |

Nilai `q` dan `κ` dipilih pada set kalibrasi supaya precision seluruh kebijakan memenuhi target, dengan target utama 0,7.

**Kalau ditanya.**

- *Kenapa XGBoost, bukan deep learning?* Datanya tabular. MLP tetap diuji sebagai pembanding, dan model yang lebih mahal hanya dipertahankan bila selisih AP-nya positif dan melewati ambang.
- *Bagaimana mencegah kebocoran data?* Fitur hanya memakai event di dalam jendela, batas `age_bin12` dihitung dari train saja, lengan F2 dan F3 menguji akun yang tidak muncul di train, dan holdout terkunci sampai akhir.
- *Lebar blok ID berapa?* 20.000, dipilih dari korelogram residual pada data train.
- *Dense block memakai M-Zoom?* Tidak. Implementasinya greedy peeling buatan sendiri yang bergaya M-Zoom dan sudah diuji dengan blok suntikan. M-Zoom dan RABBIT-ng tidak dijalankan.

### Slide 8. Metrik Evaluasi

**Pesan utama.** AP per stratum menjadi metrik utama karena kelas positif hanya sekitar 2%.

**Cara menyampaikan.** Baca tabel berdasarkan kolom pertanyaan, lalu jelaskan AURT dan kriteria keputusan.

**Cara membaca AURT.** Untuk jendela tetap `c`, AURT = `R(c) · (T − c) / T`. Misalnya, kalau 40% akun hilang tertangkap pada menit 30, AURT = 0,4 × 45 / 75 = 0,24 (hanya untuk ilustrasi). Kebijakan adaptif bisa unggul karena sebagian akun ditandai sebelum menit 30.

**Kriteria keputusan.** Selisih AP didukung bila batas bawah CI 95% di atas 0 dan selisihnya minimal ambang efektif, yaitu nilai terbesar antara 0,01 dan dua kali simpangan baku antar-seed. Selisih AURT didukung bila batas bawah CI 95% di atas 0. Koreksi Holm diterapkan pada H1a, H2a, H4a, dan H5.

**Kalau ditanya.**

- *Kenapa bukan akurasi?* Karena akun hilang hanya sekitar 2%, model yang menebak semua akun tidak hilang sudah benar sekitar 98%.
- *Kenapa `T` = 75 menit, bukan 60?* Supaya penandaan pada menit 60 tetap bernilai. Sensitivitasnya diuji pada 65 dan 90 menit.
- *Kenapa bootstrap per blok ID?* Akun hilang cenderung berkelompok, jadi sampel ulang per akun bisa membuat interval terlalu sempit. Validasi langsung bootstrap ini untuk AP pada data klaster tidak ditemukan dalam pencarian yang dilakukan, jadi ini ekstrapolasi.
- *Metrik untuk RQ3 dan audit manual?* RQ3 memakai AP untuk memulihkan positif yang disembunyikan. Audit manual memakai Cohen's kappa dengan batas minimal 0,60.

## Pertanyaan umum

- **Output akhirnya apa?** Metode untuk menandai lebih awal akun GitHub yang kelak hilang, beserta bukti seberapa akurat metode itu kalau diuji dengan benar. Wujudnya berupa tabel, figur, dan kode untuk bahan paper.
- **Hasilnya bagaimana?** Holdout sudah dibuka satu kali. Keenam hipotesis berstatus didukung menurut aturan keputusan, tetapi H4a dan H5 sangat bergantung pada satu jam data. Rinciannya ada di [draf-hasil-penelitian.md](draf-hasil-penelitian.md).
- **Bisa langsung dipakai platform?** Belum. Hasilnya simulasi atas data arsip, dan waktu penandaan berjangkar pada awal jam. Penelitian ini juga tidak menjatuhkan tindakan apa pun terhadap akun.

## Batasan yang perlu disampaikan terus terang

- Akun hilang bukan ukuran pelanggaran.
- Snapshot status hanya diambil satu kali, yaitu 10 November 2026.
- Data hanya mencakup 24 jam studi dalam empat minggu April sampai Mei 2024.
- Jam pengembangan tidak mewakili stratum 20 event ke atas. Tingkat hilangnya 38,9%, sedangkan pada train 7,4%.
- Hanya 4,7% akun hilang yang punya objek untuk diperiksa pada probe ghost, jadi buktinya parsial.
- Rancangan dibekukan lewat tag git lokal, jadi sebutannya rancangan yang dibekukan sebelum analisis, bukan pra-registrasi.
- Pipeline dibangun dengan Claude Code, dan keputusan lanjut atau tidaknya tahap validasi label, pembekuan rancangan, serta pembukaan holdout didelegasikan kepadanya. Audit manual tetap membutuhkan dua anotator manusia.
