# Draf Hasil Penelitian

Draf bagian Hasil untuk naskah paper. Angka konfirmatori berasal dari satu kali pembukaan holdout pada 10 November 2026 (`results/tables/`, `results/numbers.json`). Semua metrik dihitung terhadap label teramati `s`, yaitu akun hilang, bukan pelanggaran. Bagian yang berlabel eksploratif tidak memengaruhi keputusan hipotesis.

## Ringkasan keputusan

Evaluasi memakai minggu holdout `w3`, dengan model dilatih pada `w0` sampai `w2`. Lengan utama F3 memuat 24.249 akun dan 504 akun hilang. Pada stratum 5–19 event terdapat 23.316 akun dan 471 akun hilang, dengan base rate 2,02%.

| Hipotesis | Pernyataan | Estimasi | CI 95% | Keputusan | Catatan penafsiran |
| --- | --- | --- | --- | --- | --- |
| H1a | `M_behav` > `B2`, F3, stratum 5–19 | Selisih AP +0,173 | 0,100 sampai 0,249 | Didukung | Positif pada keenam jam holdout |
| H1b | AUC di dalam sel > 0,5, F3 | 0,736 | 0,700 sampai 0,771 | Didukung | |
| H2a | Rasio tambahan AP split acak terhadap blok ID > 1 | 1,176 | 1,032 sampai 1,330 | Didukung | Dihitung pada `w0` sampai `w2` |
| H2b | Galat CV acak > galat CV blok ID | 0,042 | Degeneratif | Didukung | Intervalnya tidak informatif |
| H4a | AURT adaptif > jendela tetap terpilih, F3 | Selisih +0,058 | 0,014 sampai 0,120 | Didukung | Pembandingnya lemah, dan efeknya terkonsentrasi pada satu jam |
| H5 | `M_coord` > `M_behav`, F3, stratum 5–19 | Selisih AP +0,107 | 0,078 sampai 0,140 | Didukung | Berasal dari fitur proksi pada satu jam, bukan dari dense block |

Pada keluarga konfirmatori H1a, H2a, H4a, dan H5, tidak ada satu pun dari 2.000 replikasi bootstrap yang selisihnya nol atau negatif, sehingga nilai p Holm tertulis 0.

## RQ1: sinyal di luar aktivitas dan usia

Pada F3 stratum 5–19, AP `B2` adalah 0,084 dan AP `M_behav` dengan XGBoost adalah 0,258. MLP mencapai 0,279, tetapi XGBoost tetap menjadi model utama karena pada tahap pengembangan selisih MLP tidak melewati ambang. `M_robust`, yang tidak memakai keluarga fitur waktu dan repo, mencapai 0,205.

AUC di dalam sel aktivitas dan usia adalah 0,736, jadi model mengurutkan akun lebih baik dari acak di antara akun yang setara.

Pada analisis eksploratif per jam, selisih AP `M_behav` terhadap `B2` positif pada keenam jam, antara +0,049 dan +0,235. Tanpa salah satu jam, selisihnya tetap antara +0,124 dan +0,188.

## RQ2: audit desain split

Pada stratum 5–19, estimasi validasi silang adalah 0,397 untuk split acak dan 0,355 untuk blok ID lebar 20.000, sedangkan AP forward pada holdout adalah 0,260. Kedua estimasi melebihi performa forward, masing-masing sebesar 0,137 dan 0,095. Split acak melebih-lebihkan tambahan AP dibanding blok ID sekitar 18%.

Interval H2b degeneratif. AP forward berada di bawah kedua estimasi validasi silang, dan estimasi itu diperlakukan tetap, sehingga selisih galat hampir selalu sama dengan selisih kedua estimasi. Status didukung pada H2b tidak menambah bukti di luar H2a.

Bagian test yang tidak bertetangga dengan train, yaitu tanpa blok ID berisi akun train apa pun, memuat 1.365 akun dan 161 akun hilang. AP stratum 5–19 pada bagian ini adalah 0,133 untuk `B2` dan 0,515 untuk `M_behav`, dengan base rate 11,5%.

## RQ3: PU learning (eksploratif, tahap pengembangan)

Pada uji semi-sintetis, metode PU terbaik yaitu SAR-EM dengan propensity usia mengungguli model naive sebesar 0,010 (CI 95% 0,005 sampai 0,015). Metode terbaik dipilih pada data yang sama, jadi hasil ini optimistis. RQ3 tidak dievaluasi pada holdout.

## RQ4: latensi dan kebijakan adaptif

Pada lengan F2, kohort tetap, stratum 5–19:

| Jendela (menit) | 5 | 10 | 15 | 30 | 60 |
| --- | --- | --- | --- | --- | --- |
| AP `B2` | 0,054 | 0,097 | 0,088 | 0,082 | 0,086 |
| AP `M_behav` | 0,076 | 0,145 | 0,152 | 0,192 | 0,278 |

Pada kohort deployable, populasinya berbeda untuk tiap jendela, jadi angkanya tidak dibandingkan sebagai kurva penurunan. AP `M_behav` adalah 0,443, 0,498, 0,433, 0,338, dan 0,287 untuk jendela 5, 10, 15, 30, dan 60 menit.

Pada target precision 0,7, kohort tetap, F3, kebijakan adaptif menandai 78 akun dengan precision 0,769, recall 0,119, AURT 0,065, dan median waktu penandaan menit ke-30. Jendela tetap yang terpilih pada set kalibrasi adalah menit ke-30, yang hanya menandai 9 akun dengan AURT 0,007. Selisih AURT pada horizon 65 dan 90 menit adalah 0,051 dan 0,066.

Jendela tetap terpilih itu ternyata lemah pada holdout. Jendela 15 menit mencapai AURT 0,048. Pada perbandingan precision teramati yang disamakan (eksploratif, `q` dipilih dengan label holdout untuk kedua kebijakan):

| Precision minimal | AURT adaptif | AURT jendela tetap terbaik | Selisih |
| --- | --- | --- | --- |
| 0,5 | 0,090 | 0,072 | +0,018 |
| 0,7 | 0,065 | 0,063 | +0,002 |
| 0,9 | 0,046 | 0,044 | +0,002 |

Pada analisis eksploratif per jam, 40 dari 58 true positive kebijakan adaptif berasal dari satu jam (30 April pukul 15 UTC). Tanpa jam itu, selisih AURT turun ke 0,009.

## RQ5: fitur koordinasi

Pada F3 stratum 5–19, AP `M_behav` adalah 0,256, `M_proxy` 0,362, dan `M_coord` 0,364. Hampir seluruh selisih berasal dari 10 fitur proksi koordinasi. Fitur dense block hanya menambah 0,001 di atas `M_proxy`. Pada tahap pengembangan, selisih `M_coord` terhadap `M_behav` adalah -0,012 (CI 95% -0,035 sampai 0,012).

Pada analisis eksploratif per jam, tambahan AP dari fitur proksi terkonsentrasi pada satu jam (4 Mei pukul 15 UTC), yaitu +0,326. Tanpa jam itu, tambahannya +0,014. Di antara 471 akun hilang, tiga kelompok pesan commit yang sama masing-masing dipakai 105, 87, dan 57 akun. Pola ini konsisten dengan satu atau beberapa kampanye, jadi hasilnya tidak bisa dibaca sebagai efek umum fitur koordinasi.

Keanggotaan blok tidak selektif, karena seluruh 504 akun hilang pada F3 berada di dalam blok. Dense block memakai implementasi greedy peeling bergaya M-Zoom dari proyek ini.

## Batasan

- Akun hilang mencampur penghapusan sendiri, moderasi, dan penyebab lain.
- Holdout hanya memuat enam jam. Bootstrap per blok ID tidak menangkap ketergantungan antarakun dalam satu jam, sehingga interval H4a dan H5 kemungkinan terlalu sempit.
- Urutan baris data berbeda antarproses, jadi skor model sedikit berubah saat dijalankan ulang. Run eksploratif memberi AP `M_behav` antara 0,255 dan 0,260 dan selisih AURT H4a 0,044. Angka konfirmatori tetap berasal dari satu run.
- Audit manual oleh dua anotator belum dilakukan, jadi `tab_audit_results` belum ada.
- Snapshot status hanya diambil satu kali, dan rancangan dibekukan dengan tag git lokal, bukan pendaftaran publik.
- Keputusan gerbang A, B, dan D diambil oleh Claude Code atas delegasi pengguna. Penyimpangan tercatat di `docs/DEVIATIONS.md`.
