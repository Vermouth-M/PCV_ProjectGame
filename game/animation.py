"""game/animation.py -- animasi sprite sederhana (frame bergantian menurut waktu)."""


class Animation:
    """
    frames : list pygame.Surface (boleh kosong = tidak ada aset -> pemanggil pakai vektor)
    fps    : frame per detik
    offset : geser waktu awal, supaya banyak musuh tidak bergerak serempak
    """

    def __init__(self, frames, fps=8, offset=0.0):
        self.frames = list(frames)
        self.fps = max(0.001, float(fps))
        self.time = float(offset)

    def update(self, dt):
        self.time += dt

    @property
    def frame(self):
        if not self.frames:
            return None
        return self.frames[int(self.time * self.fps) % len(self.frames)]

    def __bool__(self):
        return bool(self.frames)
