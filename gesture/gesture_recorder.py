"""
gesture/gesture_recorder.py
============================
Menyimpan lintasan (path) titik-titik posisi tangan selama pemain
menahan tombol SPASI (mode "siap/rekam jurus").
"""

import math
import time

import config


class GestureRecorder:
    def __init__(self):
        self.recording = False
        self.points = []
        self._start_time = 0.0

    def start(self):
        self.recording = True
        self.points = []
        self._start_time = time.time()

    def stop(self):
        self.recording = False
        pts = list(self.points)
        self.points = []
        return pts

    def add_point(self, pt):
        if not self.recording or pt is None:
            return
        if time.time() - self._start_time > config.GESTURE_MAX_RECORD_SECONDS:
            return
        if self.points:
            lx, ly = self.points[-1]
            dist = math.hypot(pt[0] - lx, pt[1] - ly)
            if dist < config.GESTURE_MIN_MOVE_DIST:
                return
        self.points.append(pt)

    def elapsed(self):
        if not self.recording:
            return 0.0
        return time.time() - self._start_time

    def is_expired(self):
        return self.recording and self.elapsed() > config.GESTURE_MAX_RECORD_SECONDS
