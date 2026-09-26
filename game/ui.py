"""game/ui.py -- HUD: health bar, XP bar, status jurus & instruksi kontrol."""

import pygame

import config


class UI:
    def __init__(self):
        pygame.font.init()
        self.font = pygame.font.SysFont("consolas", 18)
        self.font_big = pygame.font.SysFont("consolas", 34, bold=True)
        self.font_small = pygame.font.SysFont("consolas", 14)

    def draw_bar(self, surface, x, y, w, h, ratio, bg_color, fg_color, border=(0, 0, 0)):
        pygame.draw.rect(surface, bg_color, (x, y, w, h))
        pygame.draw.rect(surface, fg_color, (x, y, int(w * max(0, min(1, ratio))), h))
        pygame.draw.rect(surface, border, (x, y, w, h), width=2)

    def draw_hud(self, surface, player, elapsed, skill_manager, recording, camera_available):
        # HP
        self.draw_bar(surface, 20, 20, 260, 22, player.hp / player.max_hp,
                      config.COLOR_HP_BAR_BG, config.COLOR_HP_BAR_FG)
        hp_text = self.font_small.render(f"HP {int(max(0, player.hp))}/{player.max_hp}", True, config.COLOR_TEXT)
        surface.blit(hp_text, (28, 24))

        # XP
        self.draw_bar(surface, 20, 48, 260, 14, player.xp / player.xp_to_next,
                      config.COLOR_XP_BAR_BG, config.COLOR_XP_BAR_FG)
        lvl_text = self.font_small.render(f"Level {player.level}", True, config.COLOR_TEXT)
        surface.blit(lvl_text, (290, 46))

        # Waktu bertahan & kill count
        mins, secs = divmod(int(elapsed), 60)
        timer_text = self.font_big.render(f"{mins:02d}:{secs:02d}", True, config.COLOR_TEXT)
        surface.blit(timer_text, (surface.get_width() // 2 - timer_text.get_width() // 2, 16))

        kills_text = self.font.render(f"Kills: {player.kills}", True, config.COLOR_TEXT_DIM)
        surface.blit(kills_text, (surface.get_width() // 2 - kills_text.get_width() // 2, 54))

        self._draw_skill_list(surface, skill_manager)
        self._draw_gesture_status(surface, recording, camera_available, skill_manager)

    def _draw_skill_list(self, surface, skill_manager):
        x, y = 20, surface.get_height() - 150
        for shape, cfg in config.SKILL_DEFS.items():
            ratio = skill_manager.cooldown_ratio(shape)
            ready = skill_manager.is_ready(shape)
            color = cfg["color"] if ready else config.COLOR_TEXT_DIM
            label = f"[{shape.upper():<8}] {cfg['name']}"
            text = self.font_small.render(label, True, color)
            surface.blit(text, (x, y))
            self.draw_bar(surface, x + 320, y + 2, 80, 10, ratio, (40, 40, 40), color)
            y += 22

    def _draw_gesture_status(self, surface, recording, camera_available, skill_manager):
        x, y = 20, 80
        if not camera_available:
            msg = "Kamera tidak terdeteksi - gestur nonaktif (cek README, coba tombol 1-5)"
            color = (255, 120, 120)
        elif recording:
            msg = "MEREKAM JURUS... gambar pola dengan tanganmu di depan kamera"
            color = (255, 230, 90)
        else:
            msg = "Tahan [SPASI] lalu gambar pola (segitiga/lingkaran/kotak/garis/zigzag)"
            color = config.COLOR_TEXT_DIM
        text = self.font_small.render(msg, True, color)
        surface.blit(text, (x, y))

        if skill_manager.message_timer > 0:
            msg2 = self.font.render(skill_manager.last_message, True, (255, 255, 255))
            surface.blit(msg2, (x, y + 22))

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
