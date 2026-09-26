"""game/player.py -- entitas pemain: gerakan WASD, HP, XP, leveling, perisai."""

import math
import pygame

import config


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

        if dx != 0 or dy != 0:
            length = math.hypot(dx, dy)
            dx, dy = dx / length, dy / length
            self.facing = (dx, dy)
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
    def draw(self, surface, cam_x, cam_y):
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)

        color = config.COLOR_PLAYER
        if self.invuln_timer > 0 and int(self.invuln_timer * 20) % 2 == 0:
            color = config.COLOR_PLAYER_HIT

        pygame.draw.circle(surface, color, (sx, sy), self.radius)

        # indikator arah hadap
        tip = (sx + self.facing[0] * (self.radius + 8), sy + self.facing[1] * (self.radius + 8))
        pygame.draw.line(surface, (255, 255, 255), (sx, sy), tip, 3)

        if self.is_shielded:
            pulse = 4 * math.sin(pygame.time.get_ticks() / 120.0)
            half = self.radius + 14 + pulse
            rect = pygame.Rect(0, 0, half * 2, half * 2)
            rect.center = (sx, sy)
            pygame.draw.rect(surface, config.COLOR_SHIELD, rect, width=3, border_radius=6)
