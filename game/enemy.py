"""game/enemy.py -- musuh yang bergerak lurus menuju posisi pemain."""

import math
import random

import pygame

import config
from game import assets
from game.animation import Animation


class Enemy:
    def __init__(self, x, y, kind, hp_mult=1.0, speed_mult=1.0):
        self.x = x
        self.y = y
        self.kind = kind

        stats = config.ENEMY_STATS[kind]
        self.radius = stats["radius"]
        self.max_hp = stats["hp"] * hp_mult
        self.hp = self.max_hp
        self.speed = stats["speed"] * speed_mult
        self.damage = stats["damage"]
        self.xp_value = stats["xp"]
        self.score_value = stats["score"]
        self.color = config.ENEMY_COLORS[kind]

        self.knockback_x = 0.0
        self.knockback_y = 0.0
        self.hit_flash_timer = 0.0

        # tampilan sprite (kosong kalau aset tidak ada -> vektor)
        self.face_left = False
        size = int(self.radius * 2 * config.SPRITE_SCALE["enemy"])
        frames = assets.get().frames(f"sprites/enemies/{kind}_walk",
                                     f"sprites/enemies/{kind}", size=size)
        self.anim = Animation(frames, config.ANIM_FPS["enemy"], offset=random.random() * 2.0)

    @property
    def pos(self):
        return (self.x, self.y)

    def update(self, dt, player_pos):
        if abs(self.knockback_x) > 0.5 or abs(self.knockback_y) > 0.5:
            self.x += self.knockback_x * dt
            self.y += self.knockback_y * dt
            self.knockback_x *= 0.86
            self.knockback_y *= 0.86
        else:
            dx = player_pos[0] - self.x
            dy = player_pos[1] - self.y
            dist = math.hypot(dx, dy)
            if dist > 1e-3:
                dx, dy = dx / dist, dy / dist
                self.x += dx * self.speed * dt
                self.y += dy * self.speed * dt

        if self.hit_flash_timer > 0:
            self.hit_flash_timer = max(0.0, self.hit_flash_timer - dt)

        self.anim.update(dt)
        face_dx = player_pos[0] - self.x
        if abs(face_dx) > 2:
            self.face_left = face_dx < 0

    def take_damage(self, amount, knockback=None):
        self.hp -= amount
        self.hit_flash_timer = 0.12
        if knockback:
            self.knockback_x += knockback[0]
            self.knockback_y += knockback[1]
        return self.hp <= 0

    def draw(self, surface, cam_x, cam_y):
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)

        frame = self.anim.frame
        if frame is not None:
            manager = assets.get()
            img = manager.flipped(frame) if self.face_left else frame
            if self.hit_flash_timer > 0:
                img = manager.tinted(img, (255, 255, 255))
            surface.blit(img, img.get_rect(center=(sx, sy)))
            half_h = img.get_height() // 2
        else:
            color = (255, 255, 255) if self.hit_flash_timer > 0 else self.color
            pygame.draw.circle(surface, color, (sx, sy), self.radius)
            half_h = self.radius

        if self.hp < self.max_hp:
            w = self.radius * 2
            ratio = max(0.0, self.hp / self.max_hp)
            top = sy - half_h - 8
            pygame.draw.rect(surface, (40, 10, 10), pygame.Rect(sx - w // 2, top, w, 4))
            pygame.draw.rect(surface, (220, 60, 60), pygame.Rect(sx - w // 2, top, int(w * ratio), 4))
