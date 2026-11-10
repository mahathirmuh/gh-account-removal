# Naskah Presentasi Prediksi Akun GitHub Hilang

Naskah ini bisa langsung diucapkan, mengikuti urutan slide di [presentasi-akun-github-hilang.pptx](presentasi-akun-github-hilang.pptx). Durasinya sekitar 10 menit dengan tempo bicara biasa. Teks miring dalam tanda kurung adalah petunjuk dan tidak perlu diucapkan. Untuk menjawab pertanyaan, lihat [presentasi-akun-github-hilang-penjelasan.md](presentasi-akun-github-hilang-penjelasan.md).

## Slide 1. Judul

Selamat pagi, Bapak/Ibu dosen dan teman-teman semua.

Perkenalkan, saya Mahathir. Hari ini saya akan mempresentasikan project saya untuk mata kuliah Topik Dalam Data Mining, dengan judul *Predicting GitHub Account Removal from Short Public Event Windows*. Kalau dibahasakan, prediksi akun GitHub yang kelak hilang, hanya dari aktivitas publiknya dalam waktu singkat.

Pertanyaan besarnya sederhana. Kalau kita hanya melihat aktivitas sebuah akun selama beberapa menit, apakah kita bisa memperkirakan bahwa akun itu kelak akan hilang dari GitHub? Dan kalau bisa, seberapa jauh angka evaluasinya bisa kita percaya?

## Slide 2. Latar Belakang Masalah

Kenapa ini perlu diteliti? Ada empat masalah yang saya lihat.

Masalah nomor satu, penelitian yang ada butuh histori panjang. GitSec, misalnya, memakai event dari tahun 2015 sampai 2018, dan penelitian Du dan kawan-kawan memakai 2015 sampai 2019. Padahal kalau keputusan perlu diambil lebih awal, histori sepanjang itu tidak tersedia. Prediksi dari satu jendela enam puluh menit atau kurang tidak ditemukan dalam pencarian yang dilakukan.

Masalah nomor dua, usia akun dan jumlah aktivitas saja sudah sangat prediktif. Di data saya, untuk akun dengan 5 sampai 19 event, kelompok akun paling baru tingkat hilangnya di atas 10 persen. Kelompok akun paling lama, di bawah 1 persen. Jadi model bisa terlihat bagus hanya karena tahu akun itu masih baru. Karena itu, model harus terbukti lebih baik daripada sekadar melihat usia dan aktivitas.

Masalah nomor tiga, evaluasinya rawan bias. Akun bisa dibuat berkelompok, sehingga ID-nya berdekatan. Kalau data dibagi acak, akun yang bertetangga bisa masuk ke train dan test sekaligus. Di studi lain tentang deteksi bot, hasilnya turun dari sekitar 98 persen ke sekitar 55 persen ketika diuji pada kelas bot yang tidak terlihat saat pelatihan.

Masalah nomor empat, jendela tetap menunda keputusan. Semua akun harus menunggu sama lama, padahal sebagian mungkin sudah cukup jelas sejak menit-menit awal.

*(Tunjuk kotak gelap di bawah.)*

Ada satu hal yang perlu saya tegaskan. Target penelitian ini adalah akun hilang, artinya ID numerik akun menghasilkan 404 sekitar 31 bulan setelah diamati. Akun hilang tidak berarti akun itu melanggar aturan, karena bisa saja dihapus sendiri oleh pemiliknya.

## Slide 3. Novelty

Lalu novelty-nya di mana? Saya perlu jujur dari awal, penelitian ini tidak mengusulkan algoritma baru. Kebaruannya ada pada kombinasi tiga hal.

Yang nomor satu adalah targetnya. Saya memprediksi akun yang hilang sekitar 31 bulan kemudian, hanya dari satu jendela event publik selama enam puluh menit atau kurang.

Yang nomor dua adalah audit desain split pada akun GitHub. Akun dikelompokkan berdasarkan kedekatan ID dan pola aktivitasnya, lalu saya ukur seberapa besar cara membagi data mengubah performa yang terlihat.

Yang nomor tiga adalah metode usulan penelitian ini, yaitu kebijakan penandaan dini adaptif. Jadi model tidak menunggu sampai waktu yang sama untuk semua akun, tetapi memutuskan per akun kapan sudah cukup yakin untuk menandai, dengan syarat precision tetap terjaga.

*(Tunjuk baris bawah.)*

Di bagian bawah, saya tuliskan hal-hal yang sudah ada sebelumnya dan tidak saya klaim, seperti label status platform dari GitSec, ID berdekatan sebagai kebocoran data, dense block, PU learning, dan aturan berhenti sebagai gagasan umum.

Jadi klaim saya hati-hati. Kombinasi ketiganya tidak ditemukan dalam pencarian yang dilakukan, dan ketiadaan itu bukan bukti kebaruan.

## Slide 4. Kontribusi

Dari situ, penelitian ini punya enam kontribusi, dan semuanya bersifat empiris dan evaluatif.

*(Tunjuk kartu gelap.)*

Saya mulai dari K6, karena ini metode usulannya. Pertanyaannya, apakah akun bisa ditandai lebih cepat pada precision yang sama, dibanding kalau kita memakai jendela waktu yang tetap?

Lima kontribusi lainnya mendukung itu. K1 menguji apakah akun yang kelak hilang bisa diprediksi dari jendela pendek. K2 mengukur seberapa besar desain split mengubah performa. K3 membandingkan akun yang aktivitas dan usianya setara, supaya hasilnya bukan sekadar efek volume. K4 melihat seberapa turun performa saat jendela dipendekkan dari 60 menit menjadi 5 menit. Dan K5 menguji apakah fitur koordinasi lintas jenis event menambah nilai. Kalau ternyata tidak, hasil itu tetap saya laporkan.

Selain itu ada analisis PU learning yang sifatnya eksploratif. Klaim akhirnya mengikuti hasil pada data holdout, dan hipotesis yang gagal tetap dilaporkan.

## Slide 5. Tabel Posisi Penelitian

Posisi penelitian ini terhadap karya terdekat bisa dilihat di tabel ini. Tiap baris adalah satu karya, dan tiap kolom adalah kriteria.

*(Tunjuk beberapa baris.)*

GitSec dan StarScout sama-sama memakai data GitHub, tetapi tidak dari jendela enam puluh menit. LOBO adalah contoh terdekat untuk audit split, tetapi pada bot Twitter. ECTS dan eRisk punya aturan berhenti, tetapi pada deret waktu dan post pengguna.

*(Tunjuk baris terakhir.)*

Baris terakhir menunjukkan rancangan penelitian ini, bukan hasilnya. Perlu saya sampaikan juga, kolom kosong pada karya lain bukan bukti kontribusi. Kombinasi ini baru bernilai kalau hasilnya memang mengubah kesimpulan.

## Slide 6. Dataset

Sekarang datanya. Saya memakai GH Archive, yaitu arsip event publik GitHub per jam. Totalnya 25 jam dari April sampai Mei 2024, berisi sekitar 5,3 juta event.

Status akunnya diambil satu kali pada 10 November 2026, sekitar 31 bulan kemudian, lewat GitHub API. Saya memakai ID numerik, supaya akun yang berganti nama tidak terhitung hilang. Dari sekitar 885 ribu akun, ada sekitar 18 ribu akun yang hilang, atau sekitar 2 persen. Jadi kelasnya sangat tidak seimbang.

*(Tunjuk pembagian waktu.)*

Datanya dibagi berdasarkan waktu. Satu jam untuk pengembangan, 12 jam untuk train, 6 jam untuk validasi, dan 6 jam terakhir untuk holdout yang hanya dibuka satu kali.

*(Tunjuk grafik.)*

Grafik ini menunjukkan tingkat hilang di data train. Akun yang sangat aktif lebih sering hilang. Fokus utama saya ada di akun dengan 5 sampai 19 event.

Labelnya juga sudah divalidasi. Dari 2.000 sampel akun hilang yang diperiksa ulang lewat REST API, semuanya cocok. Dan dari 200 akun hilang yang dicek di web, 192 juga menghasilkan 404. Login akun diganti dengan pseudonim, jadi identitas akun tidak muncul di hasil.

## Slide 7. Alur Metode Penelitian

Alur penelitiannya ada sepuluh langkah.

Langkah 1 sampai 5 menyiapkan data. Arsipnya diunduh, event diolah, login diganti pseudonim, lalu fitur dibangun untuk jendela 5 sampai 60 menit. Ada 48 fitur perilaku, misalnya komposisi jenis event, pola waktu, dan pola repo. Setelah itu status akun diambil dan labelnya divalidasi.

Langkah 6 sampai 10 adalah analisis. Langkah 6 membandingkan beberapa cara membagi data, yaitu acak, blok ID, signature aktivitas, dan forward, artinya latih di minggu awal dan uji di minggu berikutnya. Langkah 7 membandingkan baseline yang hanya tahu aktivitas dan usia dengan model yang ditambah fitur perilaku. Model utamanya XGBoost, dengan Logistic Regression dan MLP sebagai pembanding, dan hyperparameter-nya dicari dengan Optuna. Langkah 8 menguji PU learning dan melihat penurunan performa dari 60 ke 5 menit.

*(Tunjuk kotak gelap nomor 9, lalu rumus di bawah.)*

Langkah 9 adalah metode usulannya. Caranya begini. Pada menit 5, 10, 15, 30, dan 60, model memberi peluang bahwa akun itu kelak hilang. Akun ditandai pada checkpoint paling awal yang peluangnya melewati ambang. Ambangnya dibuat lebih ketat di menit-menit awal, karena buktinya masih sedikit. Nilai parameternya dipilih pada data kalibrasi, supaya precision keseluruhan tetap memenuhi target.

Terakhir, langkah 10. Data holdout dibuka satu kali saja di akhir, dan ada audit manual oleh dua anotator untuk melihat seperti apa sebenarnya akun yang mendapat skor tinggi.

## Slide 8. Metrik Evaluasi

Sekarang metrik evaluasinya.

Metrik utamanya AP, atau Average Precision, dan dihitung per kelompok aktivitas. Kenapa bukan akurasi? Karena akun hilang hanya sekitar 2 persen. Model yang menebak semua akun tidak hilang pun sudah benar sekitar 98 persen, padahal tidak berguna.

*(Tunjuk tabel.)*

Tabel ini disusun berdasarkan pertanyaannya. Untuk seberapa baik model mengurutkan akun, dipakai AP, Precision at k, Recall at k, dan AUROC. Untuk melihat apakah model lebih baik dari aktivitas dan usia, dipakai AUC di dalam sel, yaitu membandingkan akun yang aktivitas dan usianya setara. Untuk kecepatan penandaan, dipakai AURT. Untuk kalibrasi, dipakai Brier dan ECE. Dan untuk memastikan selisihnya nyata, dipakai paired cluster bootstrap per blok ID dengan koreksi Holm.

*(Tunjuk kartu AURT.)*

AURT ini pada dasarnya luas di bawah kurva recall terhadap waktu. Makin banyak dan makin cepat akun hilang tertangkap, makin besar nilainya.

Hipotesis dinyatakan didukung kalau batas bawah interval kepercayaan 95 persen dari selisihnya berada di atas nol, dan untuk AP, selisihnya minimal 0,01. Semua metrik dihitung terhadap akun hilang, bukan terhadap pelanggaran.

## Penutup

Hasil akhirnya belum saya tampilkan di sini. Fokus hari ini adalah masalah, posisi, data, metode, dan cara evaluasinya.

*(Sesuaikan kalimat berikut dengan aturan mata kuliah.)*

Sebagai catatan, pipeline penelitian ini dibangun dengan bantuan Claude Code.

Demikian presentasi dari saya. Terima kasih atas perhatiannya, dan saya persilakan kalau ada pertanyaan atau masukan.
