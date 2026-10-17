"""
tools/check_assets.py
=======================
Menampilkan daftar aset yang dikenali game dan mana yang SUDAH/BELUM ada di
folder assets/. Tidak membuka jendela game dan tidak butuh kamera.

Jalankan dari folder proyek:
    python tools/check_assets.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402
from game.assets import AssetManager  # noqa: E402


def main():
    manager = AssetManager(enabled=True)
    print(f"Folder aset : {manager.root}")
    if not config.USE_ASSETS:
        print("PERHATIAN   : config.USE_ASSETS = False, aset diabaikan oleh game.\n")

    rows = manager.status()
    width = max(len(r[0]) for r in rows)
    for label, prefix, n_frames, hint in rows:
        if n_frames:
            note = "1 gambar" if n_frames == 1 else f"{n_frames} frame"
            print(f"  [ada]    {label:<{width}}  <- assets/{prefix}  ({note})")
        else:
            print(f"  [belum]  {label:<{width}}  -> assets/{prefix}.png  atau  assets/{prefix}_0.png, _1.png, ...")
            print(f"           {'':<{width}}     {hint}")

    have = sum(1 for r in rows if r[2] > 0)
    print(f"\n{have}/{len(rows)} aset tersedia. Yang belum ada memakai gambar vektor bawaan.")


if __name__ == "__main__":
    main()
