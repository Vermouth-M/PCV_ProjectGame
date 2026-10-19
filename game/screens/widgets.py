"""
game/screens/widgets.py
=========================
Komponen UI bersama untuk layar menu:
  - get_font / draw_text / fill_rounded / dim : helper gambar
  - draw_shape_icon                           : ikon bentuk jurus (vektor)
  - MenuItem / Menu                           : daftar pilihan (keyboard + mouse)

Kontrol Menu:  W/S atau panah atas/bawah = pilih,  Enter / klik = jalankan,
               A/D atau panah kiri/kanan = ubah nilai (untuk baris pengaturan).
"""

import math

import pygame

import config

ACCENT = (255, 210, 90)
TEXT = config.COLOR_TEXT
DIM = config.COLOR_TEXT_DIM
GOOD = (110, 220, 130)
WARN = (240, 190, 70)
BAD = (240, 90, 90)
DISABLED = (90, 90, 100)

_FONTS = {}


def get_font(size, bold=False):
    if not pygame.font.get_init():
        pygame.font.init()
        _FONTS.clear()
    key = (size, bold)
    if key not in _FONTS:
        _FONTS[key] = pygame.font.SysFont("consolas", size, bold=bold)
    return _FONTS[key]


def draw_text(surface, text, size, color, pos, anchor="topleft", bold=False, shadow=False):
    """Gambar teks; `anchor` = nama atribut Rect (topleft, center, midtop, midleft, midright, ...)."""
    font = get_font(size, bold)
    img = font.render(text, True, color)
    rect = img.get_rect(**{anchor: pos})
    if shadow:
        surface.blit(font.render(text, True, (0, 0, 0)), rect.move(2, 2))
    surface.blit(img, rect)
    return rect


def wrap_text(text, size, max_width, bold=False):
    """Pecah teks menjadi beberapa baris agar tiap baris muat dalam max_width piksel."""
    font = get_font(size, bold)
    lines, current = [], ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if current and font.size(trial)[0] > max_width:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    return lines


def fill_rounded(surface, rect, rgba, radius=10, border=None, border_width=2):
    layer = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(layer, rgba, layer.get_rect(), border_radius=radius)
    if border is not None:
        pygame.draw.rect(layer, border, layer.get_rect(), width=border_width, border_radius=radius)
    surface.blit(layer, rect.topleft)


def dim(surface, alpha=150):
    layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    layer.fill((0, 0, 0, alpha))
    surface.blit(layer, (0, 0))


# ----------------------------------------------------------------------
# Ikon bentuk jurus
# ----------------------------------------------------------------------
def shape_points(kind, center, size, angle=0.0):
    """Titik garis/poligon untuk ikon bentuk (None untuk lingkaran/tidak dikenal)."""
    cx, cy = center
    r = size / 2
    if kind == "triangle":
        pts = [(0, -r), (r * 0.95, r * 0.8), (-r * 0.95, r * 0.8)]
    elif kind == "square":
        pts = [(-r * 0.8, -r * 0.8), (r * 0.8, -r * 0.8), (r * 0.8, r * 0.8), (-r * 0.8, r * 0.8)]
    elif kind == "line":
        pts = [(-r, r * 0.6), (r, -r * 0.6)]
    elif kind == "zigzag":
        pts = [(-r, r * 0.5), (-r * 0.5, -r * 0.5), (0, r * 0.5), (r * 0.5, -r * 0.5), (r, r * 0.5)]
    else:
        return None
    ca, sa = math.cos(angle), math.sin(angle)
    return [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]


def draw_shape_icon(surface, kind, center, size, color, width=3, angle=0.0):
    if kind == "circle":
        pygame.draw.circle(surface, color, (int(center[0]), int(center[1])), int(size / 2), width)
        return
    pts = shape_points(kind, center, size, angle)
    if pts is not None:
        pygame.draw.lines(surface, color, kind in ("triangle", "square"), pts, width)


# ----------------------------------------------------------------------
# Menu
# ----------------------------------------------------------------------
class MenuItem:
    """
    label    : teks (str) atau fungsi yang mengembalikan teks
    action   : dipanggil saat Enter / klik
    value    : fungsi yang mengembalikan teks nilai -> baris "label ....... < nilai >" (pengaturan)
    on_left / on_right : dipanggil saat panah kiri/kanan (A/D)
    enabled  : bool atau fungsi bool
    """

    def __init__(self, label, action=None, value=None, on_left=None, on_right=None, enabled=True):
        self.label = label
        self.action = action
        self.value = value
        self.on_left = on_left
        self.on_right = on_right
        self.enabled = enabled

    def text(self):
        return self.label() if callable(self.label) else self.label

    def value_text(self):
        return self.value() if callable(self.value) else None

    def is_enabled(self):
        return self.enabled() if callable(self.enabled) else bool(self.enabled)


class Menu:
    def __init__(self, items, center_x, top, row_w=460, row_h=48, gap=10, font_size=26):
        self.items = items
        self.font_size = font_size
        self.rects = [
            pygame.Rect(center_x - row_w // 2, top + i * (row_h + gap), row_w, row_h)
            for i in range(len(items))
        ]
        self.index = self._next_enabled(-1, +1)

    # --- navigasi ---
    def _next_enabled(self, start, delta):
        n = len(self.items)
        for k in range(1, n + 1):
            i = (start + delta * k) % n
            if self.items[i].is_enabled():
                return i
        return max(0, min(start, n - 1))

    def _hit(self, pos):
        for i, rect in enumerate(self.rects):
            if rect.collidepoint(pos):
                return i
        return None

    @property
    def selected(self):
        return self.items[self.index]

    def activate(self):
        item = self.selected
        if item.is_enabled() and item.action:
            item.action()

    def _call(self, name):
        item = self.selected
        fn = getattr(item, name)
        if item.is_enabled() and fn:
            fn()

    def handle_event(self, event):
        """Return True kalau event dipakai menu."""
        if event.type == pygame.KEYDOWN:
            key = event.key
            if key in (pygame.K_UP, pygame.K_w):
                self.index = self._next_enabled(self.index, -1)
                return True
            if key in (pygame.K_DOWN, pygame.K_s):
                self.index = self._next_enabled(self.index, +1)
                return True
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.activate()
                return True
            if key in (pygame.K_LEFT, pygame.K_a):
                self._call("on_left")
                return True
            if key in (pygame.K_RIGHT, pygame.K_d):
                self._call("on_right")
                return True
        elif event.type == pygame.MOUSEMOTION:
            i = self._hit(event.pos)
            if i is not None and self.items[i].is_enabled():
                self.index = i
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            i = self._hit(event.pos)
            if i is not None and self.items[i].is_enabled():
                self.index = i
                self.activate()
                return True
        return False

    # --- gambar ---
    def draw(self, surface):
        size = self.font_size
        for i, (item, rect) in enumerate(zip(self.items, self.rects)):
            enabled = item.is_enabled()
            selected = enabled and i == self.index

            if selected:
                fill_rounded(surface, rect, (255, 210, 90, 46), 12, border=ACCENT)
            else:
                fill_rounded(surface, rect, (0, 0, 0, 95), 12)
            color = ACCENT if selected else (TEXT if enabled else DISABLED)

            value = item.value_text()
            cy = rect.centery
            if value is None:
                draw_text(surface, item.text(), size, color, rect.center, anchor="center", bold=selected)
                if selected:
                    x = rect.x + 16
                    pygame.draw.polygon(surface, ACCENT, [(x, cy - 7), (x, cy + 7), (x + 12, cy)])
            else:
                draw_text(surface, item.text(), size - 4, color, (rect.x + 22, cy), anchor="midleft")
                vr = draw_text(surface, value, size - 4, ACCENT if selected else TEXT,
                               (rect.right - 44, cy), anchor="midright", bold=True)
                if selected:
                    lx, rx = vr.left - 22, rect.right - 34
                    pygame.draw.polygon(surface, ACCENT, [(lx, cy), (lx + 9, cy - 7), (lx + 9, cy + 7)])
                    pygame.draw.polygon(surface, ACCENT, [(rx + 9, cy), (rx, cy - 7), (rx, cy + 7)])
