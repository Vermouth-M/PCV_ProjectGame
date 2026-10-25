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
    "basic": {"hp": 20, "speed": 70, "damage": 8, "xp": 5, "radius": 14, "score": 10},
    "fast":  {"hp": 12, "speed": 140, "damage": 6, "xp": 6, "radius": 11, "score": 15},
    "tank":  {"hp": 90, "speed": 40, "damage": 16, "xp": 18, "radius": 22, "score": 50},
}
ENEMY_NAMES = {
    "basic": "Basic",
    "fast": "Fast",
    "tank": "Tank",
}
ENEMY_UNLOCK_TIME = {
    "basic": 0,
    "fast": 25,
    "tank": 60,
}

ENEMY_DIFFICULTY_HP_SCALE_PER_MIN = 0.18
ENEMY_DIFFICULTY_SPEED_SCALE_PER_MIN = 0.05
ENEMY_DIFFICULTY_HP_SCALE_PER_MIN = 0.18
ENEMY_DIFFICULTY_SPEED_SCALE_PER_MIN = 0.05

# ---------------------------------------------------------------------------
# Gestur / Kamera (OpenCV murni, TANPA mediapipe)
# ---------------------------------------------------------------------------
CAMERA_INDEX = 0
# Resolusi tangkapan kamera (dipakai untuk preview, makin besar makin tajam)
CAMERA_CAPTURE_WIDTH = 640
CAMERA_CAPTURE_HEIGHT = 480
# Resolusi kerja untuk tracking tangan. Semua threshold piksel di bawah
# (GESTURE_MIN_CONTOUR_AREA, GESTURE_MIN_BOUNDING_BOX, dst) dituning untuk
# ukuran ini, jadi jangan diubah kecuali threshold-nya ikut disesuaikan.
GESTURE_PROCESS_WIDTH = 320
GESTURE_PROCESS_HEIGHT = 240
CAMERA_MIRROR = True          # flip horizontal biar berasa seperti cermin

# Ukuran panel preview kamera di pojok kanan-bawah layar game
CAMERA_PANEL_WIDTH = 400
CAMERA_PANEL_HEIGHT = 300
CAMERA_PANEL_MARGIN = 16
CAMERA_PANEL_ALPHA = 225      # 0-255, makin kecil makin transparan

# ---------------------------------------------------------------------------
# Tracking SARUNG TANGAN HITAM (OpenCV murni; game ini HANYA melacak warna)
# ---------------------------------------------------------------------------
# --- Ambang "hitam" yang menyesuaikan pencahayaan secara otomatis ------------
# level = persentil ke-75 kanal V (kecerahan) frame, skala 0-255, dihaluskan.
# v_max = BLACK_V_RATIO * level + BLACK_V_OFFSET, lalu dibatasi MIN..MAX.
# Ruangan terang -> ambang naik; ruangan redup -> ambang turun. Otomatis.
BLACK_V_RATIO = 0.38
BLACK_V_OFFSET = 12
BLACK_V_MIN = 28
BLACK_V_MAX = 95
BLACK_V_MAX_OVERRIDE = None   # isi angka (mis. 60) untuk MEMATIKAN mode otomatis
BLACK_S_MAX = 255             # saturasi maksimum (255 = bebas)
LIGHT_SMOOTHING = 0.15        # 0-1: makin kecil makin halus tapi lambat menyesuaikan

# Batas label pada bar pencahayaan (satuan level 0-255)
LIGHT_LEVEL_TOO_DARK = 40
LIGHT_LEVEL_DIM = 80
LIGHT_LEVEL_BRIGHT = 200
LIGHT_LEVEL_OVEREXPOSED = 232

# --- Membedakan sarung tangan dari rambut & benda hitam yang diam ------------
GESTURE_AUTO_CALIBRATE_ON_START = True   # kalibrasi otomatis saat game dibuka
GESTURE_CALIB_FRAMES = 45            # jumlah frame yang dipelajari (~1.5 detik)
GESTURE_CALIB_TIMEOUT = 8.0          # detik; selesai/batal paksa kalau kamera macet
GESTURE_CALIB_PREPARE_SECONDS = 1.5   # hitung mundur sebelum kalibrasi (sempat menjauhkan sarung tangan)
GESTURE_WARMUP_FRAMES = 20           # frame awal diabaikan (auto-exposure webcam)
GESTURE_CALIB_PERSISTENCE = 0.7      # piksel hitam di >=70% frame dianggap "diam"
GESTURE_EXCLUSION_DILATE = 12        # px pelebaran zona diabaikan (toleransi kepala goyang)

# --- Filter gumpalan hitam (kandidat sarung tangan) ---------------------------
GESTURE_BLACK_MAX_AREA_RATIO = 0.25  # abaikan gumpalan > 25% luas frame
GESTURE_MIN_SOLIDITY = 0.55          # kepadatan bentuk (luas / luas convex hull)
GESTURE_TRACK_CONTINUITY_SECONDS = 0.5
GESTURE_TRACK_CONTINUITY_MIN_AREA = 0.4

GESTURE_MIN_CONTOUR_AREA = 800     # kontur di bawah ini dianggap noise
GESTURE_MIN_POINTS = 8             # minimal titik lintasan agar bisa diklasifikasi
GESTURE_MIN_BOUNDING_BOX = 30      # minimal ukuran bbox (px, di frame kamera)
GESTURE_MAX_RECORD_SECONDS = 4.0   # auto-stop kalau kelamaan
GESTURE_MIN_MOVE_DIST = 3          # jarak minimal antar titik yg direkam (px)

GESTURE_CLOSED_LOOP_RATIO = 0.35   # first-last dist / path length -> dianggap "tertutup"
GESTURE_APPROX_EPSILON_RATIO = 0.03
GESTURE_LINE_MIN_POINTS = 3        # garis cukup beberapa titik (sapuan cepat = sedikit titik)
GESTURE_LINE_MIN_LENGTH = 35       # panjang minimal garis (px, di frame kamera)
GESTURE_LINE_TOLERANCE = 0.10      # simpangan maks dari garis lurus, relatif terhadap panjang garis
GESTURE_LINE_MIN_TOLERANCE_PX = 5  # batas bawah simpangan (px) agar getar centroid tidak dihitung
GESTURE_LINE_MAX_PATH_RATIO = 1.5  # panjang lintasan / panjang garis; di atas ini = bolak-balik
GESTURE_SMOOTH_WINDOW = 5          # jendela perataan titik sebelum dicek apakah garis

GESTURE_TIME_SCALE_WHILE_DRAWING = 0.35   # slow-mo musuh saat menggambar jurus (mode fokus)


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

# ---------------------------------------------------------------------------
# Aset gambar (sprite, efek, latar, ikon). Folder `assets/` BOLEH KOSONG:
# bagian yang file-nya tidak ada otomatis memakai gambar vektor bawaan.
# Daftar nama file yang dikenali: assets/README.md atau `python tools/check_assets.py`
# ---------------------------------------------------------------------------
USE_ASSETS = True    # False = paksa semua gambar vektor (abaikan folder assets/)
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

# Ukuran sprite = diameter hitbox x faktor ini (sisi terpanjang gambar disesuaikan,
# rasio aspek dipertahankan). Naikkan/turunkan kalau sprite terasa terlalu kecil/besar.
SPRITE_SCALE = {"player": 2.2, "enemy": 2.0, "xp_orb": 3.0, "projectile": 3.0}

# Kecepatan animasi (frame per detik)
ANIM_FPS = {"player_idle": 4, "player_walk": 10, "enemy": 8, "xp_orb": 8}

LIGHTNING_THICKNESS = 30        # tebal sprite petir pada tiap sambungan (px)
BACKGROUND_TILE_SCALE = 1.0     # skala tile latar (1.0 = ukuran asli gambar)
SKILL_ICON_SIZE = 20            # ukuran ikon jurus di HUD (px)
