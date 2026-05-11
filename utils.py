import pygame
import random
import math
import array
from constants import COLOR_WHITE, COLOR_BLACK

# ── Font Cache ────────────────────────────────────────────────────────────────
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


# ── Sound Manager ─────────────────────────────────────────────────────────────
class SoundManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SoundManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
        self.initialized = True
        self.sounds = {}
        self.sfx_enabled = True
        self.sfx_volume = 0.75
        self._try_init_sounds()

    def _try_init_sounds(self):
        try:
            if not pygame.mixer.get_init():
                return
            self._init_sounds()
        except Exception as e:
            print(f"[SoundManager] Sound init failed: {e}")

    def _init_sounds(self):
        sr = pygame.mixer.get_init()[0]

        # ── waveform helpers (all return float in ~[-1, 1]) ───────────────────
        def _s(t, f):
            return math.sin(2 * math.pi * f * t)

        def _chirp(t, f0, f1, dur):
            return math.sin(2 * math.pi * (f0 + (f1 - f0) * t / max(dur, 1e-9)) * t)

        def _exp(t, rate):
            return math.exp(-rate * t)

        def _lin(t, dur):
            return max(0.0, 1.0 - t / max(dur, 1e-9))

        def _atk(t, a):
            return min(1.0, t / max(a, 1e-9))

        def _nd():
            return random.random() * 2.0 - 1.0

        # ── sound definitions: (duration_s, generator(t) -> float) ───────────
        defs = {
            # Player movement
            'jump': (
                0.15,
                lambda t: _chirp(t, 300, 650, 0.15) * _lin(t, 0.15)
            ),
            'land': (
                0.10,
                lambda t: _s(t, 150) * _exp(t, 14)
            ),
            'dash': (
                0.12,
                lambda t: _nd() * 0.5 * _exp(t, 20)
            ),
            'super_dash': (
                0.18,
                lambda t: (_nd() * 0.3 + _s(t, 500) * 0.5) * _exp(t, 12)
            ),
            # Shooting
            'shoot': (
                0.07,
                lambda t: _s(t, 900) * _exp(t, 50)
            ),
            'charge_shot': (
                0.28,
                lambda t: _chirp(t, 480, 110, 0.28) * _exp(t, 4)
            ),
            'shoot_spread': (
                0.10,
                lambda t: _s(t, 700) * _exp(t, 35)
            ),
            'shoot_homing': (
                0.22,
                lambda t: _s(t, 500 + 120 * math.sin(2 * math.pi * 6 * t)) * _exp(t, 9)
            ),
            'ex_attack': (
                0.28,
                lambda t: _chirp(t, 480, 180, 0.28) * _exp(t, 6) * 0.7
            ),
            'ultimate': (
                0.70,
                lambda t: (_chirp(t, 100, 350, 0.70) * 0.65 + _nd() * 0.3)
                          * _atk(t, 0.06) * _lin(t, 0.70)
            ),
            'ultimate_attack': (
                0.65,
                lambda t: (_chirp(t, 80, 380, 0.65) * 0.8 + _nd() * 0.35)
                          * _atk(t, 0.04) * _lin(t, 0.65)
            ),
            # Parry & combat
            'parry': (
                0.28,
                lambda t: (_s(t, 880) + 0.4 * _s(t, 1320)) * _lin(t, 0.28) * 0.65
            ),
            'perfect_parry': (
                0.38,
                lambda t: (_s(t, 1100) + 0.4 * _s(t, 1650) + 0.2 * _s(t, 2200))
                          * _lin(t, 0.38) * 0.75
            ),
            'parry_fail': (
                0.15,
                lambda t: _s(t, 120) * _exp(t, 9)
            ),
            'hit': (
                0.22,
                lambda t: (_s(t, 90) + _nd() * 0.25) * _exp(t, 10)
            ),
            # Boss
            'boss_hit': (
                0.13,
                lambda t: _chirp(t, 380, 180, 0.13) * _exp(t, 10) * 0.7
            ),
            'boss_transition': (
                0.65,
                lambda t: (_chirp(t, 200, 500, 0.65) * 0.6 + _nd() * 0.25)
                          * _atk(t, 0.1) * _lin(t, 0.65)
            ),
            'teleport': (
                0.20,
                lambda t: _chirp(t, 300, 1200, 0.20) * _exp(t, 8)
            ),
            'reality_break': (
                0.40,
                lambda t: (_s(t, 200 + 40 * math.sin(2 * math.pi * 18 * t)) * 0.7
                           + _nd() * 0.2)
                          * _atk(t, 0.08) * _lin(t, 0.40)
            ),
        }

        for name, (dur, gen) in defs.items():
            try:
                n = int(sr * dur)
                buf = array.array('h', [0] * (n * 2))
                for i in range(n):
                    t = i / sr
                    v = max(-1.0, min(1.0, gen(t)))
                    sv = int(v * 28000)
                    buf[i * 2]     = sv
                    buf[i * 2 + 1] = sv
                self.sounds[name] = pygame.mixer.Sound(buffer=buf)
            except Exception as e:
                print(f"[SoundManager] Failed to generate '{name}': {e}")

    def play(self, name, volume=1.0):
        if not self.sfx_enabled:
            return
        sound = self.sounds.get(name)
        if sound:
            sound.set_volume(max(0.0, min(1.0, volume * self.sfx_volume)))
            sound.play()

    def update_music_layers(self, hp_percent):
        pass
