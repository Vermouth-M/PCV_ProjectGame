import threading
import time

import cv2
import numpy as np

import config

_MIN_FRAMES_ON_TIMEOUT = 15


class StaticDarkFilter:
    def __init__(self):
        self._lock = threading.Lock()
        self.exclusion = None          # mask uint8 (255 = diabaikan) atau None
        self.excluded_ratio = 0.0      # porsi frame yang diabaikan, 0-1
        self.calibrating = False

        self._counts = None
        self._frames = 0
        self._target = config.GESTURE_CALIB_FRAMES
        self._started = 0.0

    # ------------------------------------------------------------------
    def begin(self, frames=None):
        """Mulai kalibrasi baru. Zona lama dihapus supaya yang dipelajari murni."""
        with self._lock:
            self._target = frames or config.GESTURE_CALIB_FRAMES
            self._counts = None
            self._frames = 0
            self._started = time.time()
            self.exclusion = None
            self.excluded_ratio = 0.0
            self.calibrating = True

    def clear(self):
        """Hapus zona yang sudah dipelajari (mis. setelah mode cermin kamera diganti)."""
        with self._lock:
            self.exclusion = None
            self.excluded_ratio = 0.0
            self.calibrating = False
            self._counts = None

    @property
    def progress(self):
        if self.calibrating:
            return min(1.0, self._frames / max(1, self._target))
        return 1.0 if self.exclusion is not None else 0.0

    def feed(self, black_mask):
        """Masukkan satu mask hitam (pra-exclusion). Selesai otomatis setelah cukup frame."""
        with self._lock:
            if not self.calibrating:
                return
            hit = (black_mask > 0).astype(np.float32)
            if self._counts is None:
                self._counts = np.zeros_like(hit)
            self._counts += hit
            self._frames += 1
            if self._frames >= self._target:
                self._finish()

    def check_timeout(self):
        """Jaga-jaga kalau kamera macet saat kalibrasi supaya game tidak membeku selamanya."""
        with self._lock:
            if self.calibrating and time.time() - self._started > config.GESTURE_CALIB_TIMEOUT:
                if self._frames >= _MIN_FRAMES_ON_TIMEOUT:
                    self._finish()
                else:
                    self.calibrating = False
                    self._counts = None

    # ------------------------------------------------------------------
    def _finish(self):
        ratio = self._counts / max(1, self._frames)
        static = (ratio >= config.GESTURE_CALIB_PERSISTENCE).astype(np.uint8) * 255
        static = cv2.morphologyEx(static, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))

        d = config.GESTURE_EXCLUSION_DILATE
        if d > 0:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * d + 1, 2 * d + 1))
            static = cv2.dilate(static, kernel)

        self.exclusion = static
        self.excluded_ratio = float(np.count_nonzero(static)) / static.size
        self._counts = None
        self.calibrating = False
