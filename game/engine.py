import pygame

import config
from game import assets, background, camera_overlay, layout, settings, audio
from game.pickups import XPOrb
from game.player import Player
from game.projectile import Projectile
from game.screens.camera_test import CameraTestScreen
from game.screens.how_to_play import HowToPlayScreen
from game.screens.main_menu import MainMenuScreen
from game.screens.overlays import GameOverScreen, PauseScreen
from game.screens.settings_screen import SettingsScreen
from game.skills import SkillManager
from game.sidebar import Sidebar
from game.spawner import Spawner
from game.ui import UI
from game.utils import circle_collide, distance
from gesture import shape_classifier
from gesture.gesture_thread import GestureThread


class Game:
    def __init__(self, use_camera=True):
        """use_camera=False: jangan membuka webcam (untuk tes / bermain dengan tombol 1-5)."""
        pygame.init()
        settings.load()    # terapkan settings.json ke config SEBELUM ada yang membacanya
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        pygame.display.set_caption(config.GAME_TITLE)
        self.clock = pygame.time.Clock()

        assets.init()   # sprite/efek/latar dari folder assets/ (kosong = gambar vektor)
        print(assets.get().summary())
        audio.init()  

        self.ui = UI()
        self.sidebar = Sidebar()
        self.running = True

        self.gesture_thread = GestureThread()
        self.camera_available = self.gesture_thread.start() if use_camera else False
        self.show_mask = False       # tombol M: tampilkan mask hitam di panel kamera
        self.calib_prepare = 0.0     # sisa hitung mundur sebelum kalibrasi dimulai (detik)

        self.space_held = False
        self._debug_shape_keys = {
            pygame.K_1: "triangle",
            pygame.K_2: "circle",
            pygame.K_4: "line",
            pygame.K_5: "zigzag",
        }

        self._reset_world()

        self.screens = {
            "menu": MainMenuScreen(self),
            "howto": HowToPlayScreen(self),
            "settings": SettingsScreen(self),
            "camera": CameraTestScreen(self),
            "paused": PauseScreen(self),
            "gameover": GameOverScreen(self),
        }
        self.state = None
        self.set_state("menu")

    # ------------------------------------------------------------------
    # Alur layar
    # ------------------------------------------------------------------
    def set_state(self, new_state):
        old = self.screens.get(self.state) if self.state else None
        if old is not None:
            old.on_exit()
        self.state = new_state
        audio.get().on_state(new_state)
        pygame.mouse.set_visible(new_state != "playing")
        screen = self.screens.get(new_state)
        if screen is not None:
            screen.on_enter()

    def open_settings(self, return_to):
        self.screens["settings"].return_to = return_to
        self.set_state("settings")

    def start_new_game(self, calibrate=True):
        """Mulai permainan baru. calibrate=True: jalankan kalibrasi rambut (kalau diaktifkan)."""
        self._reset_world()
        self._cancel_recording()
        self.set_state("playing")
        if calibrate and config.GESTURE_AUTO_CALIBRATE_ON_START:
            self.begin_calibration()

    def go_to_menu(self):
        self._cancel_recording()
        self.set_state("menu")

    def pause(self):
        self._cancel_recording()
        self.set_state("paused")

    def quit(self):
        self.running = False

    def on_setting_changed(self, key):
        """Dipanggil layar Pengaturan setelah pilihan berubah."""
        if key in ("camera_mirror", "*"):
            # zona rambut yang dipelajari memakai orientasi lama -> tidak berlaku lagi
            self.gesture_thread.tracker.background.clear()

    def _cancel_recording(self):
        if self.space_held or self.gesture_thread.is_recording():
            self.gesture_thread.end_recording()
        self.space_held = False

    # ------------------------------------------------------------------
    # Kalibrasi (hitung mundur dulu supaya sempat menjauhkan sarung tangan)
    # ------------------------------------------------------------------
    def begin_calibration(self):
        if not self.camera_available:
            return
        if config.GESTURE_CALIB_PREPARE_SECONDS > 0:
            self.calib_prepare = config.GESTURE_CALIB_PREPARE_SECONDS
        else:
            self.gesture_thread.start_calibration()

    def calibration_active(self):
        return self.calib_prepare > 0 or self.gesture_thread.is_calibrating()

    def _tick_calibration_prepare(self, dt):
        if self.calib_prepare > 0:
            self.calib_prepare -= dt
            if self.calib_prepare <= 0:
                self.calib_prepare = 0.0
                self.gesture_thread.start_calibration()

    def draw_calibration_overlay(self, surface):
        """Banner hitung mundur / progres kalibrasi (dipakai saat bermain & di Tes Kamera)."""
        if self.calib_prepare > 0:
            total = config.GESTURE_CALIB_PREPARE_SECONDS
            self.ui.draw_calibration_banner(
                surface, 1.0 - self.calib_prepare / total,
                title="BERSIAP KALIBRASI",
                subtitle=f"Jauhkan sarung tangan dari kamera... mulai {self.calib_prepare:.1f} detik")
        elif self.gesture_thread.is_calibrating():
            self.ui.draw_calibration_banner(surface, self.gesture_thread.calibration_progress())

    # ------------------------------------------------------------------
    # Loop utama
    # ------------------------------------------------------------------
    def run(self):
        while self.running:
            dt = self.clock.tick(config.FPS) / 1000.0
            self.process_events()
            self.update(dt)
            self.draw()
            pygame.display.flip()

        self.gesture_thread.stop()
        pygame.quit()

    def process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue
            if self.state == "playing":
                self._handle_play_event(event)
            else:
                screen = self.screens.get(self.state)
                if screen is not None:
                    screen.handle_event(event)

    def update(self, dt):
        self._tick_calibration_prepare(dt)
        if self.state == "playing":
            self._update_play(dt)
            self.sidebar.update(dt, self.player)
        else:
            screen = self.screens.get(self.state)
            if screen is not None:
                screen.update(dt)

    def draw(self):
        screen = self.screens.get(self.state)
        overlay = screen is not None and screen.overlay
        if self.state == "playing" or overlay:
            # di balik Jeda/Game Over panel kamera disembunyikan agar tidak menabrak teks menu
            self._draw_world(show_camera=not overlay)
        if screen is not None:
            screen.draw(self.screen)

    # ------------------------------------------------------------------
    # Input saat bermain
    # ------------------------------------------------------------------
    def _handle_play_event(self, event):
        if event.type == pygame.KEYDOWN:
            key = event.key
            if key == pygame.K_ESCAPE:
                self.pause()
            elif key == pygame.K_SPACE:
                if not self.calibration_active():
                    self.space_held = True
                    self.gesture_thread.begin_recording()
            elif key == pygame.K_c:
                if not self.space_held:
                    self.begin_calibration()
            elif key == pygame.K_m:
                self.show_mask = not self.show_mask
            elif config.DEBUG_KEYBOARD_GESTURE_FALLBACK and key in self._debug_shape_keys:
                shape = self._debug_shape_keys[key]
                self.skills.trigger(shape, self.player, self.enemies, self.player.facing)

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE and self.space_held:
                self.space_held = False
                self._finish_gesture()

    def _finish_gesture(self):
        points = self.gesture_thread.end_recording()
        shape = shape_classifier.classify(points)
        direction = shape_classifier.dominant_direction(points)
        self.skills.trigger(shape, self.player, self.enemies, direction)

    # ------------------------------------------------------------------
    # Dunia game
    # ------------------------------------------------------------------
    def _reset_world(self):
        self.player = Player(0, 0)
        self.spawner = Spawner()
        self.skills = SkillManager()
        self.enemies = []
        self.orbs = []
        self.projectiles = []
        self.elapsed = 0.0

    def _update_play(self, dt):
        calibrating = self.calibration_active()
        if not calibrating:
            self.elapsed += dt

        # auto-stop kalau merekam gestur kelamaan
        if self.gesture_thread.recording_expired():
            self.space_held = False
            self._finish_gesture()

        # dunia membeku selama kalibrasi; musuh melambat selagi pemain menggambar jurus
        if calibrating:
            time_scale = 0.0
        elif self.gesture_thread.is_recording():
            time_scale = config.GESTURE_TIME_SCALE_WHILE_DRAWING
        else:
            time_scale = 1.0
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
            self._cancel_recording()
            self.set_state("gameover")

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
                if self.player.take_damage(e.damage):
                    if self.player.is_alive():
                        audio.get().play_sfx("enemy_hit")

    def _cleanup_dead_enemies(self):
        alive = []
        for e in self.enemies:
            if e.hp <= 0:
                self.orbs.append(XPOrb(e.x, e.y, e.xp_value))
                self.player.add_kill(e)
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
    # Gambar dunia + HUD (juga jadi latar layar Jeda / Game Over)
    # ------------------------------------------------------------------
    def _draw_world(self, show_camera=True):
        self.screen.fill(config.COLOR_BG)

        # dunia hanya digambar di area game (kiri); kolom kanan diisi sidebar
        game_surf = self.screen.subsurface(layout.GAME_RECT)
        cam_x = self.player.x - layout.GAME_RECT.width / 2
        cam_y = self.player.y - layout.GAME_RECT.height / 2

        background.draw_background(game_surf, cam_x, cam_y)

        for orb in self.orbs:
            orb.draw(game_surf, cam_x, cam_y)
        for e in self.enemies:
            e.draw(game_surf, cam_x, cam_y)
        for effect in self.skills.effects:
            effect.draw(game_surf, cam_x, cam_y)
        for p in self.projectiles:
            p.draw(game_surf, cam_x, cam_y)

        self.player.draw(game_surf, cam_x, cam_y)

        frame, mask, centroid = self.gesture_thread.get_preview()
        points = self.gesture_thread.current_points()

        self.ui.draw_hud(game_surf, self.player, self.elapsed, self.skills,
                         self.gesture_thread.is_recording(), self.camera_available,
                         glove_visible=centroid is not None)

        # kolom kanan: health, potret, skill, bingkai webcam
        self.sidebar.draw(self.screen, self.player, self.skills)

        if not show_camera:
            return    # di balik Jeda/Game Over: bingkai webcam dibiarkan kosong

        camera_overlay.draw_camera_panel(
            self.screen, frame, mask, points, centroid=centroid,
            exclusion=self.gesture_thread.get_exclusion(), show_mask=self.show_mask,
            rect=layout.WEBCAM_VIDEO, alpha=255)
        self.sidebar.draw_live_badge(self.screen, self.camera_available)

        if self.camera_available:
            # bar pencahayaan dipindah ke pojok kanan-bawah area game
            light_rect = pygame.Rect(layout.GAME_RECT.right - 408, layout.GAME_RECT.bottom - 8, 400, 0)
            self.ui.draw_lighting_bar(
                self.screen, light_rect,
                self.gesture_thread.get_lighting(), self.gesture_thread.exclusion_ratio(),
                self.calibration_active())
            self.draw_calibration_overlay(game_surf)
