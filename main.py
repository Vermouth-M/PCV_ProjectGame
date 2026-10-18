"""
Vampire Gesture Survivor (versi ringkas) -- jalankan:  python main.py

Kontrol:  W A S D = gerak | tahan SPASI = rekam jurus lalu gambar pola dengan sarung tangan hitam
          1-5 = jurus tanpa kamera | C = kalibrasi ulang | M = tampilkan mask | R = main lagi | ESC = keluar
"""

import math
import os
import random

import cv2
import numpy as np
import pygame

import gestur

# ======================================================================
# PENGATURAN (ubah angka di sini untuk menyetel game)
# ======================================================================
LEBAR, TINGGI, FPS = 1000, 700, 60
PANEL_L, PANEL_T, JARAK = 400, 300, 16            # ukuran & jarak panel kamera (pojok kanan-bawah)
PAKAI_ASET = True                                  # False = selalu pakai gambar vektor
JURUS_KEYBOARD = True                              # tombol 1-5 memicu jurus tanpa kamera
SLOWMO_MENGGAMBAR = 0.35                           # musuh melambat segini saat SPASI ditahan

PEMAIN = dict(radius=16, kecepatan=220, hp=100, kebal=0.7, magnet=90, damage=6, jeda=1.2, jangkau=260)
XP_AWAL, XP_NAIK = 20, 1.35
MUSUH = {
    "basic": dict(hp=20, kecepatan=70, damage=8, xp=5, radius=14, warna=(200, 70, 90), muncul=0),
    "fast": dict(hp=12, kecepatan=140, damage=6, xp=6, radius=11, warna=(230, 150, 40), muncul=25),
    "tank": dict(hp=90, kecepatan=40, damage=16, xp=18, radius=22, warna=(140, 90, 200), muncul=60),
}
MUNCUL_AWAL, MUNCUL_CEPAT, MUNCUL_RAMP, MUSUH_MAKS = 1.4, 0.25, 180.0, 220
HP_PER_MENIT, KECEPATAN_PER_MENIT = 0.18, 0.05    # musuh makin kuat tiap menit
JURUS = {
    "triangle": dict(nama="Jurus Segitiga Pedang", damage=34, radius=100, sudut=130, cooldown=3.0, warna=(255, 210, 90)),
    "circle": dict(nama="Jurus Lingkaran Gelombang Kejut", damage=22, radius=140, dorong=260, cooldown=5.0, warna=(120, 200, 255)),
    "square": dict(nama="Jurus Kotak Perisai", durasi=3.0, cooldown=9.0, warna=(120, 255, 180)),
    "line": dict(nama="Jurus Garis Tebasan", damage=42, panjang=420, lebar=46, cooldown=4.0, warna=(255, 120, 200)),
    "zigzag": dict(nama="Jurus Zigzag Petir", damage=16, rantai=5, jarak=220, cooldown=6.0, warna=(255, 255, 120)),
}
SKALA = dict(pemain=2.2, musuh=2.0, orb=3.0, peluru=3.0)   # ukuran sprite = diameter hitbox x angka ini
ANIM = dict(diam=4, jalan=10, musuh=8, orb=8)              # kecepatan animasi (frame/detik)
FOLDER_ASET = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
WARNA_TEKS, WARNA_REDUP = (230, 230, 235), (150, 150, 160)


# ======================================================================
# ALAT BANTU KECIL
# ======================================================================
class Benda:
    """Wadah data sederhana: Benda(x=1, y=2).x -> 1. Dipakai untuk pemain, musuh, orb, peluru, efek."""

    def __init__(self, **data):
        self.__dict__.update(data)


def jarak(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def selisih_sudut(a, b):
    return abs((a - b + math.pi) % (2 * math.pi) - math.pi)


def pukul(musuh, damage, dorong=None):
    musuh.hp -= damage
    musuh.kilat = 0.12                             # berkedip putih sebentar
    if dorong:
        musuh.kx += dorong[0]
        musuh.ky += dorong[1]


# ---------------- aset gambar (folder assets/ boleh kosong -> otomatis gambar vektor) ----------------
_cache_gambar, _cache_cermin = {}, {}


def muat(nama, ukuran=None):
    """Daftar gambar dari assets/<nama>.png, atau animasi <nama>_0.png, _1.png, ... ([] kalau tidak ada).
    ukuran: angka = sisi terpanjang jadi segini (rasio tetap), atau (lebar, tinggi)."""
    kunci = (nama, ukuran)
    if kunci not in _cache_gambar:
        berkas = []
        if PAKAI_ASET:
            i = 0
            while cari(f"{nama}_{i}"):
                berkas.append(cari(f"{nama}_{i}"))
                i += 1
            if not berkas and cari(nama):
                berkas = [cari(nama)]
        hasil = []
        for b in berkas:
            try:
                hasil.append(skala(pygame.image.load(b).convert_alpha(), ukuran))
            except (pygame.error, OSError) as e:
                print(f"[aset] gagal memuat {b} ({e}); pakai gambar vektor")
        _cache_gambar[kunci] = hasil
    return _cache_gambar[kunci]


def cari(nama):
    for ext in ("png", "webp", "jpg", "jpeg"):
        path = os.path.join(FOLDER_ASET, *nama.split("/")) + "." + ext
        if os.path.isfile(path):
            return path
    return None


def skala(img, ukuran):
    if ukuran is None:
        return img
    w, h = img.get_size()
    if isinstance(ukuran, int):
        w, h = w * ukuran / max(w, h), h * ukuran / max(w, h)
    else:
        w, h = ukuran
    return pygame.transform.smoothscale(img, (max(1, int(w)), max(1, int(h))))


def cermin(img):
    """Versi dibalik kiri-kanan (disimpan supaya tidak dibuat ulang tiap frame)."""
    if id(img) not in _cache_cermin:
        _cache_cermin[id(img)] = (img, pygame.transform.flip(img, True, False))
    return _cache_cermin[id(img)][1]


def frame_ke(daftar, t, fps):
    return daftar[int(t * fps) % len(daftar)] if daftar else None


def ke_surface(gambar):
    """Gambar OpenCV (BGR atau abu-abu) -> pygame.Surface seukuran panel. Return (surface, data)."""
    kecil = cv2.resize(gambar, (PANEL_L, PANEL_T))
    kode = cv2.COLOR_GRAY2RGB if kecil.ndim == 2 else cv2.COLOR_BGR2RGB
    data = cv2.cvtColor(kecil, kode).tobytes()          # `data` harus tetap hidup selama surface dipakai
    return pygame.image.frombuffer(data, (PANEL_L, PANEL_T), "RGB"), data


# ======================================================================
# GAME
# ======================================================================
class Game:
    def __init__(self, kamera=None):
        pygame.init()
        self.layar = pygame.display.set_mode((LEBAR, TINGGI))
        pygame.display.set_caption("Vampire Gesture Survivor")
        self.jam = pygame.time.Clock()
        self.font = {14: pygame.font.SysFont("consolas", 14), 18: pygame.font.SysFont("consolas", 18),
                     34: pygame.font.SysFont("consolas", 34, bold=True)}
        self.lapisan = pygame.Surface((LEBAR, TINGGI), pygame.SRCALPHA)    # tempat efek vektor transparan
        self.layar_gelap = pygame.Surface((LEBAR, TINGGI), pygame.SRCALPHA)
        self.layar_gelap.fill((0, 0, 0, 160))                              # tirai gelap saat game over
        self.cache_teks, self.cache_panel, self.cache_tint = {}, None, None
        self.tombol_jurus = {pygame.K_1: "triangle", pygame.K_2: "circle", pygame.K_3: "square",
                             pygame.K_4: "line", pygame.K_5: "zigzag"}

        self.kamera = kamera or gestur.Kamera()
        self.kamera_pernah_ada = self.kamera.mulai()
        if self.kamera_pernah_ada:
            self.kamera.kalibrasi()                                       # pelajari rambut/benda hitam diam
        self.tampil_mask = False
        self.ulang()

    def ulang(self):
        """Mulai permainan baru (juga dipakai saat pertama kali)."""
        p = PEMAIN
        self.pemain = Benda(x=0.0, y=0.0, radius=p["radius"], hp=p["hp"], hp_maks=p["hp"], kebal=0.0,
                            perisai=0.0, level=1, xp=0, xp_perlu=XP_AWAL, hadap=(1.0, 0.0), kiri=False,
                            bergerak=False, jeda_serang=0.0, kill=0, t=0.0)
        self.musuh, self.orb, self.peluru, self.efek = [], [], [], []
        self.jeda = {nama: 0.0 for nama in JURUS}
        self.waktu, self.timer_muncul, self.state = 0.0, 0.0, "main"        # state: main | selesai
        self.pesan_teks, self.pesan_waktu = "", 0.0
        self.tahan_spasi = False
        self.kamera.selesai_rekam()

    # ------------------------------------------------------------------
    # LOOP UTAMA
    # ------------------------------------------------------------------
    def jalan(self):
        try:
            while True:
                dt = min(self.jam.tick(FPS) / 1000.0, 0.05)       # batasi dt supaya lag tidak membuat musuh "teleport"
                if not self.tangani_input():
                    break
                if self.state == "main":
                    self.update(dt)
                self.gambar()
                pygame.display.flip()
        finally:
            self.kamera.berhenti()
            pygame.quit()

    def tangani_input(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False
            if e.type == pygame.KEYUP and e.key == pygame.K_SPACE and self.tahan_spasi:
                self.lepas_spasi()
            if e.type != pygame.KEYDOWN:
                continue
            main = self.state == "main"
            if e.key == pygame.K_ESCAPE:
                return False
            if e.key == pygame.K_SPACE and main and not self.kamera.sedang_kalibrasi():
                self.tahan_spasi = True
                self.kamera.mulai_rekam()
            elif e.key == pygame.K_c and main and not self.tahan_spasi:
                self.kamera.kalibrasi()
            elif e.key == pygame.K_m:
                self.tampil_mask = not self.tampil_mask
            elif e.key == pygame.K_r and not main:
                self.ulang()
            elif e.key in self.tombol_jurus and JURUS_KEYBOARD and main:
                self.pakai_jurus(self.tombol_jurus[e.key], self.pemain.hadap)
        return True

    def lepas_spasi(self):
        """SPASI dilepas (atau waktu rekam habis): kenali bentuknya lalu keluarkan jurus."""
        self.tahan_spasi = False
        titik = self.kamera.selesai_rekam()
        self.pakai_jurus(gestur.klasifikasi(titik), gestur.arah(titik))

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------
    def update(self, dt):
        kalibrasi = self.kamera.sedang_kalibrasi()
        if not kalibrasi:
            self.waktu += dt
        if self.kamera.rekam_habis():
            self.lepas_spasi()
        # dunia beku saat kalibrasi, melambat saat pemain menggambar jurus
        dunia = 0.0 if kalibrasi else (SLOWMO_MENGGAMBAR if self.kamera.merekam else 1.0)
        wd = dt * dunia

        self.gerak_pemain(dt, pygame.key.get_pressed())
        self.munculkan(wd)
        for m in self.musuh:
            self.gerak_musuh(m, wd)
        self.serang_otomatis()

        for b in self.peluru:
            b.x, b.y, b.umur = b.x + b.vx * dt, b.y + b.vy * dt, b.umur - dt
        self.peluru = [b for b in self.peluru if b.umur > 0]
        for nama in self.jeda:
            self.jeda[nama] = max(0.0, self.jeda[nama] - dt)
        for ef in self.efek:
            ef.umur += dt
        self.efek = [ef for ef in self.efek if ef.umur < ef.durasi]
        self.pesan_waktu = max(0.0, self.pesan_waktu - dt)
        for o in self.orb:
            self.tarik_orb(o, dt)

        self.tabrakan()
        self.bersihkan()
        if self.pemain.hp <= 0:
            self.state, self.tahan_spasi = "selesai", False
            self.kamera.selesai_rekam()

    def gerak_pemain(self, dt, tombol):
        p = self.pemain
        dx = int(bool(tombol[pygame.K_d])) - int(bool(tombol[pygame.K_a]))
        dy = int(bool(tombol[pygame.K_s])) - int(bool(tombol[pygame.K_w]))
        p.bergerak = (dx, dy) != (0, 0)
        if p.bergerak:
            panjang = math.hypot(dx, dy)                    # bagi panjang = diagonal tidak lebih cepat
            p.hadap = (dx / panjang, dy / panjang)
            p.kiri = dx < 0 if dx else p.kiri
            p.x += p.hadap[0] * PEMAIN["kecepatan"] * dt
            p.y += p.hadap[1] * PEMAIN["kecepatan"] * dt
        p.kebal, p.perisai = max(0.0, p.kebal - dt), max(0.0, p.perisai - dt)
        p.jeda_serang, p.t = max(0.0, p.jeda_serang - dt), p.t + dt

    def munculkan(self, dt):
        if len(self.musuh) >= MUSUH_MAKS:
            return
        self.timer_muncul -= dt
        if self.timer_muncul > 0:
            return
        self.timer_muncul = MUNCUL_AWAL + (MUNCUL_CEPAT - MUNCUL_AWAL) * min(self.waktu / MUNCUL_RAMP, 1.0)
        jenis = random.choice([k for k, v in MUSUH.items() if self.waktu >= v["muncul"]])
        sudut = random.uniform(0, math.tau)
        jauh = math.hypot(LEBAR, TINGGI) / 2 + 120           # di luar layar, termasuk sudut layar
        menit = self.waktu / 60
        s = MUSUH[jenis]
        hp = s["hp"] * (1 + menit * HP_PER_MENIT)
        ukuran = int(s["radius"] * 2 * SKALA["musuh"])
        self.musuh.append(Benda(
            jenis=jenis, x=self.pemain.x + math.cos(sudut) * jauh, y=self.pemain.y + math.sin(sudut) * jauh,
            radius=s["radius"], hp=hp, hp_maks=hp, kecepatan=s["kecepatan"] * (1 + menit * KECEPATAN_PER_MENIT),
            damage=s["damage"], xp=s["xp"], warna=s["warna"], kx=0.0, ky=0.0, kilat=0.0, kiri=False,
            t=random.random() * 2, gambar=muat(f"sprites/enemies/{jenis}_walk", ukuran) or muat(f"sprites/enemies/{jenis}", ukuran)))

    def gerak_musuh(self, m, dt):
        p = self.pemain
        if abs(m.kx) > 0.5 or abs(m.ky) > 0.5:               # sedang terpental: redam pelan-pelan
            m.x, m.y = m.x + m.kx * dt, m.y + m.ky * dt
            redam = 0.86 ** (dt * 60)                         # per detik, bukan per frame -> sama di semua FPS
            m.kx, m.ky = m.kx * redam, m.ky * redam
        else:
            dx, dy = p.x - m.x, p.y - m.y
            d = math.hypot(dx, dy)
            if d > 1e-3:
                m.x, m.y = m.x + dx / d * m.kecepatan * dt, m.y + dy / d * m.kecepatan * dt
        m.kilat, m.t = max(0.0, m.kilat - dt), m.t + dt
        if abs(p.x - m.x) > 2:
            m.kiri = p.x < m.x

    def serang_otomatis(self):
        p = self.pemain
        if p.jeda_serang > 0 or not self.musuh:
            return
        dekat = min(self.musuh, key=lambda m: jarak(p, m))
        d = jarak(p, dekat)
        if d > PEMAIN["jangkau"]:
            return
        d = d or 1.0                                          # musuh tepat di atas pemain: hindari bagi nol
        vx, vy = (dekat.x - p.x) / d * 420, (dekat.y - p.y) / d * 420
        sprite = muat("sprites/projectiles/bullet", int(5 * 2 * SKALA["peluru"]))
        putar = pygame.transform.rotate(sprite[0], -math.degrees(math.atan2(vy, vx))) if sprite else None
        self.peluru.append(Benda(x=p.x, y=p.y, vx=vx, vy=vy, radius=5, umur=2.0, gambar=putar))
        p.jeda_serang = PEMAIN["jeda"]

    def tarik_orb(self, o, dt):
        o.t += dt
        dx, dy = self.pemain.x - o.x, self.pemain.y - o.y
        d = math.hypot(dx, dy)
        if 1e-3 < d < PEMAIN["magnet"]:                      # makin dekat makin cepat tertarik
            laju = 260 * (1 - d / PEMAIN["magnet"]) + 60
            o.x, o.y = o.x + dx / d * laju * dt, o.y + dy / d * laju * dt

    def tabrakan(self):
        for b in self.peluru:
            for m in self.musuh:
                if jarak(b, m) <= b.radius + m.radius:
                    pukul(m, PEMAIN["damage"])
                    b.umur = 0
                    break
        p = self.pemain
        for m in self.musuh:
            if jarak(p, m) <= p.radius + m.radius and p.kebal <= 0 and p.perisai <= 0:
                p.hp -= m.damage
                p.kebal = PEMAIN["kebal"]

    def bersihkan(self):
        """Musuh mati -> jadi orb XP. Orb yang dekat pemain -> diambil."""
        p = self.pemain
        hidup = []
        for m in self.musuh:
            if m.hp <= 0:
                self.orb.append(Benda(x=m.x, y=m.y, nilai=m.xp, t=0.0))
                p.kill += 1
            else:
                hidup.append(m)
        self.musuh = hidup
        if p.hp <= 0:
            return                                            # sudah mati: tidak boleh "hidup lagi" karena level-up
        sisa = []
        for o in self.orb:
            if jarak(p, o) < p.radius + 5:
                self.tambah_xp(o.nilai)
            else:
                sisa.append(o)
        self.orb = sisa

    def tambah_xp(self, jumlah):
        p = self.pemain
        p.xp += jumlah
        while p.xp >= p.xp_perlu:
            p.xp -= p.xp_perlu
            p.level += 1
            p.xp_perlu = int(p.xp_perlu * XP_NAIK)
            p.hp_maks += 6
            p.hp = p.hp_maks                                  # naik level = HP terisi penuh

    # ------------------------------------------------------------------
    # JURUS
    # ------------------------------------------------------------------
    def pesan(self, teks):
        self.pesan_teks, self.pesan_waktu = teks, 1.6

    def pakai_jurus(self, bentuk, arah):
        if self.state != "main":
            return
        if bentuk not in JURUS:
            return self.pesan("Pola tidak dikenali, coba lagi!")
        j = JURUS[bentuk]
        if self.jeda[bentuk] > 0:
            return self.pesan(f"{j['nama']} masih cooldown!")
        self.jeda[bentuk] = j["cooldown"]
        self.pesan(j["nama"] + "!")

        p = self.pemain
        ef = Benda(jenis=bentuk, x=p.x, y=p.y, umur=0.0, warna=j["warna"], durasi=0.25, sprite=[], garis=[])
        if bentuk == "triangle":
            ef.sudut, ef.radius, ef.setengah = math.atan2(p.hadap[1], p.hadap[0]), j["radius"], math.radians(j["sudut"] / 2)
            for m in self.musuh:
                d = jarak(p, m)
                if 1e-3 < d <= ef.radius and selisih_sudut(math.atan2(m.y - p.y, m.x - p.x), ef.sudut) <= ef.setengah:
                    pukul(m, j["damage"])
            tebal = 2 * ef.radius * math.sin(ef.setengah)
            self.sprite_arah(ef, "effects/triangle_slash", ef.radius, tebal, ef.sudut, p.x, p.y)
        elif bentuk == "circle":
            ef.durasi, ef.radius = 0.35, j["radius"]
            for m in self.musuh:
                d = jarak(p, m)
                if d <= ef.radius:
                    pukul(m, j["damage"], ((m.x - p.x) / (d or 1) * j["dorong"], (m.y - p.y) / (d or 1) * j["dorong"]))
        elif bentuk == "square":
            p.perisai = j["durasi"]
            return                                            # gambar perisai ada di gambar_pemain()
        elif bentuk == "line":
            ef.sudut = math.atan2(arah[1], arah[0])
            dx, dy = math.cos(ef.sudut), math.sin(ef.sudut)
            for m in self.musuh:
                ex, ey = m.x - p.x, m.y - p.y
                if 0 <= ex * dx + ey * dy <= j["panjang"] and abs(-ex * dy + ey * dx) <= j["lebar"] / 2:
                    pukul(m, j["damage"])
            ef.panjang, ef.lebar = j["panjang"], j["lebar"]
            self.sprite_arah(ef, "effects/line_slash", j["panjang"], j["lebar"], ef.sudut, p.x, p.y)
        elif bentuk == "zigzag":
            ef.durasi = 0.3
            sisa, sekarang = list(self.musuh), (p.x, p.y)
            while sisa and len(ef.garis) < j["rantai"]:
                m = min(sisa, key=lambda m: math.hypot(m.x - sekarang[0], m.y - sekarang[1]))
                if math.hypot(m.x - sekarang[0], m.y - sekarang[1]) > j["jarak"]:
                    break
                pukul(m, j["damage"])
                ef.garis.append((sekarang, (m.x, m.y)))
                sekarang = (m.x, m.y)
                sisa.remove(m)
            for a, b in ef.garis:                             # satu sprite petir per sambungan
                self.sprite_arah(ef, "effects/lightning", math.dist(a, b), 30, math.atan2(b[1] - a[1], b[0] - a[0]), a[0], a[1])
        self.efek.append(ef)

    def sprite_arah(self, ef, nama, panjang, tebal, sudut, ox, oy):
        """Sprite 'pangkal di kiri-tengah, ujung ke kanan' diregangkan & diputar. Kalau tidak ada aset: tidak ditambah."""
        dasar = muat(nama)
        if not dasar or panjang < 1:
            return
        img = pygame.transform.rotate(skala(dasar[0], (panjang, tebal)), -math.degrees(sudut))
        ef.sprite.append((img, ox + math.cos(sudut) * panjang / 2, oy + math.sin(sudut) * panjang / 2))

    # ------------------------------------------------------------------
    # GAMBAR
    # ------------------------------------------------------------------
    def gambar(self):
        p = self.pemain
        cx, cy = p.x - LEBAR / 2, p.y - TINGGI / 2            # posisi kamera: pemain selalu di tengah layar
        self.layar.fill((18, 18, 24))
        self.gambar_latar(cx, cy)
        for o in self.orb:
            self.gambar_orb(o, cx, cy)
        for m in self.musuh:
            self.gambar_musuh(m, cx, cy)
        self.gambar_efek(cx, cy)
        for b in self.peluru:
            sx, sy = int(b.x - cx), int(b.y - cy)
            if b.gambar:
                self.layar.blit(b.gambar, b.gambar.get_rect(center=(sx, sy)))
            else:
                pygame.draw.circle(self.layar, (200, 230, 255), (sx, sy), b.radius)
        self.gambar_pemain(cx, cy)
        self.gambar_hud()
        self.gambar_panel()
        if self.state == "selesai":
            menit, detik = divmod(int(self.waktu), 60)
            self.layar.blit(self.layar_gelap, (0, 0))
            self.teks("GAME OVER", 34, (255, 255, 255), LEBAR // 2, TINGGI // 2 - 40, tengah=True)
            self.teks(f"Bertahan {menit:02d}:{detik:02d} - {p.kill} kill.  Tekan R untuk main lagi.", 18, WARNA_REDUP,
                      LEBAR // 2, TINGGI // 2 + 10, tengah=True)

    def gambar_latar(self, cx, cy):
        ubin = muat("backgrounds/ground")
        if ubin:
            w, h = ubin[0].get_size()
            for y in range(-int(cy) % h - h, TINGGI, h):
                for x in range(-int(cx) % w - w, LEBAR, w):
                    self.layar.blit(ubin[0], (x, y))
            return
        for x in range(-int(cx) % 64, LEBAR, 64):             # tidak ada aset: pakai garis kotak-kotak
            pygame.draw.line(self.layar, (32, 32, 40), (x, 0), (x, TINGGI))
        for y in range(-int(cy) % 64, TINGGI, 64):
            pygame.draw.line(self.layar, (32, 32, 40), (0, y), (LEBAR, y))

    def tempel(self, daftar, t, fps, x, y, kiri=False, warna=None):
        """Gambar satu frame sprite di (x, y). Return False kalau tidak ada sprite (pakai vektor)."""
        img = frame_ke(daftar, t, fps)
        if img is None:
            return False
        img = cermin(img) if kiri else img
        if warna:                                             # kilat: tambah warna ke sprite
            img = img.copy()
            img.fill(warna, special_flags=pygame.BLEND_RGB_ADD)
        self.layar.blit(img, img.get_rect(center=(x, y)))
        return True

    def gambar_orb(self, o, cx, cy):
        sx, sy = int(o.x - cx), int(o.y - cy)
        if not self.tempel(muat("sprites/pickups/xp_orb", int(5 * 2 * SKALA["orb"])), o.t, ANIM["orb"], sx, sy):
            pygame.draw.circle(self.layar, (240, 200, 40), (sx, sy), 5)
            pygame.draw.circle(self.layar, (255, 255, 255), (sx, sy), 5, 1)

    def gambar_musuh(self, m, cx, cy):
        sx, sy = int(m.x - cx), int(m.y - cy)
        if not (-60 < sx < LEBAR + 60 and -60 < sy < TINGGI + 60):
            return                                            # di luar layar, tidak perlu digambar
        if not self.tempel(m.gambar, m.t, ANIM["musuh"], sx, sy, m.kiri, (255, 255, 255) if m.kilat > 0 else None):
            pygame.draw.circle(self.layar, (255, 255, 255) if m.kilat > 0 else m.warna, (sx, sy), m.radius)
        if m.hp < m.hp_maks:                                  # bar HP kecil di atas kepala
            lebar = m.radius * 2
            pygame.draw.rect(self.layar, (40, 10, 10), (sx - lebar // 2, sy - m.radius - 8, lebar, 4))
            pygame.draw.rect(self.layar, (220, 60, 60), (sx - lebar // 2, sy - m.radius - 8, int(lebar * max(0, m.hp / m.hp_maks)), 4))

    def gambar_pemain(self, cx, cy):
        p = self.pemain
        sx, sy = int(p.x - cx), int(p.y - cy)
        kedip = p.kebal > 0 and int(p.kebal * 20) % 2 == 0
        ukuran = int(p.radius * 2 * SKALA["pemain"])
        diam, jalan = muat("sprites/player/idle", ukuran), muat("sprites/player/walk", ukuran)
        daftar, fps = (jalan, ANIM["jalan"]) if (p.bergerak and jalan) else (diam or jalan, ANIM["diam"])
        if not self.tempel(daftar, p.t, fps, sx, sy, p.kiri, (160, 30, 30) if kedip else None):
            pygame.draw.circle(self.layar, (255, 80, 80) if kedip else (80, 200, 255), (sx, sy), p.radius)
            ujung = (sx + p.hadap[0] * (p.radius + 8), sy + p.hadap[1] * (p.radius + 8))
            pygame.draw.line(self.layar, (255, 255, 255), (sx, sy), ujung, 3)
        if p.perisai > 0:                                     # perisai berdenyut
            setengah = p.radius + 14 + 4 * math.sin(pygame.time.get_ticks() / 120.0)
            sprite = muat("effects/shield", int(setengah * 2))
            if sprite:
                self.layar.blit(sprite[0], sprite[0].get_rect(center=(sx, sy)))
            else:
                kotak = pygame.Rect(0, 0, setengah * 2, setengah * 2)
                kotak.center = (sx, sy)
                pygame.draw.rect(self.layar, (90, 220, 255), kotak, width=3, border_radius=6)

    def gambar_efek(self, cx, cy):
        """Efek jurus. Yang tanpa sprite digambar vektor di satu lapisan transparan, lalu ditempel sekali."""
        if not self.efek:
            return
        self.lapisan.fill((0, 0, 0, 0))
        ada_vektor = False
        for ef in self.efek:
            pudar = max(0.0, 1 - ef.umur / ef.durasi)
            ox, oy = ef.x - cx, ef.y - cy
            if ef.jenis == "circle":
                jari = max(1, int(ef.radius * (1 - pudar)))
                dasar = muat("effects/circle_shockwave")
                if dasar:
                    gambar = skala(dasar[0], (max(2, jari * 2), max(2, jari * 2)))
                    gambar.set_alpha(int(220 * pudar))
                    self.layar.blit(gambar, gambar.get_rect(center=(int(ox), int(oy))))
                else:
                    pygame.draw.circle(self.lapisan, (*ef.warna, int(200 * pudar)), (int(ox), int(oy)), jari, 6)
                    ada_vektor = True
            elif ef.sprite:
                for img, px, py in ef.sprite:
                    img.set_alpha(int(255 * pudar))
                    self.layar.blit(img, img.get_rect(center=(px - cx, py - cy)))
            elif ef.jenis == "triangle":                      # juring (wedge) = persis area yang kena damage
                sisi = [(ox + math.cos(ef.sudut + a) * ef.radius, oy + math.sin(ef.sudut + a) * ef.radius)
                        for a in np.linspace(-ef.setengah, ef.setengah, 12)]
                pygame.draw.polygon(self.lapisan, (*ef.warna, int(160 * pudar)), [(ox, oy)] + sisi)
                ada_vektor = True
            elif ef.jenis == "line":
                ujung = (ox + math.cos(ef.sudut) * ef.panjang, oy + math.sin(ef.sudut) * ef.panjang)
                pygame.draw.line(self.lapisan, (*ef.warna, int(220 * pudar)), (ox, oy), ujung, int(ef.lebar))
                ada_vektor = True
            elif ef.jenis == "zigzag":
                for a, b in ef.garis:
                    pygame.draw.line(self.lapisan, (*ef.warna, int(255 * pudar)), (a[0] - cx, a[1] - cy), (b[0] - cx, b[1] - cy), 3)
                    ada_vektor = True
        if ada_vektor:
            self.layar.blit(self.lapisan, (0, 0))

    # ---------------- HUD & panel kamera ----------------
    def teks(self, isi, ukuran, warna, x, y, tengah=False):
        kunci = (isi, ukuran, warna)
        if kunci not in self.cache_teks:
            if len(self.cache_teks) > 300:
                self.cache_teks.clear()
            self.cache_teks[kunci] = self.font[ukuran].render(isi, True, warna)
        img = self.cache_teks[kunci]
        self.layar.blit(img, (x - img.get_width() // 2 if tengah else x, y))

    def bar(self, x, y, w, h, rasio, latar, isi, tepi=(0, 0, 0)):
        pygame.draw.rect(self.layar, latar, (x, y, w, h))
        pygame.draw.rect(self.layar, isi, (x, y, int(w * max(0, min(1, rasio))), h))
        pygame.draw.rect(self.layar, tepi, (x, y, w, h), width=2)

    def gambar_hud(self):
        p = self.pemain
        self.bar(20, 20, 260, 22, p.hp / p.hp_maks, (60, 20, 20), (220, 40, 40))
        self.teks(f"HP {int(max(0, p.hp))}/{p.hp_maks}", 14, WARNA_TEKS, 28, 24)
        self.bar(20, 48, 260, 14, p.xp / p.xp_perlu, (30, 30, 50), (240, 200, 40))
        self.teks(f"Level {p.level}", 14, WARNA_TEKS, 290, 46)
        menit, detik = divmod(int(self.waktu), 60)
        self.teks(f"{menit:02d}:{detik:02d}", 34, WARNA_TEKS, LEBAR // 2, 16, tengah=True)
        self.teks(f"Kills: {p.kill}", 18, WARNA_REDUP, LEBAR // 2, 54, tengah=True)

        y = TINGGI - 150                                      # daftar jurus + bar cooldown
        for bentuk, j in JURUS.items():
            siap = self.jeda[bentuk] <= 0
            warna = j["warna"] if siap else WARNA_REDUP
            ikon = muat(f"ui/skill_{bentuk}", 20)
            x_teks = 20
            if ikon:
                gambar = ikon[0]
                if not siap:                                  # ikon redup saat cooldown
                    gambar = gambar.copy()
                    gambar.fill((110, 110, 110, 255), special_flags=pygame.BLEND_RGBA_MULT)
                self.layar.blit(gambar, (20, y - 3))
                x_teks = 46
            self.teks(f"[{bentuk.upper():<8}] {j['nama']}", 14, warna, x_teks, y)
            self.bar(430, y + 2, 80, 10, 1 - self.jeda[bentuk] / j["cooldown"], (40, 40, 40), warna)
            y += 22

        kamera = self.kamera
        _, _, pusat, _, _, _ = kamera.ambil()
        if not kamera.ok:
            alasan = f" ({kamera.galat})" if kamera.galat else ""
            status, warna = f"Kamera tidak aktif{alasan} - gestur nonaktif, coba tombol 1-5", (255, 120, 120)
        elif kamera.merekam and pusat is None:
            status, warna = "MEREKAM... tapi sarung tangan hitam TIDAK terlihat (dekatkan / cek cahaya)", (255, 140, 100)
        elif kamera.merekam:
            status, warna = "MEREKAM JURUS... gambar pola dengan sarung tangan hitam di depan kamera", (255, 230, 90)
        else:
            status, warna = "Tahan [SPASI] lalu gambar pola dengan sarung tangan hitam", WARNA_REDUP
        self.teks(status, 14, warna, 20, 80)
        if self.pesan_waktu > 0:
            self.teks(self.pesan_teks, 18, (255, 255, 255), 20, 102)

    def gambar_panel(self):
        """Preview kamera + zona diabaikan (merah) + posisi sarung tangan (hijau) + lintasan gestur (kuning)."""
        kamera = self.kamera
        if not kamera.ok and kamera.frame is None:
            return
        frame, mask, pusat, cahaya, abaikan, rasio = kamera.ambil()
        x, y = LEBAR - PANEL_L - JARAK, TINGGI - PANEL_T - JARAK
        sumber = mask if (self.tampil_mask and mask is not None) else frame
        panel = pygame.Surface((PANEL_L, PANEL_T))
        if sumber is None:
            panel.fill((25, 25, 30))
        else:
            if self.cache_panel is None or self.cache_panel[0] is not sumber:    # konversi hanya saat frame baru
                self.cache_panel = (sumber,) + ke_surface(sumber)
            panel.blit(self.cache_panel[1], (0, 0))
        if abaikan is not None:
            if self.cache_tint is None or self.cache_tint[0] is not abaikan:     # zona merah: buat sekali per kalibrasi
                merah = np.zeros(abaikan.shape + (3,), np.uint8)
                merah[abaikan > 0, 2] = 95                                       # BGR: kanal 2 = merah
                self.cache_tint = (abaikan,) + ke_surface(merah)
            panel.blit(self.cache_tint[1], (0, 0), special_flags=pygame.BLEND_ADD)
        sk_x, sk_y = PANEL_L / gestur.LEBAR, PANEL_T / gestur.TINGGI
        jejak = kamera.jejak()
        if len(jejak) > 1:
            pygame.draw.lines(panel, (255, 230, 60), False, [(a * sk_x, b * sk_y) for a, b in jejak], 4)
        if pusat is not None:
            tengah = (int(pusat[0] * sk_x), int(pusat[1] * sk_y))
            pygame.draw.circle(panel, (60, 255, 120), tengah, 14, 3)
            pygame.draw.circle(panel, (60, 255, 120), tengah, 3)
        pygame.draw.rect(panel, (255, 255, 255), panel.get_rect(), width=2)
        panel.set_alpha(225)
        self.layar.blit(panel, (x, y))
        self.gambar_info_cahaya(x, y, cahaya, rasio)
        if kamera.sedang_kalibrasi():
            self.gambar_banner_kalibrasi(kamera.progres())

    def gambar_info_cahaya(self, x, y, cahaya, rasio):
        atas = y - 98
        latar = pygame.Surface((PANEL_L, 96), pygame.SRCALPHA)
        latar.fill((0, 0, 0, 150))
        self.layar.blit(latar, (x, atas - 4))
        if cahaya is None:
            return self.teks("Pencahayaan: menunggu kamera...", 14, WARNA_REDUP, x + 6, atas)
        level, batas, label, status, saran = cahaya
        warna = {"good": (110, 220, 130), "warn": (240, 190, 70), "bad": (240, 90, 90)}[status]
        self.teks(f"Pencahayaan: {label}", 14, warna, x + 6, atas)
        self.teks(f"level {int(level)}/255", 14, WARNA_REDUP, x + PANEL_L - 100, atas)
        batas_zona = [0, 40, 80, 200, 232, 255]               # gelap | redup | ideal | terang | terlalu terang
        warna_zona = [(150, 45, 45), (190, 130, 40), (50, 160, 85), (140, 185, 70), (190, 60, 55)]
        for i, wz in enumerate(warna_zona):
            x1, x2 = x + batas_zona[i] * PANEL_L // 255, x + batas_zona[i + 1] * PANEL_L // 255
            pygame.draw.rect(self.layar, wz, (x1, atas + 26, max(1, x2 - x1), 12))
        penanda = x + int(max(0, min(255, level)) / 255 * PANEL_L)
        pygame.draw.line(self.layar, (255, 255, 255), (penanda, atas + 23), (penanda, atas + 40), 3)
        self.teks(f"Ambang hitam V<{batas} (auto) | Diabaikan: {int(rasio * 100)}%", 14, WARNA_TEKS, x + 6, atas + 44)
        self.teks(saran, 14, warna, x + 6, atas + 60)
        legenda = "Kalibrasi berjalan..." if self.kamera.mengkalibrasi else "[C] kalibrasi  [M] mask  merah=diabaikan"
        self.teks(legenda, 14, WARNA_REDUP, x + 6, atas + 76)

    def gambar_banner_kalibrasi(self, progres):
        x, y, w, h = LEBAR // 2 - 300, 110, 600, 92
        latar = pygame.Surface((w, h), pygame.SRCALPHA)
        latar.fill((0, 0, 0, 200))
        self.layar.blit(latar, (x, y))
        pygame.draw.rect(self.layar, (255, 230, 90), (x, y, w, h), width=2)
        self.teks("KALIBRASI LATAR (rambut & benda hitam diam)", 18, (255, 230, 90), LEBAR // 2, y + 10, tengah=True)
        self.teks("Duduk diam. Jauhkan sarung tangan dari kamera, atau gerakkan terus.", 14, WARNA_TEKS, LEBAR // 2, y + 38, tengah=True)
        self.bar(x + 20, y + 64, w - 40, 14, progres, (40, 40, 40), (255, 230, 90), tepi=(255, 255, 255))


if __name__ == "__main__":
    Game().jalan()
