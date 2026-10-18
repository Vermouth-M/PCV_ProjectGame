"""
gestur.py -- kamera, pelacak sarung tangan hitam, dan pengenal bentuk (OpenCV murni).

Alur singkat:
  1. Kamera dibaca di thread terpisah supaya game tidak lag.
  2. Setiap frame dicari gumpalan HITAM terbesar (= sarung tangan).
  3. Saat SPASI ditahan, posisi sarung tangan direkam jadi daftar titik.
  4. klasifikasi(titik) mengubah titik itu jadi nama bentuk.
"""

import math
import threading
import time

import cv2
import numpy as np

LEBAR, TINGGI = 320, 240          # resolusi kerja pelacakan
KERNEL = np.ones((5, 5), np.uint8)


# ======================================================================
# PENGENAL BENTUK
# ======================================================================
def haluskan(titik):
    """Redam getaran centroid (kalau titik rapat), lalu ratakan jarak antar titik (8 px)."""
    p = np.array(titik, dtype=np.float32)
    jarak = np.hypot(*np.diff(p, axis=0).T)
    if np.median(jarak) < 6:                              # titik rapat -> rata-rata bergerak
        k = min(5, len(p) | 1)
        pad = np.pad(p, ((k // 2, k // 2), (0, 0)), mode="edge")
        p = np.stack([np.convolve(pad[:, i], np.ones(k) / k, mode="valid") for i in (0, 1)], axis=1)
        jarak = np.hypot(*np.diff(p, axis=0).T)
    total = np.concatenate([[0.0], np.cumsum(jarak)])
    if total[-1] < 1e-3:
        return p
    t = np.linspace(0, total[-1], max(8, int(total[-1] / 8)))
    return np.stack([np.interp(t, total, p[:, 0]), np.interp(t, total, p[:, 1])], axis=1).astype(np.float32)


def klasifikasi(titik):
    """Return 'triangle', 'circle', 'square', 'line', 'zigzag', atau 'unknown'."""
    if len(titik) < 8:
        return "unknown"
    p = haluskan(titik)
    lebar, tinggi = p.max(axis=0) - p.min(axis=0)
    panjang = float(np.hypot(*np.diff(p, axis=0).T).sum())
    if max(lebar, tinggi) < 30 or panjang < 1e-3:
        return "unknown"
    ujung = float(np.linalg.norm(p[-1] - p[0]))
    if ujung / panjang < 0.35:                            # awal & akhir berdekatan = tertutup
        return bentuk_tertutup(p)
    return bentuk_terbuka(p, lebar, tinggi)


def bentuk_tertutup(p):
    hull = cv2.convexHull(p.reshape(-1, 1, 2))
    keliling = cv2.arcLength(hull, True)
    if keliling <= 0:
        return "unknown"
    sudut = len(cv2.approxPolyDP(hull, 0.03 * keliling, True))
    bulat = 4 * math.pi * cv2.contourArea(hull) / keliling ** 2    # 1.0 = lingkaran sempurna
    if sudut == 3:
        return "triangle"
    if sudut == 4:
        return "square"
    if bulat > 0.75 or sudut >= 5:
        return "circle"
    return "unknown"


def bentuk_terbuka(p, lebar, tinggi):
    x, y = (p[:, 0], p[:, 1]) if lebar >= tinggi else (p[:, 1], p[:, 0])
    selisih = y - np.polyval(np.polyfit(x, y, 1), x)
    lurus = math.sqrt(float(np.mean(selisih ** 2))) / max(lebar, tinggi, 1.0)
    if putar_balik(p) >= 2:                               # banyak belokan tajam = zigzag
        return "zigzag"
    return "line" if lurus < 0.12 else "unknown"


def putar_balik(p):
    """Berapa kali arah gerak berbelok lebih dari 55 derajat."""
    v = [p[i + 2] - p[i] for i in range(0, len(p) - 2, 2)]
    v = [a for a in v if np.linalg.norm(a) > 1e-3]
    hitung = 0
    for a, b in zip(v, v[1:]):
        sudut = math.atan2(abs(a[0] * b[1] - a[1] * b[0]), a[0] * b[0] + a[1] * b[1])
        hitung += sudut > math.radians(55)
    return hitung


def arah(titik):
    """Arah umum lintasan (vektor satuan dari titik awal ke akhir); default ke kanan."""
    if len(titik) < 2:
        return (1.0, 0.0)
    dx, dy = titik[-1][0] - titik[0][0], titik[-1][1] - titik[0][1]
    panjang = math.hypot(dx, dy)
    return (dx / panjang, dy / panjang) if panjang > 1e-3 else (1.0, 0.0)


# ======================================================================
# PENCAHAYAAN: ambang "hitam" menyesuaikan kecerahan ruangan
# ======================================================================
def ambang_hitam(level):
    return int(round(min(95, max(28, 0.38 * level + 12))))


def info_cahaya(level):
    """(label, status, saran). status: good / warn / bad (untuk warna teks)."""
    if level < 40:
        return "Terlalu gelap", "bad", "Nyalakan lampu / pindah ke tempat terang"
    if level < 80:
        return "Redup", "warn", "Tambah cahaya agar lebih akurat"
    if level <= 200:
        return "Ideal", "good", "Pencahayaan bagus, ambang otomatis"
    if level <= 232:
        return "Terang", "good", "Cukup terang, ambang otomatis"
    return "Terlalu terang", "bad", "Kurangi cahaya ke kamera / jauhi jendela"


# ======================================================================
# KAMERA + PELACAK
# ======================================================================
class Kamera:
    def __init__(self, indeks=0):
        self.indeks, self.cap, self.thread = indeks, None, None
        self.ok = False                  # True selama kamera masih mengirim gambar
        self.galat = ""                  # alasan kalau kamera berhenti
        self.kunci = threading.Lock()    # melindungi semua data di bawah (dipakai 2 thread)
        self.jalan = False
        self.frame = self.mask = self.pusat = self.cahaya = None
        self.level, self.jumlah_frame = None, 0
        self.pusat_lama, self.waktu_lama = None, 0.0
        self.merekam, self.titik, self.t_rekam = False, [], 0.0
        self.mengkalibrasi, self.hitungan, self.n_kalib, self.t_kalib = False, None, 0, 0.0
        self.abaikan, self.rasio_abaikan = None, 0.0     # zona hitam diam (rambut dkk)

    # ---------------- hidup-mati kamera ----------------
    def mulai(self):
        try:
            self.cap = cv2.VideoCapture(self.indeks)
        except cv2.error:
            self.cap = None
        if self.cap is None or not self.cap.isOpened():
            return False
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.ok = self.jalan = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        return True

    def berhenti(self):
        self.jalan = False
        if self.thread is not None:
            self.thread.join(timeout=1.0)
        if self.cap is not None:
            self.cap.release()

    def _loop(self):
        terakhir = time.time()
        try:
            while self.jalan:
                berhasil, frame = self.cap.read()
                if not berhasil:
                    if time.time() - terakhir > 2:
                        self.ok, self.galat = False, "kamera berhenti mengirim gambar"
                        return
                    time.sleep(0.01)
                    continue
                terakhir = time.time()
                self.proses(cv2.flip(frame, 1))          # flip = seperti cermin
        except Exception as e:                           # jangan mati diam-diam
            self.ok, self.galat = False, f"error di thread kamera: {e}"

    # ---------------- pemrosesan satu frame ----------------
    def proses(self, frame):
        """Cari sarung tangan di satu frame BGR. Return posisinya (x, y) atau None."""
        kecil = cv2.resize(frame, (LEBAR, TINGGI), interpolation=cv2.INTER_AREA)
        hsv = cv2.cvtColor(cv2.GaussianBlur(kecil, (7, 7), 0), cv2.COLOR_BGR2HSV)
        sekarang = float(np.percentile(hsv[::4, ::4, 2], 75))     # kecerahan ruangan

        with self.kunci:
            self.level = sekarang if self.level is None else self.level + 0.15 * (sekarang - self.level)
            batas = ambang_hitam(self.level)
            mask = cv2.inRange(hsv, np.array([0, 0, 0], np.uint8), np.array([179, 255, batas], np.uint8))
            mask = cv2.dilate(cv2.erode(mask, KERNEL), KERNEL, iterations=2)
            self.jumlah_frame += 1

            pusat = None
            if self.mengkalibrasi:
                if self.jumlah_frame > 20:                       # 20 frame awal: kamera masih menyesuaikan
                    self._pelajari(mask)
            else:
                if self.abaikan is not None:
                    mask = cv2.bitwise_and(mask, cv2.bitwise_not(self.abaikan))
                pusat = self._cari_sarung(mask)

            if self.merekam and pusat is not None and time.time() - self.t_rekam <= 4.0:
                if not self.titik or math.hypot(pusat[0] - self.titik[-1][0], pusat[1] - self.titik[-1][1]) >= 3:
                    self.titik.append(pusat)

            label, status, saran = info_cahaya(self.level)
            self.frame, self.mask, self.pusat = frame, mask, pusat
            self.cahaya = (self.level, batas, label, status, saran)
        return pusat

    def _cari_sarung(self, mask):
        kontur, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        kandidat = []
        for c in kontur:
            luas = cv2.contourArea(c)
            if luas < 800 or luas > 0.25 * LEBAR * TINGGI:       # terlalu kecil (noise) / terlalu besar
                continue
            hull = cv2.contourArea(cv2.convexHull(c))
            if hull > 0 and luas / hull >= 0.55:                 # bentuk harus cukup padat
                kandidat.append((luas, c))
        if not kandidat:
            return None

        kandidat.sort(key=lambda k: k[0], reverse=True)
        terpilih = kandidat[0][1]
        baru = self.pusat_lama is not None and time.time() - self.waktu_lama <= 0.5
        if baru and len(kandidat) > 1:                           # utamakan yang dekat posisi terakhir
            sepadan = [c for luas, c in kandidat if luas >= kandidat[0][0] * 0.4]
            terpilih = min(sepadan, key=lambda c: math.dist(self._tengah(c), self.pusat_lama))
        pusat = self._tengah(terpilih)
        self.pusat_lama, self.waktu_lama = pusat, time.time()
        return pusat

    @staticmethod
    def _tengah(kontur):
        m = cv2.moments(kontur)
        return (int(m["m10"] / m["m00"]), int(m["m01"] / m["m00"]))

    # ---------------- kalibrasi: pelajari rambut / benda hitam yang DIAM ----------------
    def kalibrasi(self):
        if not self.ok:
            return False
        with self.kunci:
            self.mengkalibrasi, self.hitungan, self.n_kalib = True, None, 0
            self.t_kalib, self.abaikan, self.rasio_abaikan = time.time(), None, 0.0
        return True

    def _pelajari(self, mask):
        hitam = (mask > 0).astype(np.float32)
        self.hitungan = hitam if self.hitungan is None else self.hitungan + hitam
        self.n_kalib += 1
        if self.n_kalib >= 45:
            self._selesai_kalibrasi()

    def _selesai_kalibrasi(self):
        diam = ((self.hitungan / self.n_kalib) >= 0.7).astype(np.uint8) * 255   # hitam di >=70% frame
        diam = cv2.morphologyEx(diam, cv2.MORPH_OPEN, KERNEL)
        diam = cv2.dilate(diam, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
        self.abaikan = diam
        self.rasio_abaikan = float(np.count_nonzero(diam)) / diam.size
        self.mengkalibrasi, self.hitungan = False, None

    def sedang_kalibrasi(self):
        with self.kunci:
            if self.mengkalibrasi and not self.ok:
                self.mengkalibrasi = False                       # kamera mati: jangan bekukan game
            elif self.mengkalibrasi and time.time() - self.t_kalib > 8.0:
                if self.n_kalib >= 15:
                    self._selesai_kalibrasi()
                else:
                    self.mengkalibrasi, self.hitungan = False, None
            return self.mengkalibrasi

    def progres(self):
        with self.kunci:
            if self.mengkalibrasi:
                return min(1.0, self.n_kalib / 45)
            return 1.0 if self.abaikan is not None else 0.0

    # ---------------- rekam lintasan gestur ----------------
    def mulai_rekam(self):
        with self.kunci:
            self.merekam, self.titik, self.t_rekam = True, [], time.time()

    def selesai_rekam(self):
        with self.kunci:
            hasil, self.titik, self.merekam = list(self.titik), [], False
        return hasil

    def rekam_habis(self):
        with self.kunci:
            return self.merekam and time.time() - self.t_rekam > 4.0

    def jejak(self):
        with self.kunci:
            return list(self.titik)

    def ambil(self):
        """(frame, mask, posisi sarung tangan, info cahaya, zona diabaikan, % diabaikan) untuk digambar."""
        with self.kunci:
            return self.frame, self.mask, self.pusat, self.cahaya, self.abaikan, self.rasio_abaikan
