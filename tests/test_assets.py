import os
import shutil
import sys
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

pygame.init()
SCREEN = pygame.display.set_mode((1000, 700))

import config  # noqa: E402
from game import assets, background  # noqa: E402
from game.assets import AssetManager  # noqa: E402
from game.enemy import Enemy  # noqa: E402
from game.pickups import XPOrb  # noqa: E402
from game.player import Player  # noqa: E402
from game.projectile import Projectile  # noqa: E402
from game.skills import SkillManager  # noqa: E402
from game.ui import UI  # noqa: E402

CAM = (-500, -350)     # entitas di (0, 0) tampil di tengah layar (500, 350)
RESULTS = []
TMP_DIRS = []


def check(name, ok, info=""):
    RESULTS.append(ok)
    print(f"[{'OK' if ok else 'GAGAL'}] {name} {info}")


def px(x, y):
    return tuple(SCREEN.get_at((x, y)))[:3]


def close(a, b, tol=16):
    return all(abs(i - j) <= tol for i, j in zip(a, b))


def new_root():
    d = tempfile.mkdtemp(prefix="vgs_assets_")
    TMP_DIRS.append(d)
    return d


def make_png(root, rel, size=(64, 64), color=(0, 255, 0), halves=None):
    """halves=(warna_kiri, warna_kanan) untuk gambar asimetris (menguji flip)."""
    path = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    surf = pygame.Surface(size, pygame.SRCALPHA)
    surf.fill(tuple(color) + (255,))
    if halves:
        half = size[0] // 2
        surf.fill(tuple(halves[0]) + (255,), (0, 0, half, size[1]))
        surf.fill(tuple(halves[1]) + (255,), (half, 0, size[0] - half, size[1]))
    pygame.image.save(surf, path)


def clear():
    SCREEN.fill((0, 0, 0))


# ---------------------------------------------------------------------------
def test_loader():
    root = new_root()
    m = assets.init(root=root)
    check("Folder kosong: frames()/image() kosong, tanpa error",
          m.frames("sprites/player/walk") == [] and m.image("effects/shield") is None)
    check("Ringkasan folder kosong menyebut 0 aset", "0/" in m.summary(), f"-> {m.summary()[:40]}...")

    make_png(root, "sprites/player/walk_0.png", (80, 40))
    make_png(root, "sprites/player/walk_1.png", (80, 40))
    make_png(root, "sprites/player/walk_3.png", (80, 40))      # nomor 2 bolong
    make_png(root, "sprites/enemies/basic.png", (80, 40))
    make_png(root, "sprites/pickups/xp_orb.png")
    m = assets.init(root=root)

    check("Animasi bernomor berhenti di celah (0,1 ada; 3 diabaikan)",
          len(m.frames("sprites/player/walk")) == 2)
    check("Prefix berurutan: basic_walk tak ada -> pakai basic.png",
          len(m.frames("sprites/enemies/basic_walk", "sprites/enemies/basic")) == 1)
    check("Skala size=int mempertahankan rasio (80x40 -> 40x20)",
          m.image("sprites/enemies/basic", size=40).get_size() == (40, 20))
    check("Skala size=tuple memberi ukuran persis",
          m.image("sprites/enemies/basic", size=(33, 77)).get_size() == (33, 77))
    check("Hasil di-cache (objek sama dipakai ulang)",
          m.frames("sprites/player/walk", size=30) is m.frames("sprites/player/walk", size=30))

    st = {r[0]: r[2] for r in m.status()}
    check("status() melaporkan jumlah frame", st["Pemain - jalan"] == 2 and st["Musuh basic"] == 1
          and st["Pemain - diam"] == 0, f"-> {st['Pemain - jalan']}, {st['Musuh basic']}, {st['Pemain - diam']}")

    # ekstensi lain (jpg) -- dilewati bila build pygame tidak bisa menulis jpg
    try:
        path = os.path.join(root, "backgrounds")
        os.makedirs(path, exist_ok=True)
        pygame.image.save(pygame.Surface((32, 32)), os.path.join(path, "ground.jpg"))
        m = assets.init(root=root)
        check("Ekstensi .jpg dikenali", m.image("backgrounds/ground") is not None)
    except pygame.error:
        print("[SKIP] penulisan jpg tidak didukung build pygame ini")

    # file rusak -> None, tidak crash, tidak error saat diminta ulang
    bad = os.path.join(root, "sprites", "enemies", "tank.png")
    with open(bad, "wb") as f:
        f.write(b"ini bukan gambar")
    m = assets.init(root=root)
    check("File rusak -> None tanpa crash", m.image("sprites/enemies/tank") is None
          and m.image("sprites/enemies/tank") is None)

    check("USE_ASSETS=False menonaktifkan pemuatan", _with_assets_disabled(root))


def _with_assets_disabled(root):
    config.USE_ASSETS = False
    try:
        m = assets.init(root=root)
        return m.frames("sprites/player/walk") == [] and "dinonaktifkan" in m.summary()
    finally:
        config.USE_ASSETS = True


def test_transforms():
    root = new_root()
    make_png(root, "sprites/player/walk_0.png", (60, 20), halves=((255, 0, 0), (0, 0, 255)))
    m = assets.init(root=root)
    img = m.image("sprites/player/walk")
    flip = m.flipped(img)
    check("flipped menukar kiri-kanan",
          close(tuple(img.get_at((5, 10)))[:3], (255, 0, 0)) and close(tuple(flip.get_at((5, 10)))[:3], (0, 0, 255)))
    check("flipped di-cache", m.flipped(img) is flip)
    check("rotated 90 derajat menukar lebar-tinggi", m.rotated(img, 90).get_size() == (20, 60))
    white = m.tinted(img, (255, 255, 255))
    check("tinted memutihkan", close(tuple(white.get_at((5, 10)))[:3], (255, 255, 255)))
    dim = m.dimmed(img)
    check("dimmed menggelapkan", tuple(dim.get_at((5, 10)))[0] < 160)

    res = m.directional(("sprites/player/walk",), 100, 20, 0.0)
    check("directional sudut 0: ukuran 100x20, pusat bergeser setengah panjang",
          res is not None and res[0].get_size() == (100, 20) and res[1] == (50.0, 0.0))
    check("directional tanpa aset -> None", m.directional(("effects/tidak_ada",), 10, 10, 0) is None)


def test_entities_with_sprites():
    root = new_root()
    make_png(root, "sprites/player/walk_0.png", (64, 64), halves=((255, 0, 0), (0, 0, 255)))
    make_png(root, "sprites/enemies/basic.png", (64, 64), color=(255, 0, 255))
    make_png(root, "sprites/pickups/xp_orb_0.png", (32, 32), color=(255, 0, 0))
    make_png(root, "sprites/pickups/xp_orb_1.png", (32, 32), color=(0, 255, 0))
    make_png(root, "sprites/projectiles/bullet.png", (80, 20), color=(255, 255, 0))
    make_png(root, "effects/shield.png", (64, 64), color=(0, 255, 255))
    assets.init(root=root)

    p = Player(0, 0)
    clear(); p.draw(SCREEN, *CAM)
    check("Pemain: sprite tampil (tanpa idle, pakai frame pertama walk), menghadap kanan",
          close(px(480, 358), (255, 0, 0)) and close(px(520, 358), (0, 0, 255)),
          f"-> kiri {px(480, 358)}, kanan {px(520, 358)}")

    p.face_left = True
    clear(); p.draw(SCREEN, *CAM)
    check("Pemain jalan ke kiri: sprite di-flip", close(px(480, 358), (0, 0, 255)))

    p.face_left = False
    p.invuln_timer = 0.1          # fase kedip
    clear(); p.draw(SCREEN, *CAM)
    check("Pemain kena hit: sprite berkedip merah", close(px(480, 358), (255, 30, 30)), f"-> {px(480, 358)}")

    p.invuln_timer = 0.0
    p.activate_shield(2.0)
    clear(); p.draw(SCREEN, *CAM)
    check("Perisai memakai sprite effects/shield", close(px(480, 358), (0, 255, 255)), f"-> {px(480, 358)}")

    keys = {pygame.K_a: True, pygame.K_d: False, pygame.K_w: False, pygame.K_s: False}

    class Keys(dict):
        def __getitem__(self, k):
            return self.get(k, False)

    p2 = Player(0, 0)
    p2.handle_input(Keys(keys), 0.016)
    check("handle_input: jalan ke kiri -> moving & face_left", p2.moving and p2.face_left)
    p2.handle_input(Keys({pygame.K_w: True}), 0.016)
    check("Jalan vertikal tidak mengubah sisi hadap horizontal", p2.moving and p2.face_left)
    p2.handle_input(Keys(), 0.016)
    check("Tidak menekan tombol -> moving False", not p2.moving)

    e = Enemy(0, 0, "basic")
    clear(); e.draw(SCREEN, *CAM)
    check("Musuh: sprite tampil", close(px(506, 356), (255, 0, 255)), f"-> {px(506, 356)}")
    e.hit_flash_timer = 0.1
    clear(); e.draw(SCREEN, *CAM)
    check("Musuh kena hit: kilat putih", close(px(506, 356), (255, 255, 255)), f"-> {px(506, 356)}")
    e.update(0.016, (-100, 0))
    check("Musuh menoleh ke arah pemain (flip)", e.face_left)

    far = (10_000, 10_000)
    orb = XPOrb(0, 0, 5)
    clear(); orb.draw(SCREEN, *CAM)
    first = px(500, 350)
    orb.update(0.2, far)
    clear(); orb.draw(SCREEN, *CAM)
    check("Orb XP beranimasi (frame berganti)", close(first, (255, 0, 0)) and close(px(500, 350), (0, 255, 0)),
          f"-> {first} lalu {px(500, 350)}")

    bullet = Projectile(0, 0, (0, 100), damage=1)
    w, h = bullet._sprite.get_size()
    clear(); bullet.draw(SCREEN, *CAM)
    check("Peluru: sprite diputar mengikuti arah tembakan (ke bawah -> tinggi > lebar)",
          h > w and close(px(500, 360), (255, 255, 0)), f"-> {(w, h)}")


def test_entities_without_assets():
    assets.init(root=new_root())      # folder kosong -> fallback vektor
    p = Player(0, 0)
    clear(); p.draw(SCREEN, *CAM)
    check("Tanpa aset: pemain vektor (lingkaran biru)", close(px(492, 358), config.COLOR_PLAYER),
          f"-> {px(492, 358)}")
    e = Enemy(0, 0, "basic")
    clear(); e.draw(SCREEN, *CAM)
    check("Tanpa aset: musuh vektor", close(px(506, 356), config.ENEMY_COLORS["basic"]), f"-> {px(506, 356)}")
    e.hit_flash_timer = 0.1
    clear(); e.draw(SCREEN, *CAM)
    check("Tanpa aset: kilat putih tetap jalan", close(px(506, 356), (255, 255, 255)))
    orb = XPOrb(0, 0, 5)
    clear(); orb.draw(SCREEN, *CAM)
    check("Tanpa aset: orb vektor", close(px(500, 350), config.COLOR_XP_BAR_FG), f"-> {px(500, 350)}")
    pr = Projectile(0, 0, (100, 0), damage=1, color=(10, 200, 10))
    clear(); pr.draw(SCREEN, *CAM)
    check("Tanpa aset: peluru vektor", close(px(500, 350), (10, 200, 10)))
    p.activate_shield(2.0)
    clear(); p.draw(SCREEN, *CAM)
    check("Tanpa aset: perisai vektor tetap tampil", any(close(px(500 + dx, 350), config.COLOR_SHIELD, 30)
                                                          for dx in range(-36, -20)))


def _enemies_in_line():
    return [Enemy(80, 0, "basic"), Enemy(150, 40, "basic"), Enemy(200, -30, "basic")]


def test_skill_effects():
    root = new_root()
    make_png(root, "effects/triangle_slash.png", (100, 60), color=(255, 128, 0))
    make_png(root, "effects/circle_shockwave.png", (64, 64), color=(0, 255, 255))
    make_png(root, "effects/line_slash.png", (200, 30), color=(255, 255, 0))
    make_png(root, "effects/lightning.png", (100, 20), color=(255, 255, 255))
    assets.init(root=root)

    player = Player(0, 0)
    for shape in ("triangle", "circle", "line", "zigzag"):
        sm = SkillManager()
        sm.trigger(shape, player, _enemies_in_line(), (1.0, 0.0))
        eff = sm.effects[-1]
        has_sprite = {
            "triangle": lambda: eff._sprite is not None,
            "line": lambda: eff._sprite is not None,
            "circle": lambda: eff._base is not None,
            "zigzag": lambda: bool(eff._parts),
        }[shape]()
        # animasikan penuh: tidak boleh ada exception
        err = None
        try:
            for step in range(12):
                eff.age = eff.duration * step / 11
                clear(); eff.draw(SCREEN, *CAM)
        except Exception as exc:      # noqa: BLE001
            err = exc
        check(f"Efek {shape}: memakai sprite & animasi penuh tanpa error", has_sprite and err is None, f"{err or ''}")

    sm = SkillManager()
    sm.trigger("line", player, [], (1.0, 0.0))
    clear(); sm.effects[-1].draw(SCREEN, *CAM)
    check("Efek garis: sprite membentang dari pemain ke arah tebasan", close(px(600, 350), (255, 255, 0)),
          f"-> {px(600, 350)}")
    sm = SkillManager()
    sm.trigger("triangle", player, [], (1.0, 0.0))
    clear(); sm.effects[-1].draw(SCREEN, *CAM)
    check("Efek segitiga: sprite di depan pemain", close(px(540, 350), (255, 128, 0)), f"-> {px(540, 350)}")
    sm = SkillManager()
    sm.trigger("zigzag", player, [Enemy(100, 0, "basic")], (1.0, 0.0))
    clear(); sm.effects[-1].draw(SCREEN, *CAM)
    check("Efek petir: sprite membentang ke musuh pertama", close(px(550, 350), (255, 255, 255)),
          f"-> {px(550, 350)}")

    sm = SkillManager()
    sm.trigger("square", player, [], (1.0, 0.0))
    check("Jurus kotak mengaktifkan perisai", player.is_shielded)

    # fallback vektor untuk semua jurus
    assets.init(root=new_root())
    player = Player(0, 0)
    ok, err = True, None
    try:
        for shape in config.SKILL_DEFS:
            sm = SkillManager()
            sm.trigger(shape, player, _enemies_in_line(), (1.0, 0.0))
            for eff in sm.effects:
                if eff._sprite is not None or getattr(eff, "_parts", []) or getattr(eff, "_base", None) is not None:
                    ok = False
                for step in range(6):
                    eff.age = eff.duration * step / 5
                    clear(); eff.draw(SCREEN, *CAM)
    except Exception as exc:          # noqa: BLE001
        err = exc
    check("Tanpa aset: kelima jurus tetap tampil (vektor) tanpa error", ok and err is None, f"{err or ''}")


def test_background_and_ui():
    root = new_root()
    make_png(root, "backgrounds/ground.png", (64, 64), halves=((30, 90, 40), (90, 30, 30)))
    assets.init(root=root)
    A, B = (30, 90, 40), (90, 30, 30)

    clear(); background.draw_background(SCREEN, 0, 0)
    check("Latar tile: posisi awal (kiri A, kanan B)", close(px(10, 10), A) and close(px(40, 10), B))
    clear(); background.draw_background(SCREEN, 32, 0)
    check("Latar tile bergeser mengikuti kamera (tanpa celah)", close(px(10, 10), B) and close(px(40, 10), A)
          and all(px(x, y) != (0, 0, 0) for x, y in ((0, 0), (999, 699), (500, 350))))
    clear(); background.draw_background(SCREEN, -37, 1234)
    check("Latar tile: kamera negatif/besar tetap menutup seluruh layar",
          all(px(x, y) != (0, 0, 0) for x in (0, 1, 500, 998, 999) for y in (0, 1, 350, 698, 699)))

    assets.init(root=new_root())
    SCREEN.fill(config.COLOR_BG)
    background.draw_background(SCREEN, 0, 0)
    check("Tanpa tile: grid vektor", close(px(0, 10), config.COLOR_GRID) and close(px(10, 10), config.COLOR_BG))

    # ikon jurus di HUD
    root = new_root()
    make_png(root, "ui/skill_triangle.png", (40, 40), color=(255, 100, 0))
    assets.init(root=root)
    ui, sm = UI(), SkillManager()
    clear(); ui._draw_skill_list(SCREEN, sm)
    ready_px = px(30, 557)
    sm.cooldowns["triangle"] = 2.0
    clear(); ui._draw_skill_list(SCREEN, sm)
    check("Ikon jurus tampil di HUD, redup saat cooldown",
          close(ready_px, (255, 100, 0)) and px(30, 557)[0] < ready_px[0] - 60,
          f"-> siap {ready_px}, cooldown {px(30, 557)}")
    assets.init(root=new_root())
    clear()
    try:
        ui._draw_skill_list(SCREEN, SkillManager())
        check("HUD tanpa ikon: daftar jurus tetap tampil", True)
    except Exception as exc:          # noqa: BLE001
        check("HUD tanpa ikon: daftar jurus tetap tampil", False, str(exc))


def main():
    try:
        for fn in (test_loader, test_transforms, test_entities_with_sprites,
                   test_entities_without_assets, test_skill_effects, test_background_and_ui):
            print(f"\n== {fn.__name__} ==")
            fn()
    finally:
        for d in TMP_DIRS:
            shutil.rmtree(d, ignore_errors=True)
    passed = sum(RESULTS)
    print(f"\n{passed}/{len(RESULTS)} pemeriksaan lolos.")
    if passed != len(RESULTS):
        sys.exit(1)


if __name__ == "__main__":
    main()
