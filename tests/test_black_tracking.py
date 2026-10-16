"""
tests/test_black_tracking.py
==============================
Tes untuk tracking sarung tangan hitam memakai scene SINTETIS (tanpa webcam):

  1. Bar pencahayaan: label & ambang hitam otomatis di berbagai kecerahan ruangan
  2. Sarung tangan terdeteksi di ruangan redup sampai sangat terang
  3. Perpindahan ruangan (terang -> redup): ambang menyesuaikan
  4. Rambut hitam vs sarung tangan: sebelum & sesudah kalibrasi
  5. Toleransi kepala goyang, sarung tangan menempel rambut, kalibrasi saat
     sarung tangan bergerak, warm-up auto-exposure, timeout, kontinuitas

Jalankan:
    python tests/test_black_tracking.py
"""

import math
import os
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402
from gesture.hand_tracker import HandTracker  # noqa: E402
from gesture.lighting import LightingMonitor  # noqa: E402

RNG = np.random.default_rng(7)
HAIR_CENTER = (160, 32)
HAIR_AXES = (62, 36)


def make_scene(wall, glove=None, hair=True, hair_shift=(0, 0), glove_radius=22):
    """Frame 320x240: dinding terang, wajah, rambut hitam (atas), sarung tangan hitam."""
    f = np.full((240, 320, 3), int(wall), np.uint8)
    cv2.ellipse(f, (160, 80), (45, 55), 0, 0, 360, (int(wall * 0.78),) * 3, -1)   # wajah
    if hair:
        c = (HAIR_CENTER[0] + hair_shift[0], HAIR_CENTER[1] + hair_shift[1])
        v = int(0.22 * wall + 8)
        cv2.ellipse(f, c, HAIR_AXES, 0, 0, 360, (v,) * 3, -1)
    if glove is not None:
        v = int(0.24 * wall + 10)
        cv2.circle(f, glove, glove_radius, (v,) * 3, -1)
    noise = RNG.normal(0, 2.0, f.shape)
    return np.clip(f + noise, 0, 255).astype(np.uint8)


def warm_up(tracker, wall, n=None):
    """Lewati frame warm-up supaya kalibrasi berikutnya langsung dihitung."""
    for _ in range(n or config.GESTURE_WARMUP_FRAMES + 2):
        tracker.detect(make_scene(wall))


def calibrate(tracker, wall, glove_path=None, **scene_kw):
    tracker.background.begin()
    n = config.GESTURE_CALIB_FRAMES
    for i in range(n):
        glove = None
        if glove_path is not None:
            t = i / max(1, n - 1)
            glove = (int(40 + 240 * t), 175)   # sarung tangan digerakkan melintasi frame
        tracker.detect(make_scene(wall, glove=glove, **scene_kw))
    assert not tracker.background.calibrating, "kalibrasi seharusnya sudah selesai"


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


RESULTS = []


def check(name, ok, info=""):
    RESULTS.append(ok)
    print(f"[{'OK' if ok else 'GAGAL'}] {name} {info}")


# ---------------------------------------------------------------------------
def test_lighting_labels():
    expected = {25: "Terlalu gelap", 60: "Redup", 140: "Ideal", 215: "Terang", 245: "Terlalu terang"}
    for wall, label in expected.items():
        t = HandTracker()
        t.detect(make_scene(wall))
        st = t.lighting.state
        check(f"Bar pencahayaan dinding={wall}", st.label == label,
              f"-> '{st.label}' (level {st.level:.0f}, ambang V<{st.black_v_max})")

    thr = [LightingMonitor.black_threshold(level) for level in (20, 60, 100, 140, 180, 220, 255)]
    check("Ambang hitam naik seiring kecerahan (monoton) & terbatas MIN..MAX",
          thr == sorted(thr) and thr[0] == config.BLACK_V_MIN and thr[-1] == config.BLACK_V_MAX,
          f"-> {thr}")


def test_glove_across_lighting():
    target = (250, 150)
    for wall in (50, 70, 100, 140, 190, 230, 250):
        t = HandTracker()
        c = None
        for _ in range(5):
            c, _, _ = t.detect(make_scene(wall, glove=target, hair=False))
        check(f"Sarung tangan terdeteksi, dinding={wall}", c is not None and dist(c, target) <= 6, f"-> {c}")

    # perbandingan informatif: ambang tetap lama (V<70) di ruangan redup
    frame = make_scene(60, glove=target, hair=False)
    hsv = cv2.cvtColor(cv2.GaussianBlur(frame, (7, 7), 0), cv2.COLOR_BGR2HSV)
    fixed = cv2.inRange(hsv, (0, 0, 0), (179, 255, 70))
    print(f"      (info) ambang tetap V<70 di ruangan redup menandai {np.count_nonzero(fixed) / fixed.size:.0%} "
          f"frame sebagai 'hitam' (seluruh dinding) -> gagal; ambang adaptif tidak.")


def test_room_change():
    t = HandTracker()
    for _ in range(15):
        t.detect(make_scene(200, glove=(250, 150), hair=False))
    c = None
    for _ in range(50):   # pindah ke ruangan redup
        c, _, _ = t.detect(make_scene(60, glove=(250, 150), hair=False))
    st = t.lighting.state
    check("Pindah ruangan terang -> redup: ambang menyesuaikan & tetap terdeteksi",
          c is not None and dist(c, (250, 150)) <= 6 and st.label == "Redup",
          f"-> {c}, label '{st.label}', ambang V<{st.black_v_max}")


def test_hair_vs_glove():
    wall, glove = 140, (250, 150)

    # sebelum kalibrasi: rambut (gumpalan terbesar) menang -> inilah masalahnya
    t = HandTracker()
    c = None
    for _ in range(3):
        c, _, _ = t.detect(make_scene(wall, glove=glove))
    print(f"      (info) SEBELUM kalibrasi tracker memilih: {c} "
          f"({'rambut' if c and dist(c, HAIR_CENTER) < dist(c, glove) else 'sarung tangan'})")

    # setelah kalibrasi (sarung tangan dijauhkan): rambut diabaikan
    t = HandTracker()
    warm_up(t, wall)
    calibrate(t, wall)
    c, mask, _ = t.detect(make_scene(wall, glove=glove))
    check("Setelah kalibrasi: sarung tangan terpilih, bukan rambut",
          c is not None and dist(c, glove) <= 6, f"-> {c}, zona diabaikan {t.background.excluded_ratio:.0%}")

    c, _, _ = t.detect(make_scene(wall, glove=None))
    check("Hanya rambut di frame -> tidak ada deteksi", c is None, f"-> {c}")

    c, _, _ = t.detect(make_scene(wall, glove=glove, hair_shift=(6, 4)))
    check("Kepala goyang 6px setelah kalibrasi: rambut tetap diabaikan",
          c is not None and dist(c, glove) <= 6, f"-> {c}")

    c, _, _ = t.detect(make_scene(wall, glove=(160, 88)))
    check("Sarung tangan menempel rambut: tetap terdeteksi (agak bergeser)",
          c is not None and dist(c, (160, 88)) <= 14, f"-> {c}")

    t = HandTracker()
    warm_up(t, wall)
    calibrate(t, wall, glove_path=True)
    c, _, _ = t.detect(make_scene(wall, glove=glove))
    check("Kalibrasi saat sarung tangan digerakkan: sarung tangan TIDAK ikut diabaikan",
          c is not None and dist(c, glove) <= 6, f"-> {c}")

    for w in (60, 230):
        t = HandTracker()
        warm_up(t, w)
        calibrate(t, w)
        c, _, _ = t.detect(make_scene(w, glove=glove))
        check(f"Rambut vs sarung tangan di ruangan dinding={w}",
              c is not None and dist(c, glove) <= 6, f"-> {c}")


def test_calibration_mechanics():
    t = HandTracker()
    t.background.begin()
    check("begin() -> sedang kalibrasi", t.background.calibrating and t.background.progress == 0.0)

    # warm-up auto-exposure: 20 frame gelap total TIDAK boleh membuat semuanya diabaikan
    for _ in range(config.GESTURE_WARMUP_FRAMES):
        t.detect(np.full((240, 320, 3), 8, np.uint8))
    check("Frame warm-up diabaikan (progress masih 0)", t.background.progress == 0.0)
    for _ in range(config.GESTURE_CALIB_FRAMES):
        t.detect(make_scene(140))
    check("Kalibrasi selesai setelah cukup frame", not t.background.calibrating and t.background.exclusion is not None)
    check("Warm-up gelap tidak mencemari zona diabaikan",
          t.background.excluded_ratio < 0.25, f"-> {t.background.excluded_ratio:.0%} frame diabaikan")

    t = HandTracker()
    t.background.begin()
    t.background._started -= config.GESTURE_CALIB_TIMEOUT + 1   # simulasi kamera macet
    t.background.check_timeout()
    check("Timeout tanpa cukup frame membatalkan kalibrasi (game tidak membeku)", not t.background.calibrating)


def test_continuity():
    a, b = (80, 160), (240, 160)
    t = HandTracker()
    f1 = np.full((240, 320, 3), 140, np.uint8)
    cv2.circle(f1, a, 22, (40,) * 3, -1)
    c1, _, _ = t.detect(f1)
    f2 = f1.copy()
    cv2.circle(f2, b, 28, (40,) * 3, -1)   # gumpalan hitam lain yang lebih besar muncul
    c2, _, _ = t.detect(f2)
    check("Kontinuitas: tetap di sarung tangan lama walau ada gumpalan lebih besar",
          c1 is not None and c2 is not None and dist(c2, a) <= 6, f"-> {c2}")

    t2 = HandTracker()
    c3, _, _ = t2.detect(f2)
    check("Tanpa riwayat: memilih gumpalan terbesar", c3 is not None and dist(c3, b) <= 6, f"-> {c3}")


def main():
    for fn in (test_lighting_labels, test_glove_across_lighting, test_room_change,
               test_hair_vs_glove, test_calibration_mechanics, test_continuity):
        print(f"\n== {fn.__name__} ==")
        fn()
    passed = sum(RESULTS)
    print(f"\n{passed}/{len(RESULTS)} pemeriksaan lolos.")
    if passed != len(RESULTS):
        sys.exit(1)


if __name__ == "__main__":
    main()
