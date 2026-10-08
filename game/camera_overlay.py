"""game/camera_overlay.py -- menampilkan preview kamera + lintasan gestur di HUD."""

import cv2
import numpy as np
import pygame

import config


def cv2_frame_to_surface(frame):
    """
    Konversi frame OpenCV (BGR, array [y][x]) jadi pygame.Surface.

    pygame.surfarray memakai indeks [x][y], sedangkan OpenCV [y][x], jadi
    cukup menukar sumbu 0 dan 1 (transpose). Jangan ditambah rot90/flip:
    itu membuat gambar terputar 180 derajat (terbalik).
    """
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    rgb = np.ascontiguousarray(rgb.swapaxes(0, 1))
    return pygame.surfarray.make_surface(rgb)


def draw_camera_panel(target_surface, frame, mask, points, panel_size=None):
    """
    Gambar panel preview kamera di pojok kanan-bawah layar berisi:
    - feed kamera (ukuran diatur di config.CAMERA_PANEL_WIDTH/HEIGHT)
    - lintasan tangan yang sedang/baru saja digambar (garis kuning)

    `points` ada dalam koordinat resolusi kerja tracking
    (config.GESTURE_PROCESS_WIDTH x HEIGHT), jadi diskalakan ke ukuran panel.
    """
    if panel_size is None:
        panel_size = (config.CAMERA_PANEL_WIDTH, config.CAMERA_PANEL_HEIGHT)
    pw, ph = panel_size
    margin = config.CAMERA_PANEL_MARGIN
    x0 = target_surface.get_width() - pw - margin
    y0 = target_surface.get_height() - ph - margin

    panel = pygame.Surface((pw, ph))
    if frame is not None:
        cam_surf = cv2_frame_to_surface(frame)
        cam_surf = pygame.transform.smoothscale(cam_surf, (pw, ph))
        panel.blit(cam_surf, (0, 0))
    else:
        panel.fill((25, 25, 30))

    if points and len(points) > 1:
        sx = pw / config.GESTURE_PROCESS_WIDTH
        sy = ph / config.GESTURE_PROCESS_HEIGHT
        scaled = [(px * sx, py * sy) for (px, py) in points]
        pygame.draw.lines(panel, (255, 230, 60), False, scaled, 4)

    pygame.draw.rect(panel, (255, 255, 255), panel.get_rect(), width=2)
    panel.set_alpha(config.CAMERA_PANEL_ALPHA)
    target_surface.blit(panel, (x0, y0))
