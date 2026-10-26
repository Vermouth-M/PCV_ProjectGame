"""game/layout.py -- posisi & ukuran semua kotak UI."""

import pygame

import config

GAME_RECT = pygame.Rect(0, 0, config.GAME_AREA_WIDTH, config.SCREEN_HEIGHT)
SIDEBAR_RECT = pygame.Rect(config.GAME_AREA_WIDTH, 0,
                           config.SCREEN_WIDTH - config.GAME_AREA_WIDTH, config.SCREEN_HEIGHT)

_pad = config.UI_PAD
_frame = config.UI_FRAME
_x = SIDEBAR_RECT.left + _pad
_inner_w = SIDEBAR_RECT.width - 2 * _pad

# baris atas: health (kiri) + potret (kanan)
HEALTH = pygame.Rect(_x, _pad, config.UI_HEALTH_WIDTH, config.UI_TOP_ROW_HEIGHT)
PORTRAIT = pygame.Rect(HEALTH.right + _pad, _pad,
                       _inner_w - config.UI_HEALTH_WIDTH - _pad, config.UI_TOP_ROW_HEIGHT)

# webcam di bawah; tinggi mengikuti rasio 4:3 supaya gambar tidak gepeng
_video_w = _inner_w - 2 * _frame
_video_h = _video_w * 3 // 4
_webcam_h = _video_h + 2 * _frame
WEBCAM = pygame.Rect(_x, config.SCREEN_HEIGHT - _pad - _webcam_h, _inner_w, _webcam_h)
WEBCAM_VIDEO = WEBCAM.inflate(-2 * _frame, -2 * _frame)

# skill mengisi ruang di antara baris atas dan webcam
SKILLS = pygame.Rect(_x, HEALTH.bottom + _pad, _inner_w,
                     WEBCAM.top - _pad - (HEALTH.bottom + _pad))