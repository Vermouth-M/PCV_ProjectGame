"""game/utils.py -- helper matematika & collision kecil-kecilan."""

import math


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def normalize(vx, vy):
    length = math.hypot(vx, vy)
    if length < 1e-6:
        return 0.0, 0.0
    return vx / length, vy / length


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def circle_collide(pos_a, radius_a, pos_b, radius_b):
    return distance(pos_a, pos_b) <= (radius_a + radius_b)
