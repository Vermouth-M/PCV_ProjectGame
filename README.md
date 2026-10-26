# Mecha Demon Slayer

**Mecha Demon Slayer** adalah game survival 2D bergaya *Vampire Survivors* yang dibuat menggunakan **Python** dan **Pygame**. Pemain melawan gelombang musuh, mengumpulkan XP, naik level, dan mengaktifkan jurus dengan menggambar bentuk di depan webcam menggunakan **sarung tangan hitam**.

Pelacakan gestur menggunakan **OpenCV dan pemrosesan geometri**, tanpa MediaPipe maupun model machine learning.

## Fitur Utama

- **Survival gameplay** — musuh datang semakin sulit seiring waktu.
- **Level dan XP** — kumpulkan orb XP untuk naik level.
- **Serangan otomatis** — pemain menyerang musuh secara otomatis.
- **Empat gestur jurus** — gambar bentuk sambil menahan `SPASI`.
- **Pelacakan sarung tangan hitam** — deteksi berdasarkan warna dan kontur.
- **Kompensasi pencahayaan otomatis** — ambang warna hitam menyesuaikan kondisi cahaya.
- **Kalibrasi latar belakang** — membantu mengabaikan rambut dan objek gelap yang diam.
- **Preview kamera** — menampilkan hasil pelacakan dan lintasan gestur.
- **Mode tanpa kamera** — jurus dapat diaktifkan melalui tombol keyboard.
- **Menu permainan** — menu utama, tes kamera, panduan bermain, pengaturan, jeda, dan Game Over.
- **Aset visual dan audio** — mendukung sprite, efek jurus, latar, musik, dan efek suara.

## Daftar Jurus

| Bentuk Gestur | Nama Jurus | Efek |
|---|---|---|
| Segitiga | Jurus Segitiga Pedang | Tebasan area di depan pemain |
| Lingkaran | Jurus Lingkaran Gelombang Kejut | Ledakan 360° dan efek knockback |
| Garis lurus | Jurus Garis Tebasan | Tebasan lurus yang menembus musuh |
| Zigzag | Jurus Zigzag Petir | Serangan petir yang berpindah antar musuh |

> Catatan: tombol cadangan dapat digunakan untuk mengaktifkan jurus tanpa menggambar gestur. Periksa menu **Cara Bermain** di dalam game untuk melihat pemetaan tombol yang berlaku.

## Teknologi

- Python 3.9 atau lebih baru
- Pygame 2.5 atau lebih baru
- OpenCV-Python 4.8 atau lebih baru
- NumPy 1.24 atau lebih baru
- Webcam (opsional jika menggunakan mode tanpa kamera)

## Instalasi

### 1. Clone atau unduh proyek

Jika menggunakan Git:

```bash
git clone <URL_REPOSITORY>
cd PCV_ProjectGame
```

Jika proyek sudah diunduh sebagai ZIP, ekstrak ZIP tersebut lalu buka terminal di folder `PCV_ProjectGame`.

### 2. Buat virtual environment (opsional, disarankan)

```bash
python -m venv .venv
```

Aktifkan environment:

**Windows (Command Prompt):**

```bat
.venv\Scripts\activate
```

**Windows (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
```

**Linux/macOS:**

```bash
source .venv/bin/activate
```

### 3. Instal dependensi

```bash
pip install -r requirements.txt
```

### 4. Jalankan game

Dengan webcam:

```bash
python main.py
```

Tanpa webcam:

```bash
python main.py --no-camera
```

Pada mode tanpa kamera, gunakan tombol cadangan jurus yang ditampilkan di menu permainan.

## Kontrol

| Tombol | Fungsi |
|---|---|
| `W`, `A`, `S`, `D` | Menggerakkan pemain |
| Tahan `SPASI` | Mulai merekam gerakan sarung tangan |
| Lepas `SPASI` | Mengakhiri rekaman dan memproses bentuk gestur |
| `C` | Kalibrasi ulang latar belakang saat fitur tersedia |
| `M` | Menampilkan mask deteksi hitam saat fitur tersedia |
| `1`–`5` | Mengaktifkan jurus melalui keyboard tanpa gestur |
| `ESC` | Membuka menu jeda atau kembali dari menu tertentu |
| `R` | Memulai ulang dari layar Game Over |

Menu umumnya dapat dinavigasi menggunakan tombol `W`/`S` atau tombol panah. Gunakan `Enter` atau klik mouse untuk memilih menu.

## Cara Menggunakan Gestur

1. Pastikan webcam terhubung dan dapat diakses oleh aplikasi.
2. Kenakan atau gunakan sarung tangan berwarna hitam yang terlihat jelas oleh kamera.
3. Mulai game dan ikuti proses kalibrasi jika muncul.
4. Duduk di posisi bermain dan usahakan pencahayaan cukup.
5. Tahan `SPASI`, gambar salah satu bentuk gestur di depan kamera, lalu lepaskan `SPASI`.
6. Jika gestur sulit dikenali, buka **Tes Kamera**, periksa preview, dan lakukan kalibrasi ulang.

### Tips Pelacakan

- Gunakan latar yang cukup kontras dengan sarung tangan.
- Hindari pencahayaan yang terlalu gelap atau cahaya langsung yang menyilaukan kamera.
- Saat kalibrasi latar, tetap diam dan jauhkan sarung tangan dari kamera atau gerakkan terus agar tidak dianggap sebagai objek latar yang diam.
- Tekan `C` untuk kalibrasi ulang jika posisi kepala atau kamera berubah.
- Gunakan tombol `M` untuk membantu memeriksa hasil mask jika tersedia.

## Cara Kerja Deteksi Gestur

Sistem gestur dibagi menjadi beberapa bagian utama:

1. **Kompensasi pencahayaan** — memperkirakan tingkat kecerahan frame dan menyesuaikan ambang deteksi warna hitam.
2. **Filter latar belakang** — mempelajari area gelap yang relatif menetap selama kalibrasi agar rambut atau objek diam tidak mudah dianggap sebagai sarung tangan.
3. **Pelacakan kontur** — menyaring kandidat berdasarkan ukuran dan bentuk, kemudian memilih kandidat yang paling sesuai dengan posisi pelacakan sebelumnya.
4. **Perekaman lintasan** — merekam posisi sarung tangan selama tombol `SPASI` ditahan.
5. **Klasifikasi bentuk** — mengolah lintasan secara geometris untuk membedakan bentuk seperti segitiga, lingkaran, garis, dan zigzag.

## Struktur Proyek

```text
PCV_ProjectGame/
├── main.py                       # Entry point aplikasi
├── config.py                     # Konfigurasi gameplay, kamera, dan gestur
├── requirements.txt              # Dependensi Python
├── README.md                     # Dokumentasi proyek
├── assets/
│   ├── audio/                    # Musik dan efek suara
│   ├── backgrounds/              # Aset latar permainan
│   ├── effects/                  # Animasi efek jurus
│   ├── sprites/
│   │   ├── enemies/              # Sprite dan animasi musuh
│   │   ├── player/               # Sprite pemain
│   │   ├── pickups/              # Item dan XP
│   │   └── projectiles/          # Proyektil
│   └── ui/                       # Ikon dan aset antarmuka
├── game/
│   ├── engine.py                 # Loop dan orkestrasi game
│   ├── player.py                 # Logika pemain
│   ├── enemy.py                  # Logika musuh
│   ├── spawner.py                # Kemunculan musuh
│   ├── pickups.py                # Item dan XP
│   ├── projectile.py             # Proyektil
│   ├── skills.py                 # Sistem jurus
│   ├── settings.py               # Pengaturan tersimpan
│   ├── audio.py                  # Musik dan efek suara
│   ├── assets.py                 # Pemuatan aset visual
│   ├── animation.py              # Sistem animasi
│   ├── background.py             # Latar permainan
│   ├── camera_overlay.py         # Panel kamera
│   ├── ui.py                     # HUD dan antarmuka
│   └── screens/                  # Menu, tes kamera, jeda, Game Over
├── gesture/
│   ├── hand_tracker.py           # Pelacakan sarung tangan
│   ├── lighting.py               # Analisis dan kompensasi pencahayaan
│   ├── background_filter.py      # Filter objek latar yang diam
│   ├── gesture_recorder.py       # Perekaman lintasan gestur
│   ├── shape_classifier.py       # Klasifikasi bentuk gestur
│   └── gesture_thread.py         # Pengelolaan kamera di thread terpisah
├── tools/
│   ├── check_assets.py            # Pemeriksaan ketersediaan aset
│   └── flip_sprite.py             # Utilitas membalik sprite
└── tests/
    ├── test_assets.py
    ├── test_black_tracking.py
    ├── test_menu.py
    └── test_shape_classifier.py
```

## Memeriksa Aset

Untuk memeriksa aset yang dikenali oleh proyek, jalankan:

```bash
python tools/check_assets.py
```

Aset yang tersedia berada di folder `assets/`. Detail nama dan ketentuan aset dapat dilihat pada `assets/README.md`.

## Menjalankan Pengujian

Pengujian menggunakan modul `unittest` dapat dijalankan dengan:

```bash
python -m unittest discover -s tests -v
```

Jika suatu pengujian memerlukan kamera atau perangkat tertentu, pastikan perangkat tersebut tersedia dan ikuti hasil keluaran pengujian.

## Pengaturan

Konfigurasi teknis seperti ukuran layar, indeks kamera, ambang deteksi warna hitam, dan parameter klasifikasi gestur berada di `config.py`. Pengaturan yang dapat diubah melalui menu permainan dikelola oleh sistem pengaturan game.

Ubah nilai konfigurasi dengan hati-hati karena perubahan parameter pelacakan dapat memengaruhi kemampuan sistem mengenali sarung tangan.

## Pemecahan Masalah

**Kamera tidak terbuka**
- Pastikan webcam tidak sedang digunakan aplikasi lain.
- Periksa izin kamera pada sistem operasi.
- Coba jalankan game dengan `python main.py --no-camera` untuk bermain tanpa webcam.

**Sarung tangan tidak terdeteksi**
- Tambahkan pencahayaan dan pastikan sarung tangan terlihat jelas.
- Periksa preview melalui menu Tes Kamera.
- Lakukan kalibrasi ulang setelah mengubah posisi.

**Gestur salah dikenali**
- Gambar bentuk dengan ukuran yang cukup besar dan gerakan yang jelas.
- Hindari gerakan yang terlalu cepat atau terputus-putus.
- Gunakan menu Tes Kamera untuk mencoba bentuk sebelum bermain.

**Aset tidak muncul**
- Pastikan file berada di direktori `assets/` sesuai struktur yang dijelaskan pada `assets/README.md`.
- Jalankan `python tools/check_assets.py` untuk memeriksa aset.

## Status Pengembangan
### Gameplay
- [x] Pemain bergerak dengan WASD, HP, XP, naik level (HP maksimum +6 dan pulih penuh tiap naik level)
- [x] Serangan dasar otomatis ke musuh terdekat
- [x] Tiga tipe musuh: `basic`, `fast`, `tank`, dengan waktu buka berbeda (0 s, 25 s, 60 s)
- [x] Spawner dengan kesulitan naik seiring waktu (HP dan kecepatan musuh, laju spawn)
- [x] Orb XP yang tertarik ke pemain
- [x] 5 jurus: segitiga, lingkaran, garis, zigzag
- [x] Tombol cadangan `1`-`4` untuk memicu jurus tanpa kamera
- [x] Mode fokus: musuh melambat saat pemain menggambar jurus
### Tracking gestur
- [x] Pelacakan sarung tangan hitam dengan OpenCV murni
- [x] Kompensasi pencahayaan otomatis
- [x] Pembeda rambut vs sarung tangan lewat kalibrasi
- [x] Klasifikasi bentuk gestur (segitiga, lingkaran, kotak, garis, zigzag)
- [x] Kamera di thread terpisah (anti-lag)
### Menu dan layar
- [x] Menu utama, Tes Kamera, Cara Bermain, Pengaturan (tersimpan di `settings.json`)
- [x] Layar Jeda dan Game Over
- [x] Kontrol dengan keyboard dan mouse
### Bug Fixed
- [x] Forced Close jika Gerakan Salah
- [x] Skor system membuat game crash
- [x] Line sangat sulit dibuat/terdeteksi
- [x] Zigzag Freeze Saat Pertama Kali Digunakan
- [x] Sprite tidak ada saat skill nyala(untuk line dan slash)
### Balancing
- [x] Balancing Game Keseluruhan
