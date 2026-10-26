import pygame

import config
from game import assets


def draw_background(surface, cam_x, cam_y):
    """Tile `assets/backgrounds/ground.*` bila ada; kalau tidak, grid vektor."""
    tile = assets.get().image("backgrounds/ground", scale=config.BACKGROUND_TILE_SCALE)
    if tile is None:
        _draw_grid(surface, cam_x, cam_y)
        return

    tw, th = tile.get_size()
    w, h = surface.get_size()
    start_x = (-int(cam_x)) % tw - tw
    start_y = (-int(cam_y)) % th - th
    for y in range(start_y, h, th):
        for x in range(start_x, w, tw):
            surface.blit(tile, (x, y))


def _draw_grid(surface, cam_x, cam_y):
    spacing = 64
    w, h = surface.get_size()
    start_x = -int(cam_x) % spacing
    start_y = -int(cam_y) % spacing
    for x in range(start_x, w, spacing):
        pygame.draw.line(surface, config.COLOR_GRID, (x, 0), (x, h))
    for y in range(start_y, h, spacing):
        pygame.draw.line(surface, config.COLOR_GRID, (0, y), (w, y))
