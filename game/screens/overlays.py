"""game/screens/overlays.py -- layar yang tampil DI ATAS dunia game: Jeda dan Game Over."""

import pygame

import config
from game.screens.base import Screen
from game.screens.widgets import ACCENT, BAD, DIM, TEXT, Menu, MenuItem, dim, draw_text, fill_rounded


class PauseScreen(Screen):
    overlay = True

    def __init__(self, game):
        super().__init__(game)
        cx = config.SCREEN_WIDTH // 2
        self.menu = Menu([
            MenuItem("Lanjutkan", lambda: game.set_state("playing")),
            MenuItem("Kalibrasi Ulang", self._recalibrate, enabled=lambda: game.camera_available),
            MenuItem("Pengaturan", lambda: game.open_settings("paused")),
            MenuItem("Menu Utama", self._ask_confirm),
        ], cx, 252)
        self.confirm = Menu([
            MenuItem("Tidak, lanjut bermain", self._cancel_confirm),
            MenuItem("Ya, ke menu utama", game.go_to_menu),
        ], cx, 372)
        self.confirming = False

    def on_enter(self):
        self.confirming = False
        self.menu.index = 0

    def _recalibrate(self):
        self.game.set_state("playing")
        self.game.begin_calibration()

    def _ask_confirm(self):
        self.confirming = True
        self.confirm.index = 0

    def _cancel_confirm(self):
        self.confirming = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.confirming:
                self.confirming = False
            else:
                self.game.set_state("playing")
            return
        (self.confirm if self.confirming else self.menu).handle_event(event)

    def draw(self, surface):
        dim(surface, 185)
        cx = config.SCREEN_WIDTH // 2
        draw_text(surface, "JEDA", 52, ACCENT, (cx, 168), anchor="center", bold=True, shadow=True)
        if self.confirming:
            draw_text(surface, "Kembali ke menu utama?", 26, TEXT, (cx, 300), anchor="center", bold=True)
            draw_text(surface, "Permainan yang sedang berjalan akan hilang.", 17, BAD, (cx, 336), anchor="center")
            self.confirm.draw(surface)
        else:
            self.menu.draw(surface)
            draw_text(surface, "Esc: lanjutkan", 15, DIM, (cx, 524), anchor="center")


class GameOverScreen(Screen):
    overlay = True

    def __init__(self, game):
        super().__init__(game)
        cx = config.SCREEN_WIDTH // 2
        self.menu = Menu([
            MenuItem("Main Lagi", lambda: game.start_new_game(calibrate=False)),
            MenuItem("Menu Utama", game.go_to_menu),
        ], cx, 408)

    def on_enter(self):
        self.menu.index = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.game.start_new_game(calibrate=False)
                return
            if event.key == pygame.K_ESCAPE:
                self.game.go_to_menu()
                return
        self.menu.handle_event(event)

    def draw(self, surface):
        dim(surface, 190)
        cx = config.SCREEN_WIDTH // 2
        game = self.game
        draw_text(surface, "GAME OVER", 58, BAD, (cx, 150), anchor="center", bold=True, shadow=True)

        box = pygame.Rect(cx - 230, 214, 460, 160)
        fill_rounded(surface, box, (0, 0, 0, 150), 14, border=(90, 90, 100), border_width=1)
        mins, secs = divmod(int(game.elapsed), 60)
        rows = [("Bertahan", f"{mins:02d}:{secs:02d}"),
                ("Musuh dikalahkan", str(game.player.kills)),
                ("Level dicapai", str(game.player.level))]
        for i, (label, value) in enumerate(rows):
            y = box.y + 34 + i * 44
            draw_text(surface, label, 22, TEXT, (box.x + 30, y), anchor="midleft")
            draw_text(surface, value, 26, ACCENT, (box.right - 30, y), anchor="midright", bold=True)

        self.menu.draw(surface)
        draw_text(surface, "R: main lagi   |   Esc: menu utama", 15, DIM, (cx, 532), anchor="center")
