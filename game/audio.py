import os

import pygame

import config

EXTENSIONS = ("wav", "ogg", "mp3")

MUSIC_FILES = {"menu": "music_menu", "game": "music_game"}
SFX_FILES = {
    "enemy_hit": "sfx_enemy_hit",
    "game_over": "sfx_game_over",
    "ui_click": "sfx_click",
    "skill_triangle": "sfx_skill_triangle",    # <-- baru
    "skill_circle": "sfx_skill_circle",
    "skill_square": "sfx_skill_square",
    "skill_line": "sfx_skill_line",
    "skill_zigzag": "sfx_skill_zigzag",
}

# State game -> musik yang diputar. State yang TIDAK tercantum (paused, settings,
# howto, camera) tidak mengubah musik, jadi musik tidak restart saat jeda/pengaturan.
STATE_MUSIC = {"menu": "menu", "playing": "game", "gameover": None}
# State game -> SFX yang dimainkan sekali saat masuk state itu
STATE_SFX = {"gameover": "game_over"}


class AudioManager:
    def __init__(self, enabled=True):
        self.root = os.path.join(config.ASSETS_DIR, "audio")
        self.ready = False
        self.current_music = None
        self._sounds = {}
        self._warned = set()
        if not enabled:
            return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.ready = True
        except pygame.error as exc:
            print(f"[audio] PERINGATAN: mixer tidak bisa dibuka ({exc}); game berjalan tanpa suara.")

    # ------------------------------------------------------------------
    def _find(self, name):
        for ext in EXTENSIONS:
            path = os.path.join(self.root, f"{name}.{ext}")
            if os.path.isfile(path):
                return path
        if name not in self._warned:
            self._warned.add(name)
            print(f"[audio] file '{name}' tidak ditemukan di '{self.root}'; dilewati.")
        return None

    # ------------------------------------------------------------------
    # SFX
    # ------------------------------------------------------------------
    def _load_sfx(self, key):
        sound = self._sounds.get(key)
        if sound is not None:
            return sound
        path = self._find(SFX_FILES[key])
        if path is None:
            return None
        try:
            sound = pygame.mixer.Sound(path)
        except pygame.error as exc:
            print(f"[audio] gagal memuat '{path}' ({exc})")
            return None
        self._sounds[key] = sound
        return sound

    def play_sfx(self, key):
        if not self.ready:
            return
        sound = self._load_sfx(key)
        if sound is None:
            return
        sound.set_volume(config.SFX_VOLUME)
        sound.play()

    # ------------------------------------------------------------------
    # Musik
    # ------------------------------------------------------------------
    def play_music(self, key):
        """key = 'menu' / 'game' / None (berhenti). Kalau sudah memutar lagu yang sama, diabaikan."""
        if not self.ready or key == self.current_music:
            return
        if key is None:
            pygame.mixer.music.stop()
            self.current_music = None
            return
        path = self._find(MUSIC_FILES[key])
        if path is None:
            pygame.mixer.music.stop()
            self.current_music = None
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(config.MUSIC_VOLUME)
            pygame.mixer.music.play(loops=-1, fade_ms=600)   # loop terus, fade-in halus
            self.current_music = key
        except pygame.error as exc:
            print(f"[audio] gagal memutar '{path}' ({exc})")
            self.current_music = None

    def refresh_volume(self):
        """Panggil setelah volume di config berubah (mis. dari menu Pengaturan)."""
        if self.ready:
            pygame.mixer.music.set_volume(config.MUSIC_VOLUME)

    # ------------------------------------------------------------------
    def on_state(self, state):
        """Dipanggil engine setiap pindah layar."""
        if state in STATE_MUSIC:
            self.play_music(STATE_MUSIC[state])
        if state in STATE_SFX:
            self.play_sfx(STATE_SFX[state])


_manager = AudioManager(enabled=False)   # nonaktif sampai init() dipanggil (aman untuk tes)


def init():
    global _manager
    _manager = AudioManager(enabled=True)
    return _manager


def get():
    return _manager