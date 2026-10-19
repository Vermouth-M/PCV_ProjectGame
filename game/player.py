"""game/player.py -- entitas pemain: gerakan WASD, HP, XP, leveling, perisai, sprite."""

import math
import pygame

import config
from game import assets
from game.animation import Animation


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = config.PLAYER_RADIUS
        self.speed = config.PLAYER_SPEED

        self.max_hp = config.PLAYER_MAX_HP
        self.hp = self.max_hp
        self.invuln_timer = 0.0

        self.level = 1
        self.xp = 0
        self.xp_to_next = config.XP_BASE_REQUIREMENT

        self.facing = (1.0, 0.0)   # arah hadap terakhir (dipakai Jurus Segitiga)
        self.shield_timer = 0.0

        self.attack_cooldown_timer = 0.0
        self.kills = 0

        # tampilan sprite (kosong kalau aset tidak ada -> vektor)
        self.moving = False
        self.face_left = False     # sisi horizontal terakhir, untuk flip sprite
        size = int(self.radius * 2 * config.SPRITE_SCALE["player"])
        manager = assets.get()
        self.anim_idle = Animation(manager.frames("sprites/player/idle", size=size),
                                   config.ANIM_FPS["player_idle"])
        self.anim_walk = Animation(manager.frames("sprites/player/walk", size=size),
                                   config.ANIM_FPS["player_walk"])

    # ------------------------------------------------------------------
    @property
    def pos(self):
        return (self.x, self.y)

    @property
    def is_shielded(self):
        return self.shield_timer > 0

    @property
    def is_invulnerable(self):
        return self.invuln_timer > 0 or self.is_shielded

    # ------------------------------------------------------------------
    def handle_input(self, keys, dt):
        dx = dy = 0.0
        if keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_d]:
            dx += 1
        if keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_s]:
            dy += 1

        self.moving = dx != 0 or dy != 0
        if self.moving:
            length = math.hypot(dx, dy)
            dx, dy = dx / length, dy / length
            self.facing = (dx, dy)
            if dx != 0:
                self.face_left = dx < 0
            self.x += dx * self.speed * dt
            self.y += dy * self.speed * dt

    # ------------------------------------------------------------------
    def update(self, dt):
        if self.invuln_timer > 0:
            self.invuln_timer = max(0.0, self.invuln_timer - dt)
        if self.shield_timer > 0:
            self.shield_timer = max(0.0, self.shield_timer - dt)
        if self.attack_cooldown_timer > 0:
            self.attack_cooldown_timer = max(0.0, self.attack_cooldown_timer - dt)

        if self.moving:
            self.anim_walk.update(dt)
        else:
            self.anim_idle.update(dt)

    # ------------------------------------------------------------------
    def take_damage(self, amount):
        if self.is_invulnerable:
            return False
        self.hp -= amount
        self.invuln_timer = config.PLAYER_INVULN_TIME
        return True

    def activate_shield(self, duration):
        self.shield_timer = duration

    def gain_xp(self, amount):
        self.xp += amount
        leveled_up = False
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.xp_to_next = int(self.xp_to_next * config.XP_GROWTH)
            self.max_hp += 6
            self.hp = self.max_hp
            leveled_up = True
        return leveled_up

    def is_alive(self):
        return self.hp > 0

    # ------------------------------------------------------------------
    def _current_frame(self):
        if self.moving and self.anim_walk:
            return self.anim_walk.frame
        if self.anim_idle:
            return self.anim_idle.frame
        if self.anim_walk:                 # tidak ada idle: pakai frame pertama jalan
            return self.anim_walk.frames[0]
        return None

    def draw(self, surface, cam_x, cam_y):
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)
        blink = self.invuln_timer > 0 and int(self.invuln_timer * 20) % 2 == 0

        frame = self._current_frame()
        if frame is not None:
            manager = assets.get()
            img = manager.flipped(frame) if self.face_left else frame
            if blink:
                img = manager.tinted(img, (160, 30, 30))
            surface.blit(img, img.get_rect(center=(sx, sy)))
        else:
            color = config.COLOR_PLAYER_HIT if blink else config.COLOR_PLAYER
            pygame.draw.circle(surface, color, (sx, sy), self.radius)
            tip = (sx + self.facing[0] * (self.radius + 8), sy + self.facing[1] * (self.radius + 8))
            pygame.draw.line(surface, (255, 255, 255), (sx, sy), tip, 3)

        if self.is_shielded:
            self._draw_shield(surface, sx, sy)

    def _draw_shield(self, surface, sx, sy):
        pulse = 4 * math.sin(pygame.time.get_ticks() / 120.0)
        half = self.radius + 14 + pulse
        sprite = assets.get().image("effects/shield", size=int(half * 2))
        if sprite is not None:
            surface.blit(sprite, sprite.get_rect(center=(sx, sy)))
        else:
            rect = pygame.Rect(0, 0, half * 2, half * 2)
            rect.center = (sx, sy)
            pygame.draw.rect(surface, config.COLOR_SHIELD, rect, width=3, border_radius=6)
