"""game/ui.py -- HUD: health bar, XP bar, status jurus & instruksi kontrol."""

import pygame

import config
from game import assets


class UI:
    def __init__(self):
        pygame.font.init()
        self.font = pygame.font.SysFont("consolas", 18)
        self.font_big = pygame.font.SysFont("consolas", 34, bold=True)
        self.font_small = pygame.font.SysFont("consolas", 14)
        self.font_hud = pygame.font.SysFont("consolas", 24, bold=True)

    def draw_bar(self, surface, x, y, w, h, ratio, bg_color, fg_color, border=(0, 0, 0)):
        pygame.draw.rect(surface, bg_color, (x, y, w, h))
        pygame.draw.rect(surface, fg_color, (x, y, int(w * max(0, min(1, ratio))), h))
        pygame.draw.rect(surface, border, (x, y, w, h), width=2)

    def draw_hud(self, surface, player, elapsed, skill_manager, recording, camera_available,
                 glove_visible=True):
        """HUD di dalam area game: XP, waktu & kills (kanan atas), status gestur.
        HP dan skill digambar di kolom kanan (game/sidebar.py)."""
        # XP + level (kiri atas)
        self.draw_bar(surface, 20, 20, 260, 14, player.xp / player.xp_to_next,
                      config.COLOR_XP_BAR_BG, config.COLOR_XP_BAR_FG)
        lvl_text = self.font_small.render(f"Level {player.level}", True, config.COLOR_TEXT)
        surface.blit(lvl_text, (290, 18))

        # waktu & kills (kanan atas)
        mins, secs = divmod(int(elapsed), 60)
        self._blit_right(surface, f"TIME: {mins:02d}:{secs:02d}", 20, config.COLOR_TEXT)
        self._blit_right(surface, f"SKOR: {player.score}", 46, config.COLOR_TEXT)

        self._draw_gesture_status(surface, recording, camera_available, skill_manager, glove_visible)

    def _blit_right(self, surface, text, y, color):
        shadow = self.font_hud.render(text, True, (0, 0, 0))
        label = self.font_hud.render(text, True, color)
        x = surface.get_width() - 20 - label.get_width()
        surface.blit(shadow, (x + 1, y + 1))
        surface.blit(label, (x, y))

    def _draw_skill_list(self, surface, skill_manager):
        manager = assets.get()
        x, y = 20, surface.get_height() - 150
        for shape, cfg in config.SKILL_DEFS.items():
            ratio = skill_manager.cooldown_ratio(shape)
            ready = skill_manager.is_ready(shape)
            color = cfg["color"] if ready else config.COLOR_TEXT_DIM

            # ikon jurus (assets/ui/skill_<bentuk>.png) bila ada; redup saat cooldown
            icon = manager.image(f"ui/skill_{shape}", size=config.SKILL_ICON_SIZE)
            text_x = x
            if icon is not None:
                surface.blit(icon if ready else manager.dimmed(icon), (x, y - 3))
                text_x = x + config.SKILL_ICON_SIZE + 6

            label = f"[{shape.upper():<8}] {cfg['name']}"
            text = self.font_small.render(label, True, color)
            surface.blit(text, (text_x, y))
            self.draw_bar(surface, x + 410, y + 2, 80, 10, ratio, (40, 40, 40), color)
            y += 22

    def _draw_gesture_status(self, surface, recording, camera_available, skill_manager,
                             glove_visible=True):
        x, y = 20, 48
        if not camera_available:
            msg = "Kamera tidak terdeteksi - gestur nonaktif (cek README, coba tombol 1-5)"
            color = (255, 120, 120)
        elif recording and not glove_visible:
            msg = "MEREKAM... tapi sarung tangan hitam TIDAK terlihat (dekatkan / cek cahaya)"
            color = (255, 140, 100)
        elif recording:
            msg = "MEREKAM JURUS... gambar pola dengan sarung tangan hitam di depan kamera"
            color = (255, 230, 90)
        else:
            msg = "Tahan [SPASI] lalu gambar pola dengan sarung tangan hitam  |  [ESC] jeda"
            color = config.COLOR_TEXT_DIM
        text = self.font_small.render(msg, True, color)
        surface.blit(text, (x, y))

        if skill_manager.message_timer > 0:
            msg2 = self.font.render(skill_manager.last_message, True, (255, 255, 255))
            surface.blit(msg2, (x, y + 22))
    _LIGHT_STATUS_COLOR = {"good": (110, 220, 130), "warn": (240, 190, 70), "bad": (240, 90, 90)}
    _LIGHT_ZONE_COLORS = [(150, 45, 45), (190, 130, 40), (50, 160, 85), (140, 185, 70), (190, 60, 55)]

    def draw_lighting_bar(self, surface, panel_rect, state, excluded_ratio, calibrating):
        x, w = panel_rect.x, panel_rect.width
        top = panel_rect.y - 98
        bar_y, bar_h = top + 26, 12

        backdrop = pygame.Surface((w, 96), pygame.SRCALPHA)
        backdrop.fill((0, 0, 0, 150))
        surface.blit(backdrop, (x, top - 4))

        # zona warna: gelap | redup | ideal | terang | terlalu terang
        edges = [0, config.LIGHT_LEVEL_TOO_DARK, config.LIGHT_LEVEL_DIM,
                 config.LIGHT_LEVEL_BRIGHT, config.LIGHT_LEVEL_OVEREXPOSED, 255]
        for i, color in enumerate(self._LIGHT_ZONE_COLORS):
            x1 = x + int(edges[i] / 255 * w)
            x2 = x + int(edges[i + 1] / 255 * w)
            pygame.draw.rect(surface, color, (x1, bar_y, max(1, x2 - x1), bar_h))
        pygame.draw.rect(surface, (255, 255, 255), (x, bar_y, w, bar_h), width=1)

        if state is None:
            title = self.font_small.render("Pencahayaan: menunggu kamera...", True, config.COLOR_TEXT_DIM)
            surface.blit(title, (x + 6, top))
            return

        color = self._LIGHT_STATUS_COLOR[state.status]
        title = self.font_small.render(f"Pencahayaan: {state.label}", True, color)
        surface.blit(title, (x + 6, top))
        level_txt = self.font_small.render(f"level {int(state.level)}/255", True, config.COLOR_TEXT_DIM)
        surface.blit(level_txt, (x + w - level_txt.get_width() - 6, top))

        px = x + int(max(0.0, min(255.0, state.level)) / 255 * w)
        pygame.draw.line(surface, (255, 255, 255), (px, bar_y - 3), (px, bar_y + bar_h + 2), 3)
        pygame.draw.polygon(surface, (255, 255, 255), [(px - 5, bar_y - 9), (px + 5, bar_y - 9), (px, bar_y - 3)])

        line_y = bar_y + bar_h + 6
        info = f"Ambang hitam V<{state.black_v_max} (auto) | Diabaikan: {int(excluded_ratio * 100)}%"
        surface.blit(self.font_small.render(info, True, config.COLOR_TEXT), (x + 6, line_y))
        surface.blit(self.font_small.render(state.hint, True, color), (x + 6, line_y + 16))

        if calibrating:
            legend, legend_color = "Kalibrasi berjalan...", (255, 230, 90)
        else:
            legend, legend_color = "[C] kalibrasi  [M] mask  merah=diabaikan", config.COLOR_TEXT_DIM
        surface.blit(self.font_small.render(legend, True, legend_color), (x + 6, line_y + 32))

    def draw_calibration_banner(self, surface, progress, title=None, subtitle=None):
        w, h = 600, 92
        x = surface.get_width() // 2 - w // 2
        y = 110
        box = pygame.Surface((w, h), pygame.SRCALPHA)
        box.fill((0, 0, 0, 200))
        surface.blit(box, (x, y))
        pygame.draw.rect(surface, (255, 230, 90), (x, y, w, h), width=2)

        t1 = self.font.render(title or "KALIBRASI LATAR (rambut & benda hitam diam)", True, (255, 230, 90))
        t2 = self.font_small.render(
            subtitle or "Duduk diam. Jauhkan sarung tangan dari kamera, atau gerakkan terus.",
            True, config.COLOR_TEXT)
        surface.blit(t1, (x + w // 2 - t1.get_width() // 2, y + 10))
        surface.blit(t2, (x + w // 2 - t2.get_width() // 2, y + 38))
        self.draw_bar(surface, x + 20, y + 64, w - 40, 14, progress, (40, 40, 40), (255, 230, 90), border=(255, 255, 255))

    def draw_center_message(self, surface, text, sub_text=None):
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        title = self.font_big.render(text, True, (255, 255, 255))
        surface.blit(title, (surface.get_width() // 2 - title.get_width() // 2,
                              surface.get_height() // 2 - 40))
        if sub_text:
            sub = self.font.render(sub_text, True, config.COLOR_TEXT_DIM)
            surface.blit(sub, (surface.get_width() // 2 - sub.get_width() // 2,
                                surface.get_height() // 2 + 10))
