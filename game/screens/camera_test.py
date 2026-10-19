"""
game/screens/camera_test.py
=============================
Layar Tes Kamera: tempat memeriksa kamera, pencahayaan, dan tracking sarung
tangan SEBELUM bermain, sekaligus latihan menggambar jurus tanpa musuh.

  C      kalibrasi rambut/benda hitam diam
  M      tampilkan mask hitam
  SPASI  tahan lalu gambar bentuk; lepas -> bentuk yang dikenali ditampilkan
  ESC    kembali
"""

import pygame

import config
from game import background, camera_overlay
from game.screens.base import Screen
from game.screens.widgets import (ACCENT, BAD, DIM, GOOD, TEXT, Menu, MenuItem, dim,
                                  draw_shape_icon, draw_text, fill_rounded, wrap_text)
from gesture import shape_classifier

PANEL = pygame.Rect(40, 190, 560, 420)

HELP = [
    "1. Duduk di posisi bermain.",
    "2. Pakai sarung tangan hitam.",
    "3. Tekan C: kalibrasi rambut",
    "   (jauhkan sarung tangan).",
    "4. Tahan SPASI, gambar bentuk,",
    "   lepas SPASI untuk menguji.",
    "M: lihat mask     ESC: kembali",
]


class CameraTestScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.holding = False
        self.result = None           # (id_bentuk, jumlah_titik)
        self.menu = Menu([MenuItem("Kembali", lambda: game.set_state("menu"))],
                         800, 628, row_w=320, row_h=44, font_size=24)

    def on_enter(self):
        self.holding = False
        self.result = None

    def on_exit(self):
        if self.holding:
            self.game.gesture_thread.end_recording()
            self.holding = False

    # ------------------------------------------------------------------
    def handle_event(self, event):
        game = self.game
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game.set_state("menu")
                return
            if event.key == pygame.K_SPACE:
                if game.camera_available and not game.calibration_active() and not self.holding:
                    self.holding = True
                    self.result = None
                    game.gesture_thread.begin_recording()
                return
            if event.key == pygame.K_c:
                game.begin_calibration()
                return
            if event.key == pygame.K_m:
                game.show_mask = not game.show_mask
                return
        elif event.type == pygame.KEYUP and event.key == pygame.K_SPACE and self.holding:
            self._finish()
            return
        self.menu.handle_event(event)

    def _finish(self):
        self.holding = False
        points = self.game.gesture_thread.end_recording()
        self.result = (shape_classifier.classify(points), len(points))

    def update(self, dt):
        if self.holding and self.game.gesture_thread.recording_expired():
            self._finish()

    # ------------------------------------------------------------------
    def draw(self, surface):
        game = self.game
        gt = game.gesture_thread
        surface.fill(config.COLOR_BG)
        background.draw_background(surface, 0, 0)
        dim(surface, 175)

        draw_text(surface, "TES KAMERA", 38, ACCENT, (config.SCREEN_WIDTH // 2, 36),
                  anchor="center", bold=True, shadow=True)

        frame, mask, centroid = gt.get_preview()
        camera_overlay.draw_camera_panel(
            surface, frame, mask, gt.current_points(), centroid=centroid,
            exclusion=gt.get_exclusion(), show_mask=game.show_mask, rect=PANEL, alpha=255)

        if game.camera_available:
            game.ui.draw_lighting_bar(surface, PANEL, gt.get_lighting(), gt.exclusion_ratio(),
                                      game.calibration_active())
        else:
            self._draw_no_camera(surface)

        self._draw_side(surface, centroid)
        game.draw_calibration_overlay(surface)
        self.menu.draw(surface)

    def _draw_no_camera(self, surface):
        box = pygame.Rect(PANEL.x + 40, PANEL.centery - 70, PANEL.width - 80, 140)
        fill_rounded(surface, box, (0, 0, 0, 200), 12, border=BAD)
        draw_text(surface, "Kamera tidak terdeteksi", 24, BAD, (box.centerx, box.y + 34),
                  anchor="center", bold=True)
        draw_text(surface, "Cek izin kamera & apakah dipakai aplikasi lain,", 15, TEXT,
                  (box.centerx, box.y + 70), anchor="center")
        draw_text(surface, "atau ubah CAMERA_INDEX di config.py.", 15, TEXT,
                  (box.centerx, box.y + 92), anchor="center")
        draw_text(surface, "Game tetap bisa dimainkan dengan tombol 1-5.", 15, DIM,
                  (box.centerx, box.y + 114), anchor="center")

    def _draw_side(self, surface, centroid):
        game, gt = self.game, self.game.gesture_thread
        x = 640

        draw_text(surface, "CARA PAKAI", 20, ACCENT, (x, 92), bold=True)
        for i, line in enumerate(HELP):
            draw_text(surface, line, 16, TEXT, (x, 124 + i * 24))

        draw_text(surface, "STATUS", 20, ACCENT, (x, 306), bold=True)
        if not game.camera_available:
            draw_text(surface, "Kamera: tidak terdeteksi", 16, BAD, (x, 338))
        else:
            draw_text(surface, "Kamera: terdeteksi", 16, GOOD, (x, 338))
            if centroid is not None:
                draw_text(surface, "Sarung tangan: TERLIHAT", 16, GOOD, (x, 362))
            else:
                draw_text(surface, "Sarung tangan: tidak terlihat", 16, BAD, (x, 362))
            if self.holding:
                draw_text(surface, f"Merekam: {len(gt.current_points())} titik", 16, ACCENT, (x, 386))

        draw_text(surface, "HASIL TERAKHIR", 20, ACCENT, (x, 424), bold=True)
        box = pygame.Rect(x, 456, 320, 140)
        fill_rounded(surface, box, (0, 0, 0, 130), 12, border=(90, 90, 100), border_width=1)
        if self.result is None:
            draw_text(surface, "Belum ada. Tahan SPASI lalu", 16, DIM, (box.centerx, box.y + 56), anchor="center")
            draw_text(surface, "gambar sebuah bentuk.", 16, DIM, (box.centerx, box.y + 80), anchor="center")
            return

        shape, n_points = self.result
        cfg = config.SKILL_DEFS.get(shape)
        if cfg is None:
            draw_text(surface, "Tidak dikenali", 22, BAD, (box.centerx, box.y + 40), anchor="center", bold=True)
            hint = "Terlalu sedikit titik; coba lebih besar" if n_points < config.GESTURE_MIN_POINTS \
                else "Coba gambar lebih besar & perlahan"
            draw_text(surface, hint, 15, TEXT, (box.centerx, box.y + 76), anchor="center")
        else:
            draw_shape_icon(surface, shape, (box.x + 56, box.centery), 56, cfg["color"], 4)
            name_lines = wrap_text(cfg["name"], 17, box.right - (box.x + 104) - 10, bold=True)
            y = box.y + 34
            for line in name_lines:
                draw_text(surface, line, 17, cfg["color"], (box.x + 104, y), bold=True)
                y += 24
            draw_text(surface, f"bentuk: {shape}", 15, TEXT, (box.x + 104, y + 6))
        draw_text(surface, f"{n_points} titik terekam", 14, DIM, (box.centerx, box.bottom - 18), anchor="center")
