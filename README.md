# Prediksi Akun GitHub Hilang dari Jendela Pendek Event Publik

Paket brief untuk membangun pipeline data dan notebook paper **"Predicting GitHub Account Removal from Short Public Event Windows: A Split-Design Audit and an Adaptive Early-Flagging Policy"** (judul kerja) dengan Claude Code.

## Isi paket

- `CLAUDE.md`: instruksi kerja untuk Claude Code (dibaca otomatis).
- `docs/00`: ringkasan SOTA dan posisi novelty. Versi lengkap ada di `reports/`.
- `docs/01`–`08`: desain riset, sumber data, model data, protokol label, fitur, metode, validasi, daftar figur dan tabel.
- `notebooks/specs/00`–`16`: spesifikasi 17 notebook.

Belum ada kode. Claude Code yang membangun `src/`, `tests/`, `config/`, dan notebook dari dokumen ini.

## Cara memakai

1. Pastikan token GitHub ada di `~/.dm-git.env` (format `GITHUB_TOKEN=...`, tanpa scope).
2. Buka Claude Code di root folder ini.
3. Kirim prompt awal berikut:

```
Baca CLAUDE.md, lalu semua file di docs/ dan notebooks/specs/.
Kerjakan Fase 0: git init, scaffold repo, pyproject.toml (uv), Makefile, config/ dari blok YAML di docs/01,
paket src/ghremoval kosong dengan modul sesuai spec, tests dasar, dan notebook 00.
Setelah itu lanjut Fase 1 (notebook 01–03). Berhenti di setiap gerbang manusia.
Sebelum mulai, sebutkan asumsi atau bagian dokumen yang menurutmu ambigu.
```

4. Lanjutkan per fase. Setiap gerbang (A–D) butuh tindakan kamu; Claude Code akan berhenti dan menjelaskan apa yang perlu diisi.

## Alur besar

```
GH Archive 24 jam + 1 jam dev
        │
   nb01–03 ingest, event, kohort
        │
   nb04–05 snapshot status, validasi label ── Gerbang A
        │
   nb06–08 fitur, blok padat, replikasi pilot ── Gerbang B (prereg-v1)
        │
   ┌────┼─────────┬────────────┬──────────────┐
 nb09  nb10      nb11         nb12           nb13
 audit model     PU           latensi dan    ablasi
 split kontrol                kebijakan      koordinasi
       │                      adaptif
   nb14 audit manual ── Gerbang C
        │
   nb15 holdout dibuka sekali ── Gerbang D
        │
   nb16 figur, tabel, numbers.json
```

## Gerbang manusia

| Gerbang | Kapan | Yang kamu lakukan | Perkiraan waktu |
| --- | --- | --- | --- |
| A | Setelah nb05 | Review validasi label, putuskan label layak dipakai | 30 menit |
| B | Setelah nb08 | Konfirmasi replikasi pilot, kunci parameter (tag `prereg-v1`) | 15 menit |
| C | Setelah nb14 `sample` | Dua anotator mengaudit 200 akun | 3–4 jam per anotator |
| D | Sebelum nb15 | Nyatakan desain final, holdout dibuka satu kali | 5 menit |

Gerbang C paling berat. Kalau anotator kedua terbatas, turunkan `double_annotation_fraction` di `params.yaml` (minimum 0.2), dengan konsekuensi κ dihitung pada subset saja.

## Keputusan yang masih terbuka

Isi sebelum Gerbang B, karena memengaruhi parameter yang dikunci:

1. **Standar novelty dosen.** Posisi saat ini adalah kontribusi empiris dan evaluatif ditambah satu metode usulan terapan. Konfirmasi bahwa ini cukup.
2. **Target luaran:** tugas mata kuliah, jurnal nasional, atau konferensi internasional. Syarat AUP GitHub: riset atas informasi publik non-pribadi hanya boleh bila publikasinya open access.
3. **Anotator kedua:** siapa, dan berapa akun yang sanggup diaudit.
4. **Snapshot kedua:** apakah waktu proyek mengizinkan snapshot status kedua, minimal 30 hari setelah yang pertama. Kalau tidak, bagian validasi prospektif di RQ3 dilewati.

## Kebutuhan teknis

- Python ≥ 3.11 dan `uv`, keduanya sudah ada.
- Disk kosong sekitar 40 GB. Raw 24 jam sekitar 2,3 GB terkompresi.
- RAM 31 GB, CPU 20 core, GPU RTX 5090 untuk MLP.
- Koneksi ke `data.gharchive.org`, `api.github.com`, `github.com`, `raw.githubusercontent.com`.
- Java 8 JRE sudah ada untuk M-Zoom.

## Status bukti saat ini

Semua angka pilot berasal dari satu jam pengembangan yang tidak dipraregistrasi. Angka itu dipakai sebagai sanity check dan arah desain, bukan temuan. Jam dev tidak boleh masuk train, validasi, maupun holdout.

## Data dan etika

GH Archive berisi aktivitas publik, tetapi tetap memuat data pribadi. Email commit dibuang saat ingest, login dipseudonimkan, dan tidak ada akun yang disebut namanya di luaran. Label "akun hilang" tidak berarti akun melanggar aturan. Detail di `docs/02` dan `docs/04`.
