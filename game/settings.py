import json
import os

import config
from game import assets

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(config.__file__)), "settings.json")


class Setting:
    def __init__(self, key, label, choices, get, set_, after=None):
        self.key = key
        self.label = label
        self.choices = choices
        self._get = get
        self._set = set_
        self.after = after
        self.default = self.value()

    def index(self):
        current = self._get()
        for i, (value, _text) in enumerate(self.choices):
            if value == current:
                return i
        # nilai tidak ada di daftar (mis. diubah manual di config.py): ambil yang terdekat
        if isinstance(current, (int, float)) and not isinstance(current, bool):
            return min(range(len(self.choices)), key=lambda i: abs(self.choices[i][0] - current))
        return 0

    def value(self):
        return self.choices[self.index()][0]

    def text(self):
        return self.choices[self.index()][1]

    def apply(self, value):
        self._set(value)

    def has_choice(self, value):
        return any(value == v and type(value) is type(v) for v, _ in self.choices)

    def step(self, delta):
        idx = (self.index() + delta) % len(self.choices)
        self._set(self.choices[idx][0])
        if self.after:
            self.after()


def _attr(name):
    return (lambda: getattr(config, name)), (lambda v: setattr(config, name, v))


def _set_panel(size):
    config.CAMERA_PANEL_WIDTH, config.CAMERA_PANEL_HEIGHT = size


_YA_TIDAK = [(True, "Ya"), (False, "Tidak")]
_AKTIF = [(True, "Aktif"), (False, "Nonaktif")]

SETTINGS = [
    Setting("camera_mirror", "Kamera mode cermin", _YA_TIDAK, *_attr("CAMERA_MIRROR")),
    Setting("auto_calibrate", "Kalibrasi otomatis saat mulai", _YA_TIDAK,
            *_attr("GESTURE_AUTO_CALIBRATE_ON_START")),
    Setting("panel_size", "Ukuran panel kamera",
            [((240, 180), "Kecil"), ((400, 300), "Sedang"), ((480, 360), "Besar")],
            lambda: (config.CAMERA_PANEL_WIDTH, config.CAMERA_PANEL_HEIGHT), _set_panel),
    Setting("focus_mode", "Mode fokus (slow-mo saat gambar)",
            [(1.0, "Mati"), (0.6, "Ringan"), (0.35, "Sedang"), (0.2, "Kuat")],
            *_attr("GESTURE_TIME_SCALE_WHILE_DRAWING")),
    Setting("debug_keys", "Tombol cadangan 1-5", _AKTIF, *_attr("DEBUG_KEYBOARD_GESTURE_FALLBACK")),
    Setting("use_assets", "Aset gambar (game berikutnya)", _AKTIF, *_attr("USE_ASSETS"),
            after=lambda: assets.init()),
]


def load(path=None):
    """Terapkan settings.json ke config. Return True kalau ada nilai yang diterapkan."""
    path = path or SETTINGS_FILE
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return False
    if not isinstance(data, dict):
        return False

    applied = 0
    for setting in SETTINGS:
        if setting.key not in data:
            continue
        value = data[setting.key]
        if isinstance(value, list):
            value = tuple(value)
        if setting.has_choice(value):
            setting.apply(value)
            applied += 1
    return applied > 0


def save(path=None):
    """Simpan pilihan saat ini. Return True kalau berhasil."""
    path = path or SETTINGS_FILE
    data = {}
    for setting in SETTINGS:
        value = setting.value()
        data[setting.key] = list(value) if isinstance(value, tuple) else value
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except OSError as exc:
        print(f"[settings] PERINGATAN: gagal menyimpan '{path}' ({exc}).")
        return False


def reset_defaults():
    """Kembalikan semua pengaturan ke nilai bawaan config.py (tidak menyimpan otomatis)."""
    for setting in SETTINGS:
        setting.apply(setting.default)
    assets.init()
