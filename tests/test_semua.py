"""
tests/test_semua.py -- satu file tes untuk versi ringkas. Tanpa webcam, tanpa jendela.

Kalau pygame tidak terpasang, dipakai pygame palsu (MagicMock): cukup untuk menguji SEMUA logika
dan memastikan kode menggambar tidak error, tapi tampilan aslinya tetap harus dilihat langsung.

Jalankan:   python tests/test_semua.py
"""

import math
import os
import random
import sys
import threading
import time
import types

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

try:
    import pygame  # noqa: E402
    PYGAME_ASLI = True
except ModuleNotFoundError:
    from unittest.mock import MagicMock
    pygame = MagicMock(name="pygame")
    for i, nama in enumerate(["K_a", "K_d", "K_w", "K_s", "K_SPACE", "K_ESCAPE", "K_c", "K_m", "K_r",
                              "K_1", "K_2", "K_3", "K_4", "K_5", "QUIT", "KEYDOWN", "KEYUP"]):
        setattr(pygame, nama, i + 1)
    pygame.error = Exception
    sys.modules["pygame"] = pygame
    PYGAME_ASLI = False

import gestur  # noqa: E402
import main  # noqa: E402

HASIL = []


def cek(nama, ok, info=""):
    HASIL.append(ok)
    print(f"[{'OK' if ok else 'GAGAL'}] {nama} {info}")


# ======================================================================
# 1. PENGENAL BENTUK
# ======================================================================
def jalur(sudut, n):
    return [sudut(i / n) for i in range(n + 1)]


def poligon(sudut_pojok, n=40):
    titik = []
    for a, b in zip(sudut_pojok, sudut_pojok[1:]):
        titik += [(a[0] + (b[0] - a[0]) * t / n, a[1] + (b[1] - a[1]) * t / n) for t in range(n)]
    return titik


BENTUK = {
    "line": lambda: [(40 + 200 * i / 120, 120 + 10 * i / 120) for i in range(121)],
    "circle": lambda: [(160 + 60 * math.cos(2 * math.pi * i / 150), 120 + 60 * math.sin(2 * math.pi * i / 150)) for i in range(151)],
    "square": lambda: poligon([(110, 70), (210, 70), (210, 170), (110, 170), (110, 70)]),
    "triangle": lambda: poligon([(160, 60), (110, 170), (210, 170), (160, 60)]),
}


def zigzag_rapat(n=30, dx=40, dy=45, segmen=5):
    titik, x, y = [], 40, 120
    for i in range(segmen):
        ty = 120 + (dy if i % 2 == 0 else -dy)
        titik += [(x + dx * t / n, y + (ty - y) * t / n) for t in range(n)]
        x, y = x + dx, ty
    return titik


BENTUK["zigzag"] = zigzag_rapat


def rekam(titik):
    """Meniru perekaman asli: titik yang < 3 px dari titik sebelumnya dibuang."""
    hasil = []
    for p in titik:
        if not hasil or math.hypot(p[0] - hasil[-1][0], p[1] - hasil[-1][1]) >= 3:
            hasil.append(p)
    return hasil


def tes_bentuk():
    for nama, buat in BENTUK.items():
        got = gestur.klasifikasi(rekam(buat()))
        cek(f"bentuk '{nama}' dikenali", got == nama, f"(hasil '{got}')")

    rng = np.random.default_rng(11)
    for sigma in (1.5, 2.0):
        for nama, buat in BENTUK.items():
            benar = 0
            for _ in range(100):
                mentah = [(x + rng.normal(0, sigma), y + rng.normal(0, sigma)) for x, y in buat()]
                benar += gestur.klasifikasi(rekam(mentah)) == nama
            cek(f"'{nama}' tetap dikenali saat getaran {sigma}px", benar >= 90, f"({benar}%)")

    cek("lintasan kosong -> unknown", gestur.klasifikasi([]) == "unknown")
    cek("semua titik sama -> unknown", gestur.klasifikasi([(5, 5)] * 20) == "unknown")
    cek("gerakan kecil diabaikan", gestur.klasifikasi([(100 + i * 0.5, 100) for i in range(30)]) == "unknown")
    garis = BENTUK["line"]()
    cek("garis pergi-pulang bukan garis", gestur.klasifikasi(rekam(garis + garis[::-1])) == "unknown")
    cek("arah() kosong -> kanan", gestur.arah([]) == (1.0, 0.0))
    d = gestur.arah([(0, 0), (0, 50)])
    cek("arah() ke bawah", abs(d[0]) < 1e-9 and abs(d[1] - 1) < 1e-9)


# ======================================================================
# 2. PELACAKAN SARUNG TANGAN (adegan sintetis)
# ======================================================================
RNG = np.random.default_rng(7)


def adegan(dinding, sarung=None, rambut=True):
    f = np.full((240, 320, 3), int(dinding), np.uint8)
    cv2.ellipse(f, (160, 80), (45, 55), 0, 0, 360, (int(dinding * 0.78),) * 3, -1)        # wajah
    if rambut:
        cv2.ellipse(f, (160, 32), (62, 36), 0, 0, 360, (int(0.22 * dinding + 8),) * 3, -1)
    if sarung is not None:
        cv2.circle(f, sarung, 22, (int(0.24 * dinding + 10),) * 3, -1)
    return np.clip(f + RNG.normal(0, 2.0, f.shape), 0, 255).astype(np.uint8)


def kamera_siap(dinding=140):
    k = gestur.Kamera()
    k.ok = True
    for _ in range(25):                                   # lewati 20 frame pemanasan
        k.proses(adegan(dinding, rambut=False))
    return k


def kalibrasi_dengan_sarung_bergerak(k, dinding):
    k.kalibrasi()
    for i in range(45):
        k.proses(adegan(dinding, sarung=(60 + 4 * i, 170 - i)))


def dekat(a, b, toleransi=6):
    return a is not None and abs(a[0] - b[0]) <= toleransi and abs(a[1] - b[1]) <= toleransi


def tes_pelacakan():
    levels = [gestur.info_cahaya(x)[0] for x in (25, 60, 140, 215, 245)]
    cek("label cahaya", levels == ["Terlalu gelap", "Redup", "Ideal", "Terang", "Terlalu terang"], str(levels))
    batas = [gestur.ambang_hitam(x) for x in (0, 40, 80, 140, 200, 250)]
    cek("ambang hitam naik & dibatasi 28..95", batas == sorted(batas) and batas[0] == 28 and batas[-1] == 95, str(batas))

    for dinding in (50, 100, 190, 250):
        k = gestur.Kamera()
        pusat = None
        for _ in range(8):
            pusat = k.proses(adegan(dinding, sarung=(250, 150), rambut=False))
        cek(f"sarung tangan terdeteksi (dinding={dinding})", dekat(pusat, (250, 150)), str(pusat))

    k = kamera_siap()
    pusat = k.proses(adegan(140, sarung=(250, 150)))
    cek("SEBELUM kalibrasi rambut ikut terbaca (alasan kalibrasi ada)", pusat is not None and pusat[1] < 80, str(pusat))

    k = kamera_siap()
    kalibrasi_dengan_sarung_bergerak(k, 140)
    cek("kalibrasi selesai", not k.sedang_kalibrasi() and k.abaikan is not None)
    cek("zona diabaikan wajar (5-40%)", 0.05 < k.rasio_abaikan < 0.4, f"({k.rasio_abaikan:.0%})")
    cek("SETELAH kalibrasi: sarung tangan dipilih, bukan rambut", dekat(k.proses(adegan(140, sarung=(250, 150))), (250, 150)))
    cek("hanya rambut -> tidak ada deteksi", k.proses(adegan(140)) is None)

    k = gestur.Kamera()
    k.ok = True
    k.kalibrasi()
    k.t_kalib -= 9                                        # seolah sudah 9 detik
    cek("kalibrasi macet dibatalkan (game tidak beku)", k.sedang_kalibrasi() is False)

    k = kamera_siap()
    k.kalibrasi()
    k.ok = False
    cek("kamera mati saat kalibrasi -> kalibrasi berhenti", k.sedang_kalibrasi() is False)

    # dari gambar -> lintasan -> bentuk (uji ujung ke ujung)
    k = kamera_siap()
    kalibrasi_dengan_sarung_bergerak(k, 140)
    k.mulai_rekam()
    for i in range(40):
        k.proses(adegan(140, sarung=(60 + 5 * i, 150)))
    titik = k.selesai_rekam()
    cek("merekam garis dari gambar sintetis", gestur.klasifikasi(titik) == "line", f"({len(titik)} titik)")
    cek("selesai_rekam menghentikan rekaman", not k.merekam and k.jejak() == [])


class CapPalsu:
    def __init__(self, hasil):
        self.hasil = hasil

    def read(self):
        return self.hasil

    def release(self):
        pass


def tes_ketahanan_kamera():
    k = gestur.Kamera()
    k.cap, k.ok, k.jalan = CapPalsu((False, None)), True, True
    t = threading.Thread(target=k._loop, daemon=True)
    t.start()
    t.join(timeout=4)
    cek("kamera putus -> ok jadi False + ada alasan", k.ok is False and "berhenti" in k.galat, f"('{k.galat}')")

    k = gestur.Kamera()
    k.cap, k.ok, k.jalan = CapPalsu((True, object())), True, True       # frame rusak -> exception di thread
    t = threading.Thread(target=k._loop, daemon=True)
    t.start()
    t.join(timeout=2)
    cek("exception di thread tidak diam-diam: ok False + alasan", k.ok is False and k.galat.startswith("error"), f"('{k.galat[:40]}')")


# ======================================================================
# 3. GAME
# ======================================================================
class KameraPalsu:
    """Pengganti gestur.Kamera supaya Game bisa diuji tanpa webcam."""

    def __init__(self):
        self.ok, self.galat, self.merekam, self.mengkalibrasi, self.habis = True, "", False, False, False
        self.titik, self.frame, self.mask, self.abaikan = [], None, None, None
        self.n_kalibrasi = 0

    def mulai(self): return True
    def kalibrasi(self): self.n_kalibrasi += 1; self.mengkalibrasi = True; return True
    def sedang_kalibrasi(self): return self.mengkalibrasi
    def progres(self): return 0.5
    def mulai_rekam(self): self.merekam, self.titik = True, []
    def rekam_habis(self): return self.habis and self.merekam
    def jejak(self): return list(self.titik)
    def berhenti(self): pass

    def selesai_rekam(self):
        self.merekam = False
        hasil, self.titik = self.titik, []
        return hasil

    def ambil(self):
        return self.frame, self.mask, (100, 100), (140.0, 65, "Ideal", "good", "Pencahayaan bagus"), self.abaikan, 0.1


class Tombol(dict):
    def __missing__(self, kunci):
        return False


def game_baru():
    random.seed(4)
    g = main.Game(kamera=KameraPalsu())
    g.kamera.mengkalibrasi, g.kamera.n_kalibrasi = False, 0      # abaikan kalibrasi otomatis saat start
    return g


def acara(tipe, tombol=None):
    return types.SimpleNamespace(type=tipe, key=tombol)


def kirim(g, *daftar):
    """Kirim event ke Game; return hasil tangani_input()."""
    asli = pygame.event.get
    pygame.event.get = lambda: list(daftar)
    try:
        return g.tangani_input()
    finally:
        pygame.event.get = asli


def tahan(*tombol):
    asli = pygame.key.get_pressed
    pygame.key.get_pressed = lambda: Tombol({t: True for t in tombol})
    return asli


def musuh_di(g, x, y, jenis="basic", hp=None):
    s = main.MUSUH[jenis]
    m = main.Benda(jenis=jenis, x=x, y=y, radius=s["radius"], hp=hp or s["hp"], hp_maks=hp or s["hp"],
                   kecepatan=s["kecepatan"], damage=s["damage"], xp=s["xp"], warna=s["warna"],
                   kx=0.0, ky=0.0, kilat=0.0, kiri=False, t=0.0, gambar=[])
    g.musuh.append(m)
    return m


def tes_pemain_dan_xp():
    g = game_baru()
    p = g.pemain
    m = musuh_di(g, 0, 0)
    g.tabrakan()
    cek("kena musuh: HP berkurang", p.hp == p.hp_maks - m.damage)
    g.tabrakan()
    cek("i-frame: tidak kena lagi seketika", p.hp == p.hp_maks - m.damage)
    p.kebal = 0
    g.tabrakan()
    cek("i-frame habis: bisa kena lagi", p.hp == p.hp_maks - 2 * m.damage)
    hp = p.hp
    p.kebal, p.perisai = 0, 2.0
    g.tabrakan()
    cek("perisai memblokir damage", p.hp == hp)

    g = game_baru()
    g.tambah_xp(main.XP_AWAL)
    cek("XP cukup -> naik level, HP penuh", g.pemain.level == 2 and g.pemain.xp == 0 and g.pemain.hp == g.pemain.hp_maks)
    g = game_baru()
    g.tambah_xp(500)
    cek("XP besar -> naik beberapa level tanpa macet", g.pemain.level > 3)

    g = game_baru()
    p = g.pemain
    p.hp, p.xp = 3, p.xp_perlu - 1
    musuh_di(g, 0, 0, "tank")
    g.orb.append(main.Benda(x=0, y=0, nilai=10, t=0.0))
    g.tabrakan()
    g.bersihkan()
    cek("BUG LAMA: hit mematikan + orb level-up TIDAK menghidupkan lagi", p.hp <= 0 and p.level == 1, f"(HP {p.hp})")

    g = game_baru()
    asli = tahan(main.pygame.K_d)
    try:
        g.gerak_pemain(1.0, pygame.key.get_pressed())
    finally:
        pygame.key.get_pressed = asli
    cek("gerak kanan 1 detik = kecepatan pemain", abs(g.pemain.x - main.PEMAIN["kecepatan"]) < 1e-6 and not g.pemain.kiri)
    g = game_baru()
    asli = tahan(main.pygame.K_d, main.pygame.K_w)
    try:
        g.gerak_pemain(1.0, pygame.key.get_pressed())
    finally:
        pygame.key.get_pressed = asli
    cek("diagonal tidak lebih cepat", abs(math.hypot(g.pemain.x, g.pemain.y) - main.PEMAIN["kecepatan"]) < 1e-6)


def tes_musuh_dan_spawn():
    g = game_baru()
    m = musuh_di(g, 100, 0)
    g.gerak_musuh(m, 1.0)
    cek("musuh bergerak mendekati pemain", m.x < 100)

    def jarak_dorong(fps):
        g = game_baru()
        m = musuh_di(g, 0, 0)
        m.kecepatan, m.kx = 0, 260.0
        for _ in range(int(fps * 3)):
            g.gerak_musuh(m, 1.0 / fps)
        return m.x
    d30, d60, d144 = jarak_dorong(30), jarak_dorong(60), jarak_dorong(144)
    cek("BUG LAMA: knockback sama di 30/60/144 FPS", abs(d30 - d60) / d60 < 0.1 and abs(d144 - d60) / d60 < 0.1,
        f"({d30:.0f}/{d60:.0f}/{d144:.0f}px)")

    g = game_baru()
    g.waktu = 100
    terlihat = 0
    for _ in range(3000):
        g.musuh.clear()
        g.timer_muncul = 0
        g.munculkan(0.016)
        e = g.musuh[0]
        if abs(e.x) < main.LEBAR / 2 + e.radius and abs(e.y) < main.TINGGI / 2 + e.radius:
            terlihat += 1
    cek("BUG LAMA: musuh tidak pernah muncul di dalam layar", terlihat == 0, f"({terlihat}/3000 terlihat)")

    g = game_baru()
    for jenis in ("basic",) * main.MUSUH_MAKS:
        musuh_di(g, 9999, 9999, jenis)
    g.timer_muncul = 0
    g.munculkan(1.0)
    cek("batas musuh maksimum dihormati", len(g.musuh) == main.MUSUH_MAKS)

    g = game_baru()
    jenis_awal = set()
    for _ in range(200):
        g.musuh.clear(); g.timer_muncul = 0; g.munculkan(0.1); jenis_awal.add(g.musuh[0].jenis)
    g.waktu = 61
    jenis_lanjut = set()
    for _ in range(300):
        g.musuh.clear(); g.timer_muncul = 0; g.munculkan(0.1); jenis_lanjut.add(g.musuh[0].jenis)
    cek("awal hanya 'basic'; setelah 60 dtk semua tipe", jenis_awal == {"basic"} and jenis_lanjut == {"basic", "fast", "tank"})

    g = game_baru()
    g.waktu = 0
    g.timer_muncul = 0
    g.munculkan(0.1)
    sebelum = g.timer_muncul
    g.waktu = 10 ** 6
    g.timer_muncul = 0
    g.munculkan(0.1)
    cek("interval spawn mengecil tapi ada batas minimum", g.timer_muncul < sebelum and abs(g.timer_muncul - main.MUNCUL_CEPAT) < 1e-9)

    g = game_baru()
    musuh_di(g, 100, 0)
    g.serang_otomatis()
    cek("auto-attack menembak musuh dalam jangkauan", len(g.peluru) == 1 and g.pemain.jeda_serang > 0)
    g = game_baru()
    musuh_di(g, 900, 0)
    g.serang_otomatis()
    cek("auto-attack tidak menembak musuh terlalu jauh", len(g.peluru) == 0)
    g = game_baru()
    musuh_di(g, 0, 0)
    g.serang_otomatis()
    cek("auto-attack aman saat musuh tepat di posisi pemain (tanpa bagi nol)", len(g.peluru) == 1)

    g = game_baru()
    m = musuh_di(g, 100, 0)
    g.serang_otomatis()
    b = g.peluru[0]
    b.x, b.y = m.x, m.y
    g.tabrakan()
    cek("peluru mengenai musuh: damage masuk, peluru hilang", m.hp == m.hp_maks - main.PEMAIN["damage"] and b.umur == 0)

    g = game_baru()
    m = musuh_di(g, 500, 0, hp=1)
    m.hp = 0
    g.bersihkan()
    cek("musuh mati -> jadi orb + kill bertambah", len(g.orb) == 1 and g.pemain.kill == 1 and not g.musuh)
    g.orb[0].x = g.orb[0].y = 0
    g.bersihkan()
    cek("orb di dekat pemain diambil jadi XP", not g.orb and g.pemain.xp == main.MUSUH["basic"]["xp"])
    o = main.Benda(x=60, y=0, nilai=5, t=0.0)
    g.tarik_orb(o, 0.1)
    cek("orb dalam radius magnet ditarik mendekat", o.x < 60)
    o = main.Benda(x=300, y=0, nilai=5, t=0.0)
    g.tarik_orb(o, 0.1)
    cek("orb di luar radius magnet diam", o.x == 300)


def tes_jurus():
    g = game_baru()
    d = musuh_di(g, 95, 0)
    b = musuh_di(g, -50, 0)
    g.pakai_jurus("triangle", g.pemain.hadap)
    cek("segitiga: kena di depan (dalam gambar), tidak kena di belakang", d.hp < d.hp_maks and b.hp == b.hp_maks)

    g = game_baru()
    g.pemain.hadap = (0.0, 1.0)
    s = musuh_di(g, 0, 90)
    sisi = musuh_di(g, 90, 0)
    g.pakai_jurus("triangle", g.pemain.hadap)
    cek("segitiga mengikuti arah hadap", s.hp < s.hp_maks and sisi.hp == sisi.hp_maks)

    g = game_baru()
    m = musuh_di(g, 80, 0)
    g.pakai_jurus("circle", (1, 0))
    cek("lingkaran: damage + terpental menjauh", m.hp < m.hp_maks and m.kx > 0)
    hp = m.hp
    g.pakai_jurus("circle", (1, 0))
    cek("jurus cooldown tidak terpicu ulang", m.hp == hp and "cooldown" in g.pesan_teks)
    g.jeda["circle"] = 0
    g.pakai_jurus("circle", (1, 0))
    cek("setelah cooldown bisa dipakai lagi", m.hp < hp)

    g = game_baru()
    g.pakai_jurus("ngawur", (1, 0))
    cek("pola tak dikenal: pesan + tanpa cooldown", all(v == 0 for v in g.jeda.values()) and "tidak dikenali" in g.pesan_teks)

    g = game_baru()
    g.pakai_jurus("square", (1, 0))
    cek("kotak mengaktifkan perisai sesuai durasi", g.pemain.perisai == main.JURUS["square"]["durasi"])

    g = game_baru()
    depan, belakang, jauh, samping = musuh_di(g, 200, 5), musuh_di(g, -50, 0), musuh_di(g, 500, 0), musuh_di(g, 200, 100)
    g.pakai_jurus("line", (1.0, 0.0))
    cek("garis: kena di depan; tidak kena belakang/terlalu jauh/samping",
        depan.hp < depan.hp_maks and all(m.hp == m.hp_maks for m in (belakang, jauh, samping)))
    g = game_baru()
    bawah = musuh_di(g, 0, 200)
    g.pakai_jurus("line", (0.0, 1.0))
    cek("garis mengikuti arah gestur", bawah.hp < bawah.hp_maks)

    g = game_baru()
    rantai = [musuh_di(g, 60 * (i + 1), 0) for i in range(8)]
    g.pakai_jurus("zigzag", (1, 0))
    kena = sum(m.hp < m.hp_maks for m in rantai)
    cek("zigzag melompat maksimal 5 musuh", kena == main.JURUS["zigzag"]["rantai"], f"(kena {kena})")
    g = game_baru()
    g.pakai_jurus("zigzag", (1, 0))
    cek("zigzag tanpa musuh tidak error", True)
    g = game_baru()
    jauh = musuh_di(g, 900, 0)
    g.pakai_jurus("zigzag", (1, 0))
    cek("zigzag tidak menjangkau musuh di luar radius rantai", jauh.hp == jauh.hp_maks)

    g = game_baru()
    g.state = "selesai"
    g.pakai_jurus("square", (1, 0))
    cek("BUG LAMA: jurus tidak bisa dipakai saat game over", g.pemain.perisai == 0 and g.jeda["square"] == 0)


def tes_input_dan_alur():
    g = game_baru()
    kirim(g, acara(pygame.KEYDOWN, pygame.K_SPACE))
    cek("SPASI ditekan -> mulai merekam", g.tahan_spasi and g.kamera.merekam)
    g.kamera.titik = rekam(BENTUK["circle"]())
    kirim(g, acara(pygame.KEYUP, pygame.K_SPACE))
    cek("SPASI dilepas -> bentuk dikenali, jurus keluar", not g.tahan_spasi and g.jeda["circle"] > 0 and "Lingkaran" in g.pesan_teks)

    g = game_baru()
    g.kamera.mengkalibrasi = True
    kirim(g, acara(pygame.KEYDOWN, pygame.K_SPACE))
    cek("SPASI diabaikan saat kalibrasi", not g.tahan_spasi)

    g = game_baru()
    kirim(g, acara(pygame.KEYDOWN, pygame.K_c))
    cek("C = kalibrasi ulang", g.kamera.n_kalibrasi == 1)
    g.kamera.mengkalibrasi = False
    kirim(g, acara(pygame.KEYDOWN, pygame.K_SPACE), acara(pygame.KEYDOWN, pygame.K_c))
    cek("C diabaikan saat SPASI ditahan", g.kamera.n_kalibrasi == 1)

    g = game_baru()
    kirim(g, acara(pygame.KEYDOWN, pygame.K_m))
    cek("M menyalakan mask", g.tampil_mask)
    kirim(g, acara(pygame.KEYDOWN, pygame.K_2))
    cek("tombol 2 memicu jurus lingkaran tanpa kamera", g.jeda["circle"] > 0)
    cek("ESC = keluar", kirim(g, acara(pygame.KEYDOWN, pygame.K_ESCAPE)) is False)
    cek("tutup jendela = keluar", kirim(g, acara(pygame.QUIT)) is False)

    g = game_baru()
    g.state = "selesai"
    kirim(g, acara(pygame.KEYDOWN, pygame.K_1))
    cek("BUG LAMA: tombol 1-5 mati saat game over", g.jeda["triangle"] == 0)
    kirim(g, acara(pygame.KEYDOWN, pygame.K_r))
    cek("R saat game over -> main lagi", g.state == "main")

    g = game_baru()
    kirim(g, acara(pygame.KEYDOWN, pygame.K_r))
    cek("R saat masih main diabaikan", g.state == "main" and g.pemain.kill == 0 and g.waktu == 0)

    g = game_baru()
    kirim(g, acara(pygame.KEYDOWN, pygame.K_SPACE))
    g.pemain.hp = 0
    g.update(0.016)
    cek("mati saat merekam: rekaman dibatalkan, state selesai", g.state == "selesai" and not g.kamera.merekam and not g.tahan_spasi)
    kirim(g, acara(pygame.KEYDOWN, pygame.K_SPACE), acara(pygame.KEYDOWN, pygame.K_r))
    cek("BUG LAMA: restart tidak meninggalkan slow-mo/rekaman", g.state == "main" and not g.tahan_spasi and not g.kamera.merekam)

    g = game_baru()
    g.kamera.mulai_rekam()
    g.kamera.habis = True
    g.tahan_spasi = True
    g.kamera.titik = rekam(BENTUK["square"]())
    asli = tahan()
    try:
        g.update(0.016)
    finally:
        pygame.key.get_pressed = asli
    cek("waktu rekam habis -> jurus otomatis keluar", not g.tahan_spasi and g.jeda["square"] > 0)


def tes_waktu_dan_slowmo():
    def maju(g, dt, detik=1.0):
        asli = tahan()
        try:
            for _ in range(int(detik / dt)):
                g.update(dt)
        finally:
            pygame.key.get_pressed = asli

    g = game_baru()
    m = musuh_di(g, 400, 0)
    g.timer_muncul = 999
    maju(g, 0.01)
    normal = 400 - m.x
    g = game_baru()
    m = musuh_di(g, 400, 0)
    g.timer_muncul = 999
    g.kamera.mulai_rekam()
    maju(g, 0.01)
    lambat = 400 - m.x
    cek("saat menggambar musuh melambat ke 35%", abs(lambat / normal - main.SLOWMO_MENGGAMBAR) < 0.05, f"({lambat / normal:.2f})")

    g = game_baru()
    m = musuh_di(g, 400, 0)
    g.kamera.mengkalibrasi = True
    maju(g, 0.01)
    cek("saat kalibrasi dunia beku & timer tidak jalan", m.x == 400 and g.waktu == 0)

    g = game_baru()
    g.timer_muncul = 999
    g.kamera.mulai_rekam()
    maju(g, 0.01)
    cek("timer HUD memakai waktu nyata walau slow-mo", abs(g.waktu - 1.0) < 0.02, f"({g.waktu:.2f})")

    g = game_baru()
    g.pemain.hp = 1
    musuh_di(g, 0, 0)
    maju(g, 0.016, 0.2)
    cek("HP habis -> game over", g.state == "selesai")


def tes_jalan_dan_dt():
    """jalan(): dt dibatasi 0.05 walau satu frame berlangsung 5 detik."""
    g = game_baru()
    g.timer_muncul = 999
    urutan = [[], [acara(pygame.QUIT)]]
    asli_event, asli_tick, asli_quit = pygame.event.get, g.jam.tick, pygame.quit
    asli_keys = tahan()
    pygame.event.get = lambda: urutan.pop(0)
    g.jam = types.SimpleNamespace(tick=lambda fps: 5000)
    pygame.quit = lambda: None
    try:
        g.jalan()
    finally:
        pygame.event.get, pygame.quit, pygame.key.get_pressed = asli_event, asli_quit, asli_keys
    cek("lag 5 detik hanya dihitung 0.05 detik (dt dibatasi)", g.waktu <= 0.05 + 1e-9, f"(waktu {g.waktu:.3f})")


def tes_smoke():
    """Jalankan ratusan frame penuh (update + gambar + input acak + gestur) -> tidak boleh error."""
    random.seed(9)
    g = game_baru()
    g.kamera.frame = np.zeros((480, 640, 3), np.uint8)
    g.kamera.mask = np.zeros((240, 320), np.uint8)
    g.kamera.abaikan = np.zeros((240, 320), np.uint8)
    g.kamera.abaikan[:50] = 255
    semua = [pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s]
    galat = None
    try:
        for frame in range(1500):
            asli = tahan(*[k for k in semua if random.random() < 0.4])
            try:
                if frame % 40 == 0:
                    kirim(g, acara(pygame.KEYDOWN, random.choice([pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5])))
                if frame % 97 == 0:
                    kirim(g, acara(pygame.KEYDOWN, pygame.K_SPACE))
                    g.kamera.titik = rekam(BENTUK[random.choice(list(BENTUK))]())
                if frame % 97 == 30:
                    kirim(g, acara(pygame.KEYUP, pygame.K_SPACE))
                if frame % 300 == 150:
                    kirim(g, acara(pygame.KEYDOWN, pygame.K_m))
                g.kamera.mengkalibrasi = 200 < frame < 215
                if g.state == "main":
                    g.update(1 / 60)
                else:
                    kirim(g, acara(pygame.KEYDOWN, pygame.K_r))
                g.gambar()
            finally:
                pygame.key.get_pressed = asli
    except Exception as e:                                    # noqa: BLE001
        galat = f"frame {frame}: {type(e).__name__}: {e}"
    cek("smoke test: 1500 frame update+gambar tanpa error", galat is None, galat or "")
    cek("invarian: musuh <= batas, HP <= HP maks", len(g.musuh) <= main.MUSUH_MAKS and g.pemain.hp <= g.pemain.hp_maks)


def main_tes():
    print(f"(pygame: {'ASLI' if PYGAME_ASLI else 'PALSU/MagicMock -- tampilan asli tidak diuji'})\n")
    for fn in (tes_bentuk, tes_pelacakan, tes_ketahanan_kamera, tes_pemain_dan_xp, tes_musuh_dan_spawn,
               tes_jurus, tes_input_dan_alur, tes_waktu_dan_slowmo, tes_jalan_dan_dt, tes_smoke):
        print(f"\n== {fn.__name__}")
        fn()
    lolos = sum(HASIL)
    print(f"\n{lolos}/{len(HASIL)} pemeriksaan lolos.")
    sys.exit(0 if lolos == len(HASIL) else 1)


if __name__ == "__main__":
    main_tes()
