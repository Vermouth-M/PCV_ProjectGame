"""
gesture/gesture_thread.py
===========================
Menjalankan capture kamera + deteksi tangan di THREAD terpisah supaya
tidak bikin lag game loop pygame (baca kamera relatif lambat
dibanding target 60 FPS).

Main thread (pygame) cukup:
    gt = GestureThread()
    gt.start()
    ...
    gt.begin_recording()        # saat SPASI ditekan
    ...
    points = gt.end_recording() # saat SPASI dilepas
    shape = shape_classifier.classify(points)
"""

import threading

from gesture.hand_tracker import HandTracker
from gesture.gesture_recorder import GestureRecorder


class GestureThread:
    def __init__(self, camera_index=None, mode=None):
        self.tracker = HandTracker(camera_index=camera_index, mode=mode)
        self.recorder = GestureRecorder()

        self._lock = threading.Lock()
        self._latest_frame = None
        self._latest_mask = None
        self._latest_centroid = None
        self._camera_ok = False

        self._running = False
        self._thread = None

    # ------------------------------------------------------------------
    def start(self):
        self._camera_ok = self.tracker.open()
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self._camera_ok

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        self.tracker.close()

    @property
    def camera_available(self):
        return self._camera_ok

    # ------------------------------------------------------------------
    def _loop(self):
        while self._running:
            if not self._camera_ok:
                break
            frame = self.tracker.read_frame()
            if frame is None:
                continue

            centroid, mask, _contour = self.tracker.detect(frame)

            with self._lock:
                self._latest_frame = frame
                self._latest_mask = mask
                self._latest_centroid = centroid

            if self.recorder.recording:
                self.recorder.add_point(centroid)

    # ------------------------------------------------------------------
    def get_preview(self):
        """Ambil salinan frame + mask + centroid terbaru buat ditampilkan di HUD."""
        with self._lock:
            return self._latest_frame, self._latest_mask, self._latest_centroid

    def begin_recording(self):
        self.recorder.start()

    def end_recording(self):
        return self.recorder.stop()

    def is_recording(self):
        return self.recorder.recording

    def recording_expired(self):
        return self.recorder.is_expired()

    def current_points(self):
        return list(self.recorder.points)
