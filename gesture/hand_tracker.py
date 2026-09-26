"""
gesture/hand_tracker.py
========================
Deteksi posisi tangan menggunakan OpenCV MURNI (TIDAK memakai mediapipe
atau model machine-learning apapun).

Teknik yang dipakai: color thresholding (HSV) + operasi morfologi +
pencarian kontur terbesar. Ini bukan hand-pose estimation yang canggih,
tapi cukup untuk melacak *satu titik pusat tangan* (centroid) yang
dipakai untuk "menggambar" pola jurus di udara.

Dua mode:
- "skin"   : mendeteksi warna kulit (default, tidak butuh alat tambahan)
- "marker" : mendeteksi benda/sarung tangan berwarna cerah (lebih stabil
             di pencahayaan yang sulit)

Kalibrasi bisa dilakukan lewat tools/calibrate_hsv.py; hasilnya disimpan
ke hsv_calibration.json dan otomatis dipakai kalau file itu ada.
"""

import json
import os

import cv2
import numpy as np

import config


class HandTracker:
    def __init__(self, camera_index=None, mode=None):
        self.camera_index = camera_index if camera_index is not None else config.CAMERA_INDEX
        self.mode = mode or config.GESTURE_DETECTION_MODE
        self.cap = None
        self.available = False

        self.lower, self.upper = self._load_hsv_range()
        self._kernel = np.ones((5, 5), np.uint8)

    # ------------------------------------------------------------------
    def _load_hsv_range(self):
        lower, upper = config.SKIN_HSV_LOWER, config.SKIN_HSV_UPPER
        if self.mode == "marker":
            lower, upper = config.MARKER_HSV_LOWER, config.MARKER_HSV_UPPER

        if os.path.exists(config.HSV_CALIBRATION_FILE):
            try:
                with open(config.HSV_CALIBRATION_FILE, "r") as f:
                    data = json.load(f)
                if data.get("mode") == self.mode:
                    lower = tuple(data["lower"])
                    upper = tuple(data["upper"])
            except (json.JSONDecodeError, KeyError, OSError):
                pass
        return np.array(lower, dtype=np.uint8), np.array(upper, dtype=np.uint8)

    # ------------------------------------------------------------------
    def open(self):
        """Coba buka kamera. Mengembalikan True kalau berhasil."""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
        except cv2.error:
            self.cap = None

        if self.cap is not None and self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_CAPTURE_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_CAPTURE_HEIGHT)
            self.available = True
        else:
            self.available = False
        return self.available

    def close(self):
        if self.cap is not None:
            self.cap.release()
        self.available = False

    # ------------------------------------------------------------------
    def read_frame(self):
        """Ambil satu frame mentah (BGR) dari kamera, atau None kalau gagal."""
        if not self.available or self.cap is None:
            return None
        ok, frame = self.cap.read()
        if not ok:
            return None
        if config.CAMERA_MIRROR:
            frame = cv2.flip(frame, 1)
        return frame

    # ------------------------------------------------------------------
    def detect(self, frame):
        """
        Deteksi tangan pada satu frame BGR.

        Return: (centroid, mask, contour)
          centroid : (x, y) posisi pusat tangan dalam koordinat frame, atau None
          mask     : citra biner hasil threshold (untuk ditampilkan/debug)
          contour  : kontur terbesar yang lolos filter area, atau None
        """
        blurred = cv2.GaussianBlur(frame, (7, 7), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower, self.upper)

        mask = cv2.erode(mask, self._kernel, iterations=1)
        mask = cv2.dilate(mask, self._kernel, iterations=2)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None, mask, None

        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) < config.GESTURE_MIN_CONTOUR_AREA:
            return None, mask, None

        moments = cv2.moments(largest)
        if moments["m00"] == 0:
            return None, mask, largest

        cx = int(moments["m10"] / moments["m00"])
        cy = int(moments["m01"] / moments["m00"])
        return (cx, cy), mask, largest
