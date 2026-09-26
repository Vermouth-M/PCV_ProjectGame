"""
tools/calibrate_hsv.py
=========================
Alat bantu KALIBRASI warna kulit / marker memakai trackbar OpenCV.

Cara pakai:
    python tools/calibrate_hsv.py --mode skin
    python tools/calibrate_hsv.py --mode marker

Geser trackbar sampai HANYA tangan/marker kamu yang berwarna putih di
jendela "mask" -- latar belakang & benda lain sebisa mungkin hitam.
Tekan 's' untuk menyimpan ke hsv_calibration.json, 'q' untuk keluar
tanpa menyimpan.
"""

import argparse
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402  (harus setelah sys.path.insert)


def _nothing(_x):
    pass


def main():
    parser = argparse.ArgumentParser(description="Kalibrasi rentang HSV untuk deteksi tangan/marker.")
    parser.add_argument("--mode", choices=["skin", "marker"], default="skin")
    parser.add_argument("--camera", type=int, default=config.CAMERA_INDEX)
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"Tidak bisa membuka kamera index {args.camera}.")
        return

    default_lower = config.SKIN_HSV_LOWER if args.mode == "skin" else config.MARKER_HSV_LOWER
    default_upper = config.SKIN_HSV_UPPER if args.mode == "skin" else config.MARKER_HSV_UPPER

    win = f"Kalibrasi HSV - {args.mode}"
    cv2.namedWindow(win)
    cv2.createTrackbar("H min", win, default_lower[0], 179, _nothing)
    cv2.createTrackbar("H max", win, default_upper[0], 179, _nothing)
    cv2.createTrackbar("S min", win, default_lower[1], 255, _nothing)
    cv2.createTrackbar("S max", win, default_upper[1], 255, _nothing)
    cv2.createTrackbar("V min", win, default_lower[2], 255, _nothing)
    cv2.createTrackbar("V max", win, default_upper[2], 255, _nothing)

    print("Geser trackbar sampai jendela 'mask' menampilkan tangan/marker dengan bersih.")
    print("Tekan 's' untuk simpan, 'q' untuk keluar tanpa simpan.")

    kernel = np.ones((5, 5), np.uint8)

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if config.CAMERA_MIRROR:
            frame = cv2.flip(frame, 1)

        hsv = cv2.cvtColor(cv2.GaussianBlur(frame, (7, 7), 0), cv2.COLOR_BGR2HSV)

        lower = np.array([
            cv2.getTrackbarPos("H min", win),
            cv2.getTrackbarPos("S min", win),
            cv2.getTrackbarPos("V min", win),
        ])
        upper = np.array([
            cv2.getTrackbarPos("H max", win),
            cv2.getTrackbarPos("S max", win),
            cv2.getTrackbarPos("V max", win),
        ])

        mask = cv2.inRange(hsv, lower, upper)
        mask = cv2.erode(mask, kernel, iterations=1)
        mask = cv2.dilate(mask, kernel, iterations=2)
        result = cv2.bitwise_and(frame, frame, mask=mask)

        cv2.imshow(win, frame)
        cv2.imshow("mask", mask)
        cv2.imshow("result", result)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord("s"):
            data = {"mode": args.mode, "lower": lower.tolist(), "upper": upper.tolist()}
            with open(config.HSV_CALIBRATION_FILE, "w") as f:
                json.dump(data, f, indent=2)
            print(f"Tersimpan ke {config.HSV_CALIBRATION_FILE}")
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
