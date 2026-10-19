"""game/screens/base.py -- kelas dasar semua layar menu."""


class Screen:
    """
    Antarmuka layar. Game (engine) memanggil metode ini sesuai state aktif.
    State "playing" ditangani langsung oleh engine, bukan lewat kelas ini.
    """

    # True = dunia game digambar dulu di belakang layar ini (jeda, game over)
    overlay = False

    def __init__(self, game):
        self.game = game

    def on_enter(self):
        """Dipanggil saat layar ini menjadi aktif."""

    def on_exit(self):
        """Dipanggil saat layar ini ditinggalkan."""

    def handle_event(self, event):
        """Terima satu event pygame."""

    def update(self, dt):
        """Perbarui animasi/logika layar (dt dalam detik)."""

    def draw(self, surface):
        """Gambar layar."""
