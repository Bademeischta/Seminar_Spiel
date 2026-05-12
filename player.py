import pygame
import math
import random
import os
from constants import *
from projectiles import PlayerProjectile, EXFlieger, EXEraser, EXRuler, EXSuper, SpreadProjectile, HomingProjectile
from boss_projectiles import ProtractorSpin
from utils import SoundManager, draw_text
from effects import AfterimageParticle, SquareParticle, StarParticle

# ---------------------------------------------------------------------------
# Animation constants
# ---------------------------------------------------------------------------

_SPRITE_SCALE = 2          # 30×30 canvas  →  60×60 on screen
_RUN_SPD_THRESHOLD = 30    # min |vel.x| to enter run state
_RUN_FRAME_DURATION = 0.11 # seconds per run frame

# Offset table – all values are in canvas pixels (30×30 grid).
#
# Meaning of the two numbers per entry:
#   ox  – shift the draw position RIGHT by (ox × scale) pixels so that the
#          visual foot centre aligns with hitbox.centerx.
#          When facing LEFT the sign is negated automatically.
#   oy  – extra transparent rows below the visual feet in this frame.
#          The sprite is shifted DOWN by (oy × scale) so the feet touch
#          hitbox.bottom exactly, regardless of how much blank space exists
#          at the bottom of the canvas.
#
# How the values were derived: for every frame the bounding box of all
# non-transparent pixels was measured; ox = canvas_w//2 − visual_feet_x,
# oy = canvas_h − visual_feet_y.
#
_ANIM_OFFSETS: dict[tuple[str, int], tuple[int, int]] = {
    # --- IDLE ---
    ('idle', 0):   ( 7,  3),

    # --- RUN (6 frames, all drawn in their natural right-facing orientation) ---
    # Frames 0-5 each have a slightly different foot position.
    # Without these per-frame x-offsets the figure would jitter left/right
    # because half the frames were drawn facing the opposite direction.
    ('run',  0):   ( 3,  2),
    ('run',  1):   ( 0,  2),
    ('run',  2):   ( 1,  2),
    ('run',  3):   (-1,  4),
    ('run',  4):   ( 3,  3),
    ('run',  5):   (-1,  2),

    # --- JUMP (4 phases) ---
    # Phase 2 (apex) has a large oy because the figure tucks its legs up.
    ('jump', 0):   ( 2,  2),   # absprung   – take-off crouch
    ('jump', 1):   ( 0,  3),   # aufstieg   – rising
    ('jump', 2):   (-1,  9),   # scheitelpunkt – apex, legs tucked
    ('jump', 3):   ( 2,  2),   # landung    – descending / landing

    # --- SHOOT (5 phases) ---
    # The charging / ready-up poses lean far to one side; ox=6/7 corrects that.
    ('shoot', 0):  ( 6,  3),   # aufladen   – charging
    ('shoot', 1):  ( 2,  3),   # entladen   – discharge
    ('shoot', 2):  ( 0,  2),   # rückstoß   – recoil
    ('shoot', 3):  ( 6,  2),   # recover    – recovery
    ('shoot', 4):  ( 7,  3),   # readyup    – ready-up / return to idle
}


class Player(pygame.sprite.Sprite):
    """Player character.

    Physics, collision and combat logic are unchanged from the original.
    The animation system is a clean rewrite:

      * self.rect  – invisible hitbox used for ALL physics and collision.
      * self.image – 1×1 transparent surface (required by Sprite; never drawn).
      * Sprites are drawn manually in draw() with per-frame pixel offsets from
        _ANIM_OFFSETS so the visual figure stays anchored to the hitbox.
    """

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def __init__(self, game, x, y):
        super().__init__()
        self.game = game
        self.sound_manager = SoundManager()

        # Hitbox – the only rect used for physics and collision.
        self.width = 40
        self.height = 60
        self.color = COLOR_BLUE
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.bottomleft = (x, y)

        # image is required by pygame.sprite.Sprite but never rendered.
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)

        self.squash_factor = pygame.math.Vector2(1.0, 1.0)
        self.squash_timer = 0

        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(0, 0)
        self.acc = pygame.math.Vector2(0, 0)

        # Stats
        self.hp = PLAYER_MAX_HP
        self.cards = 0.0
        self.max_cards = PLAYER_MAX_CARDS

        # State flags
        self.facing_right = True
        self.is_grounded = False
        self.on_wall = None
        self.wall_cling_timer = 0
        self.momentum_boost = 1.0

        # Jump
        self.jump_count = 0
        self.max_jumps = 2
        self.jump_timer = 0
        self.max_jump_time = 0.25
        self.parry_boost_active = False

        # Dash
        self.is_dashing = False
        self.dash_timer = 0
        self.dash_cooldown_timer = 0
        self.can_air_dash = True
        self.dash_direction = pygame.math.Vector2(1, 0)
        self.is_super_dash = False
        self.perfect_dash_window = 0

        # Invincibility
        self.i_frames = 0

        # Parry
        self.parry_active_timer = 0
        self.perfect_parry_window = 0
        self.parry_chain = 0
        self.parry_chain_timer = 0
        self.parry_counter_timer = 0
        self.streber_mode = False

        # Combat
        self.shoot_timer = 0
        self.charge_timer = 0
        self.is_charging = False

        # Defense
        self.shield_active = False
        self.shield_cooldown = 0
        self.selected_ex = "Flieger"
        self.focus_time = PLAYER_FOCUS_MAX_DURATION
        self.is_focusing = False
        self.can_dash = True
        self.jump_buffer = 0
        self.prev_on_wall = None
        self.is_slam_down = False

        self.drop_timer = 0
        self.ability_labels = []
        self.momentum_grace_timer = 0

        # ---------------------------------------------------------------
        # Animation state
        # ---------------------------------------------------------------
        self._sprites: dict[str, list] = {}
        self._state = 'idle'        # current animation state
        self._frame = 0             # current frame index within state
        self._frame_timer = 0.0     # accumulator for run frame advances
        self._shot_anim_timer = 0.0 # post-shot animation clock
        self._jump_start_timer = 0.0

        self._load_sprites()

    # ------------------------------------------------------------------
    # Sprite loading
    # ------------------------------------------------------------------

    def _load_sprites(self):
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sprites', 'Spieler')
        s = _SPRITE_SCALE

        def _load(rel_path: str):
            path = os.path.join(base, rel_path)
            try:
                img = pygame.image.load(path).convert_alpha()
                w, h = img.get_size()
                return pygame.transform.scale(img, (w * s, h * s))
            except Exception:
                return None

        self._sprites = {
            'idle':  [_load('idle.png')],
            'run':   [_load(f'run/run_{i}.png') for i in range(6)],
            'jump':  [_load(f'jump/jump_{i}.png') for i in range(4)],
            'shoot': [_load(f'shoot/shoot_{i}.png') for i in range(5)],
        }

    # ------------------------------------------------------------------
    # Animation state machine
    # ------------------------------------------------------------------

    def _update_anim_state(self):
        """Determine which animation state and frame should be active."""

        # SHOOT has the highest priority so the action reads clearly.
        if self._shot_anim_timer > 0:
            self._state = 'shoot'
            t = self._shot_anim_timer
            if   t > 0.20: self._frame = 1   # discharge
            elif t > 0.13: self._frame = 2   # recoil
            elif t > 0.07: self._frame = 3   # recovery
            else:          self._frame = 4   # ready-up
            return

        if self.is_charging:
            self._state = 'shoot'
            self._frame = 0  # charging pose
            return

        # JUMP – any time the feet leave the ground.
        if not self.is_grounded:
            self._state = 'jump'
            if self._jump_start_timer > 0:
                self._frame = 0  # take-off
            else:
                vy = -self.vel.y if self.game.inverted_gravity else self.vel.y
                if   vy < -150: self._frame = 1   # rising fast
                elif abs(vy) <= 150: self._frame = 2  # apex
                else:            self._frame = 3   # descending
            return

        # RUN – grounded and moving.
        if abs(self.vel.x) > _RUN_SPD_THRESHOLD:
            self._state = 'run'
            # frame index is advanced in _update_run_timer(); keep it stable here.
            return

        # IDLE – default.
        self._state = 'idle'
        self._frame = 0

    def _update_run_timer(self, dt: float):
        """Advance the run cycle frame counter."""
        if self._state == 'run':
            self._frame_timer += dt
            if self._frame_timer >= _RUN_FRAME_DURATION:
                self._frame_timer -= _RUN_FRAME_DURATION
                self._frame = (self._frame + 1) % len(self._sprites['run'])
        else:
            self._frame_timer = 0.0
            if self._state != 'run':
                self._frame = 0

    # ------------------------------------------------------------------
    # Per-frame draw offset
    # ------------------------------------------------------------------

    def _get_draw_offset(self) -> tuple[int, int]:
        """Return (screen_dx, screen_dy) to add to the default midbottom position."""
        ox, oy = _ANIM_OFFSETS.get((self._state, self._frame), (0, 0))
        sign = 1 if self.facing_right else -1
        return sign * ox * _SPRITE_SCALE, oy * _SPRITE_SCALE

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_input(self, dt):
        if self.game.state == "DEMO" and self.game.is_demo_bot:
            return

        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pressed()

        move_left = keys[pygame.K_a]
        move_right = keys[pygame.K_d]
        if self.game.inverted_controls:
            move_left, move_right = move_right, move_left

        # Focus Mode
        if keys[pygame.K_f] and not self.is_dashing and self.focus_time > 0:
            self.is_focusing = True
            if self.game.effect_manager.slowmo_timer <= 0:
                self.game.effect_manager.time_scale = 0.5
            self.focus_time -= dt
        else:
            if self.is_focusing:
                if self.game.effect_manager.slowmo_timer <= 0:
                    self.game.effect_manager.time_scale = 1.0
            self.is_focusing = False
            if self.focus_time < PLAYER_FOCUS_MAX_DURATION and not self.is_dashing:
                self.focus_time += PLAYER_FOCUS_REGEN_RATE * dt

        # Movement
        if not self.is_dashing:
            self.acc = pygame.math.Vector2(0, 0)
            if move_left:
                self.acc.x = -PLAYER_ACCELERATION * self.momentum_boost
                self.facing_right = False
            elif move_right:
                self.acc.x = PLAYER_ACCELERATION * self.momentum_boost
                self.facing_right = True

            # Variable jump hold
            if keys[pygame.K_SPACE]:
                if self.jump_timer > 0:
                    self.vel.y -= 1080 * dt
                    self.jump_timer -= dt
            else:
                self.jump_timer = 0

        # Shooting
        if mouse[0]:
            self.is_charging = True
            self.charge_timer += dt
        else:
            if self.is_charging:
                if self.charge_timer >= PLAYER_CHARGE_DURATION:
                    self.shoot_charge()
                else:
                    self.shoot_basic()
                self.game.action_log.append("shoot")
                if len(self.game.action_log) > 10:
                    self.game.action_log.pop(0)
                self.is_charging = False
                self.charge_timer = 0

        if mouse[2]:
            self.shoot_ex()

        # Shield
        if keys[pygame.K_e] and self.shield_cooldown <= 0:
            self.activate_shield()

        # EX switch
        if keys[pygame.K_1]: self.selected_ex = "Flieger"
        if keys[pygame.K_2]: self.selected_ex = "Eraser"
        if keys[pygame.K_3]: self.selected_ex = "Ruler"
        if keys[pygame.K_4]: self.selected_ex = "Spread"
        if keys[pygame.K_5]: self.selected_ex = "Homing"

    # ------------------------------------------------------------------
    # Jump / Dash
    # ------------------------------------------------------------------

    def jump(self):
        if not self.is_grounded and not self.on_wall:
            self.jump_buffer = 0.15
            return
        self.perform_jump()

    def perform_jump(self):
        if self.on_wall:
            self.sound_manager.play("jump")
            self.vel.y = PLAYER_JUMP_FORCE
            self.vel.x = 600 if self.on_wall == 'left' else -600
            self.jump_count = 1
            self.on_wall = None
            self.check_momentum_chain()
            self.spawn_jump_particles()
            return

        if self.jump_count < self.max_jumps or self.is_grounded:
            self.sound_manager.play("jump")

            force = PLAYER_JUMP_FORCE
            if self.parry_boost_active:
                force *= 1.5
                self.parry_boost_active = False

            if self.game.inverted_gravity:
                force = -force

            self.vel.y = force

            if self.jump_count > 0 and not self.is_grounded:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_a]: self.vel.x = -PLAYER_MAX_SPEED
                if keys[pygame.K_d]: self.vel.x = PLAYER_MAX_SPEED

            self.jump_timer = self.max_jump_time
            self.jump_count += 1
            self.is_grounded = False
            self.drop_timer = 0
            self._jump_start_timer = 0.10

            self.squash_factor = pygame.math.Vector2(0.8, 1.2)
            self.squash_timer = 0.166
            self.spawn_jump_particles()
            self.game.effect_manager.apply_shake(0.1, 2, type='directional', vector=(0, 1))

    def dash(self):
        if not self.can_dash:
            return

        if self.dash_cooldown_timer <= 0:
            if self.is_grounded or self.can_air_dash:
                keys = pygame.key.get_pressed()
                cost = 1 if keys[pygame.K_LCTRL] else 0
                if cost == 1 and self.cards >= 1:
                    self.cards -= 1
                    self.is_super_dash = True
                else:
                    self.is_super_dash = False

                self.sound_manager.play("super_dash" if self.is_super_dash else "dash")
                self.is_dashing = True
                self.dash_timer = PLAYER_DASH_DURATION * (2 if self.is_super_dash else 1)
                self.dash_cooldown_timer = PLAYER_DASH_COOLDOWN
                self.i_frames = self.dash_timer
                self.perfect_dash_window = 0.166

                if not self.is_grounded:
                    self.can_air_dash = False

                dir_x = 0
                dir_y = 0
                if keys[pygame.K_a]: dir_x = -1
                elif keys[pygame.K_d]: dir_x = 1
                if keys[pygame.K_w]: dir_y = -1
                elif keys[pygame.K_s]: dir_y = 1

                if dir_x == 0 and dir_y == 0:
                    dir_x = 1 if self.facing_right else -1

                if dir_y == 1 and not self.is_grounded:
                    self.is_slam_down = True
                    self.vel.y = PLAYER_DASH_SPEED * 1.5
                    self.dash_timer = 0.33
                    self.game.effect_manager.apply_shake(0.1, 5, type='directional', vector=(0, 1))
                    return
                else:
                    self.is_slam_down = False

                self.dash_direction = pygame.math.Vector2(dir_x, dir_y).normalize()
                if dir_x != 0:
                    self.facing_right = dir_x > 0

                if self.is_super_dash:
                    self.game.particle_manager.spawn_speed_lines()

                self.game.action_log.append("dash")
                if len(self.game.action_log) > 10:
                    self.game.action_log.pop(0)

    # ------------------------------------------------------------------
    # Combat
    # ------------------------------------------------------------------

    def activate_shield(self):
        self.shield_active = True
        self.shield_cooldown = PLAYER_SHIELD_COOLDOWN

    def shoot_basic(self):
        if self.game.challenge and self.game.challenge.name == "Parry Only":
            return
        if self.shoot_timer <= 0:
            self.sound_manager.play("shoot")
            damage = 1
            color = COLOR_BLUE
            is_gold = False

            if self.parry_counter_timer > 0 or self.streber_mode:
                damage = damage * PLAYER_STREBER_DAMAGE_MULT
                color = COLOR_GOLD
                is_gold = True

            dist = pygame.math.Vector2(self.rect.center).distance_to(self.game.boss.rect.center)
            if dist < 100:
                self.cards = min(self.cards + 0.05, PLAYER_MAX_CARDS)

            bullet = PlayerProjectile(
                self.game, self.rect.centerx, self.rect.centery,
                720 if self.facing_right else -720, 0, damage, color)
            bullet.is_golden = is_gold
            self.game.all_sprites.add(bullet)
            self.game.player_bullets.add(bullet)
            self.shoot_timer = 0.166
            self._shot_anim_timer = 0.25

    def shoot_charge(self):
        if self.game.challenge and self.game.challenge.name == "Parry Only":
            return
        self.sound_manager.play("charge_shot")
        bullet = PlayerProjectile(
            self.game, self.rect.centerx, self.rect.centery,
            900 if self.facing_right else -900, 0,
            PLAYER_CHARGE_SHOT_DAMAGE, COLOR_LIGHT_BLUE, size=(30, 30))
        self.game.all_sprites.add(bullet)
        self.game.player_bullets.add(bullet)
        self._shot_anim_timer = 0.25

    def shoot_spread(self):
        if self.game.challenge and self.game.challenge.name == "Parry Only":
            return
        if self.cards >= 2:
            self.cards -= 2
            self.sound_manager.play("shoot_spread")
            for i in range(-2, 3):
                angle = i * 10
                rad = math.radians(angle)
                vel_x = (720 if self.facing_right else -720) * math.cos(rad)
                vel_y = 720 * math.sin(rad)
                bullet = SpreadProjectile(self.game, self.rect.centerx, self.rect.centery, vel_x, vel_y)
                self.game.all_sprites.add(bullet)
                self.game.player_bullets.add(bullet)

    def shoot_homing(self):
        if self.game.challenge and self.game.challenge.name == "Parry Only":
            return
        if self.cards >= 3:
            self.cards -= 3
            self.sound_manager.play("shoot_homing")
            for i in range(3):
                bullet = HomingProjectile(self.game, self.rect.centerx, self.rect.centery - 20 + i * 20)
                self.game.all_sprites.add(bullet)
                self.game.player_bullets.add(bullet)

    def shoot_ex(self):
        if self.game.challenge and self.game.challenge.name == "Parry Only":
            return
        if self.cards >= 5:
            self.sound_manager.play("ultimate")
            self.cards -= 5
            bullet = EXSuper(self.game, self.rect.centerx, self.rect.centery, 1 if self.facing_right else -1)
            self.game.all_sprites.add(bullet)
            self.game.player_bullets.add(bullet)
            self.game.effect_manager.apply_shake(1.0, 15)
            self.game.effect_manager.apply_zoom(1.3, duration=0.5)
            return

        if self.selected_ex == "Spread":
            self.shoot_spread()
            return
        if self.selected_ex == "Homing":
            self.shoot_homing()
            return

        cost = PLAYER_EX_FLIEGER_COST
        if self.selected_ex == "Eraser": cost = PLAYER_EX_ERASER_COST
        if self.selected_ex == "Ruler":  cost = PLAYER_EX_RULER_COST

        if self.cards >= cost:
            self.cards -= cost
            bullet = None
            if self.selected_ex == "Flieger":
                bullet = EXFlieger(self.game, self.rect.centerx, self.rect.centery, 1 if self.facing_right else -1)
            elif self.selected_ex == "Eraser":
                bullet = EXEraser(self.game, self.rect.centerx, self.rect.centery, 1 if self.facing_right else -1)
            elif self.selected_ex == "Ruler":
                bullet = EXRuler(self.game, self.rect.centerx, self.rect.centery, 1 if self.facing_right else -1)

            if bullet:
                self.sound_manager.play("ex_attack")
                self.game.all_sprites.add(bullet)
                self.game.player_bullets.add(bullet)
                self.game.effect_manager.apply_shake(0.16, 3)

    def add_ability_label(self, text):
        self.ability_labels.append({"text": text, "timer": 2.0})

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt):
        self.handle_input(dt)

        if self.jump_buffer > 0:
            self.jump_buffer -= dt
            if (self.is_grounded or self.on_wall) and self.jump_buffer > 0:
                self.perform_jump()
                self.jump_buffer = 0

        self.apply_gravity(dt)
        self.update_physics(dt)
        self.check_collisions(dt)
        self.update_timers(dt)
        self.update_animation(dt)

    def apply_gravity(self, dt):
        if not self.is_dashing and not self.on_wall:
            keys = pygame.key.get_pressed()
            g = PHYSICS_GRAVITY
            if self.game.inverted_gravity:
                g = -PHYSICS_GRAVITY
            rising = self.vel.y > 0 if self.game.inverted_gravity else self.vel.y < 0
            current_gravity = g * 0.5 if (keys[pygame.K_SPACE] and rising) else g
            self.vel.y += current_gravity * dt

    def update_physics(self, dt):
        if self.is_dashing:
            if not getattr(self, 'is_slam_down', False):
                speed = PLAYER_DASH_SPEED * (2 if self.is_super_dash else 1)
                self.vel = self.dash_direction * speed
            self.pos += self.vel * dt
        else:
            friction_acc = self.vel.x * PLAYER_FRICTION
            total_acc_x = self.acc.x + friction_acc
            self.vel.x += total_acc_x * dt

            max_s = PLAYER_MAX_SPEED * self.momentum_boost
            if abs(self.vel.x) > max_s:
                self.vel.x = max_s * (1 if self.vel.x > 0 else -1)

            if abs(self.vel.x) < 10 and self.acc.x == 0:
                self.vel.x = 0

            self.pos += self.vel * dt

        self.rect.midbottom = (int(self.pos.x), int(self.pos.y))

    def update_timers(self, dt):
        if self.dash_timer > 0:
            self.dash_timer -= dt
            if self.dash_timer <= 0:
                self.is_dashing = False
            if self.is_super_dash and random.random() < 30 * dt:
                self.game.particle_manager.add(
                    StarParticle(self.rect.center,
                                 (random.uniform(-120, 120), random.uniform(-120, 120)),
                                 0.3, COLOR_BLUE, 8))

        if self.dash_cooldown_timer > 0: self.dash_cooldown_timer -= dt
        if self.perfect_dash_window > 0: self.perfect_dash_window -= dt
        if self.i_frames > 0:            self.i_frames -= dt
        if self.parry_active_timer > 0:
            self.parry_active_timer -= dt
            self.perfect_parry_window -= dt

        if self.parry_chain_timer > 0:
            self.parry_chain_timer -= dt
            if self.parry_chain_timer <= 0:
                self.parry_chain = 0
                if self.parry_counter_timer <= 0:
                    self.streber_mode = False

        if self.parry_counter_timer > 0:
            self.parry_counter_timer -= dt
            if self.parry_counter_timer <= 0:
                self.streber_mode = False

        if not self.is_dashing:
            self.is_slam_down = False

        if self.shoot_timer > 0:       self.shoot_timer -= dt
        if self.shield_cooldown > 0:   self.shield_cooldown -= dt
        if self.wall_cling_timer > 0:  self.wall_cling_timer -= dt
        if self.momentum_grace_timer > 0: self.momentum_grace_timer -= dt

        if self.squash_timer > 0:
            self.squash_timer -= dt
            if self.squash_timer <= 0:
                self.squash_factor = pygame.math.Vector2(1.0, 1.0)
            else:
                self.squash_factor += (pygame.math.Vector2(1.0, 1.0) - self.squash_factor) * 12 * dt
                self.squash_factor.x = max(0.1, self.squash_factor.x)
                self.squash_factor.y = max(0.1, self.squash_factor.y)

        for label in self.ability_labels[:]:
            label["timer"] -= dt
            if label["timer"] <= 0:
                self.ability_labels.remove(label)

    def update_animation(self, dt):
        if self._shot_anim_timer > 0:
            self._shot_anim_timer -= dt
        if self._jump_start_timer > 0:
            self._jump_start_timer -= dt

        self._update_anim_state()
        self._update_run_timer(dt)

    # ------------------------------------------------------------------
    # Collision
    # ------------------------------------------------------------------

    def check_collisions(self, dt):
        was_grounded = self.is_grounded
        self.is_grounded = False

        if not was_grounded and not self.is_dashing:
            if self.rect.left <= 0:
                self.on_wall = 'left'
                if self.prev_on_wall is None:
                    self.wall_cling_timer = PLAYER_WALL_CLING_DURATION
                if self.wall_cling_timer > 0:
                    self.vel.y = min(self.vel.y, 120)
            elif self.rect.right >= SCREEN_WIDTH:
                self.on_wall = 'right'
                if self.prev_on_wall is None:
                    self.wall_cling_timer = PLAYER_WALL_CLING_DURATION
                if self.wall_cling_timer > 0:
                    self.vel.y = min(self.vel.y, 120)
            else:
                self.on_wall = None
        else:
            self.on_wall = None

        if self.game.inverted_gravity:
            if self.pos.y <= 0:
                if not was_grounded:
                    self.spawn_jump_particles()
                    self.sound_manager.play("land")
                    self.squash_factor = pygame.math.Vector2(1.2, 0.8)
                    self.squash_timer = 0.166
                self.pos.y = 0
                self.vel.y = 0
                self.is_grounded = True
                if self.momentum_grace_timer <= 0:
                    self.momentum_boost = 1.0
                self.can_air_dash = True
                self.jump_count = 0
                self.max_jumps = 2 if not self.streber_mode else 3
        else:
            if self.pos.y >= SCREEN_HEIGHT:
                if not was_grounded:
                    self.spawn_jump_particles()
                    self.sound_manager.play("land")
                    self.squash_factor = pygame.math.Vector2(1.2, 0.8)
                    self.squash_timer = 0.166
                self.pos.y = SCREEN_HEIGHT
                self.vel.y = 0
                self.is_grounded = True
                if self.momentum_grace_timer <= 0:
                    self.momentum_boost = 1.0
                self.can_air_dash = True
                self.jump_count = 0
                self.max_jumps = 2 if not self.streber_mode else 3

        self.prev_on_wall = self.on_wall

        plat_hits = pygame.sprite.spritecollide(self, self.game.platforms, False)
        for platform in plat_hits:
            if not self.game.inverted_gravity:
                if self.vel.y > 0 and self.rect.bottom <= platform.rect.bottom + 10:
                    self.pos.y = platform.rect.top
                    self.vel.y = 0
                    self.is_grounded = True
                    if self.momentum_grace_timer <= 0:
                        self.momentum_boost = 1.0
                    self.can_air_dash = True
                    self.jump_count = 0
                    self.max_jumps = 2 if not self.streber_mode else 3
                    self.rect.bottom = int(self.pos.y)
            else:
                if self.vel.y < 0 and self.rect.top >= platform.rect.top - 10:
                    self.pos.y = platform.rect.bottom + self.height
                    self.vel.y = 0
                    self.is_grounded = True
                    if self.momentum_grace_timer <= 0:
                        self.momentum_boost = 1.0
                    self.can_air_dash = True
                    self.jump_count = 0
                    self.max_jumps = 2 if not self.streber_mode else 3
                    self.rect.bottom = int(self.pos.y)

        hits = pygame.sprite.spritecollide(self, self.game.boss_bullets, False)
        for projectile in hits:
            if isinstance(projectile, ProtractorSpin):
                continue
            if self.is_dashing:
                if self.perfect_dash_window > 0:
                    self.game.style_points += 5
                    self.cards = min(self.cards + 0.5, PLAYER_MAX_CARDS)
                    self.game.effect_manager.add_damage_number(self.rect.center, "PERFECT DASH", color=COLOR_CYAN, size=16)
                    self.game.effect_manager.apply_slowmo(0.16, 0.8)
                    self.game.particle_manager.spawn_hit(projectile.rect.center, color=COLOR_CYAN)
                projectile.kill()
                continue

            if self.parry_active_timer > 0:
                self.handle_parry(projectile)
            elif self.shield_active:
                self.shield_active = False
                projectile.kill()
                self.game.effect_manager.add_damage_number(self.rect.center, "BLOCKED", color=COLOR_CYAN, size=16)
            elif self.i_frames <= 0:
                self.take_damage()
                projectile.kill()

    def handle_parry(self, projectile):
        if projectile is None:
            return
        if not getattr(projectile, 'is_parryable', False):
            self.sound_manager.play("parry_fail")
            self.game.effect_manager.add_damage_number(self.rect.center, "KEIN PARRY!", color=COLOR_ORANGE, size=18)
            self.take_damage()
            projectile.kill()
            return

        if self.game.challenge:
            self.game.challenge.handle_parry_damage(self.perfect_parry_window > 0)

        projectile.kill()
        is_perfect = self.perfect_parry_window > 0
        self.sound_manager.play("perfect_parry" if is_perfect else "parry")
        self.game.particle_manager.spawn_parry(self.rect.center, perfect=is_perfect)

        if is_perfect:
            self.game.style_points += 10
            self.cards = min(self.cards + PLAYER_PARRY_CARD_PERFECT, PLAYER_MAX_CARDS)
            self.game.effect_manager.apply_slowmo(0.33, 0.3)
            self.game.effect_manager.apply_freeze(0.06)
            self.max_jumps = 3
            self.parry_boost_active = True
            self.game.perfect_parries += 1
        else:
            self.cards = min(self.cards + PLAYER_PARRY_CARD_NORMAL, PLAYER_MAX_CARDS)
            self.parry_boost_active = True

        self.game.action_log.append("parry")
        if len(self.game.action_log) > 10:
            self.game.action_log.pop(0)

        self.game.total_parries += 1
        self.vel.y = -300
        self.can_air_dash = True
        self.parry_chain += 1
        self.parry_chain_timer = 5.0
        self.parry_counter_timer = 1.0

        if self.parry_chain >= 3:
            self.streber_mode = True
            self.parry_chain_timer = PLAYER_STREBER_DURATION
            self.parry_counter_timer = PLAYER_STREBER_DURATION
            self.game.effect_manager.add_damage_number(self.rect.center, "STREBER MODE!", color=COLOR_GOLD, size=32)

    def take_damage(self):
        if self.i_frames > 0:
            return
        self.sound_manager.play("hit")
        self.hp -= 1

        if self.game.challenge and self.game.challenge.name == "One Hit KO":
            self.hp = 0
            self.i_frames = 0
        else:
            self.i_frames = PLAYER_IFRAMES_DURATION

        self.game.effect_manager.apply_shake(0.33, 10)
        self.game.particle_manager.spawn_hit(self.rect.center, color=COLOR_RED)
        self.momentum_boost = 1.0
        self.streber_mode = False
        if self.hp <= 0:
            self.game.game_over()

    def check_momentum_chain(self):
        self.momentum_boost = min(2.0, self.momentum_boost + 0.1)
        self.momentum_grace_timer = 0.5

    def spawn_jump_particles(self):
        self.game.particle_manager.spawn_dust((self.rect.centerx, self.rect.bottom))

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, screen, camera_offset):
        # Ability labels
        for label in self.ability_labels:
            t = label["timer"]
            alpha = 255
            if t > 1.66:
                alpha = int((2.0 - t) / 0.33 * 255)
            elif t < 0.33:
                alpha = int(t / 0.33 * 255)
            draw_text(screen, label["text"], 36,
                      self.rect.centerx - camera_offset.x,
                      self.rect.top - 80 - camera_offset.y,
                      color=COLOR_GOLD, alpha=alpha)

        # Hitbox anchor in screen space
        hb_cx = self.rect.centerx - int(camera_offset.x)
        hb_by = self.rect.bottom  - int(camera_offset.y)

        # Pick sprite for the current state / frame
        frame_list = self._sprites.get(self._state, self._sprites['idle'])
        frame_idx  = min(self._frame, len(frame_list) - 1)
        sprite     = frame_list[frame_idx]

        if sprite:
            sw, sh = sprite.get_size()
            # Squash-and-stretch
            w = max(1, int(sw * self.squash_factor.x))
            h = max(1, int(sh * self.squash_factor.y))
            scaled = pygame.transform.scale(sprite, (w, h))

            # Mirror for left-facing direction
            if not self.facing_right:
                scaled = pygame.transform.flip(scaled, True, False)

            # Tint overlays
            iframes_flash = self.i_frames > 0 and (int(self.i_frames * 6) % 2 == 0)
            if iframes_flash:
                tint = pygame.Surface(scaled.get_size(), pygame.SRCALPHA)
                tint.fill((255, 255, 255, 200))
                scaled = scaled.copy()
                scaled.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            elif self.streber_mode or self.parry_counter_timer > 0:
                tint = pygame.Surface(scaled.get_size(), pygame.SRCALPHA)
                tint.fill((80, 60, 0, 110))
                scaled = scaled.copy()
                scaled.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

            # Apply offset so visual feet land exactly on hitbox.bottom / centerx.
            # ox/oy are in scaled screen pixels; ox sign depends on facing direction.
            ox, oy = self._get_draw_offset()
            draw_rect = scaled.get_rect()
            draw_rect.midbottom = (hb_cx + ox, hb_by + oy)
            screen.blit(scaled, draw_rect)

            # Dash afterimage
            if self.is_dashing and (int(self.dash_timer * 60) % 3 == 0):
                self.game.particle_manager.add(
                    AfterimageParticle(pygame.math.Vector2(draw_rect.topleft), scaled, 0.25, 150))

            # Charge bar
            if self.is_charging:
                pct = min(1.0, self.charge_timer / PLAYER_CHARGE_DURATION)
                bar_x = hb_cx - self.width // 2
                pygame.draw.rect(screen, COLOR_WHITE,
                                 (bar_x, draw_rect.top - 8, int(self.width * pct), 5))
        else:
            # Fallback procedural rectangle when sprites are missing
            w = self.width  * self.squash_factor.x
            h = self.height * self.squash_factor.y
            color = self.color
            if self.streber_mode or self.parry_counter_timer > 0:
                color = COLOR_GOLD
            if self.i_frames > 0 and (int(self.i_frames * 6) % 2 == 0):
                color = COLOR_WHITE
            fb_rect = pygame.Rect(0, 0, w, h)
            fb_rect.midbottom = (hb_cx, hb_by)
            pygame.draw.rect(screen, color, fb_rect)
            eye_offset = 10 if self.facing_right else -10
            pygame.draw.circle(screen, COLOR_WHITE,
                                (fb_rect.centerx + eye_offset, fb_rect.top + 15), 5)
            if self.is_dashing and (int(self.dash_timer * 60) % 3 == 0):
                surf = pygame.Surface((w, h), pygame.SRCALPHA)
                pygame.draw.rect(surf, color, (0, 0, w, h))
                self.game.particle_manager.add(
                    AfterimageParticle(pygame.math.Vector2(fb_rect.topleft), surf, 0.25, 150))
            if self.is_charging:
                pct = min(1.0, self.charge_timer / PLAYER_CHARGE_DURATION)
                pygame.draw.rect(screen, COLOR_WHITE,
                                 (fb_rect.left, fb_rect.top - 10, w * pct, 5))

        # Shield ring
        if self.shield_active:
            cx = hb_cx
            cy = hb_by - self.height // 2
            pygame.draw.circle(screen, COLOR_CYAN, (cx, cy), 50, 2)
