# Catatan penyimpangan

Diisi setelah tag `prereg-v1`. Satu entri per penyimpangan. Laporkan hasil dengan dan tanpa perubahan.

| Tanggal | Apa yang berubah | Kenapa | Dampak | Commit |
| --- | --- | --- | --- | --- |
| 2026-11-10 | Urutan Gerbang C dan D ditukar: holdout dibuka sebelum audit manual dua anotator | Anotator manusia belum tersedia, dan pengguna mendelegasikan penyelesaian pipeline | Audit memakai `w2` dan tidak mengubah fitur, parameter, atau ambang. Hasil audit hanya memengaruhi penafsiran label | commit Gerbang D |
| 2026-11-10 | Sensitivitas yang disebut `docs/06` dan spec nb12 serta nb15 baru ditulis setelah tag `prereg-v1`, sebelum holdout dibuka | Terlewat saat implementasi, ditemukan saat pemeriksaan sebelum Gerbang D | Bagian `locked` tidak berubah. Analisis ini eksploratif dan tidak memengaruhi keputusan hipotesis | 4d8f9f8 |
| 2026-11-10 | Rancangan dibekukan dengan tag git lokal, bukan pendaftaran pada layanan publik | Tidak ada pendaftaran OSF sebelum model dilatih pada jam studi | Paper menyebutnya rancangan yang dibekukan sebelum analisis, bukan pra-registrasi | f04dbd3 |
| 2026-11-10 | Urutan baris `load_frame` berbeda antarproses, sehingga skor model sedikit berubah saat dijalankan ulang | Polars tidak menjamin urutan hasil `unique` dan `join`; ditemukan setelah holdout dibuka | Angka konfirmatori tetap dari satu run nb15. Run ulang eksploratif memberi AP `M_behav` 5-19 F3 0,255 sampai 0,260 dan selisih AURT H4a 0,044, dibanding 0,058 pada nb15. Perbaikan berupa pengurutan di `load_frame` belum diterapkan supaya kode sama dengan yang menghasilkan angka | dde2836 |
| 2026-11-10 | Riwayat git ditulis ulang untuk membersihkan metadata commit sebelum push | Permintaan pengguna | Isi tiap commit, author, dan waktu tidak berubah. Hash di `results/run_log.jsonl`, `results/holdout_opened.json`, keluaran notebook, dan baris di atas adalah hash lama, lihat peta di bawah | setelah fa65455 |

## Peta hash setelah penulisan ulang riwayat

| Hash lama | Hash baru |
| --- | --- |
| 4bb8558 | fa65455 |
| dde2836 | 9e39fd6 |
| 7a81136 | fde8159 |
| 4d8f9f8 | 45f3991 |
| f04dbd3 | 0823d6d |
| abfcd4a | dc26178 |
| 8fcd71f | a41da63 |
| d0981d5 | e3337da |
| ee7014a | 35484d0 |
| bdf6ff7 | 4a3c52f |
