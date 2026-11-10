# Menyempitkan Novelty Prediksi Akun GitHub Hilang

## 1. Ringkasan: kontribusi proyek ini empiris, bukan algoritma baru

**Proyek ini hanya bisa mempertahankan kontribusi empiris dan evaluasi; tidak ada algoritma baru yang bisa diklaim.** SOTA terdekat tidak bekerja dari satu jendela pendek: GitSec sudah memakai status platform GitHub sebagai label akun dengan lookup ID numerik, tetapi dari histori 2015–2018 ([Gong et al. 2019](https://user.informatik.uni-goettingen.de/~ychen/papers/GitSec-CIKM19.pdf)); StarScout dan Du et al. memakai GH Archive multi-tahun ([He et al. 2026](https://cmustrudel.github.io/papers/icse2026fakestars.pdf); [Du et al. 2020](https://personal.utdallas.edu/~shao/papers/du_acsac20.pdf)); detektor bot seperti BIMBAS butuh histori per akun ([Chidambaram et al. 2025](https://decan.lexpage.net/files/JSS-2025.pdf)). Prediksi akun hilang, yaitu API 404 pada ID numerik sekitar 31 bulan kemudian, dari satu jendela event publik 60 menit atau kurang **tidak ditemukan dalam pencarian yang dilakukan**, dan ketiadaan itu sendiri bukan bukti kebaruan. C1 sudah dilakukan dalam bentuk luasnya, C2 bukan metode baru, C3 hanya bertahan sebagai pengukuran, dan C4 harus dipersempit menjadi audit khusus data akun GitHub. Yang tidak boleh diklaim: label status GitHub berbasis ID numerik, kedekatan ID sebagai saluran leakage ([Kaufman et al. 2012](https://www.cs.umb.edu/~ding/history/470_670_fall_2011/papers/cs670_Tran_PreferredPaper_LeakingInDataMining.pdf)), dense block, PU/SAR atau group split sebagai kontribusi, 404 sebagai suspensi atau abuse, dan deteksi real-time. Bukti proyek saat ini hanya **pilot pengembangan satu jam yang tidak dipraregistrasi**: baseline usia dan aktivitas sudah mencapai AP 0,690 pada akun ≥5 event, fitur perilaku menambah sinyal terutama di stratum 5–19 event, split acak melebih-lebihkan tambahan itu sekitar 44% dibanding blok ID lebar 100.000, proxy koordinasi tidak memberi tambahan yang terukur, sedangkan PU, split waktu dan kurva latensi belum punya hasil.

## 2. Tabel SOTA: detektor GitHub butuh histori panjang, dan label status sudah ada sejak 2019

Baris bertanda **[abstrak saja]** hanya didukung abstrak atau halaman setara, dan **[non-peer-review]** adalah laporan industri atau blog. P = precision, R = recall. Angka antarbaris tidak bisa dibandingkan langsung karena data, rasio kelas dan definisi label berbeda.

### Deteksi bot GitHub

Kelompok ini memakai daftar label kurasi dan histori per akun. Pada satu-satunya test set bersama (860 akun), BotHunter mencapai F1 tertimbang 0,950 tetapi turun ke 0,787 tanpa heuristik nama, sedangkan BIMBAS 0,899 ([Chidambaram et al. 2025, Tabel 7](https://decan.lexpage.net/files/JSS-2025.pdf)). Di antara karya yang dibaca, kurva performa selalu berbasis jumlah event atau komentar.

| Peneliti (tahun) | Venue | Data | Metode | Label atau ground truth | Metrik dan hasil | Keterbatasan | Beda dengan proyek ini |
|---|---|---|---|---|---|---|---|
| [Dey et al. (2020), BIMAN](https://arxiv.org/pdf/2003.03172) | MSR | World of Code versi P: 34,4 juta ID author, 1,69 miliar commit | Regex nama (BIN), skor template pesan commit (BIM), RF fitur file dan proyek (BICA), ensemble RF | 13.150 bot dari regex BIN yang diverifikasi manual + 13.150 manusia; ensemble dilatih pada 134 author | AUC-ROC median 0,90 (0,89–0,95); 58 dari 67 bot dikenal | Golden set bisa melewatkan bot yang bersembunyi; tanpa penggabungan alias | Unit identitas commit; butuh daftar file World of Code yang tidak ada di GH Archive |
| [Golzadeh et al. (2021), BoDeGHa](https://arxiv.org/pdf/2010.03303) | JSS 175 | 136.529 repo Libraries.io; 5.000 commenter berlabel (527 bot) | RF pada pola komentar (DBSCAN) dan Gini; split stratifikasi 60/40 | Rating manual dengan nama disembunyikan, kappa 0,96 | Bot P 0,94, R 0,91, F1 0,92; F1 0,87 pada 0–4 komentar, 0,96–1,00 sejak 10 komentar | Tidak berlaku di bawah 10 komentar; akun campuran dikeluarkan | Per repo lewat GraphQL; kurva dalam jumlah komentar, bukan menit |
| [Abdellatif et al. (2022), BotHunter](https://www.ime.usp.br/~gerosa/papers/MSR2022BotHunter.pdf) | MSR | Oracle 5.107 akun (13,3% bot) | RF 19 fitur profil, aktivitas, kemiripan teks; 10-fold | Diwarisi dari BoDeGHa dan BIMAN | P 95,7, R 89,4, F1 92,4, AUC 98,3 (Tabel 3) | Hanya 300 aktivitas dalam 3 bulan; tanpa test set terpisah | Fitur profil API tidak tersedia di GH Archive; target bot |
| [Chidambaram et al. (2024), RABBIT](https://natarajan-chidambaram.github.io/papers/MSR2024_RABBIT_A_tool_for_identifying_bot_accounts_based_on_their_recent_GitHub_event_history.pdf) | MSR Data & Tool | 1.335 akun (644 bot, 691 manusia) | XGBoost 6 fitur urutan aktivitas | Gabungan dataset; relabel kappa 0,79 | Test P=R=F1 0,919, AUC 0,921; benar 86,3% (≤100 event), 98,5% (>200) | Hanya event publik; akun tak aktif tak terprediksi | Minimal 5 event dan API per akun; hanya 13,07% akun non-`[bot]` di jam pilot punya ≥5 event |
| [Chidambaram et al. (2025), BIMBAS + RABBIT](https://decan.lexpage.net/files/JSS-2025.pdf) | JSS 221 | 2.150 akun (1.035 bot), 376.638 event | Gradient Boosting 38 fitur urutan aktivitas | Empat sumber daftar; kappa 0,91 | Test weighted F1 0,899; salah klasifikasi 25% pada 8 aktivitas, 16% pada 25, maksimal 10% sejak 107 (Fig. 3) | 67,1% bot bernama "bot", bias konstruksi | Preseden terdekat C3 dalam satuan event; API per akun kecuali [mode offline RABBIT-ng](https://github.com/sgl-umons/RABBIT-ng) |
| [Golzadeh et al. (2022)](https://orbi.umons.ac.be/bitstream/20.500.12907/17537/1/botse_paper.pdf) | BotSE | 540 kontributor teratas dari 27 proyek (50 bot) | Perbandingan teknik dan ensemble | Bot vs manusia; cara pelabelan tidak tercatat | Sufiks "bot": R 0,520, P 1,000; tipe akun GitHub: R 0,360; ensemble F1 0,882 | Sampel kecil | Menunjukkan sufiks `[bot]` presisi tinggi tetapi recall rendah |
| [Bi et al. (2023), BotHawk](https://arxiv.org/pdf/2307.13386) | Preprint arXiv/SSRN | 19.779 akun (GHTorrent, BIMAN, BoDeGHa) | Undersampling + bagging RF, 17 fitur | Label manual | F1 0,882, AUC 0,947 (Tabel 4) | Angka tidak konsisten antarbagian; rekam publikasi jurnal tidak ditemukan | Fitur profil dan jaringan; target bot |
| [Liao et al. (2023), BDGOA](https://www.sciopen.com/article/10.23919/ICN.2023.0006) **[abstrak saja]** | Intelligent and Converged Networks 4(3) | "Benchmark dataset", ukuran tak terverifikasi | 24 fitur, lima classifier | Tidak tercatat | RF F1 95,83% | Precision, recall, AUC tak terverifikasi | Fokus OAuth App |
| [Horikawa et al. (2026)](https://arxiv.org/pdf/2610.36229) | Preprint arXiv | 7.837.946 commit, 1.226 repo | Deteksi commit tanpa signature | Commit agen; rincian pelabelan tidak tercatat | ROC AUC sampai 0,859; precision terbaik 0,332 pada porsi agen 0,059; transfer ke Claude Code AUC 0,524 | PR agen paling awal yang dipelajari 24 Des 2024; "Agent era" mulai Juni 2025 | Level commit; otomasi LLM pada April 2024 tetap faktor tak terukur |

### Abuse dan akun palsu di GitHub

Label status GitHub sudah muncul sebagai label latih (GitSec) dan sebagai validasi (StarScout, Du et al.). GitSec mudah terlewat: makalah ICSE StarScout sama sekali tidak menyebutnya ([catatan pencarian teks atas He et al.](https://cmustrudel.github.io/papers/icse2026fakestars.pdf)).

| Peneliti (tahun) | Venue | Data | Metode | Label atau ground truth | Metrik dan hasil | Keterbatasan | Beda dengan proyek ini |
|---|---|---|---|---|---|---|---|
| [Gong et al. (2019), GitSec](https://user.informatik.uni-goettingen.de/~ychen/papers/GitSec-CIKM19.pdf) | CIKM | 10.667.583 akun dari sampling ID lewat `api.github.com/user/ID` (Jun–Agu 2018) + event GH Archive; evaluasi 59.857 akun, ≥3 event | Dua urutan event lewat Phased LSTM dan attention, plus fitur akun, ke CatBoost | Status blokir GitHub: API 200 dan web 404 = malicious; web 200 = legitimate; API 404 dibuang sebagai "Invalid user ID" | P 0,951; R 0,896; F1 0,922; AUC 0,940. Fitur event saja F1 0,911, AUC 0,934 | Split stratifikasi 7:3 + 5-fold, tanpa split waktu atau grup | API 404 justru dibuang GitSec; jeda 3–12 minggu (dihitung); histori multi-tahun; web 200 dianggap negatif |
| [Gong et al. (2023), GitSec TKDE](https://aaltodoc.aalto.fi/bitstreams/9095077c-3398-4c13-9f15-5130dbe9b9b7/download) | IEEE TKDE 35(10) | Event 1 Jan 2015–31 Mei 2018; 2.955.783 legitimate + 57.790 malicious (≥3 event); sampel 10.000 akun | Tambahan graf user-repo dan user-user (GraphSAGE, structural hole) | Seperti CIKM; penulis menyatakan mengonfirmasi ke GitHub | AUC 0,916; hampir 0,8 pada sekitar 35% label korup | Tabel per metrik tidak terbaca bersih; dataset "upon request" | Sudah memakai graf dan uji ketahanan label; bukan PU, bukan jendela pendek |
| [Du et al. (2020)](https://personal.utdallas.edu/~shao/papers/du_acsac20.pdf) | ACSAC | GH Archive 2015–2019 (4,79 TB), 23.375.824 akun | SVM pada hitungan 14 jenis operasi, rasio star/fork, interval antaroperasi 1, 2, 3 menit dan 1 jam | 1.023 positif dari membeli promosi; 1.550 negatif kontributor repo populer | P 98,5%; R 99,7%; F1 0,991; 63.872 akun terdeteksi; 1.184 dari 28.258 (4,19%) ter-ban | Bisa dihindari dengan menambah aktivitas normal | Positif dibeli, bukan status; fitur menit dihitung atas histori multi-tahun |
| [He et al. (2026), StarScout](https://cmustrudel.github.io/papers/icse2026fakestars.pdf) | ICSE | GH Archive Jul 2019–Des 2024, >20 TB | Signature low-activity + CopyCatch (n=50, m=10, Δt=30 hari, ρ=0,5) pada graf star | Tanpa label latih; recall vs Stargazers Ghost Network; status hapus sebagai validitas kriteria | 6,0 juta star di 26.254 repo; setelah pascaproses 18.617 repo, 301 ribu akun; recall 81,23% repo, 75,95% akun; akun kampanye terhapus 57,07% vs baseline tercetak 3,54% | Ambang ad-hoc; precision tak terukur; tak cukup untuk tindakan disipliner; penyebut baseline dipertanyakan (lihat Bagian 8) | Status hanya validasi; [lookup memakai login](https://raw.githubusercontent.com/hehao98/StarScout/main/scripts/analysis/get_stargazer_info.py) sehingga rename terhitung hapus (pembacaan kode); hanya star |
| [Cheng et al. (2026)](https://arxiv.org/pdf/2604.17909) | JAWs @ ICSE | 392 instance manual (310 repo, 82 akun) | Taksonomi 8 tipe; StarScout, MLP TF-IDF, BM25, aturan | Anotasi manual | Semua metrik >89% | Skala terbatas | Tanpa status akun; bukan jendela pendek |
| [Check Point (2024)](https://research.checkpoint.com/2024/stargazers-ghost-network/) **[non-peer-review]** | Blog riset | >3.000 akun Ghost, >2.200 repo | Investigasi manual pola nama, star, email | Observasi peneliti | GitHub menurunkan sekitar 1.559 repo dan akun terkait sejak Mei 2024 | Ukuran jaringan tidak pasti; sebagian akun mungkin diretas | Bukti peran akun lintas event; deskriptif |
| [Dagster (2023)](https://dagster.io/blog/fake-stars) **[non-peer-review]** | Blog | Star dibeli (500 + 100) + GH Archive sejak 2022 | Heuristik profil dan klaster | Star dibeli | Klaster P 98%, R 85% pada repo uji | Satu repo uji; profil pembeli terhapus dalam 48 jam (anekdot) | Anekdot status, bukan label |
| [Orchid Files (2026)](https://orchidfiles.com/github-repositories-distributing-malware/) **[non-peer-review]** | Laporan | Sekitar 5 hari GH Archive, 16 juta push | Filter frekuensi update dan commit README saja | Pengamatan | Sekitar 10.000 repo cocok | Tanpa hitungan akun | Level repo |
| [Rokon et al. (2020), SourceFinder](https://www.usenix.org/conference/raid2020/presentation/omar) **[abstrak saja]** | RAID | 97 ribu repo | Identifikasi repo kode malware | Set berlabel | P 89%, R 86%; 7.504 repo | Hanya abstrak | Level repo |
| [Bae & Yagemann (2026)](https://arxiv.org/abs/2606.26291) **[abstrak saja]** | Preprint arXiv | 12,3 juta entri indeks Go, 2.289 versi malicious | Pemindaian modul | Kategori "GitHub-unobservable" (removed atau suspended) | ≥99,4% artefak masih bisa diambil lewat Go proxy | Hanya abstrak | Level repo |

### Label suspensi dan deteksi dini di platform lain

Prediksi akun yang kelak hilang atau diblokir sudah mapan di platform lain. Kurva performa umumnya dalam satuan aksi, sedangkan deadline menit terlihat pada item berita, bukan akun.

| Peneliti (tahun) | Venue | Data | Metode | Label atau ground truth | Metrik dan hasil | Keterbatasan | Beda dengan proyek ini |
|---|---|---|---|---|---|---|---|
| [Thomas et al. (2011)](https://people.eecs.berkeley.edu/~dawnsong/papers/2011%20Suspended%20accounts%20in%20retrospect%20an%20analysis%20of%20Twitter%20spam.pdf) | IMC | Twitter: 1,8 miliar tweet, 32,9 juta akun | Pengukuran retrospektif, tanpa model | API "no record", lalu redirect web ke `/suspended`, dua minggu setelah koleksi | 1,1 juta suspended (3,3%); 77% ≤1 hari, 92% ≤3 hari; audit 93% spammer | Histori akun suspended hilang | Twitter memisahkan suspensi dan hapus; proyek tidak bisa |
| [Cheng et al. (2015)](https://arxiv.org/pdf/1504.00680) | ICWSM | Disqus CNN, Breitbart, IGN | RF pada 10 post awal; dicocokkan dengan pengguna setara aktivitas | Daftar banned dari platform (1,7–3,3%) | AUC 0,82 dicocokkan, 0,87 tanpa pencocokan | Trace dan fitur moderator dari platform | Preseden kontrol aktivitas; satuan post |
| [Kumar et al. (2015), VEWS](https://arxiv.org/pdf/1507.01272) | KDD | Wikipedia: 17.027 vandal, 16.549 acak | Fitur suntingan k edit awal | Diblokir admin | Akurasi 87,82%; edit pertama saja 77,4% | Seimbang buatan | Kurva jumlah edit; ada uji temporal; bukan menit |
| [Xiao et al. (2015)](https://theory.stanford.edu/~dfreeman/papers/clustering.pdf) | AISec | LinkedIn: 260.644 akun + 30.550 bulan berikutnya | RF statistik nama dan email per klaster registrasi (IP, tanggal) | Status restriksi LinkedIn | AUC 0,98, R 0,90 pada P 95%; bulan berikut AUC 0,95, R 0,72 | Klaster adalah unit klasifikasi | Batch registrasi sebagai unit, bukan variabel desain split |
| [Klausen et al. (2016)](https://arxiv.org/pdf/1610.06242) | arXiv | Twitter: 646.961 akun | Regresi logistik metadata akun baru | Suspended per 23 Sep 2015 (5,4%) | AUC sekitar 0,83 | Akun non-suspended bisa disuspensi kemudian | Melacak akun via user ID stabil; sampel berbasis jejaring ekstremis |
| [Volkova & Bell (2017)](https://web.archive.org/web/20240111165300id_/https://ojs.aaai.org/index.php/ICWSM/article/download/14874/14724) | ICWSM | Twitter Inggris, Spanyol, Rusia | Log-linear dan LSTM; 10-fold | API Jan 2016: deleted, suspended, non-deleted | DS vs ND F1 sampai 0,92; deleted vs suspended F1 0,95–0,98 | Seimbang buatan; tanpa base rate alami | Tugas paling mirip K1; jeda 1–4 bulan; status dapat dipisah |
| [Echeverria et al. (2017), Bursty](https://arxiv.org/pdf/1709.06740) | arXiv | Twitter: sekitar 21 juta user pada satu rentang ID | Definisi botnet manual, termasuk rentang ID | Deskriptif | >500.000 bot | Satu botnet; tanpa evaluasi lintas batch | Kedekatan ID sebagai sinyal penemuan, bukan unit split |
| [Alfifi & Caverlee (2017)](https://people.engr.tamu.edu/caverlee/pubs/alfifi17socinfo.pdf) | SocInfo | Twitter Arab 2015: 26,7 juta akun, 6,2 juta kelak suspended | Classifier pada tugas seimbang | Eventually suspended | 10% awal masa hidup: akurasi 82%, AUC 90% | Tugas seimbang | Jendela relatif masa hidup akun |
| [Zheng et al. (2019), SAFE](https://arxiv.org/pdf/1809.04683) | AAAI | Twitter 51.608 akun, pantau 3 harian; Wikipedia 1.759 | Model survival neural | Waktu suspensi dengan right-censoring | F1 rata-rata @1–@5: 0,6537 Twitter, 0,7866 Wikipedia | Langkah 3 hari | Alternatif censoring terhadap PU |
| [Breuer et al. (2020), SybilEdge](https://arxiv.org/pdf/2004.04834) | WWW | Facebook, akun sangat baru | Model friend request | Label classifier internal | AUC menuju 0,91 untuk >15 request | Data privat | Satuan aksi; bukan stream publik |
| [Seyler et al. (2021)](https://web.archive.org/web/20260502120329id_/https://ojs.aaai.org/index.php/ICWSM/article/download/18091/17894) | ICWSM | Twitter 2009; 83.321 suspended + 83.321 reguler | SVM, CNN, LSTM, BERT; split per akun | Redirect web `account/suspended` | Akurasi >80% dengan 10 tweet; 78% pada 15 tweet lebih awal | Seimbang; tanggal crawl status tak tercatat | Menolak bin waktu; jendela relatif label |
| [Kapoor et al. (2021)](https://arxiv.org/pdf/2111.12395) | WI-IAT | Twitter: 56.927 suspended dari 2,2 juta | Klasifikasi 3 kelas | Suspended 29 Jun 2019, cek ulang 8 Okt 2019 | F1 0,84; 1.626 akun aktif lagi (2,86%, dihitung) | Dua titik cek | Bukti status bisa berbalik |
| [Xu et al. (2021), DEC](https://www.usenix.org/system/files/sec21-xu-teng.pdf) | USENIX Security | Facebook | Deep features dari entitas terkait | >30 juta label perkiraan + 240.000 label manusia | AUC 0,90; R 50% pada P 0,95 | Data privat | Butuh fitur entitas privat |
| [Saeed et al. (2022), TrollMagnifier](https://arxiv.org/pdf/2112.00443) | IEEE S&P | Reddit | Deteksi akun troll | Status sebagai validasi: 403 suspended, 404 deleted | 298 dari 1.248 akun suspended atau deleted | Jeda cek status tak tercatat | Reddit memisahkan kode; GitHub tidak terdokumentasi |
| [Shevtsov et al. (2023), BotArtist v1](https://arxiv.org/pdf/2306.00037v1) | arXiv | Twitter: 343.322 suspended vs 8.159.204 normal | XGBoost fitur profil | Suspended >6 bulan; akun pulih dibuang | ROC-AUC 0,796 | Versi terbaru dibingkai ulang | Filter persistensi sebagai mitigasi |
| [Liu & Wu (2018)](https://web.archive.org/web/20260305040253/https://ojs.aaai.org/index.php/AAAI/article/view/11268) **[abstrak saja]** | AAAI | Twitter, Weibo | Deteksi berita palsu dini | Label cerita | Akurasi 85% dan 92% dalam 5 menit | Unit cerita | Deadline menit pada item, bukan akun |
| [Yuan et al. (2019), Ianus](http://netsec.ccert.edu.cn/publications/ccs18-ianus) **[abstrak saja]** | CCS | Registrasi WeChat | Pola registrasi sinkron | Verifikasi tim WeChat | P >96% rata-rata; R tak tercatat | Data privat | Saat registrasi, bukan event publik |

### Dense-block dan koordinasi

Alat dense-block N-way sudah matang dan jauh melampaui skala proyek, tetapi dievaluasi terutama dengan injeksi blok dan data intrusi. Literatur koordinasi sudah memakai fitur koordinasi dan bahkan classifier PU, pada Twitter dan pada jaringan kemiripan, bukan tensor.

| Peneliti (tahun) | Venue | Data | Metode | Label atau ground truth | Metrik dan hasil | Keterbatasan | Beda dengan proyek ini |
|---|---|---|---|---|---|---|---|
| [Beutel et al. (2013), CopyCatch](https://ai.meta.com/research/publications/copycatch-stopping-group-attacks-by-spotting-lockstep-behavior-in-social-networks/) | WWW | Graf Facebook + serangan sintetis | Bipartite core koheren waktu; MapReduce | Sintetis dan audit manual | 22 klaster audit 100% Like curang | Dua mode | Inti lockstep StarScout; tanpa jenis event |
| [Hooi et al. (2016), FRAUDAR](https://bhooi.github.io/papers/fraudar_kdd16.pdf) | KDD | Injeksi Amazon; Twitter 1,47 miliar follow | Densest subgraph anti-kamuflase; jaminan ½ | Injeksi; cek manual | Blok 4031×4313 densitas 68% | Dua mode | Bukan tensor |
| [Shin et al. (2016), M-Zoom](https://www.cs.cmu.edu/~kijungs/papers/mzoomPKDD2016.pdf) | ECML PKDD | Delapan tensor sampai 483 juta tuple | Greedy N-way; jaminan 1/N | Intrusi dan injeksi | Sampai 114× lebih cepat; AUC 0,98 pada TCP | Batch in-memory | Alat kandidat K5; jenis event tidak dipakai sebagai mode |
| [Shin et al. (2017), D-Cube](https://www.cs.cmu.edu/~kijungs/papers/dcubeWSDM2017.pdf) | WSDM | Tensor sampai 2,6 TB | Out-of-core, MapReduce; jaminan 1/N | Intrusi | AUC 0,987 AirForce, 0,930 DARPA | Evaluasi intrusi | Alat kandidat K5 |
| [Shin et al. (2017), DenseAlert](https://arxiv.org/pdf/1706.03374) | KDD | Yelp, Android, YahooM., TCP | Inkremental pada tensor stream | Injeksi, TCP | AUC 0,924 pada TCP | Sampai 85 GB memori | Keluarannya deteksi, bukan fitur classifier |
| [Ban et al. (2019), ISG+D-Spot](https://arxiv.org/pdf/1810.06230) | WWW | Sembilan dataset | Information sharing graph; jaminan ≥½ | Injeksi, Yelp, Amazon | AUC sintetis 0,9843–1,0000 | Kode tidak tersedia | Blok padat pada sebagian mode, risiko utama tensor per menit |
| [Zhang et al. (2021), AugSplicing](https://arxiv.org/pdf/2012.02006) | AAAI (per arXiv) | Yelp, BeerAdvocate, app-install, Wi-Fi | Penyambungan blok pada stream | Injeksi | Sampai 320× lebih cepat | Waktu berbasis hari | Granularitas berbeda |
| [Jiang et al. (2025), Dupin](https://arxiv.org/pdf/2504.09311) | PACMMOD (SIGMOD) | Graf fraud | Peeling paralel multi-metrik | Transaksi fraud | Sampai 100× lebih cepat; sampai 94,5% fraud tercegah | Tanpa URL kode | Graf, bukan tensor |
| [Cao et al. (2014), SynchroTrap](https://users.cs.duke.edu/~xwy/publications/SynchroTrap-ccs14.pdf) | CCS | Facebook, Instagram | Klaster aksi sinkron | Inspeksi sampel manual | >2 juta akun, 1.156 kampanye; P >99% | Tanpa evaluasi train-test | Data privat; sinkron berkelanjutan |
| [Weber & Neumann (2021)](https://arxiv.org/pdf/2103.03409) | arXiv; diajukan ke SNAM | Twitter; jendela 15, 60, 360, 1.440 menit | Komunitas koordinasi dari multi-network; SVM, RF, bagging PU | Akun koordinasi ground truth; RANDOM sebagai unlabeled | Akurasi BPU 0,54–0,95 | Two-fold tanpa group split, walau anggota komunitas berbagi nilai fitur | Preseden langsung fitur koordinasi + PU |
| [Luceri et al. (2024)](https://arxiv.org/pdf/2310.09884) | Web Conference (diterima) | Twitter, lima jejak | Jaringan kemiripan gabungan, Node2Vec, RF, 10-fold | Label operasi informasi | AUC 0,94 per operasi; 0,92 global | Tanpa pemisahan grup yang dinyatakan | Supervised; jaringan kemiripan |
| [Vargas et al. (2020)](https://arxiv.org/pdf/2005.13466) | arXiv | 10 kampanye, >160 juta tweet | RF statistik jaringan koordinasi harian | Atribusi kampanye | F1 0,98 kampanye dikenal, 0,71 lintas kampanye | Banyak false positive lintas kampanye | Unit jaringan harian |
| [Sharma et al., AMDN-HAGE](https://arxiv.org/pdf/2008.11308) | Venue tak terkonfirmasi | Dataset IRA | Temporal point process + GMM | Daftar IO | AP 0,804, AUC 0,898 tanpa supervisi | Menolak suspensi sebagai label koordinasi | Peringatan langsung untuk label proyek |
| [Mannocci et al. (2026)](https://arxiv.org/pdf/2507.12108) | Information Sciences | Twitter, multiplex 5 lapis | Analisis multiplex | Label IO sebagai aproksimasi | Perataan jaringan kehilangan informasi struktur | Label aproksimasi | Analisis lintas aksi sudah ada di Twitter |
| [Mannocci et al. (2026), survei](https://arxiv.org/pdf/2408.01257) | ACM CSUR 58(16) | Survei koordinasi | Tinjauan | Tidak berlaku | Lintas aksi disebut "largely unexplored"; nol kecocokan untuk github, dense subgraph, tensor | Tanpa ground truth objektif | Jembatan dua literatur layak tetapi modest |
| [Iannucci et al. (2026)](https://arxiv.org/abs/2610.37970) **[abstrak saja]** | Preprint arXiv | 26 dataset IO, 7 modalitas | Uji hipotesis per pasangan akun | IO berlabel | Metode umum bisa menandai kelompok walau akun independen | Hanya abstrak | Ko-aktivitas padat bukan bukti koordinasi |

### PU learning dan evaluasi

Kelompok ini menetapkan standar yang harus dipenuhi, bukan sumber kontribusi.

| Peneliti (tahun) | Venue | Data | Metode | Label atau ground truth | Metrik dan hasil | Keterbatasan | Beda dengan proyek ini |
|---|---|---|---|---|---|---|---|
| [Elkan & Noto (2008)](https://cseweb.ucsd.edu/~elkan/posonly.pdf) | KDD | Protein TCDB vs SwissProt | Classifier P vs U, koreksi dengan c | SCAR | AUC 0,9912 ideal; 0,9895 P vs U | SCAR | Baseline wajib; SCAR diragukan bila pelabelan bergantung pada visibilitas |
| [Kiryo et al. (2017), nnPU](https://arxiv.org/abs/1703.00593) | NIPS | MNIST, epsilon, 20News, CIFAR-10 | Risk estimator non-negatif | Dua sampel, π diketahui | Prior terlalu rendah lebih merugikan (MNIST) | π uji 0,40–0,50 | Proyek satu sampel, prior jauh lebih kecil |
| [Bekker et al. (2019), SAR-EM](https://arxiv.org/abs/1809.03207) | ECML PKDD | 8 dataset, label PU simulasi | EM classifier dan propensity | SAR | Lebih baik signifikan dari naive, KM2, TIcE (p<0,01); naive kadang mengalahkan SCAR | Label simulasi | Aktivitas dan usia sekaligus prediktor kuat, identifikasi lemah |
| [Bekker & Davis (2020)](https://arxiv.org/abs/1811.04820) | Machine Learning 109(4) | Survei | SCAR, SAR, prior, metrik | Tidak berlaku | Prior tak teridentifikasi tanpa asumsi; F1 tak terestimasi dari data PU | Survei | Prior harus dilaporkan sebagai rentang |
| [Kumar & Lambert (2024), PULSNAR](https://pmc.ncbi.nlm.nih.gov/articles/PMC11622864/) | PeerJ CS 10 | SNAR sintetis, 6 dataset UCI | XGBoost + klaster subtipe | SNAR | Estimator SCAR meleset; TIcE 706,50 menit pada 100.000 unlabeled | Galat di gambar; α ≤5% jarang diuji | Stratum 5–19 (2,44%) berada di wilayah kurang diuji |
| [Wang et al. (2026)](https://proceedings.iclr.cc/paper_files/paper/2026/file/cbffadf96101c42be845d3e275c4b7e9-Paper-Conference.pdf) | ICLR | CIFAR-10, ImageNette, USPS, Letter | Benchmark algoritma PU | Label simulasi | Tanpa pemenang tunggal; metode dua sampel menurun pada satu sampel | Dataset relatif kecil | Tanpa label penegakan nyata |
| [Li et al. (2014)](https://doi.org/10.1109/icdm.2014.47) **[abstrak saja]** | ICDM | Review 500 restoran Shanghai | Collective PU | Review tersaring Dianping sebagai positif | F1 baseline meningkat; angka tak tercatat | Hanya abstrak | Analog terdekat label takedown dalam PU; bukan akun |
| [Dhamnani et al. (2020), Botcha](https://arxiv.org/abs/2103.01428) | OHARS @ RecSys | Log e-commerce, dataset intrusi berbias buatan | RAM, MAM, EAM vs biased SVM | Manusia sebagai positif | m=0: RAM AUC 0,897, biased SVM 0,705 | Data proprietari | Template uji bias buatan |
| [Arp et al. (2022)](https://www.usenix.org/system/files/sec22-arp.pdf) | USENIX Security | 30 makalah keamanan | Telaah 10 pitfall | Tidak berlaku | Sampling bias 60%, data snooping 57%, baseline tidak tepat 20% | Telaah manual | Standar minimum |
| [Pendlebury et al. (2019), TESSERACT](https://www.usenix.org/system/files/sec19-pendlebury.pdf) | USENIX Security | 129 ribu aplikasi Android | Konsistensi waktu, metrik AUT | Label malware | F1 0,91 ke 0,58 dan 0,83 ke 0,32 | Malware | Template lengan temporal |
| [Kapoor & Narayanan (2023)](https://arxiv.org/abs/2207.07048) | Patterns 4(9) | 17 bidang | Taksonomi leakage | Tidak berlaku | L3.2 non-independence; L2 proxy hasil | Angka paper terdampak berbeda antarversi | Dasar istilah |
| [Kaufman et al. (2012)](https://www.cs.umb.edu/~ding/history/470_670_fall_2011/papers/cs670_Tran_PreferredPaper_LeakingInDataMining.pdf) | TKDD 6(4) | KDD-Cup 2008 | Konseptual | Tidak berlaku | ID pasien berurutan sebagai leakage; menghapus ID belum tentu cukup | Medis, tanpa ukuran efek | Menggugurkan kedekatan ID sebagai ide baru |
| [Roberts et al. (2017)](https://www.biometrie.uni-freiburg.de/mitarbeiter/dormann/roberts-et-al-2017-ecography.pdf) | Ecography 40(8) | Simulasi ekologi | Blocked CV | Tidak berlaku | Blok harus jauh lebih besar dari range autokorelasi residual | Ekologi | Resep lebar blok; adaptasi ke ruang ID tidak ditemukan dalam pencarian yang dilakukan |
| [Echeverría et al. (2018), LOBO](https://arxiv.org/pdf/1809.09684) | ACSAC | Twitter >200.000 titik, 14 kelas bot | Leave One Botnet Out | Kelas bot dataset lama | 97,84% split acak, rata-rata 54,88% pada kelas tak terlihat; recall C500 94,29% ke 57,51% | Twitter | Preseden terdekat inti C4 |
| [Hays et al. (2023)](https://arxiv.org/pdf/2301.07015) | WWW | Dataset bot Twitter | Pohon dangkal, leave-one-dataset-out | Label benchmark | Kedalaman ≤4 mendekati SOTA; twibot-2020 balanced accuracy 0,78 ke 0,55 | Unit dataset | Preseden baseline sederhana yang kuat |
| [Liu et al. (2024)](https://arxiv.org/pdf/2410.19364) | arXiv | APIGraph, AndroZoo | Menghapus aplikasi test bervektor identik | Label malware | 10–40% test identik dengan train; peringkat model berbalik | Android | Preseden signature identik |
| [McDermott et al. (2024)](https://arxiv.org/abs/2401.06091) | NeurIPS | Teori dan telaah literatur | AUROC vs AUPRC | Tidak berlaku | AUPRC memihak skor tinggi dan subpopulasi prevalensi tinggi | Tidak khusus PU | Alasan AP wajib per stratum |
| [Roth (2026)](https://arxiv.org/pdf/2604.04199) | arXiv | 2.047 dataset | Pengukuran jenis leakage | Tidak berlaku | GroupKFold vs acak +0,01 AUC pada satu dataset | Penulis tunggal | Penyeimbang: efek split bisa kecil |

## 3. Matriks posisi: tidak ada baris yang mengisi semua kolom, termasuk baris proyek

"Tidak" berarti unsur itu tidak tercantum pada bagian karya yang dibaca. Baris proyek menyatakan status bukti saat ini; "(rencana)" menandai unsur yang dirancang tetapi belum punya hasil.

| Karya | Data GitHub | Jendela 60 menit atau kurang | Hanya stream publik saat inferensi | Status akun kemudian sebagai label | PU atau SAR | Kontrol aktivitas dan usia akun | Split waktu dan klaster | Kurva latensi berbasis menit | Audit desain split |
|---|---|---|---|---|---|---|---|---|---|
| Gong et al. 2019, 2023 (GitSec) | Ya | Tidak | Tidak | Ya | Tidak | Tidak | Tidak | Tidak | Tidak |
| Du et al. 2020 | Ya | Tidak | Ya | Sebagian | Tidak | Tidak | Tidak | Tidak | Tidak |
| He et al. 2026 (StarScout) | Ya | Tidak | Ya | Sebagian | Tidak | Tidak | Tidak | Tidak | Tidak |
| Chidambaram et al. 2025 (BIMBAS) | Ya | Tidak | Sebagian | Tidak | Tidak | Sebagian | Tidak | Tidak | Tidak |
| Golzadeh et al. 2021 (BoDeGHa) | Ya | Tidak | Tidak | Tidak | Tidak | Sebagian | Tidak | Tidak | Tidak |
| Volkova & Bell 2017 | Tidak | Tidak | Sebagian | Ya | Tidak | Tidak | Tidak | Tidak | Tidak |
| Cheng et al. 2015 | Tidak | Tidak | Tidak | Ya | Tidak | Sebagian | Tidak | Tidak | Tidak |
| Kumar et al. 2015 (VEWS) | Tidak | Tidak | Sebagian | Ya | Tidak | Tidak | Sebagian | Tidak | Tidak |
| Seyler et al. 2021 | Tidak | Tidak | Ya | Ya | Tidak | Tidak | Tidak | Tidak | Tidak |
| Zheng et al. 2019 (SAFE) | Tidak | Tidak | Tidak | Ya | Sebagian | Tidak | Tidak | Tidak | Tidak |
| Weber & Neumann 2021 | Tidak | Sebagian | Sebagian | Tidak | Ya | Tidak | Tidak | Sebagian | Tidak |
| Luceri et al. 2024 | Tidak | Tidak | Sebagian | Tidak | Tidak | Tidak | Tidak | Tidak | Tidak |
| Echeverría et al. 2018 (LOBO) | Tidak | Tidak | Tidak | Tidak | Tidak | Tidak | Sebagian | Tidak | Ya |
| Hays et al. 2023 | Tidak | Tidak | Tidak | Tidak | Tidak | Tidak | Sebagian | Tidak | Sebagian |
| Xiao et al. 2015 | Tidak | Tidak | Tidak | Ya | Tidak | Tidak | Sebagian | Tidak | Sebagian |
| **Proyek ini (pilot satu jam)** | Ya | Ya (satu jam; sub-jam rencana) | Ya | Ya | Tidak (rencana) | Ya (satu jam) | Sebagian (grup dan blok ID; waktu rencana) | Tidak (rencana) | Sebagian (blok ID; lengan lain rencana) |

Du et al. dan He et al. memakai status hanya untuk pengukuran atau validasi. BIMBAS memakai API per akun secara default, dengan mode offline dari daftar event; BIMBAS dan BoDeGHa melaporkan performa per jumlah event atau komentar tanpa kontrol usia. Cheng et al. mencocokkan aktivitas, tidak usia. VEWS memakai split waktu tanpa klaster; LOBO dan Hays menahan kelompok tanpa split waktu maju; Xiao et al. menguji satu bulan berikutnya dengan klaster sebagai unit klasifikasi. SAFE memodelkan right-censoring, bukan PU. Weber & Neumann memakai jendela 15–1.440 menit untuk membangun jaringan koordinasi, bukan sebagai jendela observasi pendek, dan akurasinya per ukuran jendela bukan kurva latensi.

**Kolom kosong bukan bukti kontribusi.** GitSec paling dekat pada label, Weber & Neumann pada koordinasi dan PU, LOBO pada audit split, dan Cheng et al. pada kontrol aktivitas. Kombinasi sel hanya bernilai bila hasilnya mengubah kesimpulan, dan baris proyek sendiri masih kosong pada PU, split waktu dan kurva menit.

## 4. Verdict per klaim: C1 sudah dilakukan dalam bentuk luas, C2 sampai C4 harus menyempit

### Bukti pilot: satu jam pengembangan, tidak dipraregistrasi

Semua angka di subbagian ini berasal dari **satu jam data pengembangan yang tidak dipraregistrasi**. Karena jam ini dipakai untuk mengembangkan fitur dan split, angkanya adalah petunjuk arah, bukan estimasi generalisasi. Data: GH Archive 2024-04-01 15:00–15:59 UTC, 272.191 event, 64.864 actor ID, 315 di antaranya bersufiks `[bot]`. Di antara akun lain, 52,5% tepat punya 1 event; median 1, p90 5, p99 26, maksimum 6.774. Status dicek pada 2026-11-10 lewat GitHub GraphQL API dengan legacy global ID turunan ID numerik; pada sampel 1.000 akun, seluruh 116 akun yang tidak ter-resolve juga menghasilkan 404 dari REST `GET /user/{id}`.

| Stratum event per jam (tanpa `[bot]`) | Akun | Hilang | Tingkat | Catatan |
|---|---|---|---|---|
| 1 event | 250 (sampel) | 2 (dihitung) | 0,8% | Interval Wilson 95%: 0,2–2,9% (dihitung) |
| 2–4 event | 250 (sampel) | 6 (dihitung) | 2,4% | Interval Wilson 95%: 1,1–5,1% (dihitung) |
| 5–19 event | 7.576 | 185 | 2,44% | Hitung penuh |
| ≥20 event | 858 | 334 | 38,9% | Hitung penuh |
| ≥5 event | 8.434 | 519 | 6,15% | Hitung penuh |

**Tingkat hilang naik tajam dengan aktivitas, dan ID numerik (proxy usia) sangat informatif.** Median persentil `actor_id` dalam kohort adalah 0,943 untuk akun hilang dan 0,473 untuk akun yang masih ada. Dengan asumsi ID tinggi berarti akun lebih baru, 50% ID tertinggi memuat 93,1% positif; 10% tertinggi memuat 68,0% dengan tingkat 41,8%; 5% tertinggi memuat 46,6% dengan tingkat 57,3%; 1% tertinggi hanya memuat 4,2% dengan tingkat 25,9%. Pola ini tidak monoton, dan batch pembuatan terlihat: satu blok ID lebar 5.000 berisi 61 dari 62 akun hilang, dan satu blok lebar 20.000 berisi 82 dari 88. Arah ini berlawanan dengan GitSec, yang positifnya turun dari 21,50% seluruh crawl ke 1,92% pada akun ≥3 event, tetapi kelas positifnya berbeda ([Gong et al. 2023](https://aaltodoc.aalto.fi/bitstreams/9095077c-3398-4c13-9f15-5130dbe9b9b7/download)).

Tabel berikut berasal dari out-of-fold HistGradientBoosting setelan mendekati default, 5-fold GroupKFold atas akun yang terhubung lewat repo kecil bersama atau pesan commit bersama, dengan `actor_id` mentah sebagai fitur.

| Model (pilot satu jam) | AP semua ≥5 | AP 5–19 | AP ≥20 |
|---|---|---|---|
| Base rate (dihitung) | 0,0615 | 0,0244 | 0,3893 |
| Peringkat `n_events` | 0,4029 | 0,0305 | 0,5543 |
| `actor_id` saja | 0,6166 | 0,0849 | 0,9352 |
| `n_events` + `actor_id` | 0,6726 | 0,0738 | 0,9423 |
| Perilaku + `actor_id` | 0,7386 | 0,1793 | 0,9764 |
| + konten | 0,7405 | 0,2063 | 0,9766 |
| + proxy koordinasi sederhana | 0,7383 | 0,2050 | 0,9783 |

Interval 95% group-bootstrap untuk selisih AP: perilaku+ID dikurangi `n_events`+ID adalah **+0,0651 [0,0382; 0,0927]** (semua), **+0,1045 [0,0595; 0,1594]** (5–19), dan **+0,0320 [0,0124; 0,0588]** (≥20). Proxy koordinasi dikurangi konten adalah −0,0022 [−0,0070; 0,0024], −0,0014 [−0,0177; 0,0156], dan +0,0015 [−0,0004; 0,0039]. Proxy ini adalah pesan commit bersama, repo bersama dan template nama repo, **bukan dense-block mining**.

Audit berikut memakai blok ID numerik lebar tetap dan StratifiedGroupKFold, dirata-rata atas 3 seed. Baseline adalah floor(log2 event) ditambah 12 bin usia dari ID numerik. Kolom terakhir adalah AUC di dalam sel aktivitas dan usia kasar yang sama.

| Set fitur (pilot satu jam) | Split | AP semua ≥5 | AP 5–19 | AP ≥20 | AUC dalam sel |
|---|---|---|---|---|---|
| Baseline | Acak | 0,690 | 0,090 | 0,918 | Tidak dilaporkan |
| Baseline | Blok 5.000 | 0,694 | 0,090 | 0,929 | Tidak dilaporkan |
| Baseline | Blok 20.000 | 0,693 | 0,084 | 0,934 | Tidak dilaporkan |
| Baseline | Blok 100.000 | 0,689 | 0,084 | 0,934 | Tidak dilaporkan |
| + 48 fitur perilaku | Acak | 0,767 | 0,251 | 0,979 | 0,821 |
| + 48 fitur perilaku | Blok 5.000 | 0,763 | 0,223 | 0,979 | 0,816 |
| + 48 fitur perilaku | Blok 20.000 | 0,753 | 0,197 | 0,979 | 0,786 |
| + 48 fitur perilaku | Blok 100.000 | 0,749 | 0,196 | 0,975 | 0,750 |
| + 28 fitur perilaku (tanpa keluarga temporal, repo, nama repo) | Acak | 0,749 | 0,170 | 0,976 | 0,791 |
| + 28 fitur perilaku | Blok 5.000 | 0,746 | 0,144 | 0,977 | Tidak dilaporkan |
| + 28 fitur perilaku | Blok 20.000 | 0,739 | 0,129 | 0,977 | 0,780 |
| + 48 perilaku + proxy koordinasi | Acak | 0,767 | 0,258 | 0,980 | Tidak dilaporkan |
| + 48 perilaku + proxy koordinasi | Blok 20.000 | 0,755 | 0,204 | 0,979 | Tidak dilaporkan |
| + 48 perilaku + tetangga ID (±100, ±1.000, ±5.000) | Blok 20.000 | 0,750 | 0,181 | 0,979 | Tidak dilaporkan |

**Baseline tidak sensitif terhadap split, jadi sensitivitas datang dari fitur perilaku.** Di stratum 5–19 event, tambahan AP perilaku di atas baseline adalah +0,161 pada split acak dan +0,112 pada blok 100.000, sehingga split acak melebih-lebihkan tambahan itu sekitar 44%. AUC dalam sel turun dari 0,821 ke 0,750. Stratum ≥20 hampir tidak bergerak dan sudah tertangkap baseline. Tabel ini rata-rata 3 seed tanpa interval, jadi selisih kecil antarbaris tidak boleh dibaca sebagai efek. Membatasi perilaku ke 28 fitur memberi bukti campuran: penurunan AUC dalam sel dari acak ke blok 20.000 lebih kecil (0,791 ke 0,780, dibanding 0,821 ke 0,786), tetapi tambahan AP 5–19 atas baseline menyusut lebih besar secara relatif (+0,080 ke +0,045). Fitur tetangga ID tidak menambah apa pun setelah perilaku masuk.

**Skema pengelompokan berantai tidak boleh dikutip sebagai bukti leakage.** Merantai ID atau menggabungkan blok dengan grup artefak bersama menghasilkan satu grup raksasa sehingga satu fold memegang sebagian besar positif, misalnya 4.457 akun dengan 425 dari 519 positif, 3.557 akun dengan 376 positif, dan 2.096 akun dengan 297 positif. Penurunan performa pada skema itu tidak bisa ditafsirkan sebagai leakage. Bahan laporan ini tidak memuat ukuran grup terbesar pada skema GroupKFold artefak bersama di atas, jadi skema itu pun perlu diperiksa untuk degenerasi yang sama.

**Bahan pilot untuk laporan ini tidak memuat hasil apa pun tentang** PU atau SAR, split temporal-forward, pengecualian batch, signature aktivitas identik, kurva latensi 60 sampai 5 menit, dense-block mining yang sebenarnya, dan pemodelan akun dengan kurang dari 5 event, yaitu sekitar 87% akun non-`[bot]` di jam itu.

### C1: label retrospektif level akun di GitHub dengan ID numerik

**Verdict: sudah dilakukan dalam bentuk luasnya; C1 seperti tertulis tidak bisa diklaim.** Catatan yang hanya membaca abstrak menilai C1 sebagian gugur, sedangkan catatan yang membaca full text GitSec menunjukkan intinya sudah dilakukan; laporan ini mengikuti pembacaan full text.

| Karya terdekat | Yang sama | Perbedaan konkret |
|---|---|---|
| [GitSec, CIKM 2019](https://user.informatik.uni-goettingen.de/~ychen/papers/GitSec-CIKM19.pdf) dan [TKDE 2023](https://aaltodoc.aalto.fi/bitstreams/9095077c-3398-4c13-9f15-5130dbe9b9b7/download) | Status platform GitHub sebagai label latih level akun, lookup ID numerik, event GH Archive | Positif adalah API 200 dengan web 404; API 404, yang menjadi positif proyek ini, dibuang. Jeda 3–12 minggu vs sekitar 31 bulan; histori 2015–Mei 2018 vs satu jam; web 200 negatif vs unlabeled; split acak |
| [He et al. 2026](https://cmustrudel.github.io/papers/icse2026fakestars.pdf) | Status API akun dibandingkan baseline acak | Validasi, bukan target; lookup memakai login; jeda bervariasi sampai sekitar 5,5 tahun |
| [Du et al. 2020](https://personal.utdallas.edu/~shao/papers/du_acsac20.pdf) | Halaman 404 sebagai tanda ban, dibedakan lewat kehadiran di GH Archive | Pengukuran pasca-deteksi; memakai login; 4,19% ter-ban |
| [Volkova & Bell 2017](https://web.archive.org/web/20240111165300id_/https://ojs.aaai.org/index.php/ICWSM/article/download/14874/14724) | Prediksi akun yang kelak deleted atau suspended | Twitter; status bisa dipisah; jeda 1–4 bulan; evaluasi seimbang |
| [Klausen et al. 2016](https://arxiv.org/pdf/1610.06242) | Label status kemudian dan user ID stabil lintas ganti nama | Twitter; ID untuk menautkan profil |
| [Saeed et al. 2022](https://arxiv.org/pdf/2112.00443) | Status sebagai validasi | Reddit; 403 dan 404 memisahkan suspensi dan hapus |

Yang tersisa adalah API 404 sebagai kelas positif, horizon tetap sekitar 31 bulan, input satu jendela pendek, dan akun yang bertahan sebagai unlabeled. Kombinasi ini tidak ditemukan dalam pencarian yang dilakukan. Keunggulan atas He et al. dan Du et al. hanya pada penanganan rename, karena GitSec sudah menghindarinya secara konstruksi. Lookup ID numerik sendiri adalah [fitur API yang terdokumentasi](https://docs.github.com/en/rest/users/users), jadi praktik yang benar, bukan kontribusi. Studi churn seperti [Bao et al.](https://doi.org/10.1109/tse.2019.2918536) (abstrak saja) memodelkan orang yang berhenti berkontribusi saat akunnya tetap ada, sehingga bukan pembanding C1.

### C2: dense block lintas jenis event sebagai fitur classifier PU, dengan split per klaster

**Verdict: bukan metode baru.** Setiap bahannya punya preseden, dan yang tersisa hanya kombinasi terapan.

| Karya terdekat | Yang sama | Perbedaan konkret |
|---|---|---|
| [Weber & Neumann 2021](https://arxiv.org/pdf/2103.03409) | Koordinasi berjendela waktu lintas jenis interaksi, fitur akun dan komunitas, bagging PU | Twitter; komunitas dari jaringan inferensi, bukan tensor; positif adalah akun koordinasi berlabel; two-fold tanpa group split |
| [Luceri et al. 2024](https://arxiv.org/pdf/2310.09884) | Lima jejak digabung, embedding ke RF | Twitter; jaringan kemiripan; supervised; 10-fold tanpa grup |
| [Vargas et al. 2020](https://arxiv.org/pdf/2005.13466) | Fitur jaringan koordinasi ke classifier | Unit jaringan harian; supervised |
| [He et al. 2026](https://cmustrudel.github.io/papers/icse2026fakestars.pdf) | CopyCatch pada GH Archive; akun lockstep terhapus 48,83% | Hanya star; Δt 30 hari; tanpa classifier hilir, PU, atau grup |
| [M-Zoom](https://www.cs.cmu.edu/~kijungs/papers/mzoomPKDD2016.pdf), [DenseAlert](https://arxiv.org/pdf/1706.03374), [ISG](https://arxiv.org/pdf/1810.06230) | Dense block N-way dengan mode kategorikal | Jenis event bukan mode; bukan GitHub; keluaran untuk deteksi |

Dense block pada tensor multi-atribut sudah standar, fitur koordinasi dalam classifier sudah dilakukan, PU pada fitur koordinasi sudah dilakukan di satu studi Twitter, asosiasi lockstep dengan penghapusan sudah ditunjukkan StarScout, dan split per kelompok sudah mapan lewat [LOBO](https://arxiv.org/pdf/1809.09684), [TwiBot-22](https://arxiv.org/pdf/2206.04564) dan [GroupKFold](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html). Dense block lintas jenis event pada GitHub sebagai fitur PU untuk target akun hilang tidak ditemukan dalam pencarian yang dilakukan. Pilot tidak menguji C2 yang sebenarnya, tetapi proxy koordinasi yang lebih murah tidak memberi tambahan terukur pada split mana pun, sehingga hasil negatif cukup mungkin. Dua risiko desain perlu dicatat: tensor per menit dari satu jam hanya menangkap ledakan di dalam batas file, sedangkan StarScout memakai Δt 30 hari, dan blok yang padat hanya pada sebagian mode adalah kegagalan yang disorot [Ban et al.](https://arxiv.org/pdf/1810.06230).

### C3: kurva deteksi dini saat jendela dipendekkan dari 60 ke 5 menit

**Verdict: bertahan hanya sebagai kontribusi evaluasi, dan belum ada hasil pilot untuk klaim ini.** Kurva performa terhadap jumlah observasi sudah mapan setidaknya sejak 2015, jadi yang tersisa hanya satuan menit pada level akun dengan target akun hilang.

| Karya terdekat | Yang sama | Perbedaan konkret |
|---|---|---|
| [Chidambaram et al. 2025](https://decan.lexpage.net/files/JSS-2025.pdf), [2024](https://natarajan-chidambaram.github.io/papers/MSR2024_RABBIT_A_tool_for_identifying_bot_accounts_based_on_their_recent_GitHub_event_history.pdf) | Performa vs jumlah event di GitHub | Satuan event; API per akun; target bot |
| [Golzadeh et al. 2021](https://arxiv.org/pdf/2010.03303) | F1 vs jumlah komentar | Satuan komentar per repo |
| [VEWS](https://arxiv.org/pdf/1507.01272), [Cheng et al. 2015](https://arxiv.org/pdf/1504.00680) | Performa vs k edit atau N post dengan label ban | Aksi; log lengkap |
| [Seyler et al. 2021](https://web.archive.org/web/20260502120329id_/https://ojs.aaai.org/index.php/ICWSM/article/download/18091/17894) | Performa vs jumlah teks dan jarak ke suspensi | Sengaja menolak bin waktu karena bin tidak seimbang |
| [Liu & Wu 2018](https://web.archive.org/web/20260305040253/https://ojs.aaai.org/index.php/AAAI/article/view/11268), [BiGCN](https://arxiv.org/pdf/2001.06362) | Deadline berbasis menit | Item, bukan akun |
| [SAFE 2019](https://arxiv.org/pdf/1809.04683) | Deteksi dini berindeks waktu | Langkah 3 hari |

Kurva berbasis menit pada level akun untuk target akun hilang tidak ditemukan dalam pencarian yang dilakukan. Reviewer bisa menganggapnya robustness check biasa kecuali ada temuan substantif, misalnya lantai performa yang berguna pada 5 menit. Kata "dini" di sini berarti jendela observasi pendek, bukan awal masa hidup akun, dan makna ini harus ditulis eksplisit. Karena [latensi Events API tercatat 30 detik sampai 6 jam](https://docs.github.com/en/rest/activity/events), hasilnya adalah event-time window pada data arsip, bukan deteksi real-time. Reviewer juga bisa menunjuk studi media sosial yang menyimpulkan panjang jendela menentukan pola koordinasi yang terdeteksi ([Panayiotou et al. 2026](https://arxiv.org/abs/2609.21959), abstrak saja). Satu preprint yang bisa menyentuh C3, [Early Screening of Fake Social Media Accounts](https://doi.org/10.20944/preprints202608.0136.v1), belum bisa dibuka.

### C4: audit desain split untuk prediksi akun hilang di GitHub

**Verdict: harus dipersempit.** Bentuk umumnya, yaitu mengukur inflasi performa akibat desain split, sudah dilakukan pada bot, malware dan ML klinis ([LOBO](https://arxiv.org/pdf/1809.09684); [TESSERACT](https://www.usenix.org/system/files/sec19-pendlebury.pdf); [Saeb et al. 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5441397/)). Kedekatan ID sebagai saluran leakage juga sudah dibahas Kaufman et al.

| Karya terdekat | Yang sama | Perbedaan konkret |
|---|---|---|
| [LOBO 2018](https://arxiv.org/pdf/1809.09684) | Menahan kelompok bot dan mengukur selisih dengan split acak | Twitter; unit botnet berlabel; tanpa lengan temporal |
| [Hays et al. 2023](https://arxiv.org/pdf/2301.07015) | Model dangkal mendekati SOTA; tanggal pembuatan sebagai artefak koleksi | Unit dataset; tanpa ID numerik |
| [Liu et al. 2024](https://arxiv.org/pdf/2410.19364) | Vektor fitur identik sebagai unit leakage | Aplikasi Android |
| [Xiao et al. 2015](https://theory.stanford.edu/~dfreeman/papers/clustering.pdf) | Batch registrasi; recall turun 0,90 ke 0,72 pada bulan berikutnya | Batch sebagai unit klasifikasi, bukan variabel split |
| [Kaufman et al. 2012](https://www.cs.umb.edu/~ding/history/470_670_fall_2011/papers/cs670_Tran_PreferredPaper_LeakingInDataMining.pdf) | ID berurutan sebagai leakage | Medis; tanpa ukuran efek |
| [TESSERACT 2019](https://www.usenix.org/system/files/sec19-pendlebury.pdf) | Inflasi akibat pengabaian waktu | Malware; bukan akun |

Audit desain split pada data akun GitHub dengan kedekatan ID numerik dan signature aktivitas identik sebagai unit pengelompokan tidak ditemukan dalam pencarian yang dilakukan. Pilot baru mengisi satu lengan pada satu jam. **Penurunan performa di bawah pengecualian batch menggabungkan leakage dengan pergeseran distribusi yang nyata, dan satu jam tidak bisa memisahkan keduanya.** Besaran efek di literatur juga berkisar dari +0,01 AUC ([Roth 2026](https://arxiv.org/pdf/2604.04199)) sampai selisih recall 36,78 poin ([LOBO](https://arxiv.org/pdf/1809.09684)), jadi proyek harus melaporkan efeknya sendiri, bukan meminjam.

## 5. Posisi novelty: lima kandidat bertahan dalam bentuk sempit, sebagai kontribusi empiris

**Proyek ini memberi kontribusi empiris dan evaluasi, bukan algoritma baru.** Semua unsur metodenya diambil dari literatur; nilainya terletak pada pengukuran yang jujur atas masalah label yang sulit. Saat ini K2 dan K3 paling kuat karena sudah punya bukti awal, K1 bergantung pada validitas label, K4 belum punya data, dan K5 cukup mungkin negatif.

| Kandidat | Verdict | Alasan singkat |
|---|---|---|
| K1: prediksi API 404 pada ID numerik, horizon sekitar 31 bulan, jendela pendek, survivor unlabeled | Bertahan, sempit | Kombinasi spesifik; tugasnya transfer dari Twitter dan label status sudah ada di GitSec |
| K2: audit desain split (C4 yang dipersempit) | Bertahan, sempit | Ide umum mapan; spesifik GitHub dengan kedekatan ID sebagai unit grup |
| K3: kontrol aktivitas dan usia lewat peringkat dalam sel | Bertahan sebagai desain evaluasi | Pencocokan aktivitas sudah ada; bukti pilot paling informatif |
| K4: kurva latensi menit pada kohort tetap dan deployable | Bertahan bersyarat | Belum ada hasil; nilainya tergantung temuan |
| K5: ablation fitur koordinasi lintas jenis event | Bertahan hanya sebagai uji hipotesis | Metodenya tidak baru; hasil nol masuk akal |
| Dataset terbuka terpseudonimisasi | Artefak pendukung, bukan klaim novelty | Dataset sejenis ada; satu jam terlalu kecil |
| Fitur tetangga ID, coarsening fitur sebagai pertahanan | Gugur | Pilot tidak mendukung; jangan diajukan |

### K1: prediksi akun hilang dari jendela pendek

> Studi ini memprediksi hilangnya akun GitHub, didefinisikan sebagai respons 404 pada ID numerik yang tahan lama sekitar 31 bulan setelah observasi, dari satu jendela pendek event publik, dengan akun yang masih ada diperlakukan sebagai unlabeled. Kombinasi ini tidak ditemukan dalam pencarian yang dilakukan. GitSec sudah memakai status platform GitHub sebagai label latih dengan lookup ID numerik, dengan kelas positif berbeda (API 200 dan web 404), dan target serupa sudah dipelajari di Twitter.

Yang harus ditunjukkan: replikasi di banyak jam dengan horizon yang disamakan, perbandingan PU terhadap model naive, cek silang API dan web pada sampel lebih besar, dan definisi eksplisit variabel laten y (Bagian 6). Hindari kata "deleted or suspended" dan "abuse".

### K2: audit desain split

> Kami mengukur seberapa besar desain split mengubah performa terukur pada prediksi akun hilang di GitHub, memakai kedekatan ID numerik dan signature aktivitas identik sebagai unit pengelompokan, pada split acak, grup artefak bersama, temporal-forward, dan temporal-forward dengan pengecualian batch. Audit semacam ini pada data akun GitHub tidak ditemukan dalam pencarian yang dilakukan. Kedekatan ID sebagai saluran leakage sudah dibahas Kaufman et al., dan penurunan performa memuat leakage sekaligus pergeseran distribusi.

Yang harus ditunjukkan: keempat lengan pada banyak jam, diagnosis ukuran grup dan porsi positif per fold, interval bootstrap, dan performa pada bagian test yang tidak bertetangga dengan train sebagaimana [Liu et al.](https://arxiv.org/pdf/2410.19364) untuk memisahkan memorization dari generalisasi. Angka 44% dari pilot tidak boleh dijadikan temuan.

### K3: kontrol aktivitas dan usia

> Kami menguji apakah fitur perilaku masih memberi peringkat yang berguna di antara akun dengan aktivitas dan usia kasar yang sama. Pencocokan aktivitas sudah digunakan pada forum daring; kontrol gabungan aktivitas dan usia untuk prediksi akun hilang di GitHub tidak ditemukan dalam pencarian yang dilakukan.

Preseden terdekat adalah [Cheng et al.](https://arxiv.org/pdf/1504.00680), dengan AUC turun dari 0,87 ke 0,82 setelah pencocokan aktivitas; pelaporan per kuartil aktivitas juga muncul pada [preprint kecil Katyal 2026](https://arxiv.org/pdf/2606.26127). Yang harus ditunjukkan: validasi ID numerik terhadap `created_at` pada sampel, definisi sel sebelum melihat data baru, cara agregasi AUC antarsel, dan interval pada split blok ID. Sumber peer-reviewed tentang alokasi ID GitHub tidak ditemukan dalam pencarian yang dilakukan, jadi ID sebagai proxy usia tetap asumsi yang harus diuji.

### K4: kurva latensi berbasis menit pada dua kohort

> Kami melaporkan performa per event-time window dari 60 sampai 5 menit pada kohort tetap dan kohort deployable yang dibentuk hanya dari event yang sudah terlihat. Kurva berbasis menit pada level akun dengan target akun hilang tidak ditemukan dalam pencarian yang dilakukan; kurva berbasis jumlah aksi sudah mapan.

Kohort tetap mengukur hilangnya informasi, tetapi seleksinya memakai aktivitas masa depan; kohort deployable menjawab pertanyaan operasional. Yang harus ditunjukkan: baseline aktivitas dan usia pada setiap jendela, stratifikasi per jumlah event, kurva untuk kedua kohort, dan temuan substantif, karena kurva menurun saja tidak cukup.

### K5: ablation fitur koordinasi lintas jenis event

> Kami menguji hipotesis bahwa fitur koordinasi lintas jenis event menambah nilai di atas fitur perilaku akun untuk prediksi akun hilang. Hipotesis ini dapat gagal, dan hasil nol akan dilaporkan.

Yang harus ditunjukkan: dense-block mining sebenarnya (misalnya [M-Zoom](https://github.com/kijungs/mzoom) atau [D-Cube](https://github.com/kijungs/dcube)), bukan proxy; fitur hanya dari event sebelum cutoff dan blok di-mining ulang per jendela latih, karena fitur graf yang dihitung pada seluruh graf membocorkan edge masa depan ([Khaleghpour & McKinney](https://arxiv.org/pdf/2603.06632)); perbandingan berpasangan terhadap perilaku saja pada split yang sama; dan jumlah positif di dalam blok yang cukup untuk daya uji.

### Dataset terbuka terpseudonimisasi

> Kami merilis tabel akun terpseudonimisasi berisi fitur dan label akun hilang untuk jam yang diamati, sebagai artefak replikasi.

Ini bukan klaim novelty: [dataset GitSec tercatat 10.649.574 akun](https://raw.githubusercontent.com/chenyang03/developers/master/README.md), dan [StarScout merilis data](https://doi.org/10.5281/zenodo.17009693). Pseudonimisasi juga rapuh, karena urutan event masih bisa ditautkan kembali ke GH Archive publik (inferensi). Rilis harus menghapus login, email dan ID mentah, mempertimbangkan bahwa label "hilang" pada akun orang bisa dibaca sebagai tuduhan, dan mematuhi [syarat open access AUP GitHub](https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies).

### Praktik standar yang tidak boleh diklaim

Label status platform, lookup ID numerik, target deleted atau suspended, kedekatan ID sebagai leakage, GroupKFold atau StratifiedGroupKFold, split waktu, holdout sekali buka, keseimbangan kelas realistis, baseline kuat, gradient boosting, MLP, regresi logistik, Optuna, MLflow, AP, precision at k, bootstrap interval, SCAR, SAR, PU bagging, Elkan–Noto, dense block, CopyCatch, fitur koordinasi dalam classifier, analisis lintas aksi, dan kurva performa terhadap jumlah observasi adalah praktik atau gagasan yang sudah ada ([Arp et al.](https://www.usenix.org/system/files/sec22-arp.pdf); [TESSERACT](https://www.usenix.org/system/files/sec19-pendlebury.pdf); [Bekker et al.](https://arxiv.org/abs/1809.03207)). Semua boleh dipakai, tidak satu pun boleh diklaim sebagai kontribusi.

**Frasa "tidak ditemukan dalam pencarian yang dilakukan" memiliki batas nyata.** Pencarian 2026-11-10 memakai arXiv API, OpenAlex, WebSearch dan penelusuran sitasi GitSec, Du dan He. DBLP gagal, Semantic Scholar sebagian besar kena rate limit, Crossref terbatas, ACM DL, IEEE Xplore, Google Scholar dan prosiding MSR tidak dicari langsung, basis data berbahasa Mandarin tidak dicari, dan penyaringan dilakukan pada judul dan abstrak. GitSec sendiri muncul lewat satu kueri OpenAlex, sebagai pengingat bahwa karya yang sangat relevan bisa terlewat.

## 6. Validitas label: 404 berarti akun hilang, bukan suspensi

**"Akun hilang" berarti satu hal operasional: ID numerik aktor dalam jendela tidak lagi ter-resolve pada pemeriksaan 2026-11-10, sekitar 31 bulan setelah jendela.** Istilah ini tidak berarti akun melanggar aturan, tidak berarti akun disuspensi, dan tidak menyatakan kapan akun hilang dalam rentang 31 bulan itu. Rename tidak terhitung hilang, karena endpoint memakai ["durable user ID"](https://docs.github.com/en/rest/users/users), sedangkan [login lama bisa diklaim orang lain](https://docs.github.com/en/account-and-profile/concepts/username-changes) dan [nama akun terhapus tersedia lagi setelah 90 hari](https://docs.github.com/en/account-and-profile/concepts/account-management).

| Pertanyaan | Yang diketahui | Yang tidak diketahui |
|---|---|---|
| Apa arti API 404? | Dokumentasi hanya mencantumkan 200 dan 404, tanpa menyebut suspended atau deleted ([REST](https://docs.github.com/en/rest/users/users)); 451 hanya untuk [repo dan gist](https://developer.github.com/changes/2016-03-17-the-451-status-code-is-now-supported/) | Campuran penyebabnya |
| Apakah akun disuspensi menjadi API 404? | Data 2018 GitSec: akun diblokir API 200 dan web 404, akun hapus sendiri API 404. [Squires 2022](https://www.jessesquires.com/blog/2022/04/19/github-suspending-russian-accounts/): profil akun disuspensi 404 di web. [ToS](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service) menyebut profil dihapus dalam 90 hari setelah terminasi | Perilaku API 2026 tidak terdokumentasi |
| Apakah API 200 dengan web 404 masih muncul? | Pilot satu jam: 0 dari 199 akun API-present (batas atas 95% sekitar 1,5%; sampel kecil dan purposif) | Prevalensi pada populasi |
| Seberapa cocok API dan web pada akun hilang? | Pilot: 59 dari 60 akun API-hilang web 404, 1 web 200 | Sebab satu kasus itu; login diklaim ulang adalah hipotesis |
| Berapa porsi suspensi di antara 404? | [Data transparansi GitHub](https://raw.githubusercontent.com/github/transparency/main/data/appeals_and_other_reinstatements/README.md) memisahkan hidden dan restricted, dan mengecualikan spam, phishing, malware | Tidak diketahui. Cek silang pilot tidak menjawab ini |
| Apa yang terjadi pada objek akun hilang? | Pilot: 13 dari 519 akun hilang (2,5%) punya komentar, issue, atau PR di repo orang lain, vs 2.027 dari 7.915 akun ada (25,6%). Dari 13 itu, 7 beratribusi ke `ghost`, konsisten dengan penghapusan akun, 6 objek tidak tersedia, 0 masih beratribusi ke akun. Kontrol 150 akun ada: 142 masih beratribusi, 8 tidak tersedia | 97,5% akun hilang tidak bisa diperiksa dengan cara ini; `ghost` tidak menunjukkan siapa yang menghapus |
| Kapan akun hilang, dan bisakah berbalik? | Hanya sebelum 2026-11-10. [Banding bisa sampai enam bulan](https://docs.github.com/en/site-policy/acceptable-use-policies/github-appeal-and-reinstatement); di Twitter [2,86% akun suspended aktif lagi](https://arxiv.org/pdf/2111.12395) | Waktu hilang; reversibilitas pada snapshot tunggal |

Semua baris pilot di atas berasal dari **satu jam pengembangan yang tidak dipraregistrasi**. Cek silang memakai permintaan HEAD tanpa autentikasi ke halaman profil publik; 199 akun API-present terdiri atas 19 akun terbaru dengan ≥20 event, 80 akun terbaru dengan kurang dari 20 event, dan 100 akun lebih lama. Hasil 0 dari 199 mengurangi kekhawatiran bahwa kelas positif GitSec tersembunyi dalam jumlah besar di antara akun API-present, tetapi tidak menetapkan berapa persen API 404 yang merupakan suspensi. Mitigasi di literatur hanya sebagian bisa dipakai: Twitter dapat memisahkan status ([Thomas et al.](https://people.eecs.berkeley.edu/~dawnsong/papers/2011%20Suspended%20accounts%20in%20retrospect%20an%20analysis%20of%20Twitter%20spam.pdf)), dan di sana porsi suspensi di antara akun hilang berkisar 8,8% sampai 85,3% antarsampel (dihitung dari [Volkova & Bell](https://web.archive.org/web/20240111165300id_/https://ojs.aaai.org/index.php/ICWSM/article/download/14874/14724)), sehingga angka Twitter tidak bisa dipinjam.

Akun hilang tidak setara dengan akun bermasalah. Sebuah survei 2025 memperingatkan bahwa asumsi "terhapus berarti palsu" keliru ([Dehkordi & Zehmakan](https://arxiv.org/pdf/2507.06541)), AMDN-HAGE menolak suspensi sebagai label koordinasi ([Sharma et al.](https://arxiv.org/pdf/2008.11308)), dan hanya 4,19% akun promosi yang dicurigai Du et al. ter-ban. Karena itu frasa "abuse detection" tidak dipakai untuk proyek ini; istilah yang tepat adalah **prediksi akun hilang** atau account-removal prediction. Definisikan juga y secara eksplisit. Bila y adalah "akun kelak hilang kapan pun" dan s adalah "hilang dalam 31 bulan", maka survivor memang unlabeled, tetapi kerangka survival dengan censoring seperti [SAFE](https://arxiv.org/pdf/1809.04683) menjadi pesaing alami. Bila y adalah "akun bermasalah", positif terkontaminasi penghapusan sukarela dan asumsi dasar PU p(s=1|y=0)=0 gagal. Tingkat 6,15% dan 2,44% adalah p(s=1), bukan prevalensi y.

## 7. Implikasi desain: baseline usia dan aktivitas adalah lawan yang harus dikalahkan

### Baseline wajib

| Baseline | Bentuk | Pilot satu jam (AP semua / 5–19 / ≥20) | Fungsi |
|---|---|---|---|
| Aktivitas saja | Peringkat `n_events`, regresi logistik log event | 0,4029 / 0,0305 / 0,5543 | Uji falsifikasi volume |
| Usia saja | ID mentah dan 12 bin usia | 0,6166 / 0,0849 / 0,9352 (ID mentah) | Mengukur porsi yang dijelaskan usia dan batch |
| Aktivitas + usia kasar | floor(log2 event) + 12 bin usia | 0,690 / 0,090 / 0,918 (split acak) | Lawan utama per stratum dan per split |
| Detektor literatur | RABBIT-ng offline untuk ≥5 event, fitur interval ala Du, signature StarScout untuk WatchEvent, heuristik nama login | Belum diuji | Posisi terhadap SOTA |
| Pembanding PU | Naive, Elkan–Noto, PU bagging, SAR-EM | Belum diuji | Menguji apakah PU memang membantu |

BIMBAS dilatih pada histori sampai 300 event, jadi memberi 5–60 menit adalah pergeseran distribusi yang tidak tercakup evaluasinya; hasilnya harus dilaporkan dengan catatan itu. Baseline yang kuat bukan formalitas: [Hays et al.](https://arxiv.org/pdf/2301.07015) menunjukkan pohon dangkal bisa mendekati SOTA karena artefak koleksi data.

### Stratifikasi

Laporkan selalu per stratum event per jam (1, 2–4, 5–19, ≥20), dengan akun `[bot]` terpisah, dan dalam sel aktivitas-usia. AP gabungan didominasi stratum ≥20, yang memuat 334 dari 519 positif pada base rate 38,9%; [McDermott et al.](https://arxiv.org/abs/2401.06091) menunjukkan AUPRC memihak subpopulasi berprevalensi tinggi, jadi AP gabungan saja menyesatkan. Stratum 5–19 adalah tempat klaim perilaku paling diuji, dan strata di bawah 5 event harus dimodelkan bila proyek ingin bicara tentang mayoritas akun.

### Split

Laporkan empat lengan: acak (hanya sebagai pembanding audit), grup artefak bersama, temporal-forward, dan temporal-forward dengan pengecualian batch, ditambah blok ID lebar tetap dan pengelompokan akun bersignature aktivitas identik. Hindari perantaian grup: laporkan distribusi ukuran grup dan porsi positif per fold, dan tolak skema bila satu fold memegang sebagian besar positif; [dokumentasi StratifiedGroupKFold](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html) mengingatkan stratifikasi bisa memburuk pada grup besar. Pilih lebar blok lewat korelogram residual terhadap jarak ID, mengikuti logika [Roberts et al.](https://www.biometrie.uni-freiburg.de/mitarbeiter/dormann/roberts-et-al-2017-ecography.pdf). Keanggotaan klaster dan fitur hanya boleh dihitung dari data sebelum cutoff, sesuai [Kapoor & Narayanan](https://arxiv.org/abs/2207.07048). Horizon label harus disamakan: satu snapshot status memberi follow-up berbeda bila jam sampel tersebar lintas bulan, sehingga jam harus berdekatan, status dicek berulang, atau horizon disensor ke titik bersama. Tuliskan bahwa penurunan pada pengecualian batch menggabungkan leakage dan pergeseran distribusi.

### Metrik

Metrik utama adalah AP per stratum selalu berdampingan dengan base rate, precision at k dan recall at k pada anggaran tinjauan yang realistis, dan AUC dalam sel. AUROC hanya pelengkap. Tiap jendela di K4 memakai metrik yang sama. ERDE dan F_latency bukan metrik utama, karena pada desain jendela tetap semua akun punya latensi sama sehingga suku latensinya tidak menambah informasi (inferensi; masalah ERDE sendiri dicatat [Trotzek et al.](https://arxiv.org/pdf/1804.07000)); distribusi waktu-ke-deteksi pada precision tetap adalah pelengkap yang lebih tepat. Tangani nilai skor yang sama secara deterministik, terutama pada peringkat `n_events`. Setiap tabel harus menyebut bahwa metrik dihitung terhadap label yang teramati.

### Uji statistik

Pakai paired cluster bootstrap: sampel ulang grup atau blok ID, pertahankan semua akun di dalamnya, hitung metrik kedua model pada sampel ulang yang sama, dan bentuk interval pada selisih ([Field & Welsh](https://doi.org/10.1111/j.1467-9868.2007.00593.x), abstrak saja). Validasi langsung untuk AP pada data klaster tidak ditemukan dalam pencarian yang dilakukan, jadi ini ekstrapolasi yang harus diakui. Laporkan jumlah klaster yang memuat positif dan sensitivitas terhadap klaster terbesar. DeLong dan [Obuchowski](https://doi.org/10.2307/2533958) hanya untuk AUROC. Uji [Demšar](https://www.jmlr.org/papers/volume7/demsar06a/demsar06a.pdf) hanya cocok bila jam diperlakukan sebagai replikasi independen. Tabel audit blok ID di pilot belum punya interval dan harus dilengkapi. Bekukan rancangan sebelum membuka jam baru, karena pilot ini tidak dipraregistrasi, dan buka holdout sekali.

### Penanganan PU/SAR

Setelah y didefinisikan (Bagian 6), perlakukan data sebagai satu sampel, sehingga nnPU dua sampel perlu penyesuaian ([Wang et al.](https://proceedings.iclr.cc/paper_files/paper/2026/file/cbffadf96101c42be845d3e275c4b7e9-Paper-Conference.pdf)). Bandingkan naive, Elkan–Noto, PU bagging dan SAR-EM, karena naive kadang mengalahkan metode SCAR ([Bekker et al.](https://arxiv.org/abs/1809.03207)). Aktivitas dan usia wajar sebagai atribut propensity, tetapi keduanya juga prediktor terkuat, jadi identifikasinya lemah dan estimasi SAR harus diperlakukan sebagai analisis sensitivitas atas beberapa spesifikasi propensity. Prior dilaporkan sebagai rentang dari beberapa estimator, per stratum ([PULSNAR](https://pmc.ncbi.nlm.nih.gov/articles/PMC11622864/)). Lakukan uji semi-sintetis dengan menyembunyikan positif yang diketahui mengikuti propensity berbasis aktivitas, dan audit manual sampel skor tinggi serta skor rendah oleh dua anotator ([Arp et al.](https://www.usenix.org/system/files/sec22-arp.pdf)). Precision terhadap label teramati hanya batas bawah bila positif benar-benar positif, dan batas itu bisa gagal karena penghapusan sukarela.

### Data input dan kepatuhan

GH Archive adalah poller satu halaman atas API yang tertunda, dengan [laporan kehilangan event](https://github.com/igrigorik/gharchive.org/issues/294) yang tidak terukur untuk jam ini, dan [penurunan tajam sejak Mei 2025](https://github.com/igrigorik/gharchive.org/issues/310), jadi replikasi sebaiknya tetap pada jendela 2024 dan tiap jam diperiksa tersendiri. Jendela harus disebut event-time dari `created_at`. Commit email diperlakukan sebagai data pribadi dan dibuang saat ingest. [AUP GitHub](https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies) mengizinkan riset atas informasi publik non-pribadi hanya bila publikasinya open access, syarat yang juga berlaku bagi cek silang web pilot.

## 8. Daftar pustaka dan hal yang wajib dicek sebelum mengutip

Setiap entri ditandai cara membacanya menurut catatan riset: **full text**, **abstrak saja**, atau **metadata saja**; "full text (sebagian)" berarti full text dibuka tetapi hanya bagian tertentu terbaca. Judul lengkap hanya ditulis bila tercatat di catatan riset; untuk entri lain, ambil judul dari DOI atau URL sebelum mengutip.

### Deteksi bot GitHub

- Abdellatif, Wessel, Steinmacher, Gerosa, Shihab (2022). BotHunter. MSR 2022, 6–17. DOI 10.1145/3524842.3527959. [PDF](https://www.ime.usp.br/~gerosa/papers/MSR2022BotHunter.pdf). **full text**
- Bi, Zhu, Wang, Xia, Khan, Pu (2023). BotHawk. arXiv:2307.13386. [PDF](https://arxiv.org/pdf/2307.13386). **full text**
- Chidambaram, Mens, Decan (2024). RABBIT: A tool for identifying bot accounts based on their recent GitHub event history. MSR 2024, 687–691. DOI 10.1145/3643991.3644877. [PDF](https://natarajan-chidambaram.github.io/papers/MSR2024_RABBIT_A_tool_for_identifying_bot_accounts_based_on_their_recent_GitHub_event_history.pdf). **full text**
- Chidambaram, Decan, Mens (2025). A Bot Identification Model and Tool Based on GitHub Activity Sequences. JSS 221, 112287. DOI 10.1016/j.jss.2024.112287. [PDF](https://decan.lexpage.net/files/JSS-2025.pdf). **full text**
- Dey, Mousavi, Ponce, Fry, Vasilescu, Filippova, Mockus (2020). BIMAN. MSR 2020, 209–219. DOI 10.1145/3379597.3387478. [PDF](https://arxiv.org/pdf/2003.03172). **full text**
- Golzadeh, Decan, Legay, Mens (2021). BoDeGHa. JSS 175, 110911. DOI 10.1016/j.jss.2021.110911. [PDF](https://arxiv.org/pdf/2010.03303). **full text**
- Golzadeh, Decan, Chidambaram (2022). On the accuracy of bot detection techniques. BotSE 2022. DOI 10.1145/3528228.3528406. [PDF](https://orbi.umons.ac.be/bitstream/20.500.12907/17537/1/botse_paper.pdf). **full text**
- Horikawa et al. (2026). arXiv:2610.36229. [PDF](https://arxiv.org/pdf/2610.36229). **full text (sebagian: abstrak, §1, §3.1)**
- Liao, Huang, Zhang, Wu, Cheng (2023). BDGOA. Intelligent and Converged Networks 4(3), 181–197. DOI 10.23919/ICN.2023.0006. [Halaman](https://www.sciopen.com/article/10.23919/ICN.2023.0006). **abstrak saja**
- RABBIT-ng. [README](https://github.com/sgl-umons/RABBIT-ng). **full text**

### Abuse dan akun palsu di GitHub

- Bae, Yagemann (2026). Beyond Takedown. arXiv:2606.26291. [Abstrak](https://arxiv.org/abs/2606.26291). **abstrak saja**
- Bao, Xia, Lo, Murphy. Long-time contributor prediction. IEEE TSE. DOI [10.1109/tse.2019.2918536](https://doi.org/10.1109/tse.2019.2918536). **abstrak saja**
- Check Point Research, Terefos (2024). Stargazers Ghost Network. [Laporan](https://research.checkpoint.com/2024/stargazers-ghost-network/). **full text**
- Cheng, Zhang, Yu, Ma, Shen, Liu (2026). Weaponizing the Commons. JAWs @ ICSE 2026. DOI 10.48550/arXiv.2604.17909. [PDF](https://arxiv.org/pdf/2604.17909). **full text**
- Dagster (2023). Tracking the Fake GitHub Star Black Market. [Blog](https://dagster.io/blog/fake-stars). **full text**
- Du, Yang, Zhang, Duan, Wang, Hao, Li, Yang (2020). Understanding Promotion-as-a-Service on GitHub. ACSAC 2020, 597–610. DOI 10.1145/3427228.3427258. [PDF](https://personal.utdallas.edu/~shao/papers/du_acsac20.pdf). **full text**
- Gong, Zhang, Chen, Li, Xiao, Wang, Hui (2019). Detecting Malicious Accounts in Online Developer Communities Using Deep Learning. CIKM 2019. DOI 10.1145/3357384.3357971. [PDF](https://user.informatik.uni-goettingen.de/~ychen/papers/GitSec-CIKM19.pdf). **full text**
- Gong, Liu, Zhang, Chen, Li, Xiao, Wang, Hui (2023). IEEE TKDE 35(10), 10633–10649. DOI 10.1109/TKDE.2023.3237838. [Salinan terbuka](https://aaltodoc.aalto.fi/bitstreams/9095077c-3398-4c13-9f15-5130dbe9b9b7/download). **full text (tabel per metrik tidak terbaca bersih)**
- Gong et al., README dataset dan kode GitSec. [README](https://raw.githubusercontent.com/chenyang03/developers/master/README.md). **full text**
- He, Yang, Burckhardt, Kapravelos, Vasilescu, Kästner (2026). Six Million (Suspected) Fake Stars on GitHub: A Growing Spiral of Popularity Contests, Spam, and Malware. ICSE 2026, 1469–1481. DOI 10.1145/3744916.3764531. [PDF ICSE](https://cmustrudel.github.io/papers/icse2026fakestars.pdf); [arXiv v1](https://arxiv.org/abs/2412.13459v1); [arXiv v2](https://arxiv.org/abs/2412.13459v2); [data](https://doi.org/10.5281/zenodo.17009693); [kode cek status](https://raw.githubusercontent.com/hehao98/StarScout/main/scripts/analysis/get_stargazer_info.py); [notebook](https://raw.githubusercontent.com/hehao98/StarScout/main/evaluation-deletion-ratio.ipynb). **full text**
- Orchid Files (2026). [Laporan](https://orchidfiles.com/github-repositories-distributing-malware/). **full text**
- Rokon, Islam, Darki, Papalexakis, Faloutsos (2020). SourceFinder. RAID 2020, 149–163. [Halaman](https://www.usenix.org/conference/raid2020/presentation/omar). **abstrak saja**

### Label suspensi dan deteksi dini di platform lain

- Alfifi, Caverlee (2017). Badly Evolved? SocInfo. DOI 10.1007/978-3-319-67217-5_14. [PDF](https://people.engr.tamu.edu/caverlee/pubs/alfifi17socinfo.pdf). **full text**
- Bian et al. (2020). BiGCN. AAAI 2020. [PDF](https://arxiv.org/pdf/2001.06362). **full text**
- Breuer, Eilat, Weinsberg (2020). SybilEdge. WWW 2020. DOI 10.1145/3366423.3380204. [PDF](https://arxiv.org/pdf/2004.04834). **full text**
- Cheng, Danescu-Niculescu-Mizil, Leskovec (2015). Antisocial Behavior in Online Discussion Communities. ICWSM. DOI 10.1609/icwsm.v9i1.14583. [PDF](https://arxiv.org/pdf/1504.00680). **full text**
- Dehkordi, Zehmakan (2025). Survei deteksi akun palsu berbasis graf. [PDF](https://arxiv.org/pdf/2507.06541). **full text**
- Echeverria, Besel, Zhou (2017). Discovery of the Twitter Bursty Botnet. [PDF](https://arxiv.org/pdf/1709.06740). **full text**
- Kapoor, Jain, Prabhu, Karandikar, Kumaraguru (2021). I'll be back. WI-IAT. DOI 10.1145/3486622.3493959. [PDF](https://arxiv.org/pdf/2111.12395). **full text**
- Katyal (2026). arXiv:2606.26127. [PDF](https://arxiv.org/pdf/2606.26127). **full text**
- Klausen, Marks, Zaman (2016). Finding Online Extremists in Social Networks. [PDF](https://arxiv.org/pdf/1610.06242). **full text**
- Kumar, Spezzano, Subrahmanian (2015). VEWS. KDD 2015. DOI 10.1145/2783258.2783367. [PDF](https://arxiv.org/pdf/1507.01272). **full text**
- Liu, Wu (2018). AAAI. DOI 10.1609/aaai.v32i1.11268. [Salinan Wayback](https://web.archive.org/web/20260305040253/https://ojs.aaai.org/index.php/AAAI/article/view/11268). **abstrak saja**
- Saeed et al. (2022). TrollMagnifier. IEEE S&P. [PDF](https://arxiv.org/pdf/2112.00443). **full text**
- Seyler, Tan, Li, Zhang, Li (2021). Textual Analysis and Timely Detection of Suspended Social Media Accounts. ICWSM, 644–655. DOI 10.1609/icwsm.v15i1.18091. [Salinan Wayback](https://web.archive.org/web/20260502120329id_/https://ojs.aaai.org/index.php/ICWSM/article/download/18091/17894). **full text**
- Shevtsov, Antonakaki, Lamprou, Pratikakis, Ioannidis (2023). BotArtist v1. [PDF](https://arxiv.org/pdf/2306.00037v1). **full text**
- Thomas, Grier, Song, Paxson (2011). Suspended accounts in retrospect. IMC 2011. DOI 10.1145/2068816.2068840. [PDF](https://people.eecs.berkeley.edu/~dawnsong/papers/2011%20Suspended%20accounts%20in%20retrospect%20an%20analysis%20of%20Twitter%20spam.pdf). **full text**
- Volkova, Bell (2017). Identifying Effective Signals to Predict Deleted and Suspended Accounts on Twitter Across Languages. ICWSM, 290–298. DOI 10.1609/icwsm.v11i1.14874. [Salinan Wayback](https://web.archive.org/web/20240111165300id_/https://ojs.aaai.org/index.php/ICWSM/article/download/14874/14724). **full text**
- Xiao, Freeman, Hwa (2015). Detecting Clusters of Fake Accounts in Online Social Networks. AISec 2015, 91–101. DOI 10.1145/2808769.2808779. [PDF](https://theory.stanford.edu/~dfreeman/papers/clustering.pdf). **full text**
- Xu et al. (2021). Deep Entity Classification. USENIX Security 2021. [PDF](https://www.usenix.org/system/files/sec21-xu-teng.pdf). **full text (sebagian)**
- Yuan et al. (2019). Ianus. CCS 2019, 1423–1438. DOI 10.1145/3319535.3363198. [Halaman proyek](http://netsec.ccert.edu.cn/publications/ccs18-ianus). **abstrak saja**
- Zheng, Yuan, Wu (2019). SAFE. AAAI 2019. DOI 10.1609/aaai.v33i01.33011278. [PDF](https://arxiv.org/pdf/1809.04683). **full text**

### Dense-block dan koordinasi

- Ban, Liu, Duan, Liu, Xu (2019). No Place to Hide. WWW 2019. DOI 10.1145/3308558.3313403. [PDF](https://arxiv.org/pdf/1810.06230). **full text**
- Beutel, Xu, Guruswami, Palow, Faloutsos (2013). CopyCatch. WWW 2013. DOI 10.1145/2488388.2488400. [Halaman dan PDF](https://ai.meta.com/research/publications/copycatch-stopping-group-attacks-by-spotting-lockstep-behavior-in-social-networks/). **full text**
- Cao, Yang, Yu, Palow (2014). SynchroTrap. CCS 2014, 477–488. DOI 10.1145/2660267.2660269. [PDF](https://users.cs.duke.edu/~xwy/publications/SynchroTrap-ccs14.pdf). **full text**
- Hooi, Song, Beutel, Shah, Shin, Faloutsos (2016). FRAUDAR. KDD 2016. DOI 10.1145/2939672.2939747. [PDF](https://bhooi.github.io/papers/fraudar_kdd16.pdf). **full text**
- Iannucci, Matakos, Kivelä (2026). [Abstrak](https://arxiv.org/abs/2610.37970). **abstrak saja**
- Jiang, Yao, Li, Wang, He, Chen (2025). Dupin. PACMMOD 3(3), 150. DOI 10.1145/3725287. [PDF](https://arxiv.org/pdf/2504.09311). **full text**
- Khaleghpour, McKinney (2026). arXiv:2603.06632. [PDF](https://arxiv.org/pdf/2603.06632). **full text**
- Luceri, Pantè, Burghardt, Ferrara (2024). arXiv:2310.09884. [PDF](https://arxiv.org/pdf/2310.09884). **full text**
- Mannocci et al. (2026). Information Sciences. DOI 10.1016/j.ins.2026.123125. [PDF](https://arxiv.org/pdf/2507.12108). **full text**
- Mannocci, Mazza, Monreale, Tesconi, Cresci (2026). ACM CSUR 58(16), 401. [PDF](https://arxiv.org/pdf/2408.01257). **full text**
- Panayiotou, Mannocci, Tesconi (2026). AIDEM workshop, ECML-PKDD 2026. arXiv:2609.21959. [Abstrak](https://arxiv.org/abs/2609.21959). **abstrak saja**
- Sharma, Zhang, Ferrara, Liu. AMDN-HAGE. arXiv:2008.11308. [PDF](https://arxiv.org/pdf/2008.11308). **full text**
- Shin, Hooi, Faloutsos (2016). M-Zoom. ECML PKDD. DOI 10.1007/978-3-319-46128-1_17. [PDF](https://www.cs.cmu.edu/~kijungs/papers/mzoomPKDD2016.pdf); [kode](https://github.com/kijungs/mzoom). **full text**
- Shin, Hooi, Kim, Faloutsos (2017). D-Cube. WSDM 2017. DOI 10.1145/3018661.3018676. [PDF](https://www.cs.cmu.edu/~kijungs/papers/dcubeWSDM2017.pdf); [kode](https://github.com/kijungs/dcube). **full text**
- Shin, Hooi, Kim, Faloutsos (2017). DenseAlert. KDD 2017. DOI 10.1145/3097983.3098087. [PDF](https://arxiv.org/pdf/1706.03374). **full text**
- Vargas, Emami, Traynor (2020). arXiv:2005.13466. [PDF](https://arxiv.org/pdf/2005.13466). **full text**
- Weber, Neumann (2021). arXiv:2103.03409; DOI terkait 10.1007/s13278-021-00815-2. [PDF](https://arxiv.org/pdf/2103.03409). **full text**
- Zhang, Liu, Hou, Bhatia, Shen, Yu, Cheng (2021). AugSplicing. [PDF](https://arxiv.org/pdf/2012.02006). **full text**

### PU learning dan evaluasi

- Arp et al. (2022). Dos and Don'ts of Machine Learning in Computer Security. USENIX Security 2022. [PDF](https://www.usenix.org/system/files/sec22-arp.pdf). **full text**
- Bekker, Davis (2020). Learning from positive and unlabeled data: a survey. Machine Learning 109(4), 719–760. DOI 10.1007/s10994-020-05877-5. [arXiv](https://arxiv.org/abs/1811.04820). **full text**
- Bekker, Robberechts, Davis (2019). Beyond the Selected Completely at Random Assumption. ECML PKDD. DOI 10.1007/978-3-030-46147-8_5. [arXiv](https://arxiv.org/abs/1809.03207). **full text**
- Demšar (2006). JMLR 7, 1–30. [PDF](https://www.jmlr.org/papers/volume7/demsar06a/demsar06a.pdf). **abstrak saja**
- Dhamnani et al. (2020). Botcha. OHARS @ RecSys. [arXiv](https://arxiv.org/abs/2103.01428). **full text**
- Echeverría, De Cristofaro, Kourtellis, Leontiadis, Stringhini, Zhou (2018). LOBO. ACSAC 2018, 137–146. DOI 10.1145/3274694.3274738. [PDF](https://arxiv.org/pdf/1809.09684). **full text**
- Elkan, Noto (2008). Learning classifiers from only positive and unlabeled data. KDD 2008. DOI 10.1145/1401890.1401920. [PDF](https://cseweb.ucsd.edu/~elkan/posonly.pdf). **full text**
- Field, Welsh (2007). Bootstrapping Clustered Data. JRSS-B 69(3), 369–390. DOI [10.1111/j.1467-9868.2007.00593.x](https://doi.org/10.1111/j.1467-9868.2007.00593.x). **abstrak saja**
- Hays, Schutzman, Raghavan, Walk, Zimmer (2023). WWW 2023, 3660–3669. DOI 10.1145/3543507.3583214. [PDF](https://arxiv.org/pdf/2301.07015). **full text**
- Kapoor, Narayanan (2023). Patterns 4(9), 100804. DOI 10.1016/j.patter.2023.100804. [Preprint](https://arxiv.org/abs/2207.07048). **abstrak terbit; full text preprint**
- Kaufman, Rosset, Perlich, Stitelman (2012). Leakage in Data Mining. TKDD 6(4). DOI 10.1145/2382577.2382579. [Salinan](https://www.cs.umb.edu/~ding/history/470_670_fall_2011/papers/cs670_Tran_PreferredPaper_LeakingInDataMining.pdf). **full text (versi konferensi)**
- Kiryo, Niu, du Plessis, Sugiyama (2017). nnPU. NIPS 2017. [arXiv](https://arxiv.org/abs/1703.00593). **full text**
- Kumar, Lambert (2024). PULSNAR. PeerJ CS 10, e2451. DOI 10.7717/peerj-cs.2451. [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11622864/). **full text**
- Li, Chen, Liu, Wei, Shao (2014). Spotting Fake Reviews via Collective Positive-Unlabeled Learning. ICDM 2014. DOI [10.1109/icdm.2014.47](https://doi.org/10.1109/icdm.2014.47). **abstrak saja**
- Liu, Caragea, Ou, Roy (2024). arXiv:2410.19364. [PDF](https://arxiv.org/pdf/2410.19364). **full text**
- McDermott, Zhang, Hansen, Angelotti, Gallifant (2024). NeurIPS 2024. [arXiv](https://arxiv.org/abs/2401.06091). **full text (sebagian)**
- Obuchowski (1997). Biometrics 53(2). DOI [10.2307/2533958](https://doi.org/10.2307/2533958). **abstrak saja**
- Pendlebury, Pierazzi, Jordaney, Kinder, Cavallaro (2019). TESSERACT. USENIX Security 2019. [PDF](https://www.usenix.org/system/files/sec19-pendlebury.pdf). **full text**
- Roberts et al. (2017). Ecography 40(8), 913–929. DOI 10.1111/ecog.02881. [PDF](https://www.biometrie.uni-freiburg.de/mitarbeiter/dormann/roberts-et-al-2017-ecography.pdf). **full text**
- Saeb, Lonini, Jayaraman, Mohr, Kording (2017). The need to approximate the use-case in clinical machine learning. GigaScience 6(5). DOI 10.1093/gigascience/gix019. [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC5441397/). **full text**
- Roth (2026). arXiv:2604.04199. [PDF](https://arxiv.org/pdf/2604.04199). **full text**
- scikit-learn. [GroupKFold](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html); [StratifiedGroupKFold](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html). **full text**
- Trotzek et al. (2018). [PDF](https://arxiv.org/pdf/1804.07000). **full text**
- TwiBot-22 (2022). NeurIPS Datasets and Benchmarks. [PDF](https://arxiv.org/pdf/2206.04564). **full text**
- Wang, Wu, Li, Zhang, Niu, Sugiyama (2026). ICLR 2026. [PDF](https://proceedings.iclr.cc/paper_files/paper/2026/file/cbffadf96101c42be845d3e275c4b7e9-Paper-Conference.pdf). **full text**

### Dokumentasi GitHub dan GH Archive

- GitHub. [REST users](https://docs.github.com/en/rest/users/users); [Username changes](https://docs.github.com/en/account-and-profile/concepts/username-changes); [Account management](https://docs.github.com/en/account-and-profile/concepts/account-management); [Terms of Service](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service); [Acceptable Use Policies](https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies); [Appeal and Reinstatement](https://docs.github.com/en/site-policy/acceptable-use-policies/github-appeal-and-reinstatement); [Events API](https://docs.github.com/en/rest/activity/events); [Status 451](https://developer.github.com/changes/2016-03-17-the-451-status-code-is-now-supported/). **full text**
- GitHub Transparency. [README data](https://raw.githubusercontent.com/github/transparency/main/data/appeals_and_other_reinstatements/README.md); [CSV](https://raw.githubusercontent.com/github/transparency/main/data/appeals_and_other_reinstatements/abuse_related_violations.csv). **full text**
- GH Archive. [Laman](https://www.gharchive.org/); [#294](https://github.com/igrigorik/gharchive.org/issues/294); [#310](https://github.com/igrigorik/gharchive.org/issues/310). **full text (laporan pengguna, tidak divalidasi pengelola)**
- Squires (2022). [Blog](https://www.jessesquires.com/blog/2022/04/19/github-suspending-russian-accounts/). **full text (anekdot)**

### Belum terverifikasi atau wajib dicek manual

- GitSec: mekanisme anotasi 2018 dan apakah aturan API 200 dengan web 404 masih berlaku pada 2026; tabel per metrik TKDE; [salinan dataset 10.7910/DVN/T6ZRJT](https://raw.githubusercontent.com/chenyang03/developers/master/README.md) belum dibuka.
- Perilaku API untuk akun suspended: blog `pilot2254.github.io/blog/how-github-suspended-me/` kabarnya melaporkan 404 pada lookup user ID sebelum reinstatement, tetapi halamannya gagal dibuka; bila benar, ini langsung relevan.
- Karya yang bisa mengubah verdict C3 dan belum dibuka: [Early Screening of Fake Social Media Accounts](https://doi.org/10.20944/preprints202608.0136.v1); paper IJCOPE 2026 tentang deteksi dini akun palsu; Cola, Mazza, Tesconi tentang deteksi detik setelah registrasi; DeBot (ICDM 2016).
- Utzinger, "Early Forecasting of Developer Inactivity in Open Source Projects", ICSE-Companion 2026, DOI 10.1145/3774748.3787756: **metadata saja**; isinya perlu dibaca karena menyentuh prediksi dini dan batas dengan churn. Chowdhury et al. 2020 (On Twitter Purge, DOI 10.1145/3366424.3383298): metodenya hanya dikenal lewat ringkasan sekunder.
- Sumber yang hanya dikenal lewat sumber lain atau cuplikan pencarian: Wyrich et al. dan dataset 4.654 bot; Erlenhov et al.; UFA; Anise & Wright (Black Hat 2018); Rosset et al. 2010; Valavi et al. 2019; Socket "3.7 Million Fake GitHub Stars"; klaim DEV Community bahwa user, organisasi dan bot berbagi satu pencacah ID.
- Definisi ERDE (Losada & Crestani, DOI 10.1007/978-3-319-44564-9_3) dan F_latency (Sadeque et al., DOI 10.1145/3159652.3159725): **metadata saja**; rumus harus dicek ke sumber asli. Nadeau & Bengio, Bouckaert & Frank: **metadata saja**, isi dikenal lewat dokumentasi scikit-learn. Mordelet & Vert (PU bagging): **metadata saja**.
- Venue yang belum pasti: Vargas et al. (CCSW 2020 hanya dari cuplikan), Sharma et al., versi terbit Weber & Neumann, Xiao et al. (AISec menurut Crossref, CCS di satu listing), tahun Cheng et al. (2015 vs Crossref 2021).
- Angka yang dibaca dari tabel PDF yang teratakan atau dari gambar: Volkova & Bell Tabel 3, Seyler Tabel 5, kolom Amazon di ISG, F-measure FRAUDAR, AugSplicing; cek kesejajaran kolom sebelum mengutip.
- RABBIT-ng offline: apakah batas minimum 5 event tetap berlaku belum diuji.
- Standar novelty departemen untuk kontribusi empiris belum diperiksa; konfirmasi ke dosen pembimbing.
- Angka pilot lama di catatan riset (39,2%, 7,6%, 2,2%) tidak dipakai; laporan ini memakai hitungan penuh 38,9% dan 6,15%.

### Inkonsistensi pada sumber terbit dan antarcatatan

- **StarScout, judul dan angka.** arXiv v1 (18 Des 2024) berjudul "4.5 Million (Suspected) Fake Stars in GitHub ... Scams, and Malware"; v2 (6 Sep 2025) "Six Million (Suspected) Fake Stars in GitHub ... Spams, and Malware"; versi ICSE "Six Million (Suspected) Fake Stars on GitHub ... Spam, and Malware". v1 melaporkan 4,53 juta star di 22.915 repo sebelum pascaproses dan 15.835 repo, 278 ribu akun, 3,1 juta star sesudahnya; versi terbit 6,0 juta star di 26.254 repo dan 18.617 repo, 301 ribu akun, 3,81 juta star ([v1](https://arxiv.org/html/2412.13459v1); [v2](https://arxiv.org/html/2412.13459v2)). Pendahuluan mencampur angka sebelum dan sesudah pascaproses.
- **StarScout, status hapus.** v1 per Oktober 2024: repo 90,75% dan akun 61,95%, baseline 5,84% dan 4,43%; versi terbit per Januari 2025: 90,42% dan 57,07%, baseline 5,03% dan 3,54%. Teks yang sama menyebut "at the time of detection" dan Maret 2025. Recall repo tercetak 81,23% dan "82,23%" padahal hitungannya 688 dari 847.
- **StarScout, penyebut baseline (hitungan ulang catatan, belum dikonfirmasi penulis).** [Notebook penulis](https://raw.githubusercontent.com/hehao98/StarScout/main/evaluation-deletion-ratio.ipynb) membagi jumlah terhapus pada sampel 10.000 dengan jumlah repo terdeteksi. Baseline dengan penyebut sampel menjadi 13,20% untuk repo dan 9,30% untuk akun, bukan 5,03% dan 3,54%, sehingga "16x" menjadi sekitar 6,85x dan 6,14x. Gunakan 9,30% dengan catatan bila membandingkan, dan ingat populasinya berbeda.
- **Lain-lain.** BotHunter AUC 98,3 di Tabel 3, 98,7 di abstrak; BoDeGHa 837 ribu vs 873.489 kontributor; BIMBAS 793 vs 791 akun bot; BotHawk recall 0,871 vs 0,806 dan F1 0,882 vs 0,89; RABBIT mengatribusikan P 0,667, R 0,866, F1 0,754 ke BIMAN yang tidak ditemukan di teks BIMAN; BIMBAS menyebut jendela Events API 90 hari, dokumentasi kini 30 hari setelah [perubahan retensi Januari 2025](https://github.blog/changelog/2024-11-08-upcoming-changes-to-data-retention-for-events-api-atom-feed-timeline-and-dashboard-feed-features/); Xiao et al. 260.644 vs sekitar 275.000 akun; Kapoor & Narayanan 294 (abstrak terbit) vs 329 (preprint v1); Arp et al. data snooping 57% (ada) vs 73% (setidaknya sebagian) pada catatan berbeda; D-Cube 1.600× vs 1.561× memori antara konferensi dan jurnal; urutan penulis Thomas et al. 2011 berbeda antarcatatan, laporan ini mengikuti Crossref.
- **Konflik antarcatatan.** `github_abuse_and_status_labels.md` hanya membaca abstrak GitSec, Du et al. dan RABBIT/BIMBAS, sedangkan `github_abuse_status_labels.md` dan `github_bot_detection.md` membaca full text; laporan ini mengikuti pembacaan full text, termasuk rincian label GitSec, ban 4,19% pada Du et al., dan keberadaan kolom `deleted` di [skema GHTorrent](https://github.com/ghtorrent/ghtorrent.org/blob/master/relational.md). Catatan pertama menilai status penanganan rename StarScout tidak jelas dari makalah; catatan kedua membaca kodenya dan menemukan lookup berbasis login.
