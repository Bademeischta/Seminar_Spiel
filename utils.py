import pygame
import random
import os
import struct
import math
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

def _make_beep(freq=440, duration=0.08, volume=0.25, sample_rate=22050):
    """Generate a short sine-wave beep as a pygame.Sound (no file needed)."""
    num_samples = int(sample_rate * duration)
    buf = bytearray(num_samples * 2)  # 16-bit mono
    for i in range(num_samples):
        fade = 1.0 - (i / num_samples)  # linear fade-out
        val = int(math.sin(2 * math.pi * freq * i / sample_rate) * 32767 * volume * fade)
        val = max(-32768, min(32767, val))
        struct.pack_into('<h', buf, i * 2, val)
    sound = pygame.sndarray.make_sound(
        pygame.surfarray.map_array(
            pygame.Surface((1, 1)),  # dummy – only used for type
            [[0]]
        )
    ) if False else None  # bypass – use mixer.Sound from buffer directly
    try:
        import numpy as np
        arr = np.frombuffer(bytes(buf), dtype=np.int16)
        sound = pygame.sndarray.make_sound(arr)
    except (ImportError, Exception):
        # numpy not available or mixer not initialized – return None silently
        sound = None
    return sound


_FALLBACK_FREQS = {
    'jump':            523,
    'land':            220,
    'shoot':           660,
    'charge_shot':     880,
    'shoot_spread':    700,
    'shoot_homing':    740,
    'ex_attack':       440,
    'ultimate':        330,
    'hit':             180,
    'parry':           880,
    'perfect_parry':  1047,
    'parry_fail':      200,
    'dash':            600,
    'super_dash':      800,
    'boss_hit':        300,
    'boss_transition': 200,
    'teleport':        550,
    'reality_break':   150,
    'ultimate_attack': 120,
}


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
            self.master_volume = 0.7
            self._sounds_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 'sounds')
            self._mixer_ok = False
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
                self._mixer_ok = True
            except Exception:
                pass
            self.initialized = True

    def _load(self, name):
        """Load sound from file or synthesise a fallback beep."""
        if name in self.sounds:
            return self.sounds[name]
        if not self._mixer_ok:
            self.sounds[name] = None
            return None

        # Try wav / ogg in sounds/ directory
        for ext in ('wav', 'ogg', 'mp3'):
            path = os.path.join(self._sounds_dir, f'{name}.{ext}')
            if os.path.exists(path):
                try:
                    snd = pygame.mixer.Sound(path)
                    self.sounds[name] = snd
                    return snd
                except Exception:
                    pass

        # Synthesise fallback
        freq = _FALLBACK_FREQS.get(name, 440)
        snd = _make_beep(freq)
        self.sounds[name] = snd
        return snd

    def play(self, name, volume=1.0):
        snd = self._load(name)
        if snd is None:
            return
        try:
            snd.set_volume(max(0.0, min(1.0, volume * self.master_volume)))
            snd.play()
        except Exception:
            pass

    def update_music_layers(self, hp_percent):
        """Adjust music intensity based on boss HP percentage (0.0–1.0)."""
        if not self._mixer_ok:
            return
        # Layer volumes keyed by HP thresholds
        # base: always on; intensity: < 70%; danger: < 30%; chaos: < 10%
        layer_map = [
            ('base',      1.0),
            ('intensity', 1.0 if hp_percent < 0.70 else 0.0),
            ('danger',    1.0 if hp_percent < 0.30 else 0.0),
            ('chaos',     1.0 if hp_percent < 0.10 else 0.0),
        ]
        for layer_name, vol in layer_map:
            snd = self._load(f'music_{layer_name}')
            if snd is None:
                continue
            try:
                snd.set_volume(vol * self.master_volume)
                if vol > 0 and not pygame.mixer.get_busy():
                    snd.play(loops=-1)
            except Exception:
                pass
