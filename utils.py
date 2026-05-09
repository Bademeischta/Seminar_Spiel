import pygame
import random
import math
import array as _array
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
            self._mixer_ok = self._init_mixer()
            self.sounds = {}
            self.music_layers = {
                'base': None,
                'intensity': None,
                'danger': None,
                'chaos': None,
            }
            self.current_layers = []
            self.initialized = True
            if self._mixer_ok:
                self._generate_placeholders()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, name, path):
        """Load a sound file and register it under *name*."""
        if not self._mixer_ok:
            return
        try:
            self.sounds[name] = pygame.mixer.Sound(path)
        except Exception as e:
            print(f"Sound '{name}' nicht geladen: {e}")

    def play(self, name, volume=1.0):
        """Play a previously loaded or generated sound by name."""
        if not self._mixer_ok:
            return
        snd = self.sounds.get(name)
        if snd is not None:
            snd.set_volume(max(0.0, min(1.0, volume)))
            snd.play()

    def update_music_layers(self, hp_percent):
        pass  # reserved for dynamic music layer system

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _init_mixer():
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            return True
        except Exception as e:
            print(f"pygame.mixer konnte nicht initialisiert werden: {e}")
            return False

    def _make_tone(self, freq, duration, volume=0.45, wave='sine',
                   freq_end=None, attack=0.01, decay=0.1):
        """Return a pygame.mixer.Sound generated from raw PCM data.

        freq      – start frequency in Hz
        freq_end  – end frequency for a linear sweep (None = no sweep)
        attack    – fraction of duration spent fading in
        decay     – fraction of duration spent fading out at the end
        wave      – 'sine' | 'square' | 'noise'
        """
        sample_rate = 44100
        n = int(sample_rate * duration)
        buf = _array.array('h', [0] * (n * 2))  # stereo 16-bit

        for i in range(n):
            t = i / sample_rate
            progress = i / n

            # Optional frequency sweep
            f = freq if freq_end is None else freq + (freq_end - freq) * progress

            # Waveform
            if wave == 'sine':
                raw = math.sin(2 * math.pi * f * t)
            elif wave == 'square':
                raw = 1.0 if math.sin(2 * math.pi * f * t) >= 0 else -1.0
            else:  # noise
                raw = random.uniform(-1.0, 1.0)

            # Amplitude envelope: linear attack + exponential decay
            if progress < attack:
                env = progress / attack
            elif progress > (1.0 - decay):
                env = (1.0 - progress) / decay
            else:
                env = 1.0

            val = int(raw * env * volume * 32767)
            buf[i * 2] = val      # left channel
            buf[i * 2 + 1] = val  # right channel

        return pygame.mixer.Sound(buffer=buf)

    def _generate_placeholders(self):
        """Create simple synthesised placeholder sounds for every game event."""
        # (freq_start, freq_end_or_None, duration, volume, wave, attack, decay)
        defs = {
            # Player locomotion
            'jump':          (330, 660,  0.18, 0.40, 'sine',   0.01, 0.30),
            'land':          (180, 90,   0.12, 0.50, 'sine',   0.01, 0.60),
            'dash':          (400, 200,  0.12, 0.45, 'square', 0.01, 0.50),
            'super_dash':    (600, 250,  0.20, 0.55, 'square', 0.01, 0.40),
            # Weapons
            'shoot':         (900, None, 0.06, 0.30, 'sine',   0.01, 0.70),
            'charge_shot':   (500, 1200, 0.22, 0.50, 'sine',   0.05, 0.40),
            'shoot_spread':  (750, 500,  0.10, 0.35, 'sine',   0.01, 0.60),
            'shoot_homing':  (600, 900,  0.14, 0.35, 'sine',   0.02, 0.50),
            'ultimate':      (120, 60,   0.55, 0.65, 'square', 0.03, 0.35),
            'ex_attack':     (350, 700,  0.30, 0.55, 'square', 0.02, 0.40),
            # Parry
            'parry':         (880, 1100, 0.18, 0.55, 'sine',   0.01, 0.45),
            'perfect_parry': (1100, 1760, 0.30, 0.60, 'sine',  0.01, 0.35),
            'parry_fail':    (200, 100,  0.25, 0.55, 'square', 0.02, 0.40),
            # Damage / reaction
            'hit':           (300, None, 0.20, 0.55, 'noise',  0.01, 0.50),
            # Boss
            'boss_hit':      (220, None, 0.22, 0.55, 'noise',  0.01, 0.45),
            'boss_transition': (200, 800, 0.80, 0.60, 'sine',  0.10, 0.30),
            'ultimate_attack': (100, 50,  0.55, 0.65, 'square', 0.05, 0.30),
            'teleport':      (400, 1200, 0.22, 0.50, 'sine',   0.02, 0.40),
            # Game events
            'reality_break': (250, 500,  0.65, 0.60, 'square', 0.05, 0.30),
        }
        for name, args in defs.items():
            freq, freq_end, dur, vol, wave, atk, dec = args
            try:
                self.sounds[name] = self._make_tone(
                    freq, dur, volume=vol, wave=wave,
                    freq_end=freq_end, attack=atk, decay=dec,
                )
            except Exception as e:
                print(f"Placeholder-Sound '{name}' konnte nicht erzeugt werden: {e}")
