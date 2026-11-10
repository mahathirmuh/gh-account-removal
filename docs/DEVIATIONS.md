# Catatan penyimpangan

Diisi setelah tag `prereg-v1`. Satu entri per penyimpangan. Laporkan hasil dengan dan tanpa perubahan.

| Tanggal | Apa yang berubah | Kenapa | Dampak | Commit |
| --- | --- | --- | --- | --- |
| 2026-11-10 | Urutan Gerbang C dan D ditukar: holdout dibuka sebelum audit manual dua anotator | Anotator manusia belum tersedia, dan pengguna mendelegasikan penyelesaian pipeline | Audit memakai `w2` dan tidak mengubah fitur, parameter, atau ambang. Hasil audit hanya memengaruhi penafsiran label | commit Gerbang D |
| 2026-11-10 | Sensitivitas yang disebut `docs/06` dan spec nb12 serta nb15 baru ditulis setelah tag `prereg-v1`, sebelum holdout dibuka | Terlewat saat implementasi, ditemukan saat pemeriksaan sebelum Gerbang D | Bagian `locked` tidak berubah. Analisis ini eksploratif dan tidak memengaruhi keputusan hipotesis | 4d8f9f8 |
| 2026-11-10 | Rancangan dibekukan dengan tag git lokal, bukan pendaftaran pada layanan publik | Tidak ada pendaftaran OSF sebelum model dilatih pada jam studi | Paper menyebutnya rancangan yang dibekukan sebelum analisis, bukan pra-registrasi | f04dbd3 |
