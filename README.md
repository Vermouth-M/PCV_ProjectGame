# Vampire Gesture Survivor

Game bergaya *Vampire Survivors* yang dibuat dengan **Pygame**, dengan
twist: kamu bisa mengeluarkan **jurus** dengan menggambar pola/bentuk di
udara menggunakan tangan, dideteksi lewat kamera **hanya dengan OpenCV**
(TIDAK memakai MediaPipe atau model machine-learning apapun).

## Fitur

- Gameplay survival ala Vampire Survivors: musuh datang terus-menerus,
  makin lama makin sulit (HP & kecepatan musuh naik, tipe musuh baru
  muncul), kumpulkan XP dari musuh yang mati, naik level.
- Kontrol gerak **WASD**.
- **5 Jurus** yang dipicu dengan menggambar bentuk di depan kamera saat
  menahan tombol **SPASI**:

  | Bentuk yang digambar | Nama Jurus                     | Efek                                        |
  |-----------------------|--------------------------------|----------------------------------------------|
  | Segitiga               | Jurus Segitiga Pedang          | Tebasan area (cone) di depan pemain          |
  | Lingkaran               | Jurus Lingkaran Gelombang Kejut| Ledakan AoE 360° + knockback                 |
  | Kotak                    | Jurus Kotak Perisai            | Kebal total sementara                        |
  | Garis lurus                | Jurus Garis Tebasan            | Tebasan lurus menembus banyak musuh          |
  | Zigzag                       | Jurus Zigzag Petir              | Petir loncat antar musuh terdekat berantai   |

- Deteksi tangan berbasis **color thresholding (HSV) + kontur**, jadi
  ringan, tidak butuh GPU/model besar, dan 100% memakai OpenCV biasa.
  Ada mode `skin` (warna kulit) dan `marker` (benda/sarung tangan
  berwarna cerah), plus alat kalibrasi HSV interaktif.
- Kode dipecah per modul dengan tanggung jawab jelas (lihat struktur di
  bawah) — bukan 1 file raksasa.
- Fallback tombol `1`-`5` untuk memicu jurus tanpa kamera (berguna untuk
  testing/development, atau kalau webcam bermasalah).
- Ada unit test untuk algoritma pengenalan bentuk (`tests/`), bisa
  dijalankan tanpa webcam sama sekali.

## Struktur Folder

```
vampire_gesture_survivor/
├── main.py                     # entry point
├── config.py                   # semua konstanta & pengaturan (gameplay + gestur)
├── requirements.txt
├── README.md
│
├── game/                       # logika inti gameplay (tidak menyentuh kamera)
│   ├── engine.py                 # kelas Game: loop utama & orkestrasi semua sistem
│   ├── player.py                  # pemain: gerak WASD, HP, XP, level, perisai
│   ├── enemy.py                    # musuh: gerak menuju pemain, HP, damage
│   ├── spawner.py                   # sistem spawn musuh & difficulty scaling
│   ├── pickups.py                    # orb XP (dengan efek magnet)
│   ├── projectile.py                  # proyektil serangan dasar otomatis
│   ├── skills.py                       # 5 jurus: damage, area, efek visual
│   ├── ui.py                            # HUD (HP, XP, cooldown jurus, status gestur)
│   ├── camera_overlay.py                 # panel kecil preview kamera + lintasan
│   └── utils.py                           # helper matematika & collision
│
├── gesture/                    # semua yang berhubungan dengan kamera/OpenCV
│   ├── hand_tracker.py            # deteksi tangan OpenCV murni (TANPA mediapipe)
│   ├── gesture_recorder.py         # rekam lintasan tangan selama SPASI ditahan
│   ├── shape_classifier.py          # ubah lintasan -> nama bentuk (geometri murni)
│   └── gesture_thread.py             # jalankan kamera di thread terpisah (anti-lag)
│
├── tools/
│   └── calibrate_hsv.py         # alat bantu kalibrasi warna kulit/marker (trackbar)
│
└── tests/
    └── test_shape_classifier.py  # unit test klasifikasi bentuk (lintasan sintetis)
```

## Instalasi

Butuh **Python 3.9+** dan sebuah webcam.

```bash
cd vampire_gesture_survivor
pip install -r requirements.txt
```

Isi `requirements.txt` hanya: `pygame`, `opencv-python`, `numpy` —
**tidak ada mediapipe** di mana pun dalam proyek ini.

## Menjalankan

```bash
python main.py
```

## Kontrol

| Tombol            | Fungsi                                                                 |
|-------------------|-------------------------------------------------------------------------|
| `W` `A` `S` `D`   | Gerak kaki karakter                                                    |
| Tahan `SPASI`     | Masuk mode "siap jurus" — kamera mulai merekam lintasan tanganmu       |
| Lepas `SPASI`     | Selesai menggambar — bentuk otomatis diklasifikasi & jurus dikeluarkan |
| `1` - `5`         | (mode uji coba tanpa kamera) langsung memicu jurus segitiga/lingkaran/kotak/garis/zigzag |
| `ESC`             | Keluar dari game                                                       |
| `R`               | Main lagi setelah Game Over                                            |

**Cara menggambar jurus dalam praktik:** taruh tangan (misal kiri) di
keyboard untuk WASD, tahan `SPASI` dengan ibu jari, lalu gerakkan tangan
satunya (kanan) di depan kamera membentuk pola (segitiga, lingkaran,
kotak, garis lurus, atau zigzag), lalu lepas `SPASI`. Selama `SPASI`
ditahan, musuh bergerak melambat ("mode fokus") supaya kamu sempat
menggambar dengan tenang tanpa langsung dikeroyok.

## Bagaimana Deteksi Gestur Bekerja (Tanpa MediaPipe)

Karena MediaPipe tidak diperbolehkan, deteksi tangan di proyek ini
memakai teknik computer vision klasik dari OpenCV saja:

1. **Color thresholding (HSV)** — `cv2.inRange` mencari piksel yang
   warnanya mirip kulit tangan (atau warna marker cerah kalau memakai
   mode `marker`).
2. **Operasi morfologi** (`erode` + `dilate`) untuk membersihkan noise
   kecil dari mask hasil threshold.
3. **Kontur terbesar** (`cv2.findContours`) dianggap sebagai tangan,
   lalu dihitung titik pusatnya lewat `cv2.moments` sebagai posisi
   tangan pada frame tersebut.
4. Posisi tangan tiap frame **direkam sebagai lintasan** selama tombol
   `SPASI` ditahan (`gesture/gesture_recorder.py`), dijalankan di
   thread terpisah (`gesture/gesture_thread.py`) supaya pembacaan
   kamera tidak bikin game jadi patah-patah.
5. Setelah `SPASI` dilepas, lintasan dianalisis secara **geometris
   murni** di `gesture/shape_classifier.py`, tanpa model AI/ML apapun:
   - Dicek apakah lintasan **tertutup** (titik awal & akhir berdekatan
     dibanding panjang total lintasan) atau **terbuka**.
   - Kalau **tertutup**: dihitung *convex hull*-nya, lalu jumlah sudut
     diperkirakan dengan `cv2.approxPolyDP` — 3 sudut → segitiga,
     4 sudut → kotak, bentuk yang cukup membulat (circularity tinggi)
     → lingkaran.
   - Kalau **terbuka**: dihitung dulu berapa kali arah gerakannya
     berbalik tajam. Kalau berbalik berkali-kali → zigzag. Kalau tidak,
     dicek kelurusannya lewat regresi linear sederhana → garis.

Ini adalah heuristik geometri, bukan model yang dilatih dari data. Cukup
akurat untuk gerakan yang jelas dan tidak terburu-buru, tapi bisa saja
salah baca kalau pencahayaan buruk, latar belakang mirip warna kulit,
atau gerakannya terlalu kecil/cepat.

### Tips supaya deteksi lebih akurat

- Gunakan latar belakang polos dan pencahayaan yang cukup terang & merata.
- Gambar bentuk dengan **cukup besar** (isi sebagian area kamera) dan
  **jangan terlalu terburu-buru**.
- Kalau deteksi warna kulit susah stabil (pencahayaan berubah-ubah,
  banyak objek berwarna mirip kulit di latar belakang), pindah ke mode
  marker:
  1. Set `GESTURE_DETECTION_MODE = "marker"` di `config.py`.
  2. Pakai sarung tangan atau benda berwarna cerah solid (mis. hijau
     neon) yang kamu genggam/kenakan.
  3. Jalankan `python tools/calibrate_hsv.py --mode marker`, geser
     trackbar sampai jendela "mask" hanya menampilkan marker-nya saja
     (putih bersih, latar hitam), lalu tekan `s` untuk menyimpan.
     Hasilnya otomatis dipakai game berikutnya lewat
     `hsv_calibration.json`.
- Kalau kamera tidak terdeteksi sama sekali (atau kamu sedang tidak
  punya webcam), game tetap bisa dimainkan penuh memakai fallback
  tombol `1`-`5` untuk menguji semua jurus.

## Menambah Jurus / Bentuk Baru

1. Tambahkan definisi jurus baru (damage, radius/durasi, cooldown,
   warna) di `config.SKILL_DEFS`.
2. Tambahkan logika pengenalan bentuknya di
   `gesture/shape_classifier.py` (misalnya bentuk "V" atau "spiral").
3. Buat class efek baru yang mewarisi `SkillEffect` di `game/skills.py`
   untuk visual + damage-nya, lalu daftarkan cabang barunya di
   `SkillManager.trigger()`.
4. (Opsional) tambahkan tombol debug baru di `Game._debug_shape_keys`
   pada `game/engine.py` supaya bisa diuji tanpa kamera dulu.

## Menjalankan Unit Test

```bash
python tests/test_shape_classifier.py
```

Test ini memverifikasi algoritma klasifikasi bentuk memakai lintasan
titik buatan (bukan dari kamera sungguhan), sehingga bisa dijalankan
di mana saja tanpa webcam.

## Keterbatasan yang Diketahui

- Deteksi tangan berbasis warna, bukan pose/skeleton estimation — hanya
  melacak satu titik pusat tangan, tidak mengenali jari atau orientasi
  telapak tangan.
- Sensitif terhadap kondisi pencahayaan dan warna latar belakang.
- Klasifikasi bentuk adalah heuristik geometri sederhana, bukan model
  yang dilatih — kadang perlu 1-2 kali percobaan agar terbaca tepat.
- Untuk gameplay dua tangan (WASD + menggambar di kamera), disarankan
  menahan `SPASI` dengan ibu jari sambil jari lain tetap di WASD.
