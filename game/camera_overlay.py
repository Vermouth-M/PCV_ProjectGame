"""game/camera_overlay.py -- preview kamera + lintasan gestur + penanda tracking di HUD."""

import cv2
import numpy as np
import pygame

import config


def get_panel_rect(target_surface):
    """Posisi panel kamera (pojok kanan-bawah). Dipakai juga oleh HUD untuk menaruh bar cahaya."""
    pw, ph = config.CAMERA_PANEL_WIDTH, config.CAMERA_PANEL_HEIGHT
    return pygame.Rect(
        target_surface.get_width() - pw - config.CAMERA_PANEL_MARGIN,
        target_surface.get_height() - ph - config.CAMERA_PANEL_MARGIN,
        pw, ph,
    )


def _array_to_surface(rgb):
    """Array [y][x][3] (OpenCV) -> pygame.Surface. pygame berindeks [x][y], cukup transpose."""
    return pygame.surfarray.make_surface(np.ascontiguousarray(rgb.swapaxes(0, 1)))


def cv2_frame_to_surface(frame):
    """
    Konversi frame OpenCV (BGR) jadi pygame.Surface. Jangan ditambah rot90/flip:
    itu membuat gambar terputar 180 derajat (terbalik).
    """
    return _array_to_surface(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))


def draw_camera_panel(target_surface, frame, mask, points, centroid=None,
                      exclusion=None, show_mask=False):
    """
    Panel preview kamera di pojok kanan-bawah, berisi:
    - feed kamera (atau mask hitam kalau show_mask=True, tombol M)
    - zona yang DIABAIKAN (rambut dkk) berwarna merah, hasil kalibrasi
    - lingkaran hijau = posisi sarung tangan yang sedang terdeteksi
    - garis kuning = lintasan gestur yang sedang direkam

    `points`/`centroid`/`mask`/`exclusion` ada dalam koordinat resolusi kerja
    tracking (config.GESTURE_PROCESS_WIDTH x HEIGHT) dan diskalakan ke panel.
    """
    rect = get_panel_rect(target_surface)
    pw, ph = rect.size
    sx = pw / config.GESTURE_PROCESS_WIDTH
    sy = ph / config.GESTURE_PROCESS_HEIGHT

    panel = pygame.Surface((pw, ph))
    if show_mask and mask is not None:
        base = _array_to_surface(cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB))
        panel.blit(pygame.transform.scale(base, (pw, ph)), (0, 0))
    elif frame is not None:
        panel.blit(pygame.transform.smoothscale(cv2_frame_to_surface(frame), (pw, ph)), (0, 0))
    else:
        panel.fill((25, 25, 30))

    if exclusion is not None:
        tint = np.zeros(exclusion.shape + (3,), np.uint8)
        tint[:, :, 0] = np.where(exclusion > 0, 95, 0)
        tint_surf = pygame.transform.scale(_array_to_surface(tint), (pw, ph))
        panel.blit(tint_surf, (0, 0), special_flags=pygame.BLEND_ADD)

    if points and len(points) > 1:
        scaled = [(px * sx, py * sy) for (px, py) in points]
        pygame.draw.lines(panel, (255, 230, 60), False, scaled, 4)

    if centroid is not None:
        cx, cy = int(centroid[0] * sx), int(centroid[1] * sy)
        pygame.draw.circle(panel, (60, 255, 120), (cx, cy), 14, 3)
        pygame.draw.circle(panel, (60, 255, 120), (cx, cy), 3)

    pygame.draw.rect(panel, (255, 255, 255), panel.get_rect(), width=2)
    panel.set_alpha(config.CAMERA_PANEL_ALPHA)
    target_surface.blit(panel, rect.topleft)
