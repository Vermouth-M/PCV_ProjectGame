# Vampire Gesture Survivor (versi ringkas)

Game survivor ala Vampire Survivors yang jurusnya dikeluarkan dengan **menggambar pola memakai sarung tangan hitam di depan webcam**.

## Menjalankan
    pip install -r requirements.txt
    python main.py

## Kontrol
| Tombol | Fungsi |
|---|---|
| W A S D | gerak (serangan dasar otomatis ke musuh terdekat) |
| tahan SPASI | rekam gestur: gambar pola dengan sarung tangan, lepas SPASI untuk mengeluarkan jurus |
| 1-5 | jurus langsung tanpa kamera (segitiga, lingkaran, kotak, garis, zigzag) |
| C | kalibrasi ulang (pelajari rambut / benda hitam yang diam) |
| M | tampilkan mask deteksi |
| R | main lagi (saat game over) |
| ESC | keluar |

## Jurus
Segitiga = tebasan juring | Lingkaran = gelombang kejut | Kotak = perisai | Garis = tebasan lurus ke arah gerak tangan | Zigzag = petir berantai.

## Struktur (hanya 2 file)
- `gestur.py` : kamera (thread), pelacak sarung tangan hitam, kalibrasi, pengenal bentuk.
- `main.py`   : seluruh game. Angka-angka penyetelan ada di bagian PENGATURAN paling atas.
- `assets/`   : opsional. Kosong = gambar vektor otomatis. Nama berkas sama seperti versi lama
  (mis. `assets/sprites/player/idle.png` atau animasi `idle_0.png, idle_1.png, ...`).

## Tes
    python tests/test_semua.py
Tanpa webcam dan tanpa jendela.
