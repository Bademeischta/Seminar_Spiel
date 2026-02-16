import pygame
import random
from constants import WHITE, BLACK

def draw_text(screen, text, size, x, y, color=WHITE, shadow=True, center=True):
    try:
        font = pygame.font.SysFont("Arial", size, bold=True)
    except:
        font = pygame.font.Font(None, size)

    if shadow:
        shadow_surf = font.render(text, True, BLACK)
        shadow_rect = shadow_surf.get_rect()
        if center:
            shadow_rect.center = (x + 2, y + 2)
        else:
            shadow_rect.topleft = (x + 2, y + 2)
        screen.blit(shadow_surf, shadow_rect)

    surf = font.render(text, True, color)
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
            print("SoundManager initialized (Placeholder Mode)")

    def play(self, name):
        # Placeholder for real sound playing
        # print(f"Playing sound: {name}")
        pass

    def update_music_layers(self, hp_percent):
        # Logic to crossfade layers based on HP
        pass
