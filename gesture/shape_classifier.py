import math

import cv2
import numpy as np

import config


def classify(points):
    if len(points) < config.GESTURE_LINE_MIN_POINTS:
        return "unknown"

    pts = np.array(points, dtype=np.float32)
    if _is_line(pts):
        return "line"

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
    k = max(1, len(pts) // 5)                      # rata-rata 20% titik di tiap ujung
    v = pts[-k:].mean(axis=0) - pts[:k].mean(axis=0)
    norm = float(np.linalg.norm(v))
    if norm < 1e-3:
        return (1.0, 0.0)
    return (float(v[0] / norm), float(v[1] / norm))

def _smooth(pts, window):
    """Rata-rata bergerak per sumbu (ujung ditahan) untuk meredam getar centroid."""
    if window <= 1 or len(pts) < window:
        return pts
    k = window // 2
    padded = np.pad(pts, ((k, k), (0, 0)), mode="edge")
    kernel = np.ones(window, dtype=np.float32) / window
    return np.stack([np.convolve(padded[:, i], kernel, mode="valid") for i in range(2)], axis=1)


def _is_line(pts):
    """
    Garis = lintasan (setelah dihaluskan) menyimpang tipis dari garis lurus awal->akhir.
    Dicek dengan penyederhanaan Ramer-Douglas-Peucker: kalau seluruh lintasan bisa diwakili
    2 titik dalam toleransi, itu garis. Tidak peka terhadap sudut/arah garis.
    """
    n = len(pts)
    trim = int(0.08 * n)                           # buang sedikit titik di ujung (tangan menetap/terangkat)
    core = pts[trim:n - trim] if n - 2 * trim >= 3 else pts
    core = _smooth(core, config.GESTURE_SMOOTH_WINDOW)

    chord = float(np.linalg.norm(core[-1] - core[0]))
    if chord < config.GESTURE_LINE_MIN_LENGTH:
        return False

    tolerance = max(config.GESTURE_LINE_TOLERANCE * chord, config.GESTURE_LINE_MIN_TOLERANCE_PX)
    simplified = cv2.approxPolyDP(core.reshape(-1, 1, 2).astype(np.float32), tolerance, False)
    if len(simplified) != 2:
        return False
    return _path_length(core) <= chord * config.GESTURE_LINE_MAX_PATH_RATIO     # bukan bolak-balik


# ---------------------------------------------------------------------------
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
        return "unknown"
    if circularity > 0.75 or vertices >= 5:
        return "circle"
    return "unknown"


# ---------------------------------------------------------------------------
def _classify_open(pts):
    # Garis sudah ditangani _is_line() di classify(); di sini tinggal zigzag.
    if _count_direction_changes(pts) >= 2:
        return "zigzag"

    return "unknown"


def _count_direction_changes(pts, step=2):
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
