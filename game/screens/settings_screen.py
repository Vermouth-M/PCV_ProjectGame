"""game/screens/settings_screen.py -- layar Pengaturan (tersimpan otomatis ke settings.json)."""

import pygame

import config
from game import background, settings
from game.screens.base import Screen
from game.screens.widgets import ACCENT, DIM, GOOD, WARN, Menu, MenuItem, dim, draw_text


class SettingsScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.return_to = "menu"      # diisi game.open_settings(): "menu" atau "paused"
        self.saved = True

        items = []
        for setting in settings.SETTINGS:
            items.append(MenuItem(
                setting.label,
                action=lambda s=setting: self._change(s, +1),
                value=lambda s=setting: s.text(),
                on_left=lambda s=setting: self._change(s, -1),
                on_right=lambda s=setting: self._change(s, +1),
            ))
        items.append(MenuItem("Kembalikan ke bawaan", self._reset))
        items.append(MenuItem("Kembali", self._back))
        self.menu = Menu(items, config.SCREEN_WIDTH // 2, 120, row_w=720, row_h=46, gap=8, font_size=25)

    def on_enter(self):
        self.menu.index = 0

    def _change(self, setting, delta):
        setting.step(delta)
        self.saved = settings.save()
        self.game.on_setting_changed(setting.key)

    def _reset(self):
        settings.reset_defaults()
        self.saved = settings.save()
        self.game.on_setting_changed("*")

    def _back(self):
        self.game.set_state(self.return_to)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._back()
            return
        self.menu.handle_event(event)

    def draw(self, surface):
        surface.fill(config.COLOR_BG)
        background.draw_background(surface, 0, 0)
        dim(surface, 165)

        cx = config.SCREEN_WIDTH // 2
        draw_text(surface, "PENGATURAN", 40, ACCENT, (cx, 54), anchor="center", bold=True, shadow=True)
        self.menu.draw(surface)

        draw_text(surface, "A/D atau panah kiri/kanan: ubah   |   Enter: ganti   |   Esc: kembali",
                  15, DIM, (cx, 648), anchor="center")
        if self.saved:
            draw_text(surface, "Perubahan tersimpan otomatis (settings.json).", 15, GOOD,
                      (cx, 672), anchor="center")
        else:
            draw_text(surface, "Gagal menyimpan settings.json; berlaku sampai game ditutup.", 15, WARN,
                      (cx, 672), anchor="center")
