import pygame
import math
import random
from constants import *
from projectiles import PlayerProjectile, EXFlieger, EXEraser, EXRuler, EXSuper
from utils import SpriteLoader

class Player(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        super().__init__()
        self.game = game
        self.sprite_loader = SpriteLoader()
        self.image = self.sprite_loader.get_sprite("sprites/Spieler/Spieler.jpeg", scale=1.0)
        self.rect = self.image.get_rect()
        self.rect.bottomleft = (x, y)

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
        self.on_wall = None # 'left' or 'right'
        self.wall_cling_timer = 0
        self.momentum_chain_timer = 0
        self.momentum_boost = 1.0

        # Jump
        self.jump_count = 0
        self.max_jumps = 2 # Initial, becomes 3 with Perfect Parry
        self.jump_timer = 0
        self.max_jump_frames = 15

        # Dash
        self.is_dashing = False
        self.dash_timer = 0
        self.dash_cooldown_timer = 0
        self.can_air_dash = True
        self.dash_direction = pygame.math.Vector2(1, 0)
        self.is_super_dash = False

        # Invincibility
        self.i_frames = 0

        # Parry
        self.parry_active_timer = 0
        self.perfect_parry_window = 0
        self.parry_chain = 0
        self.parry_chain_timer = 0
        self.parry_counter_timer = 0

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

        # Shield
        if keys[pygame.K_e] and self.shield_cooldown <= 0:
            self.activate_shield()

        # EX Switch
        if keys[pygame.K_1]: self.selected_ex = "Flieger"
        if keys[pygame.K_2]: self.selected_ex = "Eraser"
        if keys[pygame.K_3]: self.selected_ex = "Ruler"

    def jump(self):
        # Wall Jump
        if self.on_wall:
            self.game.sound_manager.play("jump")
            self.vel.y = PLAYER_JUMP_FORCE
            self.vel.x = 10 if self.on_wall == 'left' else -10
            self.jump_count = 1
            self.on_wall = None
            self.check_momentum_chain()
            return

        # Air/Double/Triple Jump
        if self.jump_count < self.max_jumps:
            self.game.sound_manager.play("jump")
            self.vel.y = PLAYER_JUMP_FORCE
            if self.jump_count > 0: # Air jump
                keys = pygame.key.get_pressed()
                if keys[pygame.K_a]: self.vel.x = -PLAYER_MAX_SPEED
                if keys[pygame.K_d]: self.vel.x = PLAYER_MAX_SPEED

            self.jump_timer = self.max_jump_frames
            self.jump_count += 1
            self.is_grounded = False
            self.drop_timer = 0

    def dash(self):
        if self.dash_cooldown_timer <= 0:
            cost = 1 if (pygame.key.get_pressed()[pygame.K_LCTRL] or self.is_super_dash_ready()) else 0
            if cost == 1 and self.cards >= 1:
                self.cards -= 1
                self.is_super_dash = True
            else:
                self.is_super_dash = False

            if self.is_grounded or self.can_air_dash:
                self.game.sound_manager.play("dash")
                self.is_dashing = True
                self.dash_timer = PLAYER_DASH_DURATION * (2 if self.is_super_dash else 1)
                self.dash_cooldown_timer = PLAYER_DASH_COOLDOWN
                self.i_frames = self.dash_timer

                if not self.is_grounded:
                    self.can_air_dash = False

                # 8-direction dash
                keys = pygame.key.get_pressed()
                dir_x = 0
                dir_y = 0
                if keys[pygame.K_a]: dir_x = -1
                elif keys[pygame.K_d]: dir_x = 1
                if keys[pygame.K_w]: dir_y = -1
                elif keys[pygame.K_s]: dir_y = 1

                if dir_x == 0 and dir_y == 0:
                    dir_x = 1 if self.facing_right else -1

                # Slam-Down (Down + Dash)
                if dir_y == 1 and not self.is_grounded:
                    self.vel.y = PLAYER_DASH_SPEED * 1.5
                    # Special logic for slam if needed

                self.dash_direction = pygame.math.Vector2(dir_x, dir_y).normalize()
                if dir_x != 0: self.facing_right = dir_x > 0

    def is_super_dash_ready(self):
        # Logic to trigger super dash if wanted, maybe double tap shift?
        # For now let's say holding Control + Dash or if we have a card and want it.
        return False

    def activate_shield(self):
        self.shield_active = True
        self.shield_cooldown = SHIELD_COOLDOWN
        # Duration handled in update

    def shoot_basic(self):
        if self.shoot_timer <= 0:
            self.game.sound_manager.play("shoot")
            damage = 1
            color = BLUE
            if self.parry_counter_timer > 0:
                damage *= 2
                color = GOLD

            # Risk bonus check
            dist = pygame.math.Vector2(self.rect.center).distance_to(self.game.boss.rect.center)
            if dist < 100: # adjusted from 20px as it's very close
                self.cards = min(self.cards + 0.05, MAX_CARDS)

            bullet = PlayerProjectile(self.game, self.rect.centerx, self.rect.centery,
                                     12 if self.facing_right else -12, 0, damage, color)
            self.game.all_sprites.add(bullet)
            self.game.player_bullets.add(bullet)
            self.shoot_timer = 10

    def shoot_charge(self):
        self.game.sound_manager.play("charge_shot")
        bullet = PlayerProjectile(self.game, self.rect.centerx, self.rect.centery,
                                 15 if self.facing_right else -15, 0, 3, LIGHT_BLUE, size=(30, 30))
        self.game.all_sprites.add(bullet)
        self.game.player_bullets.add(bullet)

    def shoot_ex(self):
        if self.cards >= 5:
            self.game.sound_manager.play("ultimate")
            self.cards -= 5
            bullet = EXSuper(self.game, self.rect.centerx, self.rect.centery, 1 if self.facing_right else -1)
            self.game.all_sprites.add(bullet)
            self.game.player_bullets.add(bullet)
            self.game.effect_manager.apply_shake(60, 15)
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
                self.game.sound_manager.play("ex_attack")
                self.game.all_sprites.add(bullet)
                self.game.player_bullets.add(bullet)

    def update(self, dt=1.0):
        self.handle_input()
        self.apply_gravity(dt)
        self.update_physics(dt)
        self.check_collisions()
        self.update_timers(dt)

    def apply_gravity(self, dt):
        if not self.is_dashing and not self.on_wall:
            keys = pygame.key.get_pressed()
            g = GRAVITY
            if self.game.inverted_gravity:
                g = -GRAVITY

            current_gravity = g * 0.5 if (keys[pygame.K_SPACE] and self.vel.y < 0) else g
            self.vel.y += current_gravity * dt

    def update_physics(self, dt):
        if self.is_dashing:
            speed = PLAYER_DASH_SPEED * (2 if self.is_super_dash else 1)
            self.vel = self.dash_direction * speed
            self.pos += self.vel * dt
            # Trail
            color = BLUE if not self.is_super_dash else CYAN
            self.game.particle_manager.spawn_trail(self.rect.center, color, 40)
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

        if self.dash_cooldown_timer > 0: self.dash_cooldown_timer -= dt
        if self.i_frames > 0: self.i_frames -= dt
        if self.parry_active_timer > 0:
            self.parry_active_timer -= dt
            self.perfect_parry_window -= dt

        if self.parry_chain_timer > 0:
            self.parry_chain_timer -= dt
            if self.parry_chain_timer <= 0: self.parry_chain = 0

        if self.parry_counter_timer > 0: self.parry_counter_timer -= dt
        if self.shoot_timer > 0: self.shoot_timer -= dt
        if self.shield_cooldown > 0: self.shield_cooldown -= dt

        if self.on_wall:
            self.wall_cling_timer -= dt
            if self.wall_cling_timer <= 0: self.on_wall = None

    def check_collisions(self):
        # Wall Cling check
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

        # Boss and Projectiles
        if self.i_frames <= 0:
            if self.rect.colliderect(self.game.boss.rect):
                self.take_damage()

            hits = pygame.sprite.spritecollide(self, self.game.boss_bullets, False)
            for projectile in hits:
                if self.is_dashing:
                    # Perfect Dash check
                    self.cards = min(self.cards + 0.5, MAX_CARDS)
                    continue

                if self.parry_active_timer > 0:
                    self.handle_parry(projectile)
                elif self.shield_active:
                    self.shield_active = False # Shield used
                    projectile.kill()
                else:
                    self.take_damage()
                    projectile.kill()

        # Floor/Platforms (Similar to prototype but with dt)
        if self.pos.y >= SCREEN_HEIGHT:
            self.pos.y = SCREEN_HEIGHT
            self.vel.y = 0
            self.is_grounded = True
            self.can_air_dash = True
            self.jump_count = 0
            self.max_jumps = 2
        else:
            self.is_grounded = False

    def handle_parry(self, projectile):
        if not getattr(projectile, 'is_parryable', False):
            self.game.sound_manager.play("parry_fail")
            self.take_damage()
            projectile.kill()
            return

        projectile.kill()
        is_perfect = self.perfect_parry_window > 0
        self.game.sound_manager.play("perfect_parry" if is_perfect else "parry")

        self.game.effect_manager.apply_freeze(4 if is_perfect else 2)
        self.game.particle_manager.spawn_parry(self.rect.center)

        if is_perfect:
            self.cards = min(self.cards + 2, MAX_CARDS)
            self.game.effect_manager.apply_slowmo(20, 0.3)
            self.max_jumps = 3
        else:
            self.cards = min(self.cards + 1, MAX_CARDS)

        self.vel.y = PLAYER_JUMP_FORCE
        self.jump_count = 1
        self.can_air_dash = True

        self.parry_chain += 1
        self.parry_chain_timer = 300 # 5 seconds
        self.parry_counter_timer = 60 # 1 second of double damage

        if self.parry_chain >= 3:
            self.activate_streber_mode()

    def activate_streber_mode(self):
        # 10 seconds of golden shots
        self.parry_counter_timer = 600
        self.game.effect_manager.apply_shake(30, 5)

    def check_momentum_chain(self):
        # Implementation of wall jump speed boost
        self.momentum_boost = min(2.0, self.momentum_boost + 0.1)

    def take_damage(self):
        if self.i_frames <= 0:
            self.game.sound_manager.play("hit")
            self.hp -= 1
            self.i_frames = 60
            self.game.effect_manager.apply_shake(20, 10)
            self.game.particle_manager.spawn_hit(self.rect.center, color=RED)
            self.momentum_boost = 1.0
            if self.hp <= 0:
                self.game.game_over()

    def draw(self, screen, camera_offset):
        # Drawing with i-frame flicker and other visuals
        draw_pos = (self.rect.x - camera_offset.x, self.rect.y - camera_offset.y)

        image = self.image
        if not self.facing_right:
            image = pygame.transform.flip(image, True, False)

        if self.i_frames > 0 and (int(self.i_frames) // 4) % 2 == 0:
            # Simple way to flicker without modifying image
            pass
        else:
            screen.blit(image, draw_pos)

        if self.parry_counter_timer > 60: # Streber mode glow
            pygame.draw.rect(screen, GOLD, (draw_pos[0], draw_pos[1], self.rect.width, self.rect.height), 2)

        if self.is_charging:
            charge_pct = min(1.0, self.charge_timer / CHARGE_TIME)
            pygame.draw.rect(screen, WHITE, (draw_rect.x, draw_rect.y - 10, 40 * charge_pct, 5))

        if self.shield_active:
            pygame.draw.circle(screen, CYAN, (draw_rect.centerx, draw_rect.centery), 45, 2)
