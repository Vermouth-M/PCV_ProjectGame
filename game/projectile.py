"""game/projectile.py -- proyektil serangan dasar otomatis milik pemain."""

import math
import pygame


class Projectile:
    def __init__(self, x, y, target_pos, damage, speed=420, radius=5, pierce=0, color=(255, 255, 255)):
        self.x, self.y = x, y
        dx, dy = target_pos[0] - x, target_pos[1] - y
        dist = math.hypot(dx, dy) or 1.0
        self.vx, self.vy = dx / dist * speed, dy / dist * speed
        self.damage = damage
        self.radius = radius
        self.pierce = pierce
        self.color = color
        self.lifetime = 2.0
        self.hit_enemies = set()

    @property
    def pos(self):
        return (self.x, self.y)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt

    def is_dead(self):
        return self.lifetime <= 0

    def draw(self, surface, cam_x, cam_y):
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)
        pygame.draw.circle(surface, self.color, (sx, sy), self.radius)
