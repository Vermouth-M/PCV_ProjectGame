import threading
import time

from gesture.hand_tracker import HandTracker
from gesture.gesture_recorder import GestureRecorder


class GestureThread:
    def __init__(self, camera_index=None):
        self.tracker = HandTracker(camera_index=camera_index)
        self.recorder = GestureRecorder()

        self._lock = threading.Lock()
        self._latest_frame = None
        self._latest_mask = None
        self._latest_centroid = None
        self._latest_lighting = None
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
                time.sleep(0.005)
                continue

            centroid, mask, _contour = self.tracker.detect(frame)

            with self._lock:
                self._latest_frame = frame
                self._latest_mask = mask
                self._latest_centroid = centroid
                self._latest_lighting = self.tracker.lighting.state

            if self.recorder.recording:
                self.recorder.add_point(centroid)

    # ------------------------------------------------------------------
    # Data untuk HUD / preview
    # ------------------------------------------------------------------
    def get_preview(self):
        """(frame penuh, mask hitam, centroid sarung tangan atau None)."""
        with self._lock:
            return self._latest_frame, self._latest_mask, self._latest_centroid

    def get_lighting(self):
        """LightingState terbaru, atau None kalau belum ada frame."""
        with self._lock:
            return self._latest_lighting

    def get_exclusion(self):
        """Mask zona yang diabaikan (rambut dkk) atau None kalau belum dikalibrasi."""
        return self.tracker.background.exclusion

    def exclusion_ratio(self):
        return self.tracker.background.excluded_ratio

    # ------------------------------------------------------------------
    # Kalibrasi rambut / benda hitam diam
    # ------------------------------------------------------------------
    def start_calibration(self):
        if not self._camera_ok:
            return False
        self.tracker.background.begin()
        return True

    def is_calibrating(self):
        bg = self.tracker.background
        if bg.calibrating:
            bg.check_timeout()
        return bg.calibrating

    def calibration_progress(self):
        return self.tracker.background.progress

    # ------------------------------------------------------------------
    # Perekaman gestur
    # ------------------------------------------------------------------
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
