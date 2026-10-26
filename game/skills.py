import math
import pygame
import config
from game import assets, audio
from game.assets import AssetManager
from game.utils import distance

def _effect_alpha(progress, animated):
    """Efek 1 gambar: memudar terus. Efek beranimasi: penuh, baru memudar di 25% terakhir."""
    if not animated:
        return max(0.0, 1.0 - progress)
    return 1.0 if progress < 0.75 else max(0.0, (1.0 - progress) / 0.25)

class SkillEffect:
    """Efek visual sesaat -- damage sudah diterapkan saat efek dibuat."""

    def __init__(self, kind, duration, color):
        self.kind = kind
        self.age = 0.0
        self.duration = duration
        self.color = color
        self._sprites = []          # surface hasil regang+putar (milik efek ini sendiri)
        self._center = (0.0, 0.0)    # pusat sprite di koordinat dunia

    def update(self, dt):
        self.age += dt

    def is_dead(self):
        return self.age >= self.duration

    def progress(self):
        return min(1.0, self.age / self.duration) if self.duration > 0 else 1.0

    # --- bantuan sprite arah ("pangkal di kiri-tengah, ujung ke kanan") ---
    def _use_directional(self, prefix, origin, length, thickness, angle_rad):
        result = assets.get().directional_frames((prefix,), length, thickness, angle_rad)
        if result is None:
            return False
        self._sprites, offset = result
        self._center = (origin[0] + offset[0], origin[1] + offset[1])
        return True

    def _draw_sprite(self, surface, cam_x, cam_y):
        if not self._sprites:
            return

        n = len(self._sprites)
        # Batasi indeks agar selalu berada dalam rentang frame yang tersedia.
        frame_index = min(n - 1, int(self.progress() * n))
        sprite = self._sprites[frame_index]
        sprite.set_alpha(int(255 * _effect_alpha(self.progress(), n > 1)))

        # Posisikan sprite berdasarkan koordinat dunia dan offset kamera.
        rect = sprite.get_rect(
            center=(int(self._center[0] - cam_x), int(self._center[1] - cam_y))
        )

        # BUG FIX: sebelumnya sprite tidak pernah di-blit ke layar.
        surface.blit(sprite, rect)


class TriangleSlash(SkillEffect):
    def __init__(self, player_pos, facing, radius, angle_deg, color):
        super().__init__("triangle", 0.5, color)
        self.origin = player_pos
        self.facing = facing
        self.radius = radius
        self.half_angle = math.radians(angle_deg / 2)

        chord = 2 * radius * math.sin(self.half_angle)   # lebar sisi luar segitiga
        self._use_directional("effects/triangle_slash", player_pos, radius, chord,
                              math.atan2(facing[1], facing[0]))

    def hits(self, enemy_pos):
        dx, dy = enemy_pos[0] - self.origin[0], enemy_pos[1] - self.origin[1]
        dist = math.hypot(dx, dy)
        if dist > self.radius or dist < 1e-3:
            return False
        angle_to = math.atan2(dy, dx)
        facing_angle = math.atan2(self.facing[1], self.facing[0])
        diff = abs((angle_to - facing_angle + math.pi) % (2 * math.pi) - math.pi)
        return diff <= self.half_angle

    def draw(self, surface, cam_x, cam_y):
        if self._sprites:
            self._draw_sprite(surface, cam_x, cam_y)
            return
        ox, oy = self.origin[0] - cam_x, self.origin[1] - cam_y
        facing_angle = math.atan2(self.facing[1], self.facing[0])
        fade = max(0, 1 - self.progress())
        p1 = (ox, oy)
        p2 = (ox + math.cos(facing_angle - self.half_angle) * self.radius,
              oy + math.sin(facing_angle - self.half_angle) * self.radius)
        p3 = (ox + math.cos(facing_angle + self.half_angle) * self.radius,
              oy + math.sin(facing_angle + self.half_angle) * self.radius)
        surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(surf, (*self.color, int(160 * fade)), [p1, p2, p3])
        surface.blit(surf, (0, 0))


class CircleShockwave(SkillEffect):
    def __init__(self, player_pos, radius, knockback, color):
        super().__init__("circle", 0.5, color)
        self.origin = player_pos
        self.radius = radius
        self.knockback = knockback
        self._frames = assets.get().frames("effects/circle_shockwave")

    def hits(self, enemy_pos):
        return distance(self.origin, enemy_pos) <= self.radius

    def draw(self, surface, cam_x, cam_y):
        ox, oy = int(self.origin[0] - cam_x), int(self.origin[1] - cam_y)
        if self._frames:
            n = len(self._frames)
            base = self._frames[min(n - 1, int(self.progress() * n))]
            if n > 1:       # animasi: ukuran tetap, frame yang berganti
                size = max(2, int(self.radius * 2))
                alpha = int(255 * _effect_alpha(self.progress(), True))
            else:           # 1 gambar: membesar & memudar (perilaku lama)
                size = max(2, int(self.radius * 2 * self.progress()))
                alpha = max(0, 220 - int(220 * self.progress()))
            img = AssetManager.resize(base, size=(size, size))
            if img is base:
                img = img.copy()          # jangan ubah alpha surface milik cache bersama
            img.set_alpha(alpha)
            surface.blit(img, img.get_rect(center=(ox, oy)))
            return


class LineSlash(SkillEffect):
    def __init__(self, player_pos, direction, length, width, color):
        super().__init__("line", 0.4, color)
        self.origin = player_pos
        self.direction = direction
        self.length = length
        self.width = width
        self._use_directional("effects/line_slash", player_pos, length, width,
                              math.atan2(direction[1], direction[0]))

    def hits(self, enemy_pos):
        ox, oy = self.origin
        dx, dy = self.direction
        ex, ey = enemy_pos[0] - ox, enemy_pos[1] - oy
        along = ex * dx + ey * dy
        if along < 0 or along > self.length:
            return False
        perp = abs(ex * -dy + ey * dx)
        return perp <= self.width / 2

    def draw(self, surface, cam_x, cam_y):
        if self._sprites:
            self._draw_sprite(surface, cam_x, cam_y)
            return
        ox, oy = self.origin[0] - cam_x, self.origin[1] - cam_y
        dx, dy = self.direction
        end = (ox + dx * self.length, oy + dy * self.length)
        fade = max(0, 1 - self.progress())
        surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pygame.draw.line(surf, (*self.color, int(220 * fade)), (ox, oy), end, max(1, int(self.width)))
        surface.blit(surf, (0, 0))


class ZigzagChain(SkillEffect):
    def __init__(self, segments, color):
        super().__init__("zigzag", 0.3, color)
        self.segments = segments   # list of (pos_a, pos_b)

        # satu sprite petir per sambungan, diregangkan sepanjang sambungannya
        self._parts = []
        manager = assets.get()
        for pa, pb in segments:
            dx, dy = pb[0] - pa[0], pb[1] - pa[1]
            length = math.hypot(dx, dy)
            if length < 1:
                continue
            result = manager.directional(("effects/lightning",), length,
                                         config.LIGHTNING_THICKNESS, math.atan2(dy, dx))
            if result is None:
                self._parts = []
                break
            sprite, offset = result
            self._parts.append((sprite, (pa[0] + offset[0], pa[1] + offset[1])))

    def draw(self, surface, cam_x, cam_y):
        fade = max(0.0, 1 - self.progress())
        if self._parts:
            for sprite, (cx, cy) in self._parts:
                sprite.set_alpha(int(255 * fade))
                surface.blit(sprite, sprite.get_rect(center=(cx - cam_x, cy - cam_y)))
            return
        surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for a, b in self.segments:
            pa = (a[0] - cam_x, a[1] - cam_y)
            pb = (b[0] - cam_x, b[1] - cam_y)
            pygame.draw.line(surf, (*self.color, int(255 * fade)), pa, pb, 3)
        surface.blit(surf, (0, 0))


class SkillManager:
    def __init__(self):
        self.cooldowns = {name: 0.0 for name in config.SKILL_DEFS}
        self.effects = []
        self.last_message = ""
        self.message_timer = 0.0

    def update(self, dt):
        for name in self.cooldowns:
            if self.cooldowns[name] > 0:
                self.cooldowns[name] = max(0.0, self.cooldowns[name] - dt)
        for effect in self.effects:
            effect.update(dt)
        self.effects = [e for e in self.effects if not e.is_dead()]
        if self.message_timer > 0:
            self.message_timer = max(0.0, self.message_timer - dt)

    def is_ready(self, shape):
        return shape in config.SKILL_DEFS and self.cooldowns[shape] <= 0

    def cooldown_ratio(self, shape):
        d = config.SKILL_DEFS[shape]["cooldown"]
        return 1.0 - (self.cooldowns[shape] / d if d > 0 else 0)

    def set_message(self, text, duration=1.6):
        self.last_message = text
        self.message_timer = duration

    # ------------------------------------------------------------------
    def trigger(self, shape, player, enemies, gesture_direction):
        if shape not in config.SKILL_DEFS:
            self.set_message("Pola tidak dikenali, coba lagi!")
            return

        if not self.is_ready(shape):
            self.set_message(f"{config.SKILL_DEFS[shape]['name']} masih cooldown!")
            return

        cfg = config.SKILL_DEFS[shape]
        self.cooldowns[shape] = cfg["cooldown"]
        self.set_message(f"{cfg['name']}!")
        audio.get().play_sfx(f"skill_{shape}")

        if shape == "triangle":
            self._do_triangle(cfg, player, enemies)
        elif shape == "circle":
            self._do_circle(cfg, player, enemies)
        elif shape == "line":
            self._do_line(cfg, player, enemies, gesture_direction)
        elif shape == "zigzag":
            self._do_zigzag(cfg, player, enemies)

    # ------------------------------------------------------------------
    def _do_triangle(self, cfg, player, enemies):
        effect = TriangleSlash(player.pos, player.facing, cfg["radius"], cfg["angle_deg"], cfg["color"])
        for e in enemies:
            if effect.hits(e.pos):
                e.take_damage(cfg["damage"])
        self.effects.append(effect)

    def _do_circle(self, cfg, player, enemies):
        effect = CircleShockwave(player.pos, cfg["radius"], cfg["knockback"], cfg["color"])
        for e in enemies:
            if effect.hits(e.pos):
                dx, dy = e.x - player.x, e.y - player.y
                dist = math.hypot(dx, dy) or 1.0
                kb = (dx / dist * cfg["knockback"], dy / dist * cfg["knockback"])
                e.take_damage(cfg["damage"], knockback=kb)
        self.effects.append(effect)
        
    def _do_line(self, cfg, player, enemies, gesture_direction):
        gx, gy = gesture_direction
        if gx == 0 and gy == 0:
            gx, gy = player.facing
        length = math.hypot(gx, gy) or 1.0
        direction = (gx / length, gy / length)

        effect = LineSlash(player.pos, direction, cfg["length"], cfg["width"], cfg["color"])
        for e in enemies:
            if effect.hits(e.pos):
                e.take_damage(cfg["damage"])
        self.effects.append(effect)

    def _do_zigzag(self, cfg, player, enemies):
        remaining = list(enemies)
        current_pos = player.pos
        segments = []
        chained = 0
        while remaining and chained < cfg["max_chain"]:
            remaining.sort(key=lambda e: distance(current_pos, e.pos))
            nearest = remaining[0]
            if distance(current_pos, nearest.pos) > cfg["chain_radius"]:
                break
            nearest.take_damage(cfg["damage"])
            segments.append((current_pos, nearest.pos))
            current_pos = nearest.pos
            remaining.remove(nearest)
            chained += 1

        self.effects.append(ZigzagChain(segments, cfg["color"]))
