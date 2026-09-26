"""game/camera_overlay.py -- menampilkan preview kamera kecil + lintasan gestur di HUD."""

import cv2
import numpy as np
import pygame

import config


def cv2_frame_to_surface(frame):
    """Konversi frame OpenCV (BGR, HxWx3) jadi pygame.Surface."""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    rgb = np.rot90(rgb)
    surface = pygame.surfarray.make_surface(rgb)
    surface = pygame.transform.flip(surface, False, True)
    return surface


def draw_camera_panel(target_surface, frame, mask, points, panel_size=(200, 150)):
    """
    Gambar panel kecil di pojok kanan-bawah layar berisi:
    - feed kamera (kecil)
    - lintasan tangan yang sedang/baru saja digambar (garis kuning)
    """
    pw, ph = panel_size
    x0 = target_surface.get_width() - pw - 16
    y0 = target_surface.get_height() - ph - 16

    panel = pygame.Surface((pw, ph))
    if frame is not None:
        cam_surf = cv2_frame_to_surface(frame)
        cam_surf = pygame.transform.smoothscale(cam_surf, (pw, ph))
        panel.blit(cam_surf, (0, 0))
    else:
        panel.fill((25, 25, 30))

    if points and len(points) > 1:
        fh, fw = frame.shape[:2] if frame is not None else (config.CAMERA_CAPTURE_HEIGHT, config.CAMERA_CAPTURE_WIDTH)
        scaled = [(px * pw / fw, py * ph / fh) for (px, py) in points]
        pygame.draw.lines(panel, (255, 230, 60), False, scaled, 3)

    pygame.draw.rect(panel, (255, 255, 255), panel.get_rect(), width=2)
    target_surface.blit(panel, (x0, y0))
