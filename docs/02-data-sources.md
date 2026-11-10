# 02 — Sumber data

Semua fakta di bawah diperiksa pada 2026-11-10. Kalau kenyataan berbeda dari dokumen ini: berhenti, laporkan, tanya.

## GH Archive

| Hal | Nilai |
| --- | --- |
| URL | `https://data.gharchive.org/{hour_id}.json.gz` |
| Penamaan jam | Tanpa nol di depan, misalnya `2024-04-09-3` |
| Format | NDJSON terkompresi gzip, satu event per baris |
| Jam studi | 24 jam, daftar di `params.yaml`; semua merespons 200, total 2,28 GB terkompresi |
| Jam dev | `2024-04-01-15`; 138.944.498 byte terkompresi |
| File lokal pengguna | `2024-04-01-15.json/2024-04-01-15.json`, 1.000.777.728 byte, 272.191 baris |

nb01 mengunduh jam dev versi `.json.gz` dan membandingkan jumlah baris serta rentang waktunya dengan file lokal. File lokal tidak boleh dipindahkan atau dihapus.

### Skema yang teramati pada jam dev

Kunci level atas: `id`, `type`, `actor`, `repo`, `payload`, `public`, `created_at`, dan `org` (opsional, ada pada 63.524 dari 272.191 event). Semua event `public = true`.

- `actor`: `id`, `login`, `display_login`, `gravatar_id`, `url`, `avatar_url`.
- `repo`: `id`, `name`, `url`.

| Tipe event | Jumlah | Field payload yang dipakai |
| --- | ---: | --- |
| PushEvent | 158.172 | `size`, `distinct_size`, `commits[].message`, `commits[].author.email`, `commits[].distinct` |
| CreateEvent | 38.178 | `ref_type` (`branch`, `repository`, `tag`) |
| PullRequestEvent | 19.225 | `action` (`opened`, `closed`, `reopened`), `pull_request.author_association` |
| DeleteEvent | 13.897 | `ref_type` (`branch`, `tag`) |
| WatchEvent | 12.270 | `action` (`started`) |
| IssueCommentEvent | 11.183 | `action`, `comment.url` |
| PullRequestReviewEvent | 5.797 | `action` |
| IssuesEvent | 3.953 | `action` (`opened`, `closed`, `reopened`), `issue.url` |
| PullRequestReviewCommentEvent | 3.240 | `action`, `comment.url` |
| ForkEvent | 2.580 | — |
| ReleaseEvent | 1.200 | `action` |
| PublicEvent | 944 | payload kosong |
| MemberEvent | 855 | `action` |
| GollumEvent | 407 | — |
| CommitCommentEvent | 290 | `comment.url` |

### Jebakan

- `PushEvent.commits` terpotong pada 20 commit: pada jam dev, 1.076 dari 158.172 push punya `size > len(commits)`. Hitungan commit memakai `size`; fitur pesan hanya memakai commit yang ada di payload.
- GH Archive adalah poller satu halaman atas Events API, sehingga kehilangan event saat lonjakan tidak terukur. nb01 mengecek hitungan event per menit tiap jam.
- Ada laporan penurunan tangkapan sejak Mei 2025 (`igrigorik/gharchive.org#310`) dan pemangkasan payload Events API sejak 2025-10-07. Jam studi April–Mei 2024 ada sebelum keduanya, tetapi tetap periksa tiap jam. Jangan menambah jam dari 2025 atau setelahnya tanpa bertanya.
- Latensi Events API tercatat 30 detik sampai 6 jam. Jendela di studi ini adalah event-time dari `created_at` pada data arsip, bukan deteksi real-time.
- `actor` pada `PushEvent` adalah pengirim push, bukan penulis commit.

## GitHub API

Token klasik tanpa scope, dari `~/.dm-git.env`, cukup untuk data publik. Batas: 5.000 request per jam untuk REST dan 5.000 poin per jam untuk GraphQL. Batas sekunder: 100 request bersamaan, 900 poin per menit (REST), 2.000 poin per menit (GraphQL).

### Jalur utama: GraphQL `nodes`

```graphql
query($ids:[ID!]!){
  rateLimit{cost remaining resetAt}
  nodes(ids:$ids){ __typename ... on User{databaseId createdAt} ... on Organization{databaseId createdAt} }
}
```

- ID disusun dari ID numerik: `base64("04:User" + actor_id)`.
- Maksimum 100 ID per query. Pada pilot, biaya 1 poin per query dan sekitar 2,2 detik per query, berurutan.
- ID yang tidak ter-resolve menghasilkan `null` pada posisinya, plus entri `errors` bertipe `NOT_FOUND`, dengan HTTP 200.
- Tiap node yang ter-resolve memberi peringatan `DEPRECATION` di `extensions.warnings`, dengan `data.next_global_id`. Format ID lama masih berfungsi pada 2026-11-10, tetapi bisa berhenti. Catat jumlah peringatan, dan jangan menganggapnya error.
- Node bertipe `Organization` berarti akun pernah dikonversi. Perlakukan sebagai `present`.

### Jalur cadangan dan verifikasi: REST

`GET /user/{account_id}` memakai "durable user ID", jadi akun yang ganti nama tetap ter-resolve. Dokumentasi hanya mencantumkan 200 dan 404. Akun Enterprise Managed Users juga bisa 404, tetapi pada jam dev tidak ada login bergaris bawah.

Kalau GraphQL `nodes` berhenti menerima ID lama, berhenti dan tanya. Jalur REST untuk semua akun tidak praktis (sekitar 13 jam per 65 ribu akun), jadi opsinya memakai `fallback_min_events` atau `next_global_id`.

### Verifikasi `ghost`

GitHub memindahkan issue, PR, dan komentar akun yang dihapus ke pengguna `ghost`. `comment.url`, `issue.url`, dan `pull_request.url` di payload dipakai untuk memeriksanya. **Wajib:** hanya URL berawalan `https://api.github.com/repos/` yang boleh dipanggil, karena token ikut terkirim.

## Halaman profil publik

nb05 mengirim HEAD ke `https://github.com/{login}` pada sampel kecil untuk cek silang, tanpa token, satu request per `sleep_seconds`, redirect tidak diikuti. Login hanya berada di memori selama pemeriksaan. Berhenti setelah tiga respons 429.

## Alat eksternal

| Alat | Cara memperoleh | Catatan |
| --- | --- | --- |
| M-Zoom | `tools/mzoom`, diunduh tetapi **tidak dijalankan** | Sistem izin memblokir eksekusi kode yang diunduh dari luar. Pipeline memakai implementasi greedy peeling sendiri di `features/dense_blocks.py` |
| RABBIT-ng | **Tidak dipasang** | Alasan sama. Baseline ini opsional, jadi dilaporkan sebagai keterbatasan |

## Lisensi, kebijakan, dan privasi

- [Acceptable Use Policies GitHub](https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies) mengizinkan riset atas informasi publik non-pribadi hanya bila publikasinya open access. Syarat ini juga berlaku untuk cek silang halaman profil.
- GH Archive memuat login dan email. Email dibuang saat parse; login diganti pseudonim HMAC.
- Rilis dataset harus menghapus login, email, dan ID mentah. Pseudonimisasi tetap rapuh karena urutan event bisa ditautkan kembali ke GH Archive publik.
- Label "akun hilang" pada akun orang bisa dibaca sebagai tuduhan, jadi tidak ada akun yang disebut di luaran.
