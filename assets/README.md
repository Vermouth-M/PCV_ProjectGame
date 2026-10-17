# Folder Assets

Taruh gambar buatanmu di sini. **Folder ini sengaja dikosongkan**: game tetap
jalan penuh tanpa aset apa pun. Bagian yang file-nya belum ada otomatis memakai
gambar vektor bawaan, jadi kamu bisa menambah aset **satu per satu**.

Cek mana yang sudah/belum terbaca:

```bash
python tools/check_assets.py
```

Saat game dibuka, ringkasan yang sama muncul di terminal
(`[assets] 5/18 aset ditemukan ...`).

## Aturan penamaan

- Nama file **huruf kecil**, tanpa spasi. Ekstensi: `png` (disarankan, mendukung
  transparansi), `webp`, `jpg`, `jpeg`.
- **Gambar tunggal**: `nama.png`
- **Animasi**: `nama_0.png`, `nama_1.png`, `nama_2.png`, ... berurutan dari **0**
  (angka tanpa nol di depan, mis. `walk_1` bukan `walk_01`). Pemuatan berhenti di
  nomor yang bolong, jadi jangan lewatkan nomor.
- Kalau ada `nama_0.png` dan `nama.png` sekaligus, versi animasi yang dipakai.
- Pakai **latar transparan** untuk sprite dan efek.

## Daftar aset yang dikenali

### Sprite karakter (`sprites/`)

| File (tanpa ekstensi)                        | Isi                         | Catatan |
|----------------------------------------------|-----------------------------|---------|
| `sprites/player/idle` (`_0`, `_1`, ...)      | Pemain diam                 | Gambar **menghadap kanan**; di-flip otomatis saat jalan ke kiri |
| `sprites/player/walk` (`_0`, `_1`, ...)      | Pemain berjalan             | Sama. Kalau `idle` tidak ada, frame pertama `walk` dipakai saat diam |
| `sprites/enemies/basic_walk` atau `basic`    | Musuh biasa                 | Menghadap kanan, otomatis menoleh ke arah pemain |
| `sprites/enemies/fast_walk` atau `fast`      | Musuh cepat                 | Sama |
| `sprites/enemies/tank_walk` atau `tank`      | Musuh tank                  | Sama |
| `sprites/pickups/xp_orb`                     | Orb XP                      | Boleh animasi |
| `sprites/projectiles/bullet`                 | Peluru serangan dasar       | Menghadap **kanan**; diputar mengikuti arah tembakan |

Musuh: urutan prioritas `<jenis>_walk_*` lalu `<jenis>`. Kilat putih saat kena hit
dan kedipan merah saat pemain kena hit dibuat otomatis, tidak perlu gambar terpisah.

### Efek jurus (`effects/`)

Efek diregangkan & diputar otomatis, jadi cukup gambar **satu** ilustrasi.

| File                          | Jurus            | Cara menggambarnya |
|-------------------------------|------------------|--------------------|
| `effects/triangle_slash`      | Segitiga Pedang  | **Pangkal di tengah sisi KIRI**, ujung/bilah menuju kanan. Diregangkan jadi radius x lebar busur lalu diputar ke arah hadap pemain |
| `effects/circle_shockwave`    | Lingkaran        | Gambar **persegi**, lingkaran/cincin memenuhi gambar dan berpusat. Membesar & memudar |
| `effects/line_slash`          | Garis Tebasan    | **Pangkal di tengah sisi KIRI**, menuju kanan. Diregangkan sepanjang tebasan (420 px) |
| `effects/lightning`           | Zigzag Petir     | **Pangkal di tengah sisi KIRI**, menuju kanan. Satu gambar diregangkan untuk tiap sambungan antar musuh |
| `effects/shield`              | Kotak Perisai    | Gambar **persegi**, berpusat di karakter; berdenyut otomatis |

> "Pangkal di tengah sisi kiri" artinya titik awal efek (posisi pemain / titik
> awal petir) adalah tepi kiri gambar di tengah tingginya.

### Latar & UI

| File                                | Isi                          | Catatan |
|-------------------------------------|------------------------------|---------|
| `backgrounds/ground`                | Tile lantai                  | Harus **seamless** (bisa disambung ke segala arah). Disusun berulang & bergeser mengikuti kamera. Ukuran bebas, mis. 128 atau 256 px |
| `ui/skill_triangle`, `skill_circle`, `skill_square`, `skill_line`, `skill_zigzag` | Ikon jurus di HUD | Persegi kecil; diperkecil ke 20 px. Redup otomatis saat cooldown |

## Ukuran gambar

Ukuran file bebas; game menyesuaikan lewat `config.py`:

- Sprite pemain/musuh/orb/peluru: sisi terpanjang = diameter hitbox x
  `SPRITE_SCALE` (default pemain 70 px, musuh biasa 56 px, orb 30 px). Rasio
  aspek gambar dipertahankan. Disarankan menggambar **lebih besar** (mis. 2x)
  daripada ukuran tampil agar tetap tajam.
- Kecepatan animasi: `ANIM_FPS`.
- Tebal petir: `LIGHTNING_THICKNESS`. Skala tile latar: `BACKGROUND_TILE_SCALE`.
- Mematikan semua aset sementara (paksa vektor): `USE_ASSETS = False`.

Hitbox/tabrakan **tidak** berubah mengikuti ukuran gambar (tetap `radius` di
`config.ENEMY_STATS` / `PLAYER_RADIUS`); sprite hanya tampilan.

## Struktur folder

```
assets/
├── sprites/
│   ├── player/        idle_*.png, walk_*.png
│   ├── enemies/       basic_walk_*.png / basic.png, fast..., tank...
│   ├── pickups/       xp_orb.png
│   └── projectiles/   bullet.png
├── effects/           triangle_slash.png, circle_shockwave.png, line_slash.png,
│                      lightning.png, shield.png
├── backgrounds/       ground.png
└── ui/                skill_triangle.png, skill_circle.png, skill_square.png,
                       skill_line.png, skill_zigzag.png
```

File `.gitkeep` di tiap folder hanya penanda agar folder kosong ikut tersimpan;
boleh dihapus setelah folder terisi.

## Kalau gambar tidak muncul

- Jalankan `python tools/check_assets.py`: statusnya `[belum]` berarti nama/folder belum cocok.
- Pastikan huruf kecil dan tidak ada nomor yang bolong pada animasi.
- File rusak atau format tidak didukung: game mencetak `PERINGATAN: gagal memuat ...`
  di terminal lalu memakai gambar vektor.
