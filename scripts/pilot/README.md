# Referensi pilot

Skrip eksplorasi satu kali pada jam dev `2024-04-01-15`, dijalankan 2026-11-10, tidak dipraregistrasi. Isinya hanya referensi definisi fitur dan angka sanity check di `docs/07`, bukan bagian pipeline.

- `pilot_signal.py`: definisi 48 fitur perilaku dan 10 proksi koordinasi.
- `pilot_blocks.py`: split blok ID lebar tetap dan AUC dalam sel.
- `pilot_leakage.py`: pengelompokan berantai. Hasilnya degeneratif dan tidak boleh dikutip sebagai bukti leakage.
- `pilot_neighbors.py`: fitur tetangga ID. Tidak menambah nilai, jadi tidak dipakai.
- `ghost_check.py`, `pilot_webcheck.py`: validasi arti label.
- `precheck.py`: uji sinyal awal.
- `*_result.json`: hasil agregat.

Path di dalam skrip menunjuk folder sementara yang sudah tidak ada. Daftar akun dan label tidak disertakan.
