"""
config.py
=========
Semua konstanta dan pengaturan game dikumpulkan di sini supaya mudah
di-tweak tanpa perlu mengubah logika di file lain.
"""

import os

# ---------------------------------------------------------------------------
# Layar & Umum
# ---------------------------------------------------------------------------
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60
GAME_TITLE = "Vampire Gesture Survivor"

# Warna (R, G, B)
COLOR_BG = (18, 18, 24)
COLOR_GRID = (32, 32, 40)
COLOR_PLAYER = (80, 200, 255)
COLOR_PLAYER_HIT = (255, 80, 80)
COLOR_HP_BAR_BG = (60, 20, 20)
COLOR_HP_BAR_FG = (220, 40, 40)
COLOR_XP_BAR_BG = (30, 30, 50)
COLOR_XP_BAR_FG = (240, 200, 40)
COLOR_TEXT = (230, 230, 235)
COLOR_TEXT_DIM = (150, 150, 160)
COLOR_SHIELD = (90, 220, 255)

ENEMY_COLORS = {
    "basic": (200, 70, 90),
    "fast": (230, 150, 40),
    "tank": (140, 90, 200),
}

# ---------------------------------------------------------------------------
# Pemain
# ---------------------------------------------------------------------------
PLAYER_RADIUS = 16
PLAYER_SPEED = 220.0          # pixel/detik
PLAYER_MAX_HP = 100
PLAYER_INVULN_TIME = 0.7      # detik i-frame setelah kena hit
PLAYER_PICKUP_RADIUS = 90     # radius magnet menarik orb XP
PLAYER_BASE_ATTACK_DAMAGE = 6
PLAYER_BASE_ATTACK_COOLDOWN = 1.2
PLAYER_BASE_ATTACK_RANGE = 260

# ---------------------------------------------------------------------------
# Leveling
# ---------------------------------------------------------------------------
XP_BASE_REQUIREMENT = 20
XP_GROWTH = 1.35

# ---------------------------------------------------------------------------
# Musuh & Spawner
# ---------------------------------------------------------------------------
ENEMY_SPAWN_MARGIN = 120         # jarak di luar layar tempat musuh muncul
ENEMY_BASE_SPAWN_INTERVAL = 1.4  # detik antar spawn di awal
ENEMY_MIN_SPAWN_INTERVAL = 0.25
ENEMY_SPAWN_RAMP_TIME = 180.0    # detik untuk mencapai kecepatan spawn tercepat
ENEMY_MAX_ALIVE = 220

ENEMY_STATS = {
    "basic": {"hp": 20, "speed": 70, "damage": 8, "xp": 5, "radius": 14},
    "fast":  {"hp": 12, "speed": 140, "damage": 6, "xp": 6, "radius": 11},
    "tank":  {"hp": 90, "speed": 40, "damage": 16, "xp": 18, "radius": 22},
}
# Threshold waktu (detik) sebelum tipe musuh tsb mulai dimunculkan
ENEMY_UNLOCK_TIME = {
    "basic": 0,
    "fast": 25,
    "tank": 60,
}

ENEMY_DIFFICULTY_HP_SCALE_PER_MIN = 0.18
ENEMY_DIFFICULTY_SPEED_SCALE_PER_MIN = 0.05

# ---------------------------------------------------------------------------
# Gestur / Kamera (OpenCV murni, TANPA mediapipe)
# ---------------------------------------------------------------------------
CAMERA_INDEX = 0
CAMERA_CAPTURE_WIDTH = 320
CAMERA_CAPTURE_HEIGHT = 240
CAMERA_MIRROR = True          # flip horizontal biar berasa seperti cermin

# mode deteksi tangan: "skin" (warna kulit) atau "marker" (benda berwarna cerah)
GESTURE_DETECTION_MODE = "skin"

# Rentang HSV default untuk kulit (bisa dikalibrasi lewat tools/calibrate_hsv.py)
SKIN_HSV_LOWER = (0, 30, 60)
SKIN_HSV_UPPER = (25, 150, 255)

# Rentang HSV default untuk marker hijau terang (sarung tangan/benda hijau neon)
MARKER_HSV_LOWER = (35, 80, 80)
MARKER_HSV_UPPER = (85, 255, 255)

GESTURE_MIN_CONTOUR_AREA = 800     # kontur di bawah ini dianggap noise
GESTURE_MIN_POINTS = 8             # minimal titik lintasan agar bisa diklasifikasi
GESTURE_MIN_BOUNDING_BOX = 30      # minimal ukuran bbox (px, di frame kamera)
GESTURE_MAX_RECORD_SECONDS = 4.0   # auto-stop kalau kelamaan
GESTURE_MIN_MOVE_DIST = 3          # jarak minimal antar titik yg direkam (px)

GESTURE_CLOSED_LOOP_RATIO = 0.35   # first-last dist / path length -> dianggap "tertutup"
GESTURE_APPROX_EPSILON_RATIO = 0.03

GESTURE_TIME_SCALE_WHILE_DRAWING = 0.35   # slow-mo musuh saat menggambar jurus (mode fokus)

# File hasil kalibrasi HSV dari tools/calibrate_hsv.py (opsional, auto-load kalau ada)
HSV_CALIBRATION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hsv_calibration.json")

# ---------------------------------------------------------------------------
# Skill / Jurus
# ---------------------------------------------------------------------------
SKILL_DEFS = {
    "triangle": {
        "name": "Jurus Segitiga Pedang",
        "damage": 34,
        "radius": 100,
        "angle_deg": 130,
        "cooldown": 3.0,
        "color": (255, 210, 90),
    },
    "circle": {
        "name": "Jurus Lingkaran Gelombang Kejut",
        "damage": 22,
        "radius": 140,
        "cooldown": 5.0,
        "knockback": 260,
        "color": (120, 200, 255),
    },
    "square": {
        "name": "Jurus Kotak Perisai",
        "duration": 3.0,
        "cooldown": 9.0,
        "color": (120, 255, 180),
    },
    "line": {
        "name": "Jurus Garis Tebasan",
        "damage": 42,
        "length": 420,
        "width": 46,
        "cooldown": 4.0,
        "color": (255, 120, 200),
    },
    "zigzag": {
        "name": "Jurus Zigzag Petir",
        "damage": 16,
        "max_chain": 5,
        "chain_radius": 220,
        "cooldown": 6.0,
        "color": (255, 255, 120),
    },
}

# Kalau True, tombol 1-5 bisa langsung memicu jurus tanpa kamera.
# Berguna untuk development/testing atau kalau kamera tidak tersedia.
DEBUG_KEYBOARD_GESTURE_FALLBACK = True
