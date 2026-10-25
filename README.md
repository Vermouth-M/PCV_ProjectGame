# Vampire Gesture Survivor

Game bergaya *Vampire Survivors* dengan **Pygame**. Twist-nya: kamu
mengeluarkan **jurus** dengan menggambar pola di udara memakai
**sarung tangan hitam** di depan webcam. Deteksi memakai **OpenCV murni**
(tanpa MediaPipe, tanpa model machine-learning) dan **hanya melacak warna**:
hitam.

## Fitur

- Survival ala Vampire Survivors: musuh makin kuat seiring waktu, kumpulkan
  XP, naik level. Gerak dengan **WASD**.
- **5 jurus**, dipicu dengan menahan **SPASI** lalu menggambar bentuk:

  | Bentuk        | Jurus                           | Efek                                   |
  |---------------|---------------------------------|----------------------------------------|
  | Segitiga      | Jurus Segitiga Pedang           | Tebasan area di depan pemain           |
  | Lingkaran     | Jurus Lingkaran Gelombang Kejut | Ledakan 360° + knockback               |
  | Garis lurus   | Jurus Garis Tebasan             | Tebasan lurus menembus musuh           |
  | Zigzag        | Jurus Zigzag Petir              | Petir loncat antar musuh               |

- **Pembeda rambut vs sarung tangan**: rambut hitam tidak lagi dikira sarung
  tangan (lewat kalibrasi otomatis, lihat di bawah).
- **Bar pencahayaan** di atas preview kamera + **kompensasi otomatis**:
  ambang "hitam" menyesuaikan terang/redupnya ruangan.
- Preview kamera besar dengan penanda tracking (zona diabaikan, posisi
  sarung tangan, lintasan gestur).
- Fallback tombol `1`-`4` untuk memicu jurus tanpa kamera.
- **Menu lengkap**: menu utama, Tes Kamera, Cara Bermain, Pengaturan (tersimpan),
  menu Jeda, dan layar Game Over. Bisa dipakai dengan keyboard maupun mouse.

## Struktur Folder

```
vampire_gesture_survivor/
├── main.py                      # entry point
├── config.py                    # semua konstanta (gameplay, tracking, aset)
├── requirements.txt
├── README.md
│
├── assets/                      # TEMPAT ASET GAMBAR (sengaja kosong; isi sendiri)
│   ├── README.md                  # daftar nama file, orientasi, ukuran
│   ├── sprites/                   # player/ enemies/ pickups/ projectiles/
│   ├── effects/                   # efek 5 jurus + perisai
│   ├── backgrounds/               # tile lantai
│   └── ui/                        # ikon jurus
│
├── game/                        # logika gameplay (tidak menyentuh kamera)
│   ├── engine.py                  # loop utama & orkestrasi
│   ├── player.py  enemy.py  spawner.py  pickups.py  projectile.py
│   ├── skills.py                  # 5 jurus + efek (sprite atau vektor)
│   ├── settings.py                # pengaturan yang tersimpan ke settings.json
│   ├── screens/                   # layar-layar menu
│   │   ├── main_menu.py             # menu utama
│   │   ├── how_to_play.py           # cara bermain
│   │   ├── settings_screen.py       # pengaturan
│   │   ├── camera_test.py           # tes kamera + latihan jurus
│   │   ├── overlays.py              # jeda & game over
│   │   ├── widgets.py               # Menu (keyboard+mouse), teks, ikon bentuk
│   │   └── base.py                  # kelas dasar Screen
│   ├── assets.py                  # pemuat aset: cache, skala, flip, rotasi + fallback vektor
│   ├── animation.py               # animasi frame demi frame
│   ├── background.py              # latar (tile gambar atau grid vektor)
│   ├── ui.py                      # HUD, bar pencahayaan, banner kalibrasi, ikon jurus
│   ├── camera_overlay.py          # panel preview kamera + penanda tracking
│   └── utils.py
│
├── gesture/                     # semua yang berhubungan dengan kamera/OpenCV
│   ├── hand_tracker.py            # pelacak sarung tangan hitam (gabungan semua lapisan)
│   ├── lighting.py                # pemantau cahaya + ambang hitam adaptif
│   ├── background_filter.py       # pembeda rambut/benda hitam diam (kalibrasi)
│   ├── gesture_recorder.py        # rekam lintasan selama SPASI ditahan
│   ├── shape_classifier.py        # lintasan -> nama bentuk (geometri murni)
│   └── gesture_thread.py          # kamera di thread terpisah (anti-lag)
│
├── tools/
│   └── check_assets.py            # cek aset mana yang sudah/belum terbaca
│
└── tests/
    ├── test_shape_classifier.py   # tes pengenalan bentuk
    ├── test_black_tracking.py     # tes pencahayaan, rambut vs sarung tangan, kalibrasi
    ├── test_assets.py             # tes sistem aset (sprite, efek, latar, fallback)
    └── test_menu.py               # tes menu, alur layar, jeda, pengaturan, tes kamera
```

## Instalasi

Butuh Python 3.9+ dan webcam.

```bash
conda activate opencv_env
cd vampire_gesture_survivor
pip install pygame          # opencv-python & numpy biasanya sudah ada di env
python main.py
```

Tanpa webcam (jurus lewat tombol `1`-`5` saat bermain):

```bash
python main.py --no-camera
```

(`pip install -r requirements.txt` juga bisa; isinya hanya `pygame`,
`opencv-python`, `numpy`.)

## Kontrol

| Tombol          | Fungsi                                                                  |
|-----------------|--------------------------------------------------------------------------|
| `W A S D`       | Gerak                                                                   |
| Tahan `SPASI`   | Mulai merekam lintasan sarung tangan (musuh melambat = mode fokus)      |
| Lepas `SPASI`   | Bentuk dikenali, jurus keluar                                           |
| `C`             | **Kalibrasi ulang** rambut/benda hitam diam (game membeku sebentar)     |
| `M`             | Tampilkan mask hitam di panel kamera (untuk memeriksa tracking)         |
| `1` - `5`       | Picu jurus tanpa kamera (segitiga/lingkaran/kotak/garis/zigzag)         |
| `ESC`           | **Jeda** (membuka menu jeda); `Esc` lagi untuk lanjut                   |
| `R`             | Main lagi (di layar Game Over)                                          |

## Menu

Semua menu: **W/S atau panah** memilih, **Enter atau klik mouse** menjalankan,
**Esc** kembali.

| Layar          | Isi                                                                          |
|----------------|-------------------------------------------------------------------------------|
| **Menu Utama** | Mulai Game, Tes Kamera, Cara Bermain, Pengaturan, Keluar. Menampilkan status kamera & pencahayaan |
| **Tes Kamera** | Preview besar + bar pencahayaan + zona rambut. Tekan `C` kalibrasi, `M` mask, lalu **tahan SPASI dan gambar bentuk** untuk melihat bentuk apa yang dikenali, tanpa musuh. Cocok untuk memeriksa setup sebelum bermain |
| **Cara Bermain** | Kontrol, tabel 5 jurus dengan ikon bentuk, dan tips                        |
| **Pengaturan** | Kamera mode cermin, kalibrasi otomatis, ukuran panel kamera, mode fokus (slow-mo), tombol cadangan 1-5, aset gambar, kembalikan ke bawaan. Panah kiri/kanan (A/D) mengubah nilai |
| **Jeda** (`Esc`) | Lanjutkan, Kalibrasi Ulang, Pengaturan, Menu Utama (ada konfirmasi sebelum permainan dibuang) |
| **Game Over**  | Statistik (waktu bertahan, kill, level), Main Lagi (`R`), Menu Utama (`Esc`) |

Pengaturan **tersimpan otomatis** di `settings.json` (folder proyek) dan dimuat saat game
dibuka. Hapus file itu untuk kembali ke nilai bawaan `config.py`. File yang rusak atau
berisi nilai tidak valid diabaikan.

## Cara Kerja Tracking (tiga lapisan, semua OpenCV murni)

**1. Kompensasi pencahayaan** (`gesture/lighting.py`). Sarung tangan tidak
selalu sama hitamnya: V=60 di ruangan terang, V=20 di ruangan redup. Ambang
tetap akan gagal (di ruangan redup seluruh dinding ikut dianggap hitam).
Maka tiap frame dihitung *level* = persentil ke-75 kecerahan frame
(dihaluskan), lalu ambang hitam = `0.38 × level + 12`, dibatasi 28..95.
Pindah ruangan = ambang menyesuaikan sendiri dalam sekitar 1 detik.

**2. Membedakan rambut dari sarung tangan** (`gesture/background_filter.py`).
Keduanya hitam, jadi warna saja tidak cukup; pembedanya adalah **gerakan**.
Saat kalibrasi (otomatis di awal game, atau tekan `C`), game mengumpulkan
mask hitam selama ±1,5 detik. Piksel yang hitam terus-menerus (≥70% frame)
dianggap benda diam (rambut, bezel monitor, sandaran kursi) dan masuk
**zona diabaikan** (tampil **merah** di preview), dilebarkan 12 px supaya
kepala yang sedikit goyang tetap tertutup. Sarung tangan yang bergerak
tidak hitam terus-menerus di piksel yang sama, jadi tidak ikut terpelajar.

**3. Filter kandidat** (`gesture/hand_tracker.py`). Dari gumpalan hitam yang
tersisa: buang yang terlalu kecil/besar (>25% frame), buang yang bentuknya
tipis/bergerigi (solidity < 0.55, mis. tepi rambut), lalu pilih yang
terbesar, kecuali ada kandidat sepadan yang lebih dekat dengan posisi
terakhir (supaya pelacakan tidak melompat-lompat).

Setelah itu posisi sarung tangan direkam sebagai lintasan selama SPASI
ditahan, dan `gesture/shape_classifier.py` mengubahnya jadi bentuk lewat
geometri (convex hull + `approxPolyDP`, regresi linear, hitung pembalikan arah).

## Bar Pencahayaan

Di atas panel kamera. Penunjuk putih menunjukkan level cahaya saat ini:

| Zona (level 0-255) | Label          | Artinya / yang perlu dilakukan                              |
|--------------------|----------------|--------------------------------------------------------------|
| < 40               | Terlalu gelap  | Nyalakan lampu / pindah tempat. Kompensasi tidak bisa menciptakan kontras yang tidak ada |
| 40 - 80            | Redup          | Masih bisa, tapi tambah cahaya lebih baik                    |
| 80 - 200           | Ideal          | Tidak perlu apa-apa                                          |
| 200 - 232          | Terang         | Aman, ambang otomatis naik                                   |
| > 232              | Terlalu terang | Kurangi cahaya langsung ke kamera / jauhi jendela            |

Baris di bawahnya menampilkan **ambang hitam otomatis** saat ini (`V<..`)
dan persentase frame yang sedang diabaikan.

## Kalibrasi Rambut: kapan dan bagaimana

- Otomatis jalan **saat Mulai Game** (bisa dimatikan di Pengaturan): hitung mundur
  1,5 detik ("Bersiap kalibrasi") supaya sempat menjauhkan sarung tangan, lalu progress
  bar kuning. Duduk diam di posisi bermain, dan **jauhkan sarung tangan dari kamera
  atau gerakkan terus** (jangan didiamkan di depan kamera; sarung tangan yang diam
  ikut diabaikan). "Main Lagi" setelah Game Over tidak mengulang kalibrasi.
- Tekan **`C`** untuk mengulang, misalnya setelah pindah posisi duduk,
  berganti ruangan, atau kepala bergeser jauh. Selama kalibrasi dunia game
  dibekukan dan waktu bertahan tidak berjalan.
- Cek hasilnya di preview: area rambutmu harus **berwarna merah**. Kalau
  tidak, tekan `C` lagi sambil tetap diam. Tekan `M` untuk melihat mask hitam
  (putih = terdeteksi hitam, merah = diabaikan).

| Pengaturan                      | Fungsi                                                          |
|---------------------------------|-----------------------------------------------------------------|
| `BLACK_V_RATIO`, `BLACK_V_OFFSET` | Naikkan jika sarung tangan tak terbaca; turunkan jika terlalu banyak yang terbaca |
| `BLACK_V_MAX_OVERRIDE`          | Isi angka (mis. 60) untuk mematikan mode otomatis dan memakai ambang tetap |
| `GESTURE_EXCLUSION_DILATE`      | Lebar margin zona rambut (px, resolusi 320x240)                 |
| `GESTURE_BLACK_MAX_AREA_RATIO`  | Naikkan jika sarung tangan tampak besar di kamera               |
| `GESTURE_AUTO_CALIBRATE_ON_START` | `False` untuk melewati kalibrasi otomatis di awal             |
| `CAMERA_PANEL_WIDTH/HEIGHT/ALPHA` | Ukuran & transparansi panel kamera                            |
| `CAMERA_MIRROR`                 | `False` untuk mematikan tampilan cermin                         |

## Aset Gambar (Sprite, Efek, Latar)

Folder `assets/` disediakan kosong. Game **tetap jalan penuh tanpa aset**; tiap
gambar yang kamu taruh langsung menggantikan versi vektornya.

```bash
python tools/check_assets.py     # daftar aset yang dikenali + status ada/belum
```

Ringkasan penamaan (detail lengkap, orientasi, dan ukuran ada di `assets/README.md`):

| Yang digantikan        | File                                                                 |
|------------------------|----------------------------------------------------------------------|
| Pemain                 | `sprites/player/idle_0.png ...`, `walk_0.png ...` (menghadap kanan)  |
| Musuh                  | `sprites/enemies/basic_walk_0.png ...` atau `basic.png`; juga `fast`, `tank` |
| Orb XP / Peluru        | `sprites/pickups/xp_orb.png`, `sprites/projectiles/bullet.png`        |
| Efek 5 jurus           | `effects/triangle_slash`, `circle_shockwave`, `line_slash`, `lightning`, `shield` |
| Latar                  | `backgrounds/ground.png` (tile seamless)                             |
| Ikon jurus di HUD      | `ui/skill_triangle.png`, `skill_circle`, `skill_square`, `skill_line`, `skill_zigzag` |

Yang diurus otomatis oleh kode: flip sprite saat menghadap kiri, musuh menoleh ke
pemain, kilat putih saat musuh kena hit, kedip merah saat pemain kena hit, efek
diregangkan/diputar sesuai arah, ikon redup saat cooldown. Hitbox tidak berubah
mengikuti ukuran gambar. Ukuran tampil dan kecepatan animasi diatur di `config.py`
(`SPRITE_SCALE`, `ANIM_FPS`, `LIGHTNING_THICKNESS`, `BACKGROUND_TILE_SCALE`, `USE_ASSETS`).

## Menambah Jurus Baru

1. Definisikan di `config.SKILL_DEFS`.
2. Tambah aturan pengenalan bentuknya di `gesture/shape_classifier.py`.
3. Buat class efek (turunan `SkillEffect`) di `game/skills.py` dan daftarkan
   di `SkillManager.trigger()`.

## Menjalankan Tes

Tidak butuh webcam (memakai scene sintetis):

```bash
python tests/test_shape_classifier.py
python tests/test_black_tracking.py
python tests/test_assets.py
python tests/test_menu.py
```

## Keterbatasan yang Diketahui

- Tes dibuat dengan scene sintetis. Webcam asli punya auto-exposure,
  noise, dan white balance sendiri, jadi `BLACK_V_RATIO`/`BLACK_V_OFFSET`
  mungkin perlu sedikit disetel di perangkatmu.
- Pembeda rambut mengandalkan rambut yang **relatif diam**. Kalau kepala
  bergeser lebih dari margin (±12 px di resolusi kerja) setelah kalibrasi,
  tepi rambut bisa terbaca; tekan `C`.
- Sarung tangan yang bersinggungan dengan zona rambut terpotong di bagian
  yang tumpang tindih, sehingga titiknya sedikit bergeser.
- Di ruangan yang benar-benar gelap, kompensasi tidak bisa menolong karena
  sarung tangan dan latar sama-sama gelap; bar akan memperingatkan.
- Hanya melacak satu titik pusat gumpalan hitam, bukan pose/jari.
