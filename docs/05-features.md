# 05 — Jendela, kohort, dan fitur

## Jendela

Jendela `w` ∈ `windows_minutes` mencakup event dengan `second_of_hour < 60·w`, berjangkar pada awal jam (event-time). Jendela terikat batas file: ledakan yang melewati batas jam akan terpotong, dan ini dinyatakan di ancaman validitas.

Semua fitur pada jendela `w` hanya boleh memakai event sebelum `60·w` detik.

## Kohort

| Kohort | Definisi | Kegunaan | Catatan |
| --- | --- | --- | --- |
| Tetap | `n_events ≥ fixed_min_events` dalam 60 menit, bukan `[bot]` | Mengukur hilangnya informasi saat jendela dipendekkan | Seleksinya memakai aktivitas masa depan |
| Deployable | ≥ `deployable_min_events` event dalam `w` menit, bukan `[bot]` | Menjawab pertanyaan operasional | Tanpa informasi masa depan; populasi berbeda per `w` |
| Strata rendah | `n_events` 1 atau 2–4 dalam 60 menit | Deskriptif, supaya klaim tidak hanya tentang minoritas akun | Hanya pada jendela 60 menit |

Akun `[bot]` dikeluarkan dari semua kohort dan dilaporkan terpisah.

Akun kohort tetap yang belum punya event sebelum cutoff jendela `w` tidak punya baris fitur pada jendela itu, dan dianggap belum muncul.

## Fitur dasar

| Fitur | Definisi |
| --- | --- |
| `n_events_log` | `log1p(n_events)` |
| `n_events_coarse` | `floor(log2(n_events))` |
| `id_recency_log` | `log1p(max_id_in_hour − actor_id)` |
| `age_bin12` | 12 kuantil `id_recency`; batas dihitung hanya dari train |

Jangan memakai `actor_id` mentah pada lengan forward. Nilainya tidak stasioner antarjam, jadi `id_recency` wajib dipakai.

## Fitur perilaku (48)

Definisi ini mengikuti pilot. `g` adalah selisih detik antar-event berurutan milik akun itu. Jika hanya ada satu event, `g = [0]`.

### Keluarga `type_mix` (16)

- `share_<type>` untuk 15 tipe event: jumlah tipe dibagi `n_events`.
- `n_event_types`: jumlah tipe berbeda.

### Keluarga `temporal` (11)

`n_active_minutes`, `gap_mean`, `gap_std`, `gap_cv` (`std/mean`), `burstiness` (`(std−mean)/(std+mean)`), `gap_min`, `share_zero_gap`, `share_modal_gap` (porsi selisih yang sama dengan modus), `span_seconds`, `minute_entropy`, `max_events_per_minute`.

### Keluarga `repo` (6)

`n_repos`, `repos_per_event`, `repo_entropy`, `top_repo_share`, `share_own_repo`, `share_org_events`.

### Keluarga `push` (4)

`push_size_mean`, `push_size_max`, `push_size_sum`, `push_distinct_ratio` (`sum distinct / sum size`).

### Keluarga `commit_msg` (4)

`n_commit_msgs`, `msg_unique_ratio`, `msg_len_mean`, `msg_top_share` (porsi hash terbanyak).

### Keluarga `create_pr` (4)

`n_new_repos`, `n_new_branches`, `n_new_tags`, `pr_author_none_ratio` (porsi PR `opened` dengan `author_association = NONE`; −1 bila tidak ada PR `opened`).

### Keluarga `repo_names` (3)

`repo_short_len_mean`, `repo_short_digit_share`, `repo_short_unique_per_event`.

Set `robust28` membuang keluarga `temporal`, `repo`, dan `repo_names`, karena keluarga ini paling mudah menjadi sidik jari kampanye. Set ini dipakai sebagai sensitivitas, bukan sebagai pertahanan yang diklaim.

## Proksi koordinasi (10)

Dihitung atas semua akun yang aktif pada jendela yang sama, tanpa label.

- Pesan commit: `msg_others_max`, `msg_others_log_mean`, `msg_any_shared`, `msg_share_1_50`, berdasarkan banyaknya akun lain yang memakai `msg_hash` yang sama.
- Repo: `repo_others_max`, `repo_others_log_mean`, `repo_any_shared`.
- Nama repo: `short_others_max`, `short_others_log_mean`, `short_any_shared`, berdasarkan `repo_short_hash`.

## Fitur dense-block (K5)

Tensor per jam dan per jendela: mode `actor_id × repo_id × event_type × minute`, nilai = jumlah event. Dibangun hanya dari event sebelum `60·w` detik. Jalankan M-Zoom dengan densitas `dense_blocks.density`, ambil `top_k_blocks` blok.

Per akun: `in_any_block`, `best_block_rank`, `best_block_density`, `best_block_n_accounts`, `best_block_n_repos`, `share_events_in_blocks`, `n_blocks`, dan `n_event_types_in_best_block` (ukuran lintas-event).

Blok dihitung ulang per jam dan per jendela. Label tidak boleh dipakai saat mining.

## Fitur baseline literatur (opsional)

| Baseline | Bentuk |
| --- | --- |
| RABBIT-ng offline | Skor dari event dalam jendela, hanya untuk akun ≥ 5 event. BIMBAS dilatih pada histori sampai 300 event, jadi hasil pada jendela pendek adalah pergeseran distribusi; catat ini saat melaporkan |
| Interval ala Du et al. | Hitungan interval antar-operasi 1, 2, 3 menit dan 1 jam |
| Signature StarScout | Pola low-activity pada `WatchEvent` |
| Heuristik nama | `login_len`, `login_digit_ratio`, `login_hyphen_count` |

## Uji kebocoran fitur

Wajib ada di `tests/`:

1. Menambah event pada detik ≥ `60·w` tidak mengubah fitur jendela `w`.
2. Mengubah label tidak mengubah fitur apa pun.
3. Batas bin usia dan statistik praproses dihitung hanya dari train.
4. Fitur koordinasi jendela `w` tidak memakai event sesudah `60·w` detik.
