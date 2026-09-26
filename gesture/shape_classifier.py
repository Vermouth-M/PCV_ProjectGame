"""
gesture/shape_classifier.py
=============================
Mengubah kumpulan titik lintasan tangan (hasil GestureRecorder) menjadi
nama bentuk: "triangle", "circle", "square", "line", "zigzag", atau
"unknown".

Semua dilakukan dengan geometri sederhana + cv2.approxPolyDP/convexHull,
TIDAK menggunakan model machine-learning atau mediapipe apapun.

Alur:
1. Tolak lintasan yang terlalu pendek/terlalu kecil (noise).
2. Cek apakah lintasan "tertutup" (titik awal & akhir berdekatan relatif
   terhadap panjang lintasan) atau "terbuka".
3a. Kalau tertutup -> hitung convex hull, perkirakan jumlah sudut
    dengan approxPolyDP, dan hitung circularity untuk membedakan
    segitiga / kotak / lingkaran.
3b. Kalau terbuka -> cek kelurusan lewat regresi linear (garis) atau
    hitung jumlah pembalikan arah (zigzag).
"""

import math

import cv2
import numpy as np

import config


def classify(points):
    if len(points) < config.GESTURE_MIN_POINTS:
        return "unknown"

    pts = np.array(points, dtype=np.float32)

    x_min, y_min = pts.min(axis=0)
    x_max, y_max = pts.max(axis=0)
    bbox_w, bbox_h = x_max - x_min, y_max - y_min

    if max(bbox_w, bbox_h) < config.GESTURE_MIN_BOUNDING_BOX:
        return "unknown"

    path_len = _path_length(pts)
    if path_len < 1e-3:
        return "unknown"

    if _is_closed(pts, path_len):
        return _classify_closed(pts)
    return _classify_open(pts)


def dominant_direction(points):
    """Arah umum lintasan (vektor ternormalisasi dari titik awal ke titik akhir)."""
    if len(points) < 2:
        return (1.0, 0.0)
    pts = np.array(points, dtype=np.float32)
    v = pts[-1] - pts[0]
    norm = float(np.linalg.norm(v))
    if norm < 1e-3:
        return (1.0, 0.0)
    return (float(v[0] / norm), float(v[1] / norm))


# ---------------------------------------------------------------------------
def _path_length(pts):
    diffs = np.diff(pts, axis=0)
    return float(np.sum(np.hypot(diffs[:, 0], diffs[:, 1])))


def _is_closed(pts, path_len):
    first, last = pts[0], pts[-1]
    end_dist = math.hypot(last[0] - first[0], last[1] - first[1])
    return (end_dist / path_len) < config.GESTURE_CLOSED_LOOP_RATIO


# ---------------------------------------------------------------------------
def _classify_closed(pts):
    hull = cv2.convexHull(pts.reshape(-1, 1, 2))
    perimeter = cv2.arcLength(hull, True)
    if perimeter <= 0:
        return "unknown"

    epsilon = config.GESTURE_APPROX_EPSILON_RATIO * perimeter
    approx = cv2.approxPolyDP(hull, epsilon, True)
    vertices = len(approx)

    hull_area = cv2.contourArea(hull)
    circularity = 4 * math.pi * hull_area / (perimeter * perimeter)  # 1.0 = lingkaran sempurna

    if vertices == 3:
        return "triangle"
    if vertices == 4:
        return "square"
    if circularity > 0.75 or vertices >= 5:
        return "circle"
    return "unknown"


# ---------------------------------------------------------------------------
def _classify_open(pts):
    xs, ys = pts[:, 0], pts[:, 1]
    x_range = float(xs.max() - xs.min())
    y_range = float(ys.max() - ys.min())

    if x_range >= y_range:
        coeffs = np.polyfit(xs, ys, 1)
        predicted = np.polyval(coeffs, xs)
        residual = ys
    else:
        coeffs = np.polyfit(ys, xs, 1)
        predicted = np.polyval(coeffs, ys)
        residual = xs

    rmse = math.sqrt(float(np.mean((residual - predicted) ** 2)))
    span = max(x_range, y_range, 1.0)
    straightness = rmse / span

    # Prioritaskan deteksi zigzag: garis lurus asli nyaris tidak pernah
    # punya banyak pembalikan arah tajam, sedangkan zigzag yang cenderung
    # naik-turun simetris kadang kebetulan punya residual regresi linear
    # yang rendah juga (nilai straightness bisa menipu). Jadi jumlah
    # pembalikan arah dicek dulu sebelum menyimpulkan "line".
    if _count_direction_changes(pts) >= 2:
        return "zigzag"

    if straightness < 0.12:
        return "line"

    return "unknown"


def _count_direction_changes(pts, step=2):
    """Hitung berapa kali arah gerak (sudut antar segmen) berbalik cukup tajam."""
    if len(pts) < (step * 2 + 1):
        return 0

    vectors = []
    for i in range(0, len(pts) - step, step):
        v = pts[i + step] - pts[i]
        if np.linalg.norm(v) > 1e-3:
            vectors.append(v)

    changes = 0
    for i in range(len(vectors) - 1):
        a, b = vectors[i], vectors[i + 1]
        cross = a[0] * b[1] - a[1] * b[0]
        dot = a[0] * b[0] + a[1] * b[1]
        angle = math.atan2(abs(cross), dot)
        if angle > math.radians(55):
            changes += 1
    return changes
