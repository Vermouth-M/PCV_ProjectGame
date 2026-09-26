"""game/spawner.py -- mengatur kemunculan musuh dari waktu ke waktu."""

import math
import random

import config
from game.enemy import Enemy


class Spawner:
    def __init__(self):
        self.timer = 0.0
        self.elapsed = 0.0

    def _spawn_interval(self):
        t = min(self.elapsed / config.ENEMY_SPAWN_RAMP_TIME, 1.0)
        return config.ENEMY_BASE_SPAWN_INTERVAL + (
            config.ENEMY_MIN_SPAWN_INTERVAL - config.ENEMY_BASE_SPAWN_INTERVAL
        ) * t

    def _available_kinds(self):
        return [k for k, t in config.ENEMY_UNLOCK_TIME.items() if self.elapsed >= t]

    def update(self, dt, player_pos, enemies):
        self.elapsed += dt
        if len(enemies) >= config.ENEMY_MAX_ALIVE:
            return

        self.timer -= dt
        if self.timer <= 0:
            self.timer = self._spawn_interval()
            enemies.append(self._spawn_one(player_pos))

    def _spawn_one(self, player_pos):
        kind = random.choice(self._available_kinds())

        angle = random.uniform(0, math.tau)
        radius = max(config.SCREEN_WIDTH, config.SCREEN_HEIGHT) / 2 + config.ENEMY_SPAWN_MARGIN
        x = player_pos[0] + math.cos(angle) * radius
        y = player_pos[1] + math.sin(angle) * radius

        minutes = self.elapsed / 60.0
        hp_mult = 1.0 + minutes * config.ENEMY_DIFFICULTY_HP_SCALE_PER_MIN
        speed_mult = 1.0 + minutes * config.ENEMY_DIFFICULTY_SPEED_SCALE_PER_MIN

        return Enemy(x, y, kind, hp_mult=hp_mult, speed_mult=speed_mult)
