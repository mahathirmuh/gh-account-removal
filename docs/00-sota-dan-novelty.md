# 00 — SOTA dan posisi novelty

Dokumen ini ringkasan kerja untuk membangun proyek. Versi lengkap, termasuk tabel SOTA per topik dan daftar pustaka dengan status pembacaan, ada di `reports/SOTA deteksi dini akun GitHub hilang.md`. Addendum di bagian akhir dokumen ini mencakup kebijakan penandaan dini adaptif, yang belum ada di laporan itu.

## Kesimpulan

**Proyek ini memberi kontribusi empiris dan evaluatif, ditambah satu metode usulan terapan. Tidak ada algoritma baru yang diklaim.** Prediksi akun GitHub hilang dari satu jendela event publik 60 menit atau kurang tidak ditemukan dalam pencarian yang dilakukan, dan ketiadaan itu sendiri bukan bukti kebaruan.

## Karya terdekat

Angka antarbaris tidak bisa dibandingkan langsung karena data, rasio kelas, dan definisi label berbeda. Status pembacaan tiap karya ada di laporan lengkap.

| Karya | Data | Metode | Label | Hasil | Beda dengan proyek ini |
| --- | --- | --- | --- | --- | --- |
| Gong et al. 2019, GitSec (CIKM); 2023 (TKDE) | Sampling ID GitHub + event GH Archive 2015–2018 | Phased LSTM + attention + CatBoost; versi TKDE menambah graf | API 200 + web 404 = malicious; API 404 dibuang | CIKM: P 0,951, R 0,896, F1 0,922, AUC 0,940 | Kelas positif berbeda; histori multi-tahun; split acak |
| He et al. 2026, StarScout (ICSE) | GH Archive Jul 2019–Des 2024 | Signature low-activity + CopyCatch pada star | Tanpa label latih; status hapus sebagai validitas | Akun kampanye terhapus 57,07% vs baseline tercetak 3,54% | Hanya star; validasi, bukan target; lookup memakai login |
| Du et al. 2020 (ACSAC) | GH Archive 2015–2019 | SVM pada operasi dan interval waktu | Positif dari promosi yang dibeli | P 98,5%, R 99,7%; 4,19% ter-ban | Fitur menit dihitung atas histori multi-tahun |
| Chidambaram et al. 2025, BIMBAS + RABBIT (JSS) | 2.150 akun, 376.638 event | Gradient boosting 38 fitur urutan aktivitas | Daftar kurasi, κ 0,91 | Weighted F1 0,899; salah 25% pada 8 aktivitas | Satuan event, API per akun, target bot |
| Volkova & Bell 2017 (ICWSM) | Twitter Inggris, Spanyol, Rusia | Log-linear, LSTM | API: deleted, suspended, non-deleted | F1 sampai 0,92 | Tugas paling mirip; status bisa dipisah; seimbang buatan |
| Cheng et al. 2015 (ICWSM) | Disqus | RF pada 10 post awal | Daftar banned | AUC 0,82 dicocokkan, 0,87 tanpa pencocokan | Preseden kontrol aktivitas; satuan post |
| Kumar et al. 2015, VEWS (KDD) | Wikipedia | Fitur k edit awal | Diblokir admin | Akurasi 87,82% | Kurva jumlah edit, bukan menit |
| Zheng et al. 2019, SAFE (AAAI) | Twitter, Wikipedia | Model survival neural | Waktu suspensi, right-censoring | F1 rata-rata 0,6537 dan 0,7866 | Alternatif censoring terhadap PU |
| Weber & Neumann 2021 (arXiv) | Twitter | Komunitas koordinasi + bagging PU | Akun koordinasi berlabel | Akurasi BPU 0,54–0,95 | Preseden langsung fitur koordinasi + PU |
| Shin et al. 2016–2017, M-Zoom, D-Cube, DenseAlert | Tensor sampai TB | Greedy dense-subtensor, jaminan 1/N | Injeksi, intrusi | AUC 0,98 pada TCP (M-Zoom) | Jenis event belum dipakai sebagai mode; bukan GitHub |
| Echeverría et al. 2018, LOBO (ACSAC) | Twitter, 14 kelas bot | Leave One Botnet Out | Kelas bot | 97,84% acak vs 54,88% kelas tak terlihat | Preseden terdekat audit split |
| Pendlebury et al. 2019, TESSERACT (USENIX Sec) | Android | Konsistensi waktu, metrik AUT | Label malware | F1 0,91 turun ke 0,58 | Template lengan temporal |
| Kaufman et al. 2012 (TKDD) | KDD-Cup 2008 | Konseptual | — | ID berurutan sebagai leakage | Menggugurkan kedekatan ID sebagai ide baru |
| Bekker et al. 2019, SAR-EM (ECML PKDD) | 8 dataset | EM classifier + propensity | SAR | Mengungguli naive, KM2, TIcE | Propensity bergantung pada atribut |
| Renault et al. 2025 (TMLR) | Benchmark ECTS | Sembilan algoritma early classification | Label deret waktu | Tidak ada protokol evaluasi bersama sebelumnya | Deret waktu, bukan akun |

## Matriks posisi

| Karya | GitHub | Jendela ≤ 60 menit | Stream publik saja | Status kemudian = label | PU/SAR | Kontrol aktivitas + usia | Split waktu + klaster | Kurva menit | Audit split | Aturan berhenti per unit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GitSec | Ya | Tidak | Tidak | Ya | Tidak | Tidak | Tidak | Tidak | Tidak | Tidak |
| StarScout | Ya | Tidak | Ya | Sebagian | Tidak | Tidak | Tidak | Tidak | Tidak | Tidak |
| BIMBAS | Ya | Tidak | Sebagian | Tidak | Tidak | Sebagian | Tidak | Tidak | Tidak | Tidak |
| Volkova & Bell | Tidak | Tidak | Sebagian | Ya | Tidak | Tidak | Tidak | Tidak | Tidak | Tidak |
| Cheng et al. | Tidak | Tidak | Tidak | Ya | Tidak | Sebagian | Tidak | Tidak | Tidak | Tidak |
| Weber & Neumann | Tidak | Sebagian | Sebagian | Tidak | Ya | Tidak | Tidak | Sebagian | Tidak | Tidak |
| LOBO | Tidak | Tidak | Tidak | Tidak | Tidak | Tidak | Sebagian | Tidak | Ya | Tidak |
| ECTS (Renault et al.) | Tidak | Tidak relevan | Tidak relevan | Tidak | Tidak | Tidak | Tidak | Tidak | Tidak | Ya, deret waktu |
| eRisk (ERDE, F_latency) | Tidak | Tidak | Ya | Tidak | Tidak | Tidak | Tidak | Tidak | Tidak | Ya, post pengguna |
| **Proyek ini (rencana)** | Ya | Ya | Ya | Ya | Ya, sensitivitas | Ya | Ya | Ya | Ya | Ya |

Kolom kosong bukan bukti kontribusi. Kombinasi sel hanya bernilai bila hasilnya mengubah kesimpulan.

## Verdict klaim awal

| Klaim | Verdict | Karya yang menggugurkan atau membatasi |
| --- | --- | --- |
| C1: label retrospektif level akun di GitHub dengan ID numerik | Sudah dilakukan dalam bentuk luas | GitSec memakai status platform sebagai label latih dengan lookup ID numerik |
| C2: dense block lintas event sebagai fitur PU, split klaster | Bukan metode baru | Weber & Neumann, Luceri et al., Vargas et al., keluarga M-Zoom |
| C3: kurva 60 ke 5 menit | Bertahan hanya sebagai kontribusi evaluasi | Kurva per jumlah aksi sudah mapan |
| C4: audit desain split | Harus dipersempit | LOBO, TESSERACT, Kaufman et al. |

## Kontribusi yang boleh ditulis

| Kode | Kontribusi | Syarat agar klaim berlaku |
| --- | --- | --- |
| K1 | Prediksi hilangnya akun (404 pada ID numerik) pada horizon sekitar 31 bulan dari jendela pendek event publik | Replikasi pada banyak jam, definisi `y` eksplisit, cek silang API dan web |
| K2 | Audit desain split pada data akun GitHub, memakai kedekatan ID dan signature aktivitas sebagai unit grup | Semua lengan pada banyak jam, diagnosis ukuran grup, interval bootstrap |
| K3 | Analisis terkontrol aktivitas dan usia, peringkat di dalam sel | Validasi ID sebagai proksi usia, sel ditetapkan sebelum melihat data baru |
| K4 | Kurva latensi berbasis menit pada kohort tetap dan deployable | Baseline di tiap jendela, temuan substantif |
| K5 | Ablasi fitur koordinasi lintas jenis event | Dense-block sungguhan, hasil nol tetap dilaporkan |
| K6 | **Metode usulan:** kebijakan penandaan dini adaptif per akun dengan kendala precision | Mengungguli jendela tetap pada holdout, lihat `docs/06` |

Dataset terpseudonimisasi adalah artefak pendukung, bukan klaim novelty.

### Rumusan yang disarankan

- K1: "Studi ini memprediksi hilangnya akun GitHub, didefinisikan sebagai respons 404 pada ID numerik yang tahan lama sekitar 31 bulan setelah observasi, dari satu jendela pendek event publik. Kombinasi ini tidak ditemukan dalam pencarian yang dilakukan. GitSec sudah memakai status platform GitHub sebagai label latih dengan lookup ID numerik, dengan kelas positif berbeda, dan target serupa sudah dipelajari di Twitter."
- K2: "Kami mengukur seberapa besar desain split mengubah performa terukur pada prediksi akun hilang di GitHub. Kedekatan ID sebagai saluran leakage sudah dibahas Kaufman et al., dan penurunan performa memuat leakage sekaligus pergeseran distribusi."
- K6: "Kami menerapkan aturan berhenti pada skor terkalibrasi untuk memutuskan per akun kapan menandai, dengan kendala precision, dan membandingkannya dengan jendela tetap. Aturan berhenti sudah mapan pada early classification dan sequential testing; penerapannya pada prediksi akun hilang dari stream event publik tidak ditemukan dalam pencarian yang dilakukan."

### Tidak boleh diklaim sebagai kontribusi

Label status platform, lookup ID numerik, target deleted atau suspended, kedekatan ID sebagai leakage, GroupKFold, split waktu, holdout sekali buka, baseline kuat, gradient boosting, MLP, regresi logistik, Optuna, MLflow, AP, precision at k, bootstrap, SCAR, SAR, PU bagging, Elkan–Noto, dense block, CopyCatch, fitur koordinasi dalam classifier, kurva performa terhadap jumlah observasi, dan aturan berhenti sebagai gagasan umum.

Fitur tetangga ID dan coarsening fitur sebagai pertahanan tidak didukung pilot, jadi jangan diajukan.

## Addendum: kebijakan penandaan dini adaptif (K6)

Pencarian 2026-11-10, memakai empat kueri WebSearch: survei early classification, aturan berhenti adaptif untuk akun palsu dan bot, AMOC dan sequential testing untuk akun, serta deteksi dini akun GitHub pada stream event.

| Karya | Isi | Status baca |
| --- | --- | --- |
| Renault, Bondu, Cornuéjols, Lemaire 2025, "Early Classification of Time Series: A Survey and Benchmark", TMLR, arXiv:2406.18332 | Trade-off biaya menunggu dan salah klasifikasi; memisahkan komponen decision dan prediction; pustaka `ml_edm` | Abstrak |
| Gupta, Gupta, Biswas, Dutta 2020, "Approaches and Applications of Early Classification of Time Series: A Review", IEEE Trans. AI, arXiv:2005.02595 | Empat kategori: prefix, shapelet, model, miscellaneous | Abstrak |
| Jung, Paxson, Berger, Balakrishnan 2004, "Fast Portscan Detection Using Sequential Hypothesis Testing", IEEE S&P, DOI 10.1109/SECPRI.2004.1301325 | Sequential hypothesis testing per host; sekitar 4–5 percobaan koneksi | Abstrak |
| Losada & Crestani 2016 (ERDE); Sadeque, Xu, Bethard 2018 (F_latency) | Keputusan per pengguna dengan penalti keterlambatan | Metadata; rumus dari sumber sekunder di catatan riset |
| Fawcett & Provost, "Activity monitoring: Noticing interesting changes in behavior", KDD ke-5 | Asal kurva AMOC: delay terhadap false alarm | Metadata, dilihat sebagai rujukan di Jiang, Cooper, Neill "Generalized AMOC Curves" |

**Verdict.** Aturan berhenti bukan gagasan baru. Penerapan per akun pada prediksi akun hilang dari stream event publik, dengan kendala precision dan evaluasi berbasis menit, tidak ditemukan dalam pencarian yang dilakukan. Jumlah pencarian untuk addendum ini kecil, jadi sebelum mengutip, periksa juga ACM DL dan IEEE Xplore secara langsung. ERDE dan F_latency tidak dipakai sebagai metrik utama; AURT dan kurva AMOC lebih cocok karena keputusan diambil pada checkpoint bersama.

## Batas pencarian

Pencarian utama memakai arXiv API, OpenAlex, WebSearch, dan penelusuran sitasi GitSec, Du, dan He. DBLP gagal, Semantic Scholar sebagian besar kena rate limit, dan ACM DL, IEEE Xplore, Google Scholar, serta prosiding MSR tidak dicari langsung. Daftar item yang wajib dicek sebelum mengutip ada di Bagian 8 laporan lengkap.
