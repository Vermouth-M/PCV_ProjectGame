"""
tests/test_menu.py
====================
Tes sistem menu & alur layar. TIDAK membuka webcam dan tidak menyentuh
settings.json asli (memakai file sementara). Kamera disimulasikan lewat
Game(use_camera=False) + suntikan data.

Yang diuji:
  - widget Menu: navigasi keyboard, mouse, item nonaktif
  - alur: menu -> cara bermain / pengaturan / tes kamera / mulai / keluar
  - mulai game: kalibrasi dengan hitung mundur, dunia membeku, SPASI diabaikan
  - bermain: ESC jeda, rekaman dibatalkan, jeda membekukan dunia, konfirmasi menu
  - game over: R / Enter / Esc
  - pengaturan: ubah, simpan, muat, file rusak/nilai tidak valid, reset
  - tes kamera: latihan gambar jurus
  - semua layar tergambar; panel kamera tersembunyi di balik jeda
  - teks muat di layar (cek ukuran font)

Jalankan:
    python tests/test_menu.py
"""

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
import pygame  # noqa: E402

import config  # noqa: E402
from game import assets, settings  # noqa: E402
from game.enemy import Enemy  # noqa: E402
from game.engine import Game  # noqa: E402
from game.screens import how_to_play  # noqa: E402
from game.screens.widgets import Menu, MenuItem, get_font, wrap_text  # noqa: E402
from gesture.lighting import LightingMonitor  # noqa: E402
from test_shape_classifier import make_circle, make_triangle  # noqa: E402

RESULTS = []
TMP = tempfile.mkdtemp(prefix="vgs_menu_")
SETTINGS_PATH = os.path.join(TMP, "settings.json")
settings.SETTINGS_FILE = SETTINGS_PATH

_CONFIG_KEYS = ["CAMERA_MIRROR", "GESTURE_AUTO_CALIBRATE_ON_START", "CAMERA_PANEL_WIDTH",
                "CAMERA_PANEL_HEIGHT", "GESTURE_TIME_SCALE_WHILE_DRAWING",
                "DEBUG_KEYBOARD_GESTURE_FALLBACK", "USE_ASSETS"]
_ORIGINAL = {k: getattr(config, k) for k in _CONFIG_KEYS}


def check(name, ok, info=""):
    RESULTS.append(bool(ok))
    print(f"[{'OK' if ok else 'GAGAL'}] {name} {info}")


def reset_config():
    for k, v in _ORIGINAL.items():
        setattr(config, k, v)
    config.GESTURE_AUTO_CALIBRATE_ON_START = True
    config.USE_ASSETS = True
    config.DEBUG_KEYBOARD_GESTURE_FALLBACK = True


def new_game():
    reset_config()
    if os.path.exists(SETTINGS_PATH):
        os.remove(SETTINGS_PATH)
    with contextlib.redirect_stdout(io.StringIO()):
        return Game(use_camera=False)


def fake_camera(game, on=True):
    game.camera_available = on
    game.gesture_thread._camera_ok = on


def inject_preview(game, bgr=(200, 200, 200)):
    gt = game.gesture_thread
    with gt._lock:
        gt._latest_frame = np.full((480, 640, 3), bgr, np.uint8)
        gt._latest_mask = np.zeros((240, 320), np.uint8)
        gt._latest_centroid = None
        gt._latest_lighting = LightingMonitor()._build_state(150)


def press(game, key):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))
    game.process_events()


def release(game, key):
    pygame.event.post(pygame.event.Event(pygame.KEYUP, key=key))
    game.process_events()


def click(game, pos):
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1))
    game.process_events()


def hover(game, pos):
    pygame.event.post(pygame.event.Event(pygame.MOUSEMOTION, pos=pos, rel=(0, 0), buttons=(0, 0, 0)))
    game.process_events()


def current_menu(game):
    screen = game.screens[game.state]
    return screen.confirm if getattr(screen, "confirming", False) else screen.menu


def choose(game, label):
    menu = current_menu(game)
    for _ in range(len(menu.items) + 1):
        if menu.selected.text() == label:
            break
        press(game, pygame.K_DOWN)
    assert menu.selected.text() == label, f"item '{label}' tidak ditemukan"
    press(game, pygame.K_RETURN)


def labels(menu):
    return [item.text() for item in menu.items]


def run_frames(game, n=3, dt=1 / 60):
    for _ in range(n):
        game.update(dt)
        game.draw()


# ---------------------------------------------------------------------------
def test_menu_widget():
    hits = []
    items = [MenuItem("A", lambda: hits.append("A")),
             MenuItem("B", lambda: hits.append("B"), enabled=False),
             MenuItem("C", lambda: hits.append("C"))]
    m = Menu(items, 500, 100)

    def ev(t, **kw):
        return pygame.event.Event(t, **kw)

    check("Menu: item pertama yang aktif terpilih", m.index == 0)
    m.handle_event(ev(pygame.KEYDOWN, key=pygame.K_DOWN))
    check("Menu: item nonaktif dilewati (A -> C)", m.index == 2)
    m.handle_event(ev(pygame.KEYDOWN, key=pygame.K_s))
    check("Menu: navigasi melingkar (C -> A) dengan tombol S", m.index == 0)
    m.handle_event(ev(pygame.KEYDOWN, key=pygame.K_w))
    check("Menu: W naik & melingkar (A -> C)", m.index == 2)
    m.handle_event(ev(pygame.KEYDOWN, key=pygame.K_RETURN))
    m.handle_event(ev(pygame.MOUSEBUTTONDOWN, pos=m.rects[1].center, button=1))
    check("Menu: Enter menjalankan; klik item nonaktif tidak", hits == ["C"], f"-> {hits}")
    m.handle_event(ev(pygame.MOUSEMOTION, pos=m.rects[0].center, rel=(0, 0), buttons=(0, 0, 0)))
    check("Menu: hover mouse memilih item", m.index == 0)
    m.handle_event(ev(pygame.MOUSEBUTTONDOWN, pos=m.rects[0].center, button=1))
    m.handle_event(ev(pygame.MOUSEBUTTONDOWN, pos=m.rects[0].center, button=3))
    check("Menu: klik kiri menjalankan, klik kanan diabaikan", hits == ["C", "A"], f"-> {hits}")

    val = {"v": 0}
    vm = Menu([MenuItem("Nilai", value=lambda: str(val["v"]),
                        on_left=lambda: val.update(v=val["v"] - 1), on_right=lambda: val.update(v=val["v"] + 1))],
              500, 100)
    vm.handle_event(ev(pygame.KEYDOWN, key=pygame.K_RIGHT))
    vm.handle_event(ev(pygame.KEYDOWN, key=pygame.K_d))
    vm.handle_event(ev(pygame.KEYDOWN, key=pygame.K_a))
    check("Menu: panah/A/D mengubah nilai", val["v"] == 1, f"-> {val}")

    lines = wrap_text("Jurus Lingkaran Gelombang Kejut", 17, 200, bold=True)
    font = get_font(17, True)
    check("wrap_text: tiap baris muat & tidak ada kata hilang",
          len(lines) >= 2 and all(font.size(l)[0] <= 200 for l in lines)
          and " ".join(lines) == "Jurus Lingkaran Gelombang Kejut", f"-> {lines}")


def test_navigation_flow():
    g = new_game()
    check("Game dimulai di menu utama, kamera tidak dibuka",
          g.state == "menu" and not g.camera_available)
    check("Isi menu utama", labels(g.screens["menu"].menu) ==
          ["Mulai Game", "Tes Kamera", "Cara Bermain", "Pengaturan", "Keluar"],
          f"-> {labels(g.screens['menu'].menu)}")

    choose(g, "Cara Bermain")
    ok1 = g.state == "howto"
    press(g, pygame.K_ESCAPE)
    check("Cara Bermain terbuka, Esc kembali ke menu", ok1 and g.state == "menu")

    choose(g, "Pengaturan")
    ok1 = g.state == "settings" and g.screens["settings"].return_to == "menu"
    press(g, pygame.K_ESCAPE)
    check("Pengaturan terbuka (kembali ke menu), Esc kembali", ok1 and g.state == "menu")

    choose(g, "Tes Kamera")
    ok1 = g.state == "camera"
    press(g, pygame.K_ESCAPE)
    check("Tes Kamera terbuka, Esc kembali", ok1 and g.state == "menu")

    menu = g.screens["menu"].menu
    click(g, menu.rects[2].center)
    ok1 = g.state == "howto"
    click(g, g.screens["howto"].menu.rects[0].center)
    check("Klik mouse membuka layar & tombol Kembali bisa diklik", ok1 and g.state == "menu")

    press(g, pygame.K_ESCAPE)
    check("Esc di menu utama tidak menutup game", g.state == "menu" and g.running)
    hover(g, menu.rects[3].center)
    check("Hover mouse memindahkan pilihan", menu.index == 3)
    click(g, menu.rects[4].center)
    check("Item Keluar menghentikan game", not g.running)

    g.running = True
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    g.process_events()
    check("Tombol tutup jendela menghentikan game", not g.running)


def test_start_game_and_calibration():
    g = new_game()
    choose(g, "Mulai Game")
    check("Mulai Game (tanpa kamera): langsung bermain tanpa hitung mundur",
          g.state == "playing" and g.calib_prepare == 0 and g.elapsed == 0)

    g = new_game()
    fake_camera(g)
    g.enemies.append(Enemy(300, 0, "basic"))
    choose(g, "Mulai Game")
    check("Mulai Game (ada kamera): hitung mundur kalibrasi dimulai",
          g.state == "playing" and abs(g.calib_prepare - config.GESTURE_CALIB_PREPARE_SECONDS) < 1e-6
          and g.enemies == [], f"-> prepare {g.calib_prepare}")

    press(g, pygame.K_SPACE)
    check("SPASI diabaikan saat bersiap kalibrasi", not g.space_held and not g.gesture_thread.is_recording())

    elapsed0, spawn0 = g.elapsed, g.spawner.elapsed
    g.update(0.5)
    check("Dunia membeku saat hitung mundur", g.elapsed == elapsed0 and g.spawner.elapsed == spawn0
          and g.calib_prepare > 0 and not g.gesture_thread.tracker.background.calibrating)
    g.update(0.5)
    g.update(0.6)
    bg = g.gesture_thread.tracker.background
    check("Hitung mundur selesai -> kalibrasi dimulai", g.calib_prepare == 0 and bg.calibrating)
    g.update(0.5)
    check("Dunia tetap beku selama kalibrasi berjalan", g.elapsed == elapsed0)
    for _ in range(config.GESTURE_CALIB_FRAMES):
        bg.feed(np.zeros((240, 320), np.uint8))
    g.update(0.5)
    check("Kalibrasi selesai -> permainan berjalan lagi", not bg.calibrating and g.elapsed > elapsed0)
    run_frames(g, 3)

    config.GESTURE_AUTO_CALIBRATE_ON_START = False
    g.start_new_game()
    check("Pengaturan kalibrasi otomatis mati: tidak ada hitung mundur", g.calib_prepare == 0)
    config.GESTURE_AUTO_CALIBRATE_ON_START = True
    g.start_new_game(calibrate=False)
    check("start_new_game(calibrate=False) tidak menghitung mundur", g.calib_prepare == 0)

    g.begin_calibration()
    press(g, pygame.K_c)
    check("Tombol C saat sudah bersiap tidak merusak (tetap menghitung)", g.calib_prepare > 0)


def test_playing_pause_and_controls():
    g = new_game()
    g.start_new_game(calibrate=False)

    press(g, pygame.K_SPACE)
    rec_before = g.gesture_thread.is_recording()
    press(g, pygame.K_ESCAPE)
    check("Esc saat bermain -> jeda; rekaman gestur dibatalkan",
          rec_before and g.state == "paused" and not g.space_held and not g.gesture_thread.is_recording())

    g.enemies.append(Enemy(300, 0, "basic"))
    x0, e0 = g.enemies[0].x, g.elapsed
    run_frames(g, 20)
    check("Selama jeda dunia tidak bergerak & waktu tidak berjalan", g.enemies[0].x == x0 and g.elapsed == e0)
    release(g, pygame.K_SPACE)
    check("Melepas SPASI saat jeda tidak memicu jurus", all(v == 0 for v in g.skills.cooldowns.values()))

    press(g, pygame.K_ESCAPE)
    check("Esc di jeda -> lanjut bermain", g.state == "playing")

    g.pause()
    check("Menu jeda: Kalibrasi Ulang nonaktif tanpa kamera",
          not g.screens["paused"].menu.items[1].is_enabled() and
          g.screens["paused"].menu.selected.text() == "Lanjutkan")
    choose(g, "Lanjutkan")
    check("Item Lanjutkan melanjutkan permainan", g.state == "playing")

    fake_camera(g)
    g.pause()
    choose(g, "Kalibrasi Ulang")
    check("Jeda -> Kalibrasi Ulang: kembali bermain dengan hitung mundur", g.state == "playing" and g.calib_prepare > 0)
    g.calib_prepare = 0

    g.pause()
    choose(g, "Pengaturan")
    ok1 = g.state == "settings" and g.screens["settings"].return_to == "paused"
    press(g, pygame.K_ESCAPE)
    check("Pengaturan dari jeda kembali ke jeda", ok1 and g.state == "paused")

    choose(g, "Menu Utama")
    pause = g.screens["paused"]
    check("Menu Utama meminta konfirmasi dulu", pause.confirming and g.state == "paused")
    press(g, pygame.K_ESCAPE)
    check("Esc membatalkan konfirmasi (tetap di jeda)", not pause.confirming and g.state == "paused")
    choose(g, "Menu Utama")
    choose(g, "Tidak, lanjut bermain")
    check("Pilih 'Tidak' menutup konfirmasi", not pause.confirming and g.state == "paused")
    choose(g, "Menu Utama")
    choose(g, "Ya, ke menu utama")
    check("Pilih 'Ya' kembali ke menu utama", g.state == "menu")

    g.start_new_game(calibrate=False)
    press(g, pygame.K_1)
    check("Tombol cadangan 1 memicu Jurus Segitiga", g.skills.cooldowns["triangle"] > 0)
    config.DEBUG_KEYBOARD_GESTURE_FALLBACK = False
    press(g, pygame.K_2)
    check("Tombol cadangan dimatikan lewat pengaturan", g.skills.cooldowns["circle"] == 0)

    m0 = g.show_mask
    press(g, pygame.K_m)
    check("Tombol M mengganti tampilan mask", g.show_mask != m0)

    g2 = new_game()
    g2.start_new_game(calibrate=False)
    press(g2, pygame.K_SPACE)
    g2.gesture_thread.recorder.points = [(float(x), float(y)) for x, y in make_triangle()]
    release(g2, pygame.K_SPACE)
    check("Gestur segitiga (SPASI tahan-lepas) memicu Jurus Segitiga Pedang",
          "Segitiga" in g2.skills.last_message and g2.skills.cooldowns["triangle"] > 0,
          f"-> '{g2.skills.last_message}'")


def test_game_over():
    g = new_game()
    fake_camera(g)
    g.start_new_game(calibrate=False)
    g.player.kills = 9
    g.player.hp = 0
    g.update(1 / 60)
    check("HP habis -> layar Game Over", g.state == "gameover")
    run_frames(g, 3)

    press(g, pygame.K_r)
    check("R di Game Over: main lagi, dunia baru, tanpa kalibrasi ulang",
          g.state == "playing" and g.player.kills == 0 and g.player.hp == g.player.max_hp and g.calib_prepare == 0)

    g.player.hp = 0
    g.update(1 / 60)
    choose(g, "Main Lagi")
    check("Item Main Lagi memulai game baru", g.state == "playing" and g.player.hp > 0)

    g.player.hp = 0
    g.update(1 / 60)
    choose(g, "Menu Utama")
    check("Item Menu Utama kembali ke menu", g.state == "menu")

    g.start_new_game(calibrate=False)
    g.player.hp = 0
    g.update(1 / 60)
    press(g, pygame.K_ESCAPE)
    check("Esc di Game Over kembali ke menu", g.state == "menu")


def test_settings():
    g = new_game()
    check("Tanpa settings.json: nilai bawaan config dipakai", config.CAMERA_MIRROR is True)

    choose(g, "Pengaturan")
    sc = g.screens["settings"]
    choose(g, "Kamera mode cermin")
    check("Enter pada baris pengaturan mengganti nilainya", config.CAMERA_MIRROR is False)
    with open(SETTINGS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    check("Perubahan tersimpan ke settings.json", data["camera_mirror"] is False and "panel_size" in data
          and isinstance(data["panel_size"], list), f"-> {data}")

    press(g, pygame.K_LEFT)
    check("Panah kiri membalik nilai (toggle)", config.CAMERA_MIRROR is True)

    sc.menu.index = [i.text() for i in sc.menu.items].index("Ukuran panel kamera")
    press(g, pygame.K_RIGHT)
    check("Ukuran panel kamera berubah (Sedang -> Besar)",
          (config.CAMERA_PANEL_WIDTH, config.CAMERA_PANEL_HEIGHT) == (480, 360))
    press(g, pygame.K_RIGHT)
    check("Pilihan melingkar (Besar -> Kecil)", (config.CAMERA_PANEL_WIDTH, config.CAMERA_PANEL_HEIGHT) == (240, 180))

    sc.menu.index = [i.text() for i in sc.menu.items].index("Mode fokus (slow-mo saat gambar)")
    press(g, pygame.K_RIGHT)
    check("Mode fokus berubah (0.35 -> 0.2)", config.GESTURE_TIME_SCALE_WHILE_DRAWING == 0.2)

    # mode cermin diganti -> zona rambut lama dibuang
    g.gesture_thread.tracker.background.exclusion = np.ones((240, 320), np.uint8)
    choose(g, "Kamera mode cermin")
    check("Ganti mode cermin menghapus zona rambut lama", g.gesture_thread.tracker.background.exclusion is None)

    choose(g, "Aset gambar (game berikutnya)")
    off = (config.USE_ASSETS is False and assets.get().enabled is False)
    choose(g, "Aset gambar (game berikutnya)")
    check("Aset gambar: dimatikan lalu dinyalakan memuat ulang pemuat aset",
          off and config.USE_ASSETS is True and assets.get().enabled is True)

    # muat ulang dari file
    config.CAMERA_PANEL_WIDTH, config.CAMERA_PANEL_HEIGHT = 400, 300
    config.GESTURE_TIME_SCALE_WHILE_DRAWING = 0.35
    config.CAMERA_MIRROR = True
    check("settings.load() menerapkan isi file", settings.load() and config.GESTURE_TIME_SCALE_WHILE_DRAWING == 0.2
          and (config.CAMERA_PANEL_WIDTH, config.CAMERA_PANEL_HEIGHT) == (240, 180))

    choose(g, "Kembalikan ke bawaan")
    check("Kembalikan ke bawaan memulihkan semua nilai",
          config.GESTURE_TIME_SCALE_WHILE_DRAWING == _ORIGINAL["GESTURE_TIME_SCALE_WHILE_DRAWING"]
          and (config.CAMERA_PANEL_WIDTH, config.CAMERA_PANEL_HEIGHT) == (_ORIGINAL["CAMERA_PANEL_WIDTH"], _ORIGINAL["CAMERA_PANEL_HEIGHT"])
          and config.CAMERA_MIRROR is _ORIGINAL["CAMERA_MIRROR"])
    choose(g, "Kembali")
    check("Item Kembali menutup pengaturan", g.state == "menu")

    # ketahanan terhadap file buruk
    reset_config()
    for name, content in (("rusak", "{ini bukan json"), ("bukan dict", "[1, 2, 3]"), ("kosong", "")):
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        check(f"File {name} diabaikan tanpa crash", settings.load() is False and config.CAMERA_MIRROR is True)
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump({"focus_mode": 5.0, "camera_mirror": 1, "panel_size": [999, 1], "debug_keys": False,
                   "tidak_dikenal": True}, f)
    ok = settings.load()
    check("Nilai di luar pilihan / tipe salah diabaikan, nilai valid tetap diterapkan",
          ok and config.GESTURE_TIME_SCALE_WHILE_DRAWING == _ORIGINAL["GESTURE_TIME_SCALE_WHILE_DRAWING"]
          and config.CAMERA_MIRROR is True and config.DEBUG_KEYBOARD_GESTURE_FALLBACK is False
          and (config.CAMERA_PANEL_WIDTH, config.CAMERA_PANEL_HEIGHT) == (400, 300))
    check("save() ke lokasi yang tidak bisa ditulis -> False tanpa crash",
          settings.save(os.path.join(TMP, "tidak_ada", "x.json")) is False)

    config.GESTURE_TIME_SCALE_WHILE_DRAWING = 0.5     # diubah manual di config.py
    focus = [s for s in settings.SETTINGS if s.key == "focus_mode"][0]
    check("Nilai manual di luar daftar dipetakan ke pilihan terdekat", focus.text() == "Ringan", f"-> {focus.text()}")

    # Game baru memuat settings.json saat start
    reset_config()
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump({"camera_mirror": False, "auto_calibrate": False}, f)
    with contextlib.redirect_stdout(io.StringIO()):
        Game(use_camera=False)
    check("Game memuat settings.json saat dibuka",
          config.CAMERA_MIRROR is False and config.GESTURE_AUTO_CALIBRATE_ON_START is False)


def test_camera_test_screen():
    g = new_game()
    g.set_state("camera")
    scr = g.screens["camera"]

    press(g, pygame.K_SPACE)
    check("Tes Kamera tanpa kamera: SPASI tidak merekam", not scr.holding)

    fake_camera(g)
    press(g, pygame.K_SPACE)
    check("Tes Kamera dengan kamera: SPASI mulai merekam", scr.holding and g.gesture_thread.is_recording())
    g.gesture_thread.recorder.points = [(float(x), float(y)) for x, y in make_circle()]
    release(g, pygame.K_SPACE)
    check("Lepas SPASI: bentuk dikenali & ditampilkan (lingkaran)",
          not scr.holding and scr.result and scr.result[0] == "circle", f"-> {scr.result}")

    press(g, pygame.K_SPACE)
    g.gesture_thread.recorder.points = [(10.0, 10.0), (12.0, 11.0)]
    release(g, pygame.K_SPACE)
    check("Gambar terlalu pendek -> 'unknown' (tidak dikenali)", scr.result[0] == "unknown", f"-> {scr.result}")
    run_frames(g, 2)

    press(g, pygame.K_SPACE)
    g.gesture_thread.recorder._start_time -= config.GESTURE_MAX_RECORD_SECONDS + 1
    g.update(1 / 60)
    check("Rekaman yang kelamaan berhenti otomatis", not scr.holding and scr.result is not None)

    press(g, pygame.K_c)
    check("Tombol C di Tes Kamera memulai hitung mundur kalibrasi", g.calib_prepare > 0)
    press(g, pygame.K_SPACE)
    check("SPASI diabaikan saat kalibrasi", not scr.holding)
    g.calib_prepare = 0

    m0 = g.show_mask
    press(g, pygame.K_m)
    check("Tombol M di Tes Kamera mengganti mask", g.show_mask != m0)
    run_frames(g, 2)

    press(g, pygame.K_SPACE)
    press(g, pygame.K_ESCAPE)
    check("Keluar saat merekam membatalkan rekaman", g.state == "menu" and not g.gesture_thread.is_recording())


def test_draw_all_screens():
    for with_camera in (False, True):
        for use_assets in (True, False):
            g = new_game()
            config.USE_ASSETS = use_assets
            assets.init()
            if with_camera:
                fake_camera(g)
                inject_preview(g)
            err = None
            try:
                for state in ("menu", "howto", "settings", "camera"):
                    g.set_state(state)
                    run_frames(g, 2)
                g.start_new_game(calibrate=with_camera)
                run_frames(g, 2)
                g.pause()
                run_frames(g, 2)
                g.screens["paused"]._ask_confirm()
                run_frames(g, 2)
                g.set_state("playing")
                g.player.hp = 0
                g.update(1 / 60)
                run_frames(g, 2)
                g.calib_prepare = 0.8
                g.set_state("camera")
                run_frames(g, 2)
            except Exception as exc:      # noqa: BLE001
                err = exc
            check(f"Semua layar tergambar tanpa error (kamera={with_camera}, aset={use_assets})", err is None, f"{err or ''}")

    g = new_game()
    g.update(1 / 60)
    g.draw()
    menu = g.screens["menu"].menu
    sel, other = menu.rects[0], menu.rects[1]
    check("Baris terpilih tampil beda dari baris lain",
          g.screen.get_at((sel.x + 120, sel.y + 4))[:3] != g.screen.get_at((other.x + 120, other.y + 4))[:3])

    g = new_game()
    fake_camera(g)
    inject_preview(g, bgr=(255, 0, 0))      # biru murni (BGR): kanal biru jadi penanda panel kamera
    g.start_new_game(calibrate=False)
    run_frames(g, 2)
    rect = pygame.Rect(0, 0, config.CAMERA_PANEL_WIDTH, config.CAMERA_PANEL_HEIGHT)
    rect.bottomright = (config.SCREEN_WIDTH - config.CAMERA_PANEL_MARGIN, config.SCREEN_HEIGHT - config.CAMERA_PANEL_MARGIN)
    playing_blue = g.screen.get_at((rect.centerx, rect.centery + 40))[2]
    g.pause()
    run_frames(g, 2)
    paused_blue = g.screen.get_at((rect.centerx, rect.centery + 40))[2]
    check("Panel kamera disembunyikan di balik layar Jeda", playing_blue > 150 and paused_blue < 25,
          f"-> kanal biru: main {playing_blue}, jeda {paused_blue}")
    g.set_state("playing")
    g.player.hp = 0
    g.update(1 / 60)
    run_frames(g, 2)
    over_blue = g.screen.get_at((rect.centerx, rect.centery + 40))[2]
    check("Panel kamera juga disembunyikan di balik layar Game Over", over_blue < 25, f"-> {over_blue}")


def test_text_fits():
    W = config.SCREEN_WIDTH
    problems = []

    def fits(label, width, limit):
        if width > limit:
            problems.append(f"{label}: {width}px > {limit}px")

    for shape, cfg in config.SKILL_DEFS.items():
        fits(f"nama jurus {shape}", get_font(19, True).size(cfg["name"])[0] + 590, W - 12)
        fits(f"deskripsi jurus {shape}",
             get_font(15).size(f"{how_to_play.SHAPE_NAME[shape]}: {how_to_play.EFFECT[shape]}")[0] + 590, W - 12)
    for key, desc in how_to_play.CONTROLS:
        fits(f"kontrol '{key}'", get_font(18, True).size(key)[0] + 50, 190 - 10)
        fits(f"kontrol '{desc}'", get_font(18).size(desc)[0] + 190, 510)
    for line in how_to_play.TIPS:
        fits("tips", get_font(17).size(f"- {line}")[0] + 50, W - 20)
    for line in ("Gambar jurusmu di udara dengan sarung tangan hitam",
                 "Kamera TIDAK terdeteksi - jurus lewat tombol 1-5 saat bermain",
                 "W/S atau panah: pilih   |   Enter atau klik: jalankan"):
        fits("menu utama", get_font(19).size(line)[0], W - 20)
    fits("judul menu", get_font(54, True).size("VAMPIRE GESTURE")[0], W - 40)

    # baris pengaturan: label di kiri + nilai terpanjang di kanan harus muat di lebar baris 720
    for s in settings.SETTINGS:
        value_w = max(get_font(21, True).size(t)[0] for _, t in s.choices)
        fits(f"pengaturan '{s.label}'", get_font(21).size(s.label)[0] + value_w + 22 + 44 + 40, 720)
    from game.screens import camera_test
    for line in camera_test.HELP:
        fits("bantuan tes kamera", get_font(16).size(line)[0] + 640, W - 10)
    for cfg in config.SKILL_DEFS.values():
        for line in wrap_text(cfg["name"], 17, 320 - 104 - 10, bold=True):
            fits(f"hasil tes kamera '{line}'", get_font(17, True).size(line)[0], 320 - 104 - 10)

    check("Semua teks layar muat dalam batasnya (font tersedia di mesin ini)", not problems, "\n      ".join(problems))


def test_cli():
    result = subprocess.run([sys.executable, os.path.join(ROOT, "main.py"), "--help"],
                            capture_output=True, text=True, timeout=60)
    check("main.py --help menampilkan opsi --no-camera", result.returncode == 0 and "--no-camera" in result.stdout,
          result.stderr[-200:] if result.returncode else "")

    # siklus run() penuh: buka game, terima QUIT, bersihkan, keluar normal
    code = ("import os; os.environ['SDL_VIDEODRIVER']='dummy'; os.environ['SDL_AUDIODRIVER']='dummy';"
            "import pygame; from game.engine import Game;"
            "g = Game(use_camera=False); pygame.event.post(pygame.event.Event(pygame.QUIT));"
            "g.run(); print('RUN_SELESAI')")
    result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, timeout=90)
    check("Game.run(): loop utama berjalan & berhenti bersih saat jendela ditutup",
          result.returncode == 0 and "RUN_SELESAI" in result.stdout, result.stderr[-300:] if result.returncode else "")


def main():
    try:
        for fn in (test_menu_widget, test_navigation_flow, test_start_game_and_calibration,
                   test_playing_pause_and_controls, test_game_over, test_settings,
                   test_camera_test_screen, test_draw_all_screens, test_text_fits, test_cli):
            print(f"\n== {fn.__name__} ==")
            fn()
    finally:
        reset_config()
        shutil.rmtree(TMP, ignore_errors=True)
    passed = sum(RESULTS)
    print(f"\n{passed}/{len(RESULTS)} pemeriksaan lolos.")
    if passed != len(RESULTS):
        sys.exit(1)


if __name__ == "__main__":
    main()
