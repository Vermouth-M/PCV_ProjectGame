import math
import os
import time
import pygame

import config

EXTENSIONS = ("png", "webp", "jpg", "jpeg")

# (label, prefix yang dicoba berurutan, keterangan)
MANIFEST = [
    ("Pemain - diam", ("sprites/player/idle",), "animasi diam, menghadap KANAN"),
    ("Pemain - jalan", ("sprites/player/walk",), "animasi jalan, menghadap KANAN"),
]
for _kind in ("basic", "fast", "tank"):
    MANIFEST.append((
        f"Musuh {_kind}",
        (f"sprites/enemies/{_kind}_walk", f"sprites/enemies/{_kind}"),
        "animasi jalan atau gambar tunggal, menghadap KANAN",
    ))
MANIFEST += [
    ("Orb XP", ("sprites/pickups/xp_orb",), "gambar tunggal atau animasi"),
    ("Peluru serangan dasar", ("sprites/projectiles/bullet",), "menghadap KANAN, diputar mengikuti arah"),
    ("Efek Jurus Segitiga", ("effects/triangle_slash",), "pangkal di KIRI-TENGAH, ujung ke kanan"),
    ("Efek Jurus Lingkaran", ("effects/circle_shockwave",), "persegi, lingkaran/cincin di tengah"),
    ("Efek Jurus Garis", ("effects/line_slash",), "pangkal di KIRI-TENGAH, ujung ke kanan"),
    ("Efek Jurus Zigzag (petir)", ("effects/lightning",), "pangkal di KIRI-TENGAH, ujung ke kanan"),
    ("Efek Perisai (Jurus Kotak)", ("effects/shield",), "persegi, berpusat di karakter"),
    ("Latar / lantai", ("backgrounds/ground",), "tile yang bisa disambung (seamless)"),
]
for _shape in config.SKILL_DEFS:
    MANIFEST.append((f"Ikon jurus {_shape}", (f"ui/skill_{_shape}",), "ikon kecil untuk HUD"))


class AssetManager:
    def __init__(self, root=None, enabled=True):
        self.root = root or config.ASSETS_DIR
        self.enabled = enabled
        self._files = {}     # prefix -> [path]
        self._frames = {}    # (prefixes, size, scale) -> [Surface]
        self._flip = {}      # id(surface) -> (surface, hasil)
        self._rot = {}
        self._tint = {}
        self._dim = {}
        self._warned = set()
        self._raw = {}           
        self.preload_ms = 0.0

    # ------------------------------------------------------------------
    # Pencarian file
    # ------------------------------------------------------------------
    def _first_existing(self, rel):
        base = os.path.join(self.root, *rel.split("/"))
        for ext in EXTENSIONS:
            path = f"{base}.{ext}"
            if os.path.isfile(path):
                return path
        return None

    def find_files(self, prefix):
        if not self.enabled:
            return []
        if prefix in self._files:
            return self._files[prefix]

        files, i = [], 0
        while True:
            path = self._first_existing(f"{prefix}_{i}")
            if path is None:
                break
            files.append(path)
            i += 1
        if not files:
            single = self._first_existing(prefix)
            files = [single] if single else []

        self._files[prefix] = files
        return files

    # ------------------------------------------------------------------
    # Memuat gambar
    # ------------------------------------------------------------------
    def _warn(self, path, exc):
        if path not in self._warned:
            self._warned.add(path)
            print(f"[assets] PERINGATAN: gagal memuat '{path}' ({exc}); memakai gambar vektor.")

    def _load(self, path, cap=True):
        if path in self._raw:
            return self._raw[path]
        try:
            surf = pygame.image.load(path)
        except (pygame.error, OSError) as exc:
            self._warn(path, exc)
            self._raw[path] = None
            return None
        try:
            if pygame.display.get_surface() is not None:
                surf = surf.convert_alpha()
        except pygame.error:
            pass
        if cap and config.ASSET_MAX_SIDE and max(surf.get_size()) > config.ASSET_MAX_SIDE:
            surf = self.resize(surf, size=config.ASSET_MAX_SIDE)
        self._raw[path] = surf
        return surf

    @staticmethod
    def resize(surf, size=None, scale=None):
        """
        size  : int  -> sisi terpanjang jadi segini (rasio dipertahankan)
                tuple-> ukuran persis (w, h)
        scale : float-> pengali ukuran asli
        """
        w, h = surf.get_size()
        if size is None and scale is None:
            return surf
        if isinstance(size, tuple):
            new = size
        elif size is not None:
            f = size / max(w, h)
            new = (w * f, h * f)
        else:
            new = (w * scale, h * scale)
        new = (max(1, int(round(new[0]))), max(1, int(round(new[1]))))
        if new == (w, h):
            return surf
        try:
            return pygame.transform.smoothscale(surf, new)
        except (ValueError, pygame.error):
            return pygame.transform.scale(surf, new)

    def frames(self, *prefixes, size=None, scale=None):
        """Frame dari prefix pertama yang ada (urutan prefix = urutan prioritas). [] kalau tidak ada."""
        if not self.enabled:
            return []
        key = (prefixes, size, scale)
        if key in self._frames:
            return self._frames[key]

        result = []
        for prefix in prefixes:
            loaded = [self._load(p, cap=not prefix.startswith("backgrounds/")) for p in self.find_files(prefix)]
            loaded = [s for s in loaded if s is not None]
            if loaded:
                result = [self.resize(s, size, scale) for s in loaded]
                break
        self._frames[key] = result
        return result

    def image(self, *prefixes, size=None, scale=None):
        """Frame pertama saja, atau None kalau aset tidak ada."""
        fr = self.frames(*prefixes, size=size, scale=scale)
        return fr[0] if fr else None
    def preload(self):
        """
        Decode SEMUA aset yang ada sekarang (di awal), bukan saat pertama kali dipakai.
        Tanpa ini, jurus/musuh yang baru pertama muncul membaca disk + decode PNG di tengah
        permainan (tersendat/freeze sesaat). Return jumlah file yang berhasil dimuat.
        """
        if not self.enabled:
            return 0
        start, loaded = time.perf_counter(), 0
        for _label, prefixes, _hint in MANIFEST:
            for prefix in prefixes:
                for path in self.find_files(prefix):
                    if self._load(path, cap=not prefix.startswith("backgrounds/")) is not None:
                        loaded += 1
        self.preload_ms = (time.perf_counter() - start) * 1000.0
        return loaded

    def flipped(self, surf):
        entry = self._flip.get(id(surf))
        if entry is None:
            entry = (surf, pygame.transform.flip(surf, True, False))
            self._flip[id(surf)] = entry
        return entry[1]

    def rotated(self, surf, angle_deg):
        """Putar berlawanan jarum jam (konvensi pygame); dibulatkan per 5 derajat agar cache efektif."""
        bucket = int(round(angle_deg / 5.0)) * 5 % 360
        key = (id(surf), bucket)
        entry = self._rot.get(key)
        if entry is None:
            entry = (surf, pygame.transform.rotate(surf, bucket))
            self._rot[key] = entry
        return entry[1]

    def tinted(self, surf, rgb):
        """Tambahkan warna (mis. putih utk kilat kena hit); alpha asli tetap."""
        key = (id(surf), tuple(rgb))
        entry = self._tint.get(key)
        if entry is None:
            t = surf.copy()
            t.fill(tuple(rgb), special_flags=pygame.BLEND_RGB_ADD)
            entry = (surf, t)
            self._tint[key] = entry
        return entry[1]

    def dimmed(self, surf):
        """Versi gelap & agak transparan (mis. ikon jurus yang sedang cooldown)."""
        entry = self._dim.get(id(surf))
        if entry is None:
            d = surf.copy()
            d.fill((110, 110, 110, 255), special_flags=pygame.BLEND_RGBA_MULT)
            entry = (surf, d)
            self._dim[id(surf)] = entry
        return entry[1]

    def directional(self, prefixes, length, thickness, angle_rad):
        """
        Untuk efek yang berbentuk "pangkal di KIRI-TENGAH gambar, ujung ke kanan"
        (tebasan, petir). Gambar diregangkan jadi length x thickness lalu diputar ke
        angle_rad (sudut layar, y ke bawah).

        Return (surface_hasil_putar, offset) dengan offset = vektor dari titik pangkal
        (world) ke pusat surface; atau None kalau aset tidak ada.
        """
        base = self.image(*prefixes)
        if base is None:
            return None
        length, thickness = max(1, int(length)), max(1, int(thickness))
        img = self.resize(base, size=(length, thickness))
        rotated = pygame.transform.rotate(img, -math.degrees(angle_rad))
        offset = (math.cos(angle_rad) * length / 2, math.sin(angle_rad) * length / 2)
        return rotated, offset

    # ------------------------------------------------------------------
    # Laporan
    # ------------------------------------------------------------------
    def status(self):
        """[(label, prefix_terpakai_atau_prefix_utama, jumlah_frame, keterangan)]"""
        rows = []
        for label, prefixes, hint in MANIFEST:
            used, n = prefixes[0], 0
            for prefix in prefixes:
                files = self.find_files(prefix)
                if files:
                    used, n = prefix, len(files)
                    break
            rows.append((label, used, n, hint))
        return rows

    def summary(self):
        if not self.enabled:
            return "[assets] dinonaktifkan (config.USE_ASSETS = False): semua gambar memakai vektor."
        rows = self.status()
        have = sum(1 for r in rows if r[2] > 0)
        return (f"[assets] {have}/{len(rows)} aset ditemukan di '{self.root}' "
                f"(sisanya memakai gambar vektor). Dimuat dalam {self.preload_ms:.0f} ms.")


# ----------------------------------------------------------------------
# Manajer global. Default-nya nonaktif sampai init() dipanggil, jadi kode yang
# dijalankan tanpa init (mis. tes) otomatis jatuh ke gambar vektor.
# ----------------------------------------------------------------------
_manager = AssetManager(enabled=False)


def init(root=None):
    """Panggil sekali setelah pygame.display.set_mode() (butuh display untuk convert_alpha)."""
    global _manager
    _manager = AssetManager(root=root, enabled=config.USE_ASSETS)
    _manager.preload()          # muat semua aset SEKARANG, bukan saat jurus pertama keluar
    return _manager


def get():
    return _manager
