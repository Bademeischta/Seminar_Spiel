import pygame
from constants import WHITE, BLACK

def draw_text(screen, text, size, x, y, color=WHITE, shadow=True, center=True):
    font = pygame.font.SysFont("Arial", size, bold=True)

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

class SpriteLoader:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SpriteLoader, cls).__new__(cls)
            cls._instance.sprites = {}
        return cls._instance

    def get_sprite(self, path, scale=1.0):
        key = (path, scale)
        if key not in self.sprites:
            try:
                img = pygame.image.load(path).convert_alpha()
                if scale != 1.0:
                    w, h = img.get_size()
                    img = pygame.transform.scale(img, (int(w * scale), int(h * scale)))
                self.sprites[key] = img
            except Exception as e:
                print(f"Error loading sprite {path}: {e}")
                # Return placeholder
                surf = pygame.Surface((50, 50))
                surf.fill((255, 0, 255))
                self.sprites[key] = surf
        return self.sprites[key]

class SoundManager:
    def __init__(self):
        self.sounds = {}
        # pygame.mixer.init() # Already initialized by pygame.init() usually

    def play(self, name):
        # Placeholder for real sound playing
        # print(f"Playing sound: {name}")
        pass

    def play_beep(self, freq, duration):
        # Could implement actual beeps if needed
        pass
