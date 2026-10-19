"""game/screens/how_to_play.py -- layar Cara Bermain (kontrol, 5 jurus, tips)."""

import pygame

import config
from game import background
from game.screens.base import Screen
from game.screens.widgets import (ACCENT, DIM, TEXT, Menu, MenuItem, dim, draw_shape_icon,
                                  draw_text)

CONTROLS = [
    ("W A S D", "Gerak"),
    ("Tahan SPASI", "Mulai menggambar jurus"),
    ("Lepas SPASI", "Jurus dikeluarkan"),
    ("C", "Kalibrasi ulang"),
    ("M", "Lihat mask hitam di kamera"),
    ("1 - 5", "Jurus tanpa kamera"),
    ("ESC", "Jeda / kembali"),
]

SHAPE_NAME = {"triangle": "Segitiga", "circle": "Lingkaran", "square": "Kotak",
              "line": "Garis lurus", "zigzag": "Zigzag"}
EFFECT = {
    "triangle": "tebasan area di depan pemain",
    "circle": "ledakan sekeliling + dorong",
    "square": "perisai, kebal sementara",
    "line": "tebasan lurus menembus musuh",
    "zigzag": "petir loncat antar musuh",
}

TIPS = [
    "Pakai sarung tangan HITAM; latar terang & polos paling akurat.",
    "Saat kalibrasi: duduk diam, jauhkan atau gerakkan sarung tangan.",
    "Tahan SPASI dengan ibu jari, jari lain tetap di WASD.",
    "Selama SPASI ditahan, musuh melambat (mode fokus).",
    "Cek cahaya & tracking di menu 'Tes Kamera'.",
]


class HowToPlayScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        cx = config.SCREEN_WIDTH // 2
        self.menu = Menu([MenuItem("Kembali", lambda: game.set_state("menu"))],
                         cx, 624, row_w=300, row_h=44, font_size=24)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.set_state("menu")
            return
        self.menu.handle_event(event)

    def draw(self, surface):
        surface.fill(config.COLOR_BG)
        background.draw_background(surface, 0, 0)
        dim(surface, 165)

        draw_text(surface, "CARA BERMAIN", 40, ACCENT, (config.SCREEN_WIDTH // 2, 44),
                  anchor="center", bold=True, shadow=True)

        # kolom kiri: kontrol
        draw_text(surface, "KONTROL", 22, ACCENT, (50, 96), bold=True)
        for i, (key, desc) in enumerate(CONTROLS):
            y = 134 + i * 30
            draw_text(surface, key, 18, ACCENT, (50, y), bold=True)
            draw_text(surface, desc, 18, TEXT, (190, y))

        # kolom kanan: jurus
        draw_text(surface, "JURUS (SPASI + gambar bentuk)", 22, ACCENT, (520, 96), bold=True)
        for i, (shape, cfg) in enumerate(config.SKILL_DEFS.items()):
            y = 136 + i * 60
            draw_shape_icon(surface, shape, (548, y + 22), 36, cfg["color"], 3)
            draw_text(surface, cfg["name"], 19, cfg["color"], (590, y), bold=True)
            draw_text(surface, f"{SHAPE_NAME[shape]}: {EFFECT[shape]}", 15, DIM, (590, y + 25))

        # tips
        draw_text(surface, "TIPS", 22, ACCENT, (50, 392), bold=True)
        for i, line in enumerate(TIPS):
            draw_text(surface, f"- {line}", 17, TEXT, (50, 428 + i * 28))

        self.menu.draw(surface)
