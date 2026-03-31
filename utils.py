import pygame
import random
from constants import COLOR_WHITE, COLOR_BLACK

# Font Cache
_font_cache = {}

def get_font(name, size, bold=True):
    key = (name, size, bold)
    if key not in _font_cache:
        try:
            _font_cache[key] = pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            _font_cache[key] = pygame.font.Font(None, size)
    return _font_cache[key]

def draw_text(screen, text, size, x, y, color=COLOR_WHITE, shadow=True, center=True, alpha=255):
    font = get_font("Arial", size, bold=True)

    if shadow:
        shadow_surf = font.render(text, True, COLOR_BLACK)
        if alpha < 255:
            shadow_surf.set_alpha(alpha)
        shadow_rect = shadow_surf.get_rect()
        if center:
            shadow_rect.center = (x + 2, y + 2)
        else:
            shadow_rect.topleft = (x + 2, y + 2)
        screen.blit(shadow_surf, shadow_rect)

    surf = font.render(text, True, color)
    if alpha < 255:
        surf.set_alpha(alpha)
    rect = surf.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surf, rect)

class SoundManager:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SoundManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if not self.initialized:
            self.sounds = {}
            self.music_layers = {
                'base': None,
                'intensity': None,
                'danger': None,
                'chaos': None
            }
            self.current_layers = []
            self.initialized = True

    def play(self, name):
        pass

    def update_music_layers(self, hp_percent):
        pass
