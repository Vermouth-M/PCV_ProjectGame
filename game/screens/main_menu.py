"""game/screens/main_menu.py -- layar menu utama."""

import math
import random

import pygame

import config
from game import background
from game.screens.base import Screen
from game.screens.widgets import (ACCENT, BAD, DIM, GOOD, TEXT, WARN, Menu, MenuItem,
                                  dim, draw_shape_icon, draw_text)

_LIGHT_COLORS = {"good": GOOD, "warn": WARN, "bad": BAD}


class MainMenuScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        cx = config.SCREEN_WIDTH // 2
        self.menu = Menu([
            MenuItem("Mulai Game", game.start_new_game),
            MenuItem("Tes Kamera", lambda: game.set_state("camera")),
            MenuItem("Cara Bermain", lambda: game.set_state("howto")),
            MenuItem("Pengaturan", lambda: game.open_settings("menu")),
            MenuItem("Keluar", game.quit),
        ], cx, 262)

        self.t = 0.0
        rng = random.Random(11)
        kinds = list(config.SKILL_DEFS)
        self.decor = []
        for i in range(14):
            kind = kinds[i % len(kinds)]
            self.decor.append({
                "kind": kind,
                "x": rng.uniform(0, config.SCREEN_WIDTH), "y": rng.uniform(0, config.SCREEN_HEIGHT),
                "vx": rng.uniform(-14, 14), "vy": rng.uniform(-10, 10),
                "angle": rng.uniform(0, math.tau), "spin": rng.uniform(-0.5, 0.5),
                "size": rng.uniform(34, 78), "color": config.SKILL_DEFS[kind]["color"],
            })

    def on_enter(self):
        self.menu.index = 0

    def handle_event(self, event):
        self.menu.handle_event(event)

    def update(self, dt):
        self.t += dt
        w, h = config.SCREEN_WIDTH, config.SCREEN_HEIGHT
        for d in self.decor:
            d["x"] = (d["x"] + d["vx"] * dt) % (w + 120)
            d["y"] = (d["y"] + d["vy"] * dt) % (h + 120)
            d["angle"] += d["spin"] * dt

    def draw(self, surface):
        surface.fill(config.COLOR_BG)
        background.draw_background(surface, self.t * 18, self.t * 11)
        dim(surface, 120)

        layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for d in self.decor:
            color = (*d["color"], 70)
            draw_shape_icon(layer, d["kind"], (d["x"] - 60, d["y"] - 60), d["size"], color, 3, d["angle"])
        surface.blit(layer, (0, 0))

        # judul (berdenyut halus)
        pulse = 0.5 + 0.5 * math.sin(self.t * 2.2)
        title_color = tuple(int(a + (255 - a) * pulse * 0.45) for a in ACCENT)
        cx = config.SCREEN_WIDTH // 2
        draw_text(surface, "VAMPIRE GESTURE", 54, title_color, (cx, 92), anchor="center", bold=True, shadow=True)
        draw_text(surface, "SURVIVOR", 54, title_color, (cx, 150), anchor="center", bold=True, shadow=True)
        draw_text(surface, "Gambar jurusmu di udara dengan sarung tangan hitam", 19, DIM,
                  (cx, 204), anchor="center")

        self.menu.draw(surface)
        self._draw_status(surface)

    def _draw_status(self, surface):
        cx = config.SCREEN_WIDTH // 2
        if self.game.camera_available:
            draw_text(surface, "Kamera: terdeteksi", 16, GOOD, (cx, 618), anchor="center")
            light = self.game.gesture_thread.get_lighting()
            if light is not None:
                draw_text(surface, f"Pencahayaan: {light.label}", 16, _LIGHT_COLORS[light.status],
                          (cx, 640), anchor="center")
        else:
            draw_text(surface, "Kamera TIDAK terdeteksi - jurus lewat tombol 1-5 saat bermain",
                      16, BAD, (cx, 618), anchor="center")
        draw_text(surface, "W/S atau panah: pilih   |   Enter atau klik: jalankan", 15, DIM,
                  (cx, 672), anchor="center")
