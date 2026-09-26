"""game/pickups.py -- orb XP yang jatuh dari musuh yang mati."""

import math
import pygame

import config


class XPOrb:
    def __init__(self, x, y, value):
        self.x = x
        self.y = y
        self.value = value
        self.radius = 5

    @property
    def pos(self):
        return (self.x, self.y)

    def update(self, dt, player_pos):
        dx = player_pos[0] - self.x
        dy = player_pos[1] - self.y
        dist = math.hypot(dx, dy)
        if dist < config.PLAYER_PICKUP_RADIUS and dist > 1e-3:
            pull = 1.0 - (dist / config.PLAYER_PICKUP_RADIUS)
            speed = 260 * pull + 60
            dx, dy = dx / dist, dy / dist
            self.x += dx * speed * dt
            self.y += dy * speed * dt

    def draw(self, surface, cam_x, cam_y):
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)
        pygame.draw.circle(surface, config.COLOR_XP_BAR_FG, (sx, sy), self.radius)
        pygame.draw.circle(surface, (255, 255, 255), (sx, sy), self.radius, 1)
