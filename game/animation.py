class Animation:
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
