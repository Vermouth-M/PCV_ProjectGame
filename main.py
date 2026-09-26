"""
main.py
========
Entry point. Jalankan dengan:

    python main.py

Kontrol:
    W A S D        -> gerak
    Tahan SPASI    -> mode rekam jurus, lalu gambar pola di depan kamera
    1-5            -> (mode debug/tanpa kamera) langsung memicu jurus,
                      aktif kalau config.DEBUG_KEYBOARD_GESTURE_FALLBACK = True
    ESC            -> keluar
    R              -> main lagi setelah game over
"""

from game.engine import Game


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
