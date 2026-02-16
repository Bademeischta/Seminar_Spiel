import pygame
import math
import random
from constants import *
from projectiles import PlayerProjectile, EXFlieger, EXEraser, EXRuler, EXSuper, SpreadProjectile, HomingProjectile
from utils import SoundManager

class Player(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        super().__init__()
        self.game = game
        self.sound_manager = SoundManager()
        
        # Procedural Graphics
        self.width = 40
        self.height = 60
        self.color = BLUE
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.bottomleft = (x, y)
        self.squash_factor = pygame.math.Vector2(1.0, 1.0)
        self.squash_timer = 0

        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(0, 0)
        self.acc = pygame.math.Vector2(0, 0)

        # Stats
        self.hp = MAX_PLAYER_HP
        self.cards = 0.0
        self.max_cards = MAX_CARDS

        # State
        self.facing_right = True
        self.is_grounded = False
        self.on_wall = None 
        self.wall_cling_timer = 0
        self.momentum_boost = 1.0

        # Jump
        self.jump_count = 0
        self.max_jumps = 2 
        self.jump_timer = 0
        self.max_jump_frames = 15
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
        self.focus_time = FOCUS_MAX_TIME
        self.is_focusing = False

        self.drop_timer = 0

    def handle_input(self):
        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pressed()

        move_left = keys[pygame.K_a]
        move_right = keys[pygame.K_d]
        if self.game.inverted_controls:
            move_left, move_right = move_right, move_left

        # Focus Mode
        if keys[pygame.K_LSHIFT] and not self.is_dashing and self.focus_time > 0:
            self.is_focusing = True
            self.game.effect_manager.time_scale = 0.5
            self.focus_time -= 1
        else:
            self.is_focusing = False
            if self.focus_time < FOCUS_MAX_TIME:
                self.focus_time += FOCUS_REGEN_RATE

        # Movement
        if not self.is_dashing:
            self.acc = pygame.math.Vector2(0, 0)
            if move_left:
                self.acc.x = -PLAYER_ACC * self.momentum_boost
                self.facing_right = False
            elif move_right:
                self.acc.x = PLAYER_ACC * self.momentum_boost
                self.facing_right = True

            # Variable Jump
            if keys[pygame.K_SPACE]:
                if self.jump_timer > 0:
                    self.vel.y -= 0.3
                    self.jump_timer -= 1
            else:
                self.jump_timer = 0

        # Shooting
        if mouse[0]: # Left Click
            self.is_charging = True
            self.charge_timer += 1
        else:
            if self.is_charging:
                if self.charge_timer >= CHARGE_TIME:
                    self.shoot_charge()
                else:
                    self.shoot_basic()
                self.is_charging = False
                self.charge_timer = 0
        
        if mouse[2]: # Right Click - EX/Special
             self.shoot_ex()

        # Shield
        if keys[pygame.K_e] and self.shield_cooldown <= 0:
            self.activate_shield()

        # EX Switch
        if keys[pygame.K_1]: self.selected_ex = "Flieger"
        if keys[pygame.K_2]: self.selected_ex = "Eraser"
        if keys[pygame.K_3]: self.selected_ex = "Ruler"
        if keys[pygame.K_4]: self.selected_ex = "Spread"
        if keys[pygame.K_5]: self.selected_ex = "Homing"

    def jump(self):
        # Wall Jump
        if self.on_wall:
            self.sound_manager.play("jump")
            self.vel.y = PLAYER_JUMP_FORCE
            self.vel.x = 10 if self.on_wall == 'left' else -10
            self.jump_count = 1
            self.on_wall = None
            self.check_momentum_chain()
            self.spawn_jump_particles()
            return

        # Air/Double/Triple Jump
        if self.jump_count < self.max_jumps:
            self.sound_manager.play("jump")
            
            # Parry Boost
            force = PLAYER_JUMP_FORCE
            if self.parry_boost_active:
                force *= 1.5
                self.parry_boost_active = False # Consume boost
                
            self.vel.y = force
            
            # Directional Air Jump
            if self.jump_count > 0: 
                keys = pygame.key.get_pressed()
                if keys[pygame.K_a]: self.vel.x = -PLAYER_MAX_SPEED
                if keys[pygame.K_d]: self.vel.x = PLAYER_MAX_SPEED

            self.jump_timer = self.max_jump_frames
            self.jump_count += 1
            self.is_grounded = False
            self.drop_timer = 0
            
            # Juice
            self.squash_factor = pygame.math.Vector2(0.8, 1.2) # Stretch
            self.squash_timer = 10
            self.spawn_jump_particles()
            self.game.effect_manager.apply_shake(5, 2, type='directional', vector=(0, 1))

    def dash(self):
        if self.dash_cooldown_timer <= 0:
            keys = pygame.key.get_pressed()
            # Super Dash Check (Hold CTRL or Shift+Space logic if needed, here we use CTRL modifier)
            cost = 1 if (keys[pygame.K_LCTRL]) else 0
            if cost == 1 and self.cards >= 1:
                self.cards -= 1
                self.is_super_dash = True
            else:
                self.is_super_dash = False

            if self.is_grounded or self.can_air_dash:
                self.sound_manager.play("super_dash" if self.is_super_dash else "dash")
                self.is_dashing = True
                self.dash_timer = PLAYER_DASH_DURATION * (2 if self.is_super_dash else 1)
                self.dash_cooldown_timer = PLAYER_DASH_COOLDOWN
                self.i_frames = self.dash_timer
                self.perfect_dash_window = 10 # First 10 frames are perfect

                if not self.is_grounded:
                    self.can_air_dash = False

                # 8-direction dash
                dir_x = 0
                dir_y = 0
                if keys[pygame.K_a]: dir_x = -1
                elif keys[pygame.K_d]: dir_x = 1
                if keys[pygame.K_w]: dir_y = -1
                elif keys[pygame.K_s]: dir_y = 1

                if dir_x == 0 and dir_y == 0:
                    dir_x = 1 if self.facing_right else -1

                # Slam-Down
                if dir_y == 1 and not self.is_grounded:
                    self.vel.y = PLAYER_DASH_SPEED * 1.5
                    self.dash_timer = 20 # Short slam
                    self.game.effect_manager.apply_shake(5, 5, type='directional', vector=(0, 1))

                self.dash_direction = pygame.math.Vector2(dir_x, dir_y).normalize()
                if dir_x != 0: self.facing_right = dir_x > 0
                
                # Particles
                if self.is_super_dash:
                    self.game.particle_manager.spawn_speed_lines()

    def activate_shield(self):
        self.shield_active = True
        self.shield_cooldown = SHIELD_COOLDOWN

    def shoot_basic(self):
        if self.shoot_timer <= 0:
            self.sound_manager.play("shoot")
            damage = 1
            color = BLUE
            is_gold = False
            
            if self.parry_counter_timer > 0 or self.streber_mode:
                damage *= 2
                color = GOLD
                is_gold = True

            # Risk bonus check
            dist = pygame.math.Vector2(self.rect.center).distance_to(self.game.boss.rect.center)
            if dist < 100:
                self.cards = min(self.cards + 0.05, MAX_CARDS)

            bullet = PlayerProjectile(self.game, self.rect.centerx, self.rect.centery,
                                     12 if self.facing_right else -12, 0, damage, color)
            bullet.is_golden = is_gold
            self.game.all_sprites.add(bullet)
            self.game.player_bullets.add(bullet)
            self.shoot_timer = 10

    def shoot_charge(self):
        self.sound_manager.play("charge_shot")
        bullet = PlayerProjectile(self.game, self.rect.centerx, self.rect.centery,
                                 15 if self.facing_right else -15, 0, 3, LIGHT_BLUE, size=(30, 30))
        self.game.all_sprites.add(bullet)
        self.game.player_bullets.add(bullet)
        
    def shoot_spread(self):
        if self.cards >= 2:
            self.cards -= 2
            self.sound_manager.play("shoot_spread") # 5x pew logic handled in sound manager ideally
            for i in range(-2, 3):
                angle = i * 10
                rad = math.radians(angle)
                vel_x = (12 if self.facing_right else -12) * math.cos(rad)
                vel_y = 12 * math.sin(rad)
                bullet = SpreadProjectile(self.game, self.rect.centerx, self.rect.centery, vel_x, vel_y)
                self.game.all_sprites.add(bullet)
                self.game.player_bullets.add(bullet)

    def shoot_homing(self):
        if self.cards >= 3:
            self.cards -= 3
            self.sound_manager.play("shoot_homing")
            for i in range(3):
                bullet = HomingProjectile(self.game, self.rect.centerx, self.rect.centery - 20 + i*20)
                self.game.all_sprites.add(bullet)
                self.game.player_bullets.add(bullet)

    def shoot_ex(self):
        if self.cards >= 5: # Ultimate
            self.sound_manager.play("ultimate")
            self.cards -= 5
            bullet = EXSuper(self.game, self.rect.centerx, self.rect.centery, 1 if self.facing_right else -1)
            self.game.all_sprites.add(bullet)
            self.game.player_bullets.add(bullet)
            self.game.effect_manager.apply_shake(60, 15)
            self.game.effect_manager.apply_zoom(1.3, duration=30)
            return

        # Regular EX
        if self.selected_ex == "Spread":
            self.shoot_spread()
            return
        if self.selected_ex == "Homing":
            self.shoot_homing()
            return

        cost = EX_FLIEGER_COST
        if self.selected_ex == "Eraser": cost = EX_ERASER_COST
        if self.selected_ex == "Ruler": cost = EX_RULER_COST
        
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
                self.game.effect_manager.apply_shake(10, 3)

    def update(self, dt=1.0):
        self.handle_input()
        self.apply_gravity(dt)
        self.update_physics(dt)
        self.check_collisions()
        self.update_timers(dt)
        self.update_animation(dt)

    def apply_gravity(self, dt):
        if not self.is_dashing and not self.on_wall:
            keys = pygame.key.get_pressed()
            g = GRAVITY
            if self.game.inverted_gravity: g = -GRAVITY
            current_gravity = g * 0.5 if (keys[pygame.K_SPACE] and self.vel.y < 0) else g
            self.vel.y += current_gravity * dt

    def update_physics(self, dt):
        if self.is_dashing:
            speed = PLAYER_DASH_SPEED * (2 if self.is_super_dash else 1)
            self.vel = self.dash_direction * speed
            self.pos += self.vel * dt
            
            # Trail Logic
            if int(self.dash_timer) % 3 == 0:
                self.game.particle_manager.add(pygame.sprite.Sprite()) # Hack? No, use AfterimageParticle
                # We need to pass the current drawn image to the particle
                # We will do this in draw() actually or create a method to get current image
                pass # Handled in draw/particle manager

        else:
            self.acc.x += self.vel.x * PLAYER_FRICTION
            self.vel.x += self.acc.x * dt
            max_s = PLAYER_MAX_SPEED * self.momentum_boost
            if abs(self.vel.x) > max_s:
                self.vel.x = max_s * (1 if self.vel.x > 0 else -1)
            self.pos += (self.vel + 0.5 * self.acc * dt) * dt

        self.rect.midbottom = (int(self.pos.x), int(self.pos.y))

    def update_timers(self, dt):
        if self.dash_timer > 0:
            self.dash_timer -= dt
            if self.dash_timer <= 0: self.is_dashing = False
            
            # Spawn dash particles
            if self.is_super_dash and random.random() < 0.5:
                 self.game.particle_manager.add(pygame.sprite.Sprite()) # Placeholder logic

        if self.dash_cooldown_timer > 0: self.dash_cooldown_timer -= dt
        if self.perfect_dash_window > 0: self.perfect_dash_window -= dt
        if self.i_frames > 0: self.i_frames -= dt
        if self.parry_active_timer > 0:
            self.parry_active_timer -= dt
            self.perfect_parry_window -= dt

        if self.parry_chain_timer > 0:
            self.parry_chain_timer -= dt
            if self.parry_chain_timer <= 0: 
                self.parry_chain = 0
                self.streber_mode = False

        if self.parry_counter_timer > 0: self.parry_counter_timer -= dt
        if self.shoot_timer > 0: self.shoot_timer -= dt
        if self.shield_cooldown > 0: self.shield_cooldown -= dt
        if self.wall_cling_timer > 0: self.wall_cling_timer -= dt
            
        if self.squash_timer > 0:
            self.squash_timer -= dt
            # Lerp back to 1.0
            self.squash_factor += (pygame.math.Vector2(1.0, 1.0) - self.squash_factor) * 0.2

    def update_animation(self, dt):
        pass # Procedural handled in draw

    def check_collisions(self):
        # Wall Cling
        if not self.is_grounded and not self.is_dashing:
            if self.rect.left <= 0:
                self.on_wall = 'left'
                self.wall_cling_timer = WALL_CLING_TIME
                self.vel.y = min(self.vel.y, 2)
            elif self.rect.right >= SCREEN_WIDTH:
                self.on_wall = 'right'
                self.wall_cling_timer = WALL_CLING_TIME
                self.vel.y = min(self.vel.y, 2)
            else:
                self.on_wall = None
        else:
            self.on_wall = None

        # Floor
        if self.pos.y >= SCREEN_HEIGHT:
            if not self.is_grounded:
                self.spawn_jump_particles() # Landing dust
                self.sound_manager.play("land")
                self.squash_factor = pygame.math.Vector2(1.2, 0.8) # Squash
                self.squash_timer = 10
                
            self.pos.y = SCREEN_HEIGHT
            self.vel.y = 0
            self.is_grounded = True
            self.can_air_dash = True
            self.jump_count = 0
            self.max_jumps = 2 if not self.streber_mode else 3

        # Boss Interaction
        hits = pygame.sprite.spritecollide(self, self.game.boss_bullets, False)
        for projectile in hits:
            if self.is_dashing:
                # Perfect Dash Reward
                if self.perfect_dash_window > 0:
                    self.cards = min(self.cards + 0.5, MAX_CARDS)
                    self.game.effect_manager.add_damage_number(self.rect.center, "PERFECT DASH", color=CYAN, size=16)
                    self.game.effect_manager.apply_slowmo(10, 0.8)
                continue

            if self.parry_active_timer > 0:
                self.handle_parry(projectile)
            elif self.shield_active:
                self.shield_active = False
                projectile.kill()
                self.game.effect_manager.add_damage_number(self.rect.center, "BLOCKED", color=CYAN, size=16)
            elif self.i_frames <= 0:
                self.take_damage()
                projectile.kill()

    def handle_parry(self, projectile):
        if not getattr(projectile, 'is_parryable', False):
            self.sound_manager.play("parry_fail")
            self.take_damage()
            projectile.kill()
            return

        projectile.kill()
        is_perfect = self.perfect_parry_window > 0
        self.sound_manager.play("perfect_parry" if is_perfect else "parry")
        self.game.particle_manager.spawn_parry(self.rect.center, perfect=is_perfect)

        if is_perfect:
            self.cards = min(self.cards + 2, MAX_CARDS)
            self.game.effect_manager.apply_slowmo(20, 0.3)
            self.game.effect_manager.apply_freeze(4)
            self.max_jumps = 3
            self.parry_boost_active = True
            self.game.perfect_parries += 1
        else:
            self.cards = min(self.cards + 1, MAX_CARDS)
            self.parry_boost_active = True

        self.game.total_parries += 1
        self.vel.y = -5 # Small pop up
        self.can_air_dash = True
        self.parry_chain += 1
        self.parry_chain_timer = 300 
        self.parry_counter_timer = 60

        if self.parry_chain >= 3:
            self.streber_mode = True
            self.parry_counter_timer = 600 # 10s
            self.game.effect_manager.add_damage_number(self.rect.center, "STREBER MODE!", color=GOLD, size=32)

    def take_damage(self):
        self.sound_manager.play("hit")
        self.hp -= 1
        self.i_frames = 60
        self.game.effect_manager.apply_shake(20, 10)
        self.game.particle_manager.spawn_hit(self.rect.center, color=RED)
        self.momentum_boost = 1.0
        self.streber_mode = False
        if self.hp <= 0:
            self.game.game_over()

    def check_momentum_chain(self):
        self.momentum_boost = min(2.0, self.momentum_boost + 0.1)

    def spawn_jump_particles(self):
        self.game.particle_manager.spawn_dust((self.rect.centerx, self.rect.bottom))

    def draw(self, screen, camera_offset):
        # Procedural Draw
        draw_x = self.pos.x - camera_offset.x
        draw_y = self.pos.y - camera_offset.y
        
        # Apply Squash/Stretch
        w = self.width * self.squash_factor.x
        h = self.height * self.squash_factor.y
        
        # Color logic
        color = self.color
        if self.streber_mode or self.parry_counter_timer > 0: color = GOLD
        if self.i_frames > 0 and (self.i_frames // 4) % 2 == 0: color = WHITE # Flicker
        
        # Draw Player Rect
        rect = pygame.Rect(0, 0, w, h)
        rect.midbottom = (draw_x, draw_y)
        pygame.draw.rect(screen, color, rect)
        
        # Draw "Face" (Direction)
        eye_offset = 10 if self.facing_right else -10
        pygame.draw.circle(screen, WHITE, (rect.centerx + eye_offset, rect.top + 15), 5)
        
        # Shield
        if self.shield_active:
            pygame.draw.circle(screen, CYAN, rect.center, 50, 2)

        # Afterimage spawning (Manual call here to get the correct rect)
        if self.is_dashing and int(self.dash_timer) % 3 == 0:
            # Create a surface for afterimage
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(surf, color, (0, 0, w, h))
            from effects import AfterimageParticle # Local import to avoid circular?
            self.game.particle_manager.add(AfterimageParticle(pygame.math.Vector2(rect.center), surf, 15, 150))

        # Charge Meter
        if self.is_charging:
            pct = min(1.0, self.charge_timer / CHARGE_TIME)
            pygame.draw.rect(screen, WHITE, (rect.left, rect.top - 10, w * pct, 5))
