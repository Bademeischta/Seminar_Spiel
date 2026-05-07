import pygame

# --- Screen Settings ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
FPS = 60

# --- Colors ---
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_RED = (255, 0, 0)
COLOR_LIGHT_RED = (255, 100, 100)
COLOR_DARK_RED = (150, 0, 0)
COLOR_ORANGE = (255, 165, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_LIGHT_BLUE = (100, 100, 255)
COLOR_GREEN = (0, 255, 0)
COLOR_GRAY = (150, 150, 150)
COLOR_DARK_GRAY = (50, 50, 50)
COLOR_PINK = (255, 105, 180)
COLOR_BROWN = (139, 69, 19)
COLOR_YELLOW = (255, 255, 0)
COLOR_GOLD = (255, 215, 0)
COLOR_CYAN = (0, 255, 255)
COLOR_PURPLE = (128, 0, 128)

# Aliases for backward compatibility during refactoring if needed,
# but we aim to replace them all.
WHITE = COLOR_WHITE
BLACK = COLOR_BLACK
RED = COLOR_RED
LIGHT_RED = COLOR_LIGHT_RED
DARK_RED = COLOR_DARK_RED
ORANGE = COLOR_ORANGE
BLUE = COLOR_BLUE
LIGHT_BLUE = COLOR_LIGHT_BLUE
GREEN = COLOR_GREEN
GRAY = COLOR_GRAY
DARK_GRAY = COLOR_DARK_GRAY
PINK = COLOR_PINK
BROWN = COLOR_BROWN
YELLOW = COLOR_YELLOW
GOLD = COLOR_GOLD
CYAN = COLOR_CYAN
PURPLE = COLOR_PURPLE

# --- Physics ---
# Values converted from per-frame to per-second (assuming 60 FPS)
PHYSICS_GRAVITY = 2160  # 0.6 * 60 * 60
PLAYER_ACCELERATION = 2160 # 0.6 * 60 * 60
PLAYER_FRICTION = -6.0 # -0.1 * 60
PLAYER_MAX_SPEED = 360.0 # 6.0 * 60
PLAYER_JUMP_FORCE = -720.0 # -12 * 60
PLAYER_DASH_SPEED = 900.0 # 15 * 60
PLAYER_DASH_DURATION = 0.166 # 10 / 60
PLAYER_DASH_COOLDOWN = 0.7              # was 1.0 – faster dash recovery
PLAYER_WALL_CLING_DURATION = 2.0 # 120 / 60

# --- Combat ---
PLAYER_MAX_HP = 5                       # was 3 – more forgiving for new players
PLAYER_MAX_CARDS = 5
PLAYER_PARRY_WINDOW = 0.30              # was 0.25 – slightly larger parry window
PLAYER_PERFECT_PARRY_WINDOW = 0.167    # was 0.083 (5f) – now 10f, actually learnable
PLAYER_IFRAMES_DURATION = 2.0          # was hardcoded 1.5 in player.py
PLAYER_EX_FLIEGER_COST = 1
PLAYER_EX_ERASER_COST = 2
PLAYER_EX_RULER_COST = 2
PLAYER_EX_SUPER_COST = 5
PLAYER_EX_SUPER_DAMAGE_CAP = 25
PLAYER_CHARGE_DURATION = 1.0 # 60 / 60
PLAYER_SHIELD_COOLDOWN = 3.5           # was 5.0 – shield more usable in emergencies
PLAYER_FOCUS_MAX_DURATION = 3.0 # 180 / 60
PLAYER_FOCUS_REGEN_RATE = 0.2
PLAYER_STREBER_DURATION = 5.0          # was hardcoded 10.0 – shorter but still rewarding
PLAYER_STREBER_DAMAGE_MULT = 1.5       # was hardcoded 2 – avoids trivialising damage
PLAYER_PARRY_CARD_NORMAL = 0.5         # was hardcoded 1 – slows Ultimate spam
PLAYER_PARRY_CARD_PERFECT = 1.0        # was hardcoded 2

# --- Boss ---
BOSS_MAX_HP = 100
BOSS_PHASE_2_THRESHOLD = 70
BOSS_PHASE_3_THRESHOLD = 25            # was 30 – slightly shorter brutal phase
BOSS_PHASE1_COOLDOWN = 2.5             # was hardcoded 2.0
BOSS_PHASE2_COOLDOWN = 2.2             # was hardcoded 2.0
BOSS_PHASE3_COOLDOWN = 1.5             # was hardcoded 1.0 – phase 3 less overwhelming
BOSS_WEAK_POINT_DURATION = 2.5         # was hardcoded 1.0 – actually hittable now

# --- System ---
SYSTEM_SAVE_FILE = "save_data.json"
SAVE_FILE = SYSTEM_SAVE_FILE
