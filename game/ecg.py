import math

import pygame

import config


def ecg_wave(u):
    """Bentuk satu denyut. u = posisi dalam denyut (0..1)."""
    def g(center, width):
        return math.exp(-((u - center) / width) ** 2)
    return (0.12 * g(0.14, 0.03)        # gelombang P
            - 0.14 * g(0.235, 0.012)    # Q
            + 1.00 * g(0.27, 0.010)     # R (lonjakan tinggi)
            - 0.28 * g(0.31, 0.012)     # S
            + 0.22 * g(0.55, 0.05))     # T


def status_for(ratio):
    """Rasio HP (0..1) -> (label, bpm, warna)."""
    if ratio <= 0:
        return "DEAD", 0, (120, 120, 120)
    for min_ratio, label, bpm, color in config.ECG_STATUS:
        if ratio >= min_ratio:
            return label, bpm, color
    _, label, bpm, color = config.ECG_STATUS[-1]
    return label, bpm, color


class EcgMonitor:
    def __init__(self):
        self.phase = 0.0
        self.label, self.bpm, self.color = status_for(1.0)

    def update(self, dt, ratio):
        self.label, self.bpm, self.color = status_for(ratio)
        self.phase = (self.phase + self.bpm / 60.0 * dt) % 1.0

    def draw(self, surface, rect, ratio):
        baseline = rect.top + rect.height * 0.55
        amp = rect.height * 0.38
        points = []
        for i in range(0, rect.width + 1, 2):
            if self.bpm <= 0:
                y = baseline                       # garis datar (mati)
            else:
                u = (i / config.ECG_PIXELS_PER_BEAT + self.phase) % 1.0
                y = baseline - amp * ecg_wave(u)
            points.append((rect.left + i, y))
        glow = tuple(c // 3 for c in self.color)
        pygame.draw.lines(surface, glow, False, points, 6)     # pendar
        pygame.draw.lines(surface, self.color, False, points, 2)