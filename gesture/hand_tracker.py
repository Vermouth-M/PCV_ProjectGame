"""
gesture/hand_tracker.py
========================
Melacak SARUNG TANGAN HITAM memakai OpenCV murni (tanpa mediapipe, tanpa
machine learning). Game ini HANYA melacak warna: gumpalan hitam terbesar yang
lolos beberapa filter. Tiga masalah praktis dan solusinya:

1. Pencahayaan beda tiap ruangan
   -> ambang "hitam" dihitung otomatis dari kecerahan scene
      (gesture/lighting.py), bukan angka tetap.
2. Rambut juga hitam
   -> area hitam yang DIAM saat kalibrasi dipelajari lalu diabaikan
      (gesture/background_filter.py). Sarung tangan yang bergerak tidak ikut.
3. Gumpalan hitam lain yang kebetulan lolos
   -> disaring lewat ukuran, kepadatan bentuk (solidity), dan kontinuitas
      posisi dari frame sebelumnya.
"""

import time

import cv2
import numpy as np

import config
from gesture.background_filter import StaticDarkFilter
from gesture.lighting import LightingMonitor

_BLACK_LOWER = np.array([0, 0, 0], dtype=np.uint8)


class HandTracker:
    def __init__(self, camera_index=None):
        self.camera_index = camera_index if camera_index is not None else config.CAMERA_INDEX
        self.cap = None
        self.available = False

        self.lighting = LightingMonitor()
        self.background = StaticDarkFilter()

        self._kernel = np.ones((5, 5), np.uint8)
        self._frames_seen = 0
        self._last_centroid = None
        self._last_time = 0.0

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
        Deteksi sarung tangan hitam pada satu frame BGR (resolusi bebas; di sini
        diperkecil ke GESTURE_PROCESS_WIDTH x HEIGHT).

        Return: (centroid, mask, contour)
          centroid : (x, y) dalam koordinat RESOLUSI KERJA, atau None
          mask     : mask hitam akhir (setelah zona rambut dibuang) untuk debug/preview
          contour  : kontur sarung tangan terpilih, atau None
        """
        size = (config.GESTURE_PROCESS_WIDTH, config.GESTURE_PROCESS_HEIGHT)
        if (frame.shape[1], frame.shape[0]) != size:
            frame = cv2.resize(frame, size, interpolation=cv2.INTER_AREA)
        self._frames_seen += 1

        blurred = cv2.GaussianBlur(frame, (7, 7), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        # 1) kompensasi pencahayaan: ambang hitam menyesuaikan kecerahan ruangan
        light = self.lighting.update(hsv[:, :, 2])
        upper = np.array([179, config.BLACK_S_MAX, light.black_v_max], dtype=np.uint8)

        mask = cv2.inRange(hsv, _BLACK_LOWER, upper)
        mask = cv2.erode(mask, self._kernel, iterations=1)
        mask = cv2.dilate(mask, self._kernel, iterations=2)

        # 2) kalibrasi: pelajari area hitam yang diam (rambut dkk), belum melacak
        if self.background.calibrating:
            if self._frames_seen > config.GESTURE_WARMUP_FRAMES:
                self.background.feed(mask)
            return None, mask, None

        exclusion = self.background.exclusion
        if exclusion is not None:
            mask = cv2.bitwise_and(mask, cv2.bitwise_not(exclusion))

        # 3) pilih kandidat sarung tangan dari gumpalan hitam yang tersisa
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates = self._filter_candidates(contours, mask.shape)
        if not candidates:
            return None, mask, None

        contour = self._choose(candidates)
        centroid = self._centroid(contour)
        if centroid is None:
            return None, mask, contour

        self._last_centroid = centroid
        self._last_time = time.time()
        return centroid, mask, contour

    # ------------------------------------------------------------------
    def _filter_candidates(self, contours, shape):
        max_area = config.GESTURE_BLACK_MAX_AREA_RATIO * shape[0] * shape[1]
        candidates = []
        for c in contours:
            area = cv2.contourArea(c)
            if area < config.GESTURE_MIN_CONTOUR_AREA or area > max_area:
                continue
            hull_area = cv2.contourArea(cv2.convexHull(c))
            if hull_area <= 0 or (area / hull_area) < config.GESTURE_MIN_SOLIDITY:
                continue   # bentuk bergerigi/tipis (mis. tepi rambut), bukan sarung tangan
            candidates.append((area, c))
        return candidates

    def _choose(self, candidates):
        """Pilih gumpalan terbesar, kecuali ada kandidat sepadan yang dekat posisi terakhir."""
        candidates.sort(key=lambda item: item[0], reverse=True)
        best_area, best = candidates[0]

        recent = (self._last_centroid is not None and
                  time.time() - self._last_time <= config.GESTURE_TRACK_CONTINUITY_SECONDS)
        if recent and len(candidates) > 1:
            min_area = best_area * config.GESTURE_TRACK_CONTINUITY_MIN_AREA
            lx, ly = self._last_centroid
            nearest, nearest_dist = best, None
            for area, c in candidates:
                if area < min_area:
                    continue
                cen = self._centroid(c)
                if cen is None:
                    continue
                dist = (cen[0] - lx) ** 2 + (cen[1] - ly) ** 2
                if nearest_dist is None or dist < nearest_dist:
                    nearest, nearest_dist = c, dist
            return nearest
        return best

    @staticmethod
    def _centroid(contour):
        m = cv2.moments(contour)
        if m["m00"] == 0:
            return None
        return (int(m["m10"] / m["m00"]), int(m["m01"] / m["m00"]))
