"""
gesture/lighting.py
=====================
Memantau kondisi pencahayaan dan menghitung ambang "hitam" yang menyesuaikan
diri secara otomatis (kompensasi pencahayaan).

Masalahnya: sarung tangan hitam tidak selalu tampak sama hitamnya. Di ruangan
terang ia bisa terbaca V=60, di ruangan redup V=20. Ambang tetap (mis. V<70)
akan gagal -- di ruangan redup seluruh dinding ikut dianggap hitam.

Solusi: ambang diturunkan dari kecerahan scene.
    level = persentil ke-75 kanal V frame (permukaan yang terang), dihaluskan
    v_max = BLACK_V_RATIO * level + BLACK_V_OFFSET   (dibatasi MIN..MAX)
Sarung tangan memantulkan cahaya jauh lebih sedikit daripada dinding, jadi
kecerahannya kira-kira proporsional dengan level scene, ditambah sedikit
offset karena noise/black-level sensor kamera.
"""

from dataclasses import dataclass

import numpy as np

import config


@dataclass(frozen=True)
class LightingState:
    level: float        # kecerahan scene 0-255 (sudah dihaluskan)
    black_v_max: int    # ambang V (maks) yang dianggap hitam saat ini
    label: str          # teks untuk bar: "Terlalu gelap", "Redup", "Ideal", ...
    status: str         # "good" | "warn" | "bad" (untuk pewarnaan)
    hint: str           # saran singkat ke pemain (dijaga pendek, muat di HUD)


class LightingMonitor:
    def __init__(self):
        self._level = None
        self.state = None

    def update(self, v_channel):
        """v_channel: array 2D kanal V (HSV) dari frame saat ini. Return LightingState."""
        sample = v_channel[::4, ::4]   # subsampling: cukup untuk statistik, jauh lebih cepat
        level_now = float(np.percentile(sample, 75))

        if self._level is None:
            self._level = level_now
        else:
            self._level += config.LIGHT_SMOOTHING * (level_now - self._level)

        self.state = self._build_state(self._level)
        return self.state

    # ------------------------------------------------------------------
    @staticmethod
    def black_threshold(level):
        if config.BLACK_V_MAX_OVERRIDE is not None:
            return int(config.BLACK_V_MAX_OVERRIDE)
        raw = config.BLACK_V_RATIO * level + config.BLACK_V_OFFSET
        return int(round(min(config.BLACK_V_MAX, max(config.BLACK_V_MIN, raw))))

    def _build_state(self, level):
        v_max = self.black_threshold(level)

        if level < config.LIGHT_LEVEL_TOO_DARK:
            label, status = "Terlalu gelap", "bad"
            hint = "Nyalakan lampu / pindah ke tempat terang"
        elif level < config.LIGHT_LEVEL_DIM:
            label, status = "Redup", "warn"
            hint = "Tambah cahaya agar lebih akurat"
        elif level <= config.LIGHT_LEVEL_BRIGHT:
            label, status = "Ideal", "good"
            hint = "Pencahayaan bagus, ambang otomatis"
        elif level <= config.LIGHT_LEVEL_OVEREXPOSED:
            label, status = "Terang", "good"
            hint = "Cukup terang, ambang otomatis"
        else:
            label, status = "Terlalu terang", "bad"
            hint = "Kurangi cahaya ke kamera / jauhi jendela"

        return LightingState(level=level, black_v_max=v_max, label=label, status=status, hint=hint)
