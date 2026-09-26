"""
game/engine.py
================
Kelas Game utama: inisialisasi pygame, loop utama, update semua entitas,
serta jembatan antara input gestur (dari gesture/) dengan sistem jurus
(dari game/skills.py).
"""

import pygame

import config
from game.player import Player
from game.spawner import Spawner
from game.pickups import XPOrb
from game.projectile import Projectile
from game.skills import SkillManager
from game.ui import UI
from game.utils import circle_collide, distance
from game import camera_overlay

from gesture.gesture_thread import GestureThread
from gesture import shape_classifier


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        pygame.display.set_caption(config.GAME_TITLE)
        self.clock = pygame.time.Clock()

        self.player = Player(0, 0)
        self.spawner = Spawner()
        self.skills = SkillManager()
        self.ui = UI()

        self.enemies = []
        self.orbs = []
        self.projectiles = []

        self.elapsed = 0.0
        self.state = "playing"   # playing | gameover

        self.gesture_thread = GestureThread()
        self.camera_available = self.gesture_thread.start()

        self.space_held = False
        self._debug_shape_keys = {
            pygame.K_1: "triangle",
            pygame.K_2: "circle",
            pygame.K_3: "square",
            pygame.K_4: "line",
            pygame.K_5: "zigzag",
        }

    # ------------------------------------------------------------------
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(config.FPS) / 1000.0
            running = self._handle_events()

            if self.state == "playing":
                self._update(dt)

            self._draw()
            pygame.display.flip()

        self.gesture_thread.stop()
        pygame.quit()

    # ------------------------------------------------------------------
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False

                if event.key == pygame.K_SPACE and self.state == "playing":
                    self.space_held = True
                    self.gesture_thread.begin_recording()

                if event.key == pygame.K_r and self.state == "gameover":
                    self._restart()

                if config.DEBUG_KEYBOARD_GESTURE_FALLBACK and event.key in self._debug_shape_keys:
                    shape = self._debug_shape_keys[event.key]
                    self.skills.trigger(shape, self.player, self.enemies, self.player.facing)

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE and self.space_held:
                    self.space_held = False
                    self._finish_gesture()

        return True

    def _finish_gesture(self):
        points = self.gesture_thread.end_recording()
        shape = shape_classifier.classify(points)
        direction = shape_classifier.dominant_direction(points)
        self.skills.trigger(shape, self.player, self.enemies, direction)

    # ------------------------------------------------------------------
    def _update(self, dt):
        self.elapsed += dt

        # auto-stop kalau merekam gestur kelamaan
        if self.gesture_thread.recording_expired():
            self.space_held = False
            self._finish_gesture()

        # mode fokus: musuh melambat selagi pemain sedang menggambar jurus
        time_scale = config.GESTURE_TIME_SCALE_WHILE_DRAWING if self.gesture_thread.is_recording() else 1.0
        world_dt = dt * time_scale

        keys = pygame.key.get_pressed()
        self.player.handle_input(keys, dt)   # gerak pemain tetap normal walau sedang menggambar
        self.player.update(dt)

        self.spawner.update(world_dt, self.player.pos, self.enemies)

        for enemy in self.enemies:
            enemy.update(world_dt, self.player.pos)

        self._auto_attack(dt)

        for p in self.projectiles:
            p.update(dt)
        self.projectiles = [p for p in self.projectiles if not p.is_dead()]

        self.skills.update(dt)

        for orb in self.orbs:
            orb.update(dt, self.player.pos)

        self._handle_collisions()
        self._cleanup_dead_enemies()

        if not self.player.is_alive():
            self.state = "gameover"

    # ------------------------------------------------------------------
    def _auto_attack(self, dt):
        if self.player.attack_cooldown_timer > 0 or not self.enemies:
            return
        nearest = min(self.enemies, key=lambda e: distance(self.player.pos, e.pos))
        if distance(self.player.pos, nearest.pos) <= config.PLAYER_BASE_ATTACK_RANGE:
            self.projectiles.append(Projectile(
                self.player.x, self.player.y, nearest.pos,
                damage=config.PLAYER_BASE_ATTACK_DAMAGE, color=(200, 230, 255),
            ))
            self.player.attack_cooldown_timer = config.PLAYER_BASE_ATTACK_COOLDOWN

    def _handle_collisions(self):
        # proyektil dasar vs musuh
        for p in self.projectiles:
            for e in self.enemies:
                if e in p.hit_enemies:
                    continue
                if circle_collide(p.pos, p.radius, e.pos, e.radius):
                    e.take_damage(p.damage)
                    p.hit_enemies.add(e)
                    if p.pierce <= 0:
                        p.lifetime = 0
                    break

        # kontak musuh vs pemain
        for e in self.enemies:
            if circle_collide(self.player.pos, self.player.radius, e.pos, e.radius):
                self.player.take_damage(e.damage)

    def _cleanup_dead_enemies(self):
        alive = []
        for e in self.enemies:
            if e.hp <= 0:
                self.orbs.append(XPOrb(e.x, e.y, e.xp_value))
                self.player.kills += 1
            else:
                alive.append(e)
        self.enemies = alive

        remaining_orbs = []
        for orb in self.orbs:
            if distance(self.player.pos, orb.pos) < self.player.radius + orb.radius:
                self.player.gain_xp(orb.value)
            else:
                remaining_orbs.append(orb)
        self.orbs = remaining_orbs

    # ------------------------------------------------------------------
    def _restart(self):
        self.player = Player(0, 0)
        self.spawner = Spawner()
        self.skills = SkillManager()
        self.enemies = []
        self.orbs = []
        self.projectiles = []
        self.elapsed = 0.0
        self.state = "playing"

    # ------------------------------------------------------------------
    def _draw(self):
        self.screen.fill(config.COLOR_BG)
        cam_x = self.player.x - config.SCREEN_WIDTH / 2
        cam_y = self.player.y - config.SCREEN_HEIGHT / 2

        self._draw_grid(cam_x, cam_y)

        for orb in self.orbs:
            orb.draw(self.screen, cam_x, cam_y)
        for e in self.enemies:
            e.draw(self.screen, cam_x, cam_y)
        for effect in self.skills.effects:
            effect.draw(self.screen, cam_x, cam_y)
        for p in self.projectiles:
            p.draw(self.screen, cam_x, cam_y)

        self.player.draw(self.screen, cam_x, cam_y)

        self.ui.draw_hud(self.screen, self.player, self.elapsed, self.skills,
                          self.gesture_thread.is_recording(), self.camera_available)

        frame, mask, _centroid = self.gesture_thread.get_preview()
        points = self.gesture_thread.current_points()
        camera_overlay.draw_camera_panel(self.screen, frame, mask, points)

        if self.state == "gameover":
            mins, secs = divmod(int(self.elapsed), 60)
            self.ui.draw_center_message(
                self.screen, "GAME OVER",
                f"Bertahan {mins:02d}:{secs:02d} - {self.player.kills} kill.  Tekan R untuk main lagi.")

    def _draw_grid(self, cam_x, cam_y):
        spacing = 64
        start_x = -int(cam_x) % spacing
        start_y = -int(cam_y) % spacing
        for x in range(start_x, config.SCREEN_WIDTH, spacing):
            pygame.draw.line(self.screen, config.COLOR_GRID, (x, 0), (x, config.SCREEN_HEIGHT))
        for y in range(start_y, config.SCREEN_HEIGHT, spacing):
            pygame.draw.line(self.screen, config.COLOR_GRID, (0, y), (config.SCREEN_WIDTH, y))
