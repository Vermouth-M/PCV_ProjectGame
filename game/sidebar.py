"""game/sidebar.py -- kolom info kanan: health EKG, potret, skill, bingkai webcam."""

import random

import pygame

import config
from game import assets, layout
from game.ecg import EcgMonitor
from game.screens.widgets import draw_shape_icon

METAL_LIGHT = (128, 126, 134)
METAL_MID = (80, 78, 86)
METAL_DARK = (36, 34, 40)
BLOOD = (120, 22, 30)
TEXT = (240, 235, 235)
TEXT_DIM = (150, 140, 145)


def draw_frame(surface, rect, fill=(16, 9, 12)):
    """Bingkai logam. Return rect bagian dalam (tempat isi digambar)."""
    f = config.UI_FRAME
    pygame.draw.rect(surface, fill, rect)
    pygame.draw.rect(surface, METAL_MID, rect, width=f)
    pygame.draw.line(surface, METAL_LIGHT, rect.topleft, (rect.right - 1, rect.top), 2)
    pygame.draw.line(surface, METAL_LIGHT, rect.topleft, (rect.left, rect.bottom - 1), 2)
    pygame.draw.line(surface, METAL_DARK, (rect.left, rect.bottom - 1), (rect.right - 1, rect.bottom - 1), 2)
    pygame.draw.line(surface, METAL_DARK, (rect.right - 1, rect.top), (rect.right - 1, rect.bottom - 1), 2)
    inner = rect.inflate(-2 * f, -2 * f)
    pygame.draw.rect(surface, METAL_DARK, inner.inflate(2, 2), width=2)
    for cx, cy in ((rect.left + 4, rect.top + 4), (rect.right - 5, rect.top + 4),
                   (rect.left + 4, rect.bottom - 5), (rect.right - 5, rect.bottom - 5)):
        pygame.draw.circle(surface, METAL_LIGHT, (cx, cy), 2)    # paku keling
    return inner


class Sidebar:
    def __init__(self):
        pygame.font.init()
        self.ecg = EcgMonitor()
        self.font_hp = pygame.font.SysFont("consolas", 28, bold=True)
        self.font_status = pygame.font.SysFont("consolas", 16, bold=True)
        self.font_name = pygame.font.SysFont("consolas", 18, bold=True)
        self.font_small = pygame.font.SysFont("consolas", 12, bold=True)
        self.font_live = pygame.font.SysFont("consolas", 20, bold=True)
        self._bg = self._make_background()
        self._cover_cache = {}

    def update(self, dt, player):
        self.ecg.update(dt, player.hp / player.max_hp)

    def draw(self, surface, player, skill_manager):
        surface.blit(self._bg, layout.SIDEBAR_RECT.topleft)
        self._draw_health(surface, player)
        self._draw_portrait(surface)
        self._draw_skills(surface, skill_manager)
        draw_frame(surface, layout.WEBCAM, fill=(8, 6, 8))   # video kamera digambar engine

    # ------------------------------------------------------------------
    def _make_background(self):
        r = layout.SIDEBAR_RECT
        surf = pygame.Surface(r.size)
        top, bottom = (58, 10, 16), (22, 6, 10)
        for y in range(r.height):
            t = y / max(1, r.height - 1)
            color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
            pygame.draw.line(surf, color, (0, y), (r.width, y))
        rng = random.Random(7)
        blots = pygame.Surface(r.size, pygame.SRCALPHA)
        for _ in range(40):
            pygame.draw.circle(blots, (0, 0, 0, rng.randint(18, 40)),
                               (rng.randrange(r.width), rng.randrange(r.height)), rng.randint(20, 70))
        surf.blit(blots, (0, 0))
        pygame.draw.line(surf, (10, 4, 6), (0, 0), (0, r.height), 3)
        pygame.draw.line(surf, (140, 30, 36), (3, 0), (3, r.height), 1)
        return surf

    # ------------------------------------------------------------------
    def _draw_health(self, surface, player):
        inner = draw_frame(surface, layout.HEALTH, fill=(26, 5, 9))
        old_clip = surface.get_clip()
        surface.set_clip(inner)

        grid = (78, 14, 20)
        for x in range(inner.left, inner.right, 14):
            pygame.draw.line(surface, grid, (x, inner.top), (x, inner.bottom))
        for y in range(inner.top, inner.bottom, 14):
            pygame.draw.line(surface, grid, (inner.left, y), (inner.right, y))

        self.ecg.draw(surface, inner, player.hp / player.max_hp)

        blink_off = self.ecg.label == "DANGER" and (pygame.time.get_ticks() // 350) % 2 == 1
        if not blink_off:
            label = self.font_status.render(self.ecg.label, True, self.ecg.color)
            surface.blit(label, (inner.left + 8, inner.top + 6))

        hp_label = self.font_hp.render("HP ", True, (200, 40, 40))
        hp_value = self.font_hp.render(f"{int(max(0, player.hp))}/{player.max_hp}", True, TEXT)
        total = hp_label.get_width() + hp_value.get_width()
        x = inner.right - 8 - total
        y = inner.bottom - 6 - hp_value.get_height()
        surface.blit(hp_label, (x, y))
        surface.blit(hp_value, (x + hp_label.get_width(), y))

        surface.set_clip(old_clip)

    # ------------------------------------------------------------------
    def _cover(self, img, size):
        """Skala gambar sampai memenuhi `size`, lalu potong tengahnya."""
        key = (id(img), size)
        cached = self._cover_cache.get(key)
        if cached is None:
            w, h = img.get_size()
            f = max(size[0] / w, size[1] / h)
            scaled = pygame.transform.smoothscale(img, (max(1, round(w * f)), max(1, round(h * f))))
            out = pygame.Surface(size, pygame.SRCALPHA)
            out.blit(scaled, ((size[0] - scaled.get_width()) // 2, (size[1] - scaled.get_height()) // 2))
            cached = (img, out)
            self._cover_cache[key] = cached
        return cached[1]

    def _draw_portrait(self, surface):
        inner = draw_frame(surface, layout.PORTRAIT, fill=(14, 8, 12))
        old_clip = surface.get_clip()
        surface.set_clip(inner)

        img = assets.get().image("ui/portrait")
        if img is not None:
            surface.blit(self._cover(img, inner.size), inner.topleft)
        else:
            self._draw_placeholder_portrait(surface, inner)

        band = pygame.Rect(inner.left, inner.bottom - 30, inner.width, 30)
        shade = pygame.Surface(band.size, pygame.SRCALPHA)
        shade.fill((0, 0, 0, 170))
        surface.blit(shade, band.topleft)
        pygame.draw.line(surface, BLOOD, band.topleft, band.topright, 1)
        name = self.font_name.render(config.PLAYER_NAME, True, TEXT)
        surface.blit(name, name.get_rect(center=band.center))

        surface.set_clip(old_clip)

    def _draw_placeholder_portrait(self, surface, inner):
        pygame.draw.rect(surface, (30, 14, 20), inner)
        cx = inner.centerx
        pygame.draw.polygon(surface, (110, 16, 24), [
            (cx - 62, inner.bottom), (cx - 36, inner.top + 70),
            (cx + 36, inner.top + 70), (cx + 62, inner.bottom)])
        pygame.draw.ellipse(surface, (205, 195, 195), (cx - 22, inner.top + 22, 44, 56))
        pygame.draw.polygon(surface, (15, 10, 12), [
            (cx - 24, inner.top + 44), (cx - 20, inner.top + 18),
            (cx, inner.top + 30), (cx + 20, inner.top + 18), (cx + 24, inner.top + 44)])
        for dx in (-8, 8):
            pygame.draw.circle(surface, (230, 40, 40), (cx + dx, inner.top + 50), 3)

    # ------------------------------------------------------------------
    def _draw_skills(self, surface, skill_manager):
        inner = draw_frame(surface, layout.SKILLS, fill=(18, 10, 13))
        rect = layout.SKILLS

        cx = rect.centerx      # hiasan kecil di tengah atas bingkai
        pygame.draw.polygon(surface, METAL_MID, [(cx - 16, rect.top), (cx + 16, rect.top),
                                                  (cx + 9, rect.top + 9), (cx - 9, rect.top + 9)])
        pygame.draw.polygon(surface, BLOOD, [(cx, rect.top + 1), (cx + 5, rect.top + 4),
                                              (cx, rect.top + 8), (cx - 5, rect.top + 4)])

        shapes = list(config.SKILL_DEFS)
        n = len(shapes)
        gap = 6 if n >= 5 else 8
        slot = min(config.SKILL_SLOT_MAX, (inner.width - 16 - gap * (n - 1)) // n)
        icon_size = slot - 8
        total_w = slot * n + gap * (n - 1)
        x = inner.centerx - total_w // 2
        content_h = slot + 32
        y = inner.top + max(8, (inner.height - content_h) // 2 + 4)
        manager = assets.get()

        for i, shape in enumerate(shapes):
            cfg = config.SKILL_DEFS[shape]
            ready = skill_manager.is_ready(shape)
            ratio = skill_manager.cooldown_ratio(shape)    # 1.0 = siap, 0.0 = baru dipakai
            color = cfg["color"] if ready else TEXT_DIM
            slot_rect = pygame.Rect(x, y, slot, slot)

            pygame.draw.rect(surface, (10, 6, 8), slot_rect)
            icon = manager.image(f"ui/skill_{shape}", size=icon_size)
            if icon is not None:
                pos = icon.get_rect(center=slot_rect.center)
                surface.blit(icon if ready else manager.dimmed(icon), pos)
            else:
                draw_shape_icon(surface, shape, slot_rect.center, slot * 0.55, color, 3)

            if not ready:      # tirai gelap + hitung mundur cooldown
                h = int(slot * (1.0 - ratio))
                if h > 0:
                    veil = pygame.Surface((slot, h), pygame.SRCALPHA)
                    veil.fill((0, 0, 0, 160))
                    surface.blit(veil, slot_rect.topleft)
                secs = self.font_status.render(f"{skill_manager.cooldowns[shape]:.1f}", True, TEXT)
                surface.blit(secs, secs.get_rect(center=slot_rect.center))

            pygame.draw.rect(surface, color if ready else METAL_DARK, slot_rect, width=2)

            badge = pygame.Rect(slot_rect.right - 20, slot_rect.top + 2, 18, 15)   # nomor tombol
            pygame.draw.rect(surface, (20, 20, 24), badge)
            num = self.font_small.render(str(i + 1), True, TEXT)
            surface.blit(num, num.get_rect(center=badge.center))

            name = self.font_small.render(config.SKILL_SHORT_NAMES.get(shape, shape.upper()), True, color)
            surface.blit(name, name.get_rect(midtop=(slot_rect.centerx, slot_rect.bottom + 6)))

            bar = pygame.Rect(slot_rect.left, slot_rect.bottom + 24, slot, 6)
            pygame.draw.rect(surface, (40, 20, 24), bar)
            pygame.draw.rect(surface, color,
                             (bar.x, bar.y, int(bar.width * max(0.0, min(1.0, ratio))), bar.height))

            x += slot + gap

    # ------------------------------------------------------------------
    def draw_live_badge(self, surface, camera_available):
        """Titik merah + 'LIVE' di pojok kiri-atas video webcam."""
        v = layout.WEBCAM_VIDEO
        if camera_available:
            if (pygame.time.get_ticks() // 600) % 2 == 0:
                pygame.draw.circle(surface, (230, 30, 30), (v.left + 18, v.top + 20), 6)
            surface.blit(self.font_live.render("LIVE", True, TEXT), (v.left + 30, v.top + 10))
        else:
            surface.blit(self.font_live.render("NO CAM", True, TEXT_DIM), (v.left + 12, v.top + 10))