"""
tests/test_shape_classifier.py
=================================
Unit test sederhana (tanpa pytest) untuk gesture/shape_classifier.py.

Lintasan titik dibuat secara SINTETIS (bukan dari kamera sungguhan)
untuk memverifikasi bahwa algoritma klasifikasi bentuk bekerja sesuai
harapan, sehingga bisa dijalankan tanpa webcam sama sekali.

Jalankan:
    python tests/test_shape_classifier.py
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gesture import shape_classifier  # noqa: E402


def make_triangle(cx=160, cy=120, r=70, n_per_side=8):
    corners = [
        (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
        for a in (90, 210, 330)
    ]
    corners.append(corners[0])
    return _walk_corners(corners, n_per_side)


def make_square(cx=160, cy=120, half=60, n_per_side=8):
    corners = [
        (cx - half, cy - half), (cx + half, cy - half),
        (cx + half, cy + half), (cx - half, cy + half), (cx - half, cy - half),
    ]
    return _walk_corners(corners, n_per_side)


def _walk_corners(corners, n_per_side):
    points = []
    for i in range(len(corners) - 1):
        x1, y1 = corners[i]
        x2, y2 = corners[i + 1]
        for t in range(n_per_side):
            f = t / n_per_side
            points.append((x1 + (x2 - x1) * f, y1 + (y2 - y1) * f))
    return points


def make_circle(cx=160, cy=120, r=70, n=40):
    return [
        (cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n))
        for i in range(n + 1)
    ]


def make_line(x0=40, y0=120, x1=280, y1=130, n=20):
    return [(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n) for i in range(n + 1)]


def make_zigzag(x0=40, y0=120, n_segments=5, dx=48, dy=50):
    points = []
    x, y = x0, y0
    for i in range(n_segments):
        target_y = y0 + (dy if i % 2 == 0 else -dy)
        for t in range(6):
            f = t / 6
            points.append((x + dx * f, y + (target_y - y) * f))
        x += dx
        y = target_y
    return points


def run_case(name, points, expected):
    result = shape_classifier.classify(points)
    status = "OK" if result == expected else "GAGAL"
    print(f"[{status}] {name}: diharapkan '{expected}', hasil '{result}'")
    return result == expected


def main():
    cases = [
        ("segitiga", make_triangle(), "triangle"),
        ("kotak", make_square(), "square"),
        ("lingkaran", make_circle(), "circle"),
        ("garis", make_line(), "line"),
        ("zigzag", make_zigzag(), "zigzag"),
    ]

    passed = sum(run_case(name, points, expected) for name, points, expected in cases)
    print(f"\n{passed}/{len(cases)} test lolos.")
    if passed != len(cases):
        sys.exit(1)


if __name__ == "__main__":
    main()
