"""
main.py
========
Entry point. Jalankan dengan:

    python main.py                # normal (memakai webcam)
    python main.py --no-camera    # tanpa webcam; jurus lewat tombol 1-5 saat bermain

Menu utama: Mulai Game, Tes Kamera, Cara Bermain, Pengaturan, Keluar.

Kontrol saat bermain:
    W A S D        -> gerak
    Tahan SPASI    -> mode rekam jurus, lalu gambar pola dengan sarung tangan hitam
    C              -> kalibrasi ulang (rambut/benda hitam diam)
    M              -> tampilkan mask hitam di panel kamera
    1-5            -> picu jurus tanpa kamera (bisa dimatikan di Pengaturan)
    ESC            -> jeda (menu jeda)
"""

import argparse

from game.engine import Game


def main():
    parser = argparse.ArgumentParser(description="Vampire Gesture Survivor")
    parser.add_argument("--no-camera", action="store_true",
                        help="jangan membuka webcam (jurus lewat tombol 1-5)")
    args = parser.parse_args()

    Game(use_camera=not args.no_camera).run()


if __name__ == "__main__":
    main()
