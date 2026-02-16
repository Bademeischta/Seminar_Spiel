import pygame
import sys
import random
import math

# --- Constants ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
LIGHT_RED = (255, 100, 100)
DARK_RED = (150, 0, 0)
ORANGE = (255, 165, 0)
BLUE = (0, 0, 255)
LIGHT_BLUE = (100, 100, 255)
GREEN = (0, 255, 0)
GRAY = (150, 150, 150)
PINK = (255, 105, 180)
BROWN = (139, 69, 19)
YELLOW = (255, 255, 0)

# Physics
GRAVITY = 0.6
PLAYER_ACC = 0.8
PLAYER_FRICTION = -0.12
PLAYER_MAX_SPEED = 6.0
PLAYER_JUMP_FORCE = -12
PLAYER_DASH_SPEED = 15
PLAYER_DASH_DURATION = 10 # frames (approx 150px at speed 15)
PLAYER_DASH_COOLDOWN = 60 # frames (1s)

class Boss(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((80, 120))
        self.color = LIGHT_RED
        self.rect = self.image.get_rect()
        self.rect.midright = (950, 450)

        self.hp = 100
        self.max_hp = 100
        self.phase = 1

        self.pos = pygame.math.Vector2(self.rect.center)
        self.target_pos = pygame.math.Vector2(self.rect.center)

        # Behavior timers
        self.attack_timer = 120 # Initial wait
        self.attack_state = 0
        self.move_timer = 0
        self.vibrate_offset = pygame.math.Vector2(0, 0)

        # State
        self.is_invincible = False # For transitions maybe
        self.float_offset = 0
        self.laser_warning_y = -1
        self.laser_timer = 0

    def update(self):
        self.check_phase()
        self.update_behavior()
        self.update_laser()
        self.check_collisions()

        # Update rect position based on pos and vibration
        self.rect.center = self.pos + self.vibrate_offset

    def check_phase(self):
        if self.hp > 70:
            self.phase = 1
            self.color = LIGHT_RED
        elif self.hp > 30:
            self.phase = 2
            self.color = ORANGE
        elif self.hp > 0:
            self.phase = 3
            self.color = DARK_RED
        else:
            self.kill() # Boss dead

    def update_behavior(self):
        # Movement
        if self.phase == 1:
            self.pos = pygame.math.Vector2(910, 450)
            self.vibrate_offset = pygame.math.Vector2(0, 0)
        elif self.phase == 2:
            self.float_offset += 0.05
            self.pos.y = 300 + math.sin(self.float_offset) * 150
            self.pos.x = 850
            self.vibrate_offset = pygame.math.Vector2(0, 0)
        elif self.phase == 3:
            self.vibrate_offset = pygame.math.Vector2(random.randint(-3, 3), random.randint(-3, 3))
            self.move_timer += 1
            if self.move_timer > 90:
                self.teleport()
                self.move_timer = 0

        # Attacks
        self.attack_timer -= 1
        if self.attack_timer <= 0:
            self.run_attack()

    def run_attack(self):
        if self.phase == 1:
            if self.attack_state == 0: # Geometry Shot
                self.geometry_shot()
            else: # Bouncing Eraser
                self.bouncing_eraser()

            self.attack_state = (self.attack_state + 1) % 2
            self.attack_timer = 180 # 3 seconds between attacks

        elif self.phase == 2:
            if self.attack_state == 0: # Chalkboard Eraser
                self.chalkboard_eraser()
            else: # Equation Rain
                self.equation_rain()

            self.attack_state = (self.attack_state + 1) % 2
            self.attack_timer = 180

        elif self.phase == 3:
            if self.attack_state == 0: # Compass Hell
                self.compass_hell()
            else: # Pointer of Death
                self.pointer_of_death()

            self.attack_state = (self.attack_state + 1) % 2
            self.attack_timer = 180

    def geometry_shot(self):
        # 3 shots, 3rd is pink
        for i in range(3):
            is_pink = (i == 2)
            p = BossProjectile(self.game, self.rect.left, self.rect.centery, -5, 0, color=GREEN, is_parryable=is_pink)
            # Offset: i=0 is furthest (first shot), i=2 is at boss (last shot)
            p.rect.x -= (2 - i) * 150
            self.game.all_sprites.add(p)
            self.game.boss_bullets.add(p)

    def bouncing_eraser(self):
        eraser = BouncingEraser(self.game, self.rect.centerx, self.rect.centery)
        self.game.all_sprites.add(eraser)
        self.game.boss_bullets.add(eraser)

    def chalkboard_eraser(self):
        eraser = ChalkboardEraser(self.game)
        self.game.all_sprites.add(eraser)
        self.game.boss_bullets.add(eraser)

    def equation_rain(self):
        # Spawn 10 falling equations, 5th is pink
        for i in range(10):
            is_pink = (i == 4)
            x = random.randint(50, 950)
            eq = EquationProjectile(self.game, x, is_parryable=is_pink)
            # Offset: first ones are lower down
            eq.pos_y = -(9 - i) * 150
            self.game.all_sprites.add(eq)
            self.game.boss_bullets.add(eq)

    def compass_hell(self):
        # 8 directions, 3 bursts
        for burst in range(3):
            for i in range(8):
                angle = (i * 45) # Classic compass directions
                rad = math.radians(angle)
                vel_x = math.cos(rad) * 5
                vel_y = math.sin(rad) * 5
                p = BossProjectile(self.game, self.rect.centerx, self.rect.centery, vel_x, vel_y)
                # Offset: burst 0 is furthest out
                offset = (2 - burst) * 40
                p.rect.x += vel_x * offset
                p.rect.y += vel_y * offset
                self.game.all_sprites.add(p)
                self.game.boss_bullets.add(p)

    def pointer_of_death(self):
        self.laser_warning_y = self.game.player.rect.centery
        self.laser_timer = 60 # 1 second warning

    def update_laser(self):
        if self.laser_timer > 0:
            self.laser_timer -= 1
            if self.laser_timer == 0:
                laser = Laser(self.game, self.laser_warning_y - 20)
                self.game.all_sprites.add(laser)
                self.game.boss_bullets.add(laser)
                self.laser_warning_y = -1

    def teleport(self):
        # Teleport to a random position, avoiding the player
        valid = False
        while not valid:
            new_x = random.randint(100, 900)
            new_y = random.randint(100, 500)
            dist = pygame.math.Vector2(new_x, new_y).distance_to(self.game.player.pos)
            if dist > 200:
                self.pos = pygame.math.Vector2(new_x, new_y)
                valid = True

    def check_collisions(self):
        # Collision with player bullets
        hits = pygame.sprite.spritecollide(self, self.game.player_bullets, True)
        for bullet in hits:
            self.hp -= bullet.damage
            if self.hp < 0: self.hp = 0

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        if self.laser_warning_y != -1:
            pygame.draw.line(screen, RED, (0, self.laser_warning_y), (SCREEN_WIDTH, self.laser_warning_y), 2)

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.color = GRAY

class Player(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((40, 60))
        self.color = BLUE
        self.rect = self.image.get_rect()
        self.rect.bottomleft = (x, y)

        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(0, 0)
        self.acc = pygame.math.Vector2(0, 0)

        # Stats
        self.hp = 3
        self.cards = 0
        self.max_cards = 5

        # State
        self.facing_right = True
        self.is_grounded = False

        # Jump
        self.jump_timer = 0
        self.max_jump_frames = 15

        # Dash
        self.is_dashing = False
        self.dash_timer = 0
        self.dash_cooldown_timer = 0
        self.can_air_dash = True
        self.dash_direction = pygame.math.Vector2(1, 0)

        # Invincibility
        self.i_frames = 0

        # Parry
        self.parry_active_timer = 0

        # Drop through platform
        self.drop_timer = 0

    def jump(self):
        if self.is_grounded:
            self.vel.y = PLAYER_JUMP_FORCE
            self.jump_timer = self.max_jump_frames
            self.is_grounded = False
            self.drop_timer = 0 # Cancel drop through if jumping

    def dash(self):
        if self.dash_cooldown_timer <= 0:
            if self.is_grounded or self.can_air_dash:
                self.is_dashing = True
                self.dash_timer = PLAYER_DASH_DURATION
                self.dash_cooldown_timer = PLAYER_DASH_COOLDOWN
                self.i_frames = PLAYER_DASH_DURATION

                if not self.is_grounded:
                    self.can_air_dash = False

                # Determine direction
                keys = pygame.key.get_pressed()
                if keys[pygame.K_a]:
                    self.dash_direction = pygame.math.Vector2(-1, 0)
                    self.facing_right = False
                elif keys[pygame.K_d]:
                    self.dash_direction = pygame.math.Vector2(1, 0)
                    self.facing_right = True
                else:
                    self.dash_direction = pygame.math.Vector2(1 if self.facing_right else -1, 0)

    def shoot(self):
        # Basic shot
        bullet = Bullet(self.game, self.rect.centerx, self.rect.centery, 1 if self.facing_right else -1)
        self.game.all_sprites.add(bullet)
        self.game.player_bullets.add(bullet)

    def shoot_ex(self):
        if self.cards >= 1:
            self.cards -= 1
            bullet = EXBullet(self.game, self.rect.centerx, self.rect.centery, 1 if self.facing_right else -1)
            self.game.all_sprites.add(bullet)
            self.game.player_bullets.add(bullet)

    def update(self):
        self.handle_input()
        self.apply_gravity()
        self.update_physics()
        self.check_collisions()

        # Timers
        if self.dash_timer > 0:
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                self.is_dashing = False

        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= 1

        if self.i_frames > 0:
            self.i_frames -= 1

        if self.parry_active_timer > 0:
            self.parry_active_timer -= 1

    def handle_input(self):
        keys = pygame.key.get_pressed()

        if not self.is_dashing:
            self.acc = pygame.math.Vector2(0, 0)
            if keys[pygame.K_a]:
                self.acc.x = -PLAYER_ACC
                self.facing_right = False
            elif keys[pygame.K_d]:
                self.acc.x = PLAYER_ACC
                self.facing_right = True

            # Variable Jump
            if keys[pygame.K_SPACE]:
                if self.jump_timer > 0:
                    # Apply a small upward force while held to counteract gravity
                    self.vel.y -= 0.3
                    self.jump_timer -= 1
            else:
                self.jump_timer = 0

    def apply_gravity(self):
        if not self.is_dashing:
            # Reduced gravity while holding jump
            keys = pygame.key.get_pressed()
            current_gravity = GRAVITY * 0.5 if (keys[pygame.K_SPACE] and self.vel.y < 0) else GRAVITY
            self.vel.y += current_gravity

    def update_physics(self):
        if self.is_dashing:
            self.vel = self.dash_direction * PLAYER_DASH_SPEED
            self.pos += self.vel
        else:
            self.acc.x += self.vel.x * PLAYER_FRICTION
            self.vel.x += self.acc.x
            if abs(self.vel.x) > PLAYER_MAX_SPEED:
                self.vel.x = PLAYER_MAX_SPEED * (1 if self.vel.x > 0 else -1)

            self.pos += self.vel + 0.5 * self.acc

        self.rect.midbottom = (int(self.pos.x), int(self.pos.y))

    def take_damage(self):
        self.hp -= 1
        self.i_frames = 60 # 1 second of invincibility
        if self.hp <= 0:
            self.game.reset_game() # Simple reset for now

    def parry_success(self, projectile):
        projectile.kill()
        self.parry_active_timer = 0
        self.vel.y = PLAYER_JUMP_FORCE
        self.jump_timer = 0 # Reset jump timer to avoid double jumping too high if still holding space
        self.cards = min(self.cards + 1, self.max_cards)
        self.can_air_dash = True # Refresh dash on parry

    def check_collisions(self):
        # Collision with boss or boss projectiles
        if self.i_frames <= 0:
            # Check boss body
            if self.rect.colliderect(self.game.boss.rect):
                self.take_damage()

            # Check boss projectiles
            hits = pygame.sprite.spritecollide(self, self.game.boss_bullets, False)
            for projectile in hits:
                # Parry check
                if projectile.is_parryable and self.parry_active_timer > 0:
                    self.parry_success(projectile)
                else:
                    self.take_damage()
                    projectile.kill()

        # Floor collision
        if self.pos.y >= SCREEN_HEIGHT:
            self.pos.y = SCREEN_HEIGHT
            self.vel.y = 0
            self.is_grounded = True
            self.can_air_dash = True
        else:
            self.is_grounded = False

        # Platform collision
        if self.vel.y >= 0: # Only collide while falling
            if self.drop_timer > 0:
                self.drop_timer -= 1
            else:
                hits = pygame.sprite.spritecollide(self, self.game.platforms, False)
                for hit in hits:
                    # Check if player was above the platform in the previous frame
                    if self.pos.y - self.vel.y <= hit.rect.top:
                        self.pos.y = hit.rect.top
                        self.vel.y = 0
                        self.is_grounded = True
                        self.can_air_dash = True

    def draw(self, screen):
        color = self.color
        if self.i_frames > 0:
            # Flicker if invincible
            if (self.i_frames // 4) % 2 == 0:
                color = LIGHT_BLUE

        pygame.draw.rect(screen, color, self.rect)

        # Parry visual
        if self.parry_active_timer > 0:
            pygame.draw.circle(screen, PINK, self.rect.center, 40, 3)

class BouncingEraser(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((40, 40))
        self.rect = self.image.get_rect(center=(x, y))
        self.color = BROWN
        self.vel = pygame.math.Vector2(random.choice([-4, 4]), random.choice([-4, 4]))
        self.timer = 300 # 5 seconds at 60fps
        self.speed_up = 1.002

    def update(self):
        self.vel *= self.speed_up
        self.rect.x += self.vel.x
        self.rect.y += self.vel.y

        # Bouncing logic
        if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
            self.vel.x *= -1
            self.rect.x += self.vel.x # Move out of wall
        if self.rect.top <= 0 or self.rect.bottom >= SCREEN_HEIGHT:
            self.vel.y *= -1
            self.rect.y += self.vel.y # Move out of wall

        self.timer -= 1
        if self.timer <= 0:
            self.kill()

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

class ChalkboardEraser(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((100, SCREEN_HEIGHT))
        self.rect = self.image.get_rect(topleft=(SCREEN_WIDTH, 0))
        self.color = GRAY
        self.vel = pygame.math.Vector2(-8, 0)

    def update(self):
        self.rect.x += self.vel.x
        if self.rect.right < 0:
            self.kill()

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

class EquationProjectile(pygame.sprite.Sprite):
    def __init__(self, game, x, is_parryable=False):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((30, 30))
        self.rect = self.image.get_rect(midtop=(x, 0))
        self.start_x = x
        self.pos_y = 0.0
        self.color = PINK if is_parryable else GRAY
        self.is_parryable = is_parryable
        self.vel_y = 3
        self.amplitude = random.randint(40, 60)
        self.frequency = 0.05
        self.offset = random.random() * math.pi * 2

    def update(self):
        self.pos_y += self.vel_y
        self.rect.y = int(self.pos_y)
        self.rect.centerx = self.start_x + math.sin(self.pos_y * self.frequency + self.offset) * self.amplitude

        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

class Laser(pygame.sprite.Sprite):
    def __init__(self, game, y):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((SCREEN_WIDTH, 40))
        self.rect = self.image.get_rect(topleft=(0, y))
        self.color = YELLOW
        self.timer = 30 # Duration of laser

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            self.kill()

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

class BossProjectile(pygame.sprite.Sprite):
    def __init__(self, game, x, y, vel_x, vel_y, color=RED, is_parryable=False):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((20, 20))
        self.rect = self.image.get_rect(center=(x, y))
        self.vel = pygame.math.Vector2(vel_x, vel_y)
        self.color = PINK if is_parryable else color
        self.is_parryable = is_parryable

    def update(self):
        self.rect.x += self.vel.x
        self.rect.y += self.vel.y

        if (self.rect.right < -100 or self.rect.left > SCREEN_WIDTH + 100 or
            self.rect.bottom < -100 or self.rect.top > SCREEN_HEIGHT + 100):
            self.kill()

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, game, x, y, direction):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((10, 10))
        self.color = BLUE
        self.rect = self.image.get_rect(center=(x, y))
        self.vel = pygame.math.Vector2(direction * 10, 0)
        self.damage = 1

    def update(self):
        self.rect.x += self.vel.x
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()

class EXBullet(pygame.sprite.Sprite):
    def __init__(self, game, x, y, direction):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((40, 30))
        self.color = BLUE
        # Draw triangle
        self.rect = self.image.get_rect(center=(x, y))
        self.vel = pygame.math.Vector2(direction * 12, 0)
        self.damage = 5

    def update(self):
        self.rect.x += self.vel.x
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()

    def draw(self, screen):
        # Draw a triangle pointing in direction
        p1 = self.rect.midleft if self.vel.x < 0 else self.rect.midright
        p2 = self.rect.topright if self.vel.x < 0 else self.rect.topleft
        p3 = self.rect.bottomright if self.vel.x < 0 else self.rect.bottomleft
        pygame.draw.polygon(screen, self.color, [p1, p2, p3])

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Boss Fight Prototype - Dr. Pythagoras")
        self.clock = pygame.time.Clock()
        self.running = True

        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()
        self.boss_bullets = pygame.sprite.Group()

        self.reset_game()

    def reset_game(self):
        self.all_sprites.empty()
        self.platforms.empty()
        self.player_bullets.empty()
        self.boss_bullets.empty()

        # Create Platforms (Pyramid Layout)
        # Center: Y=350
        # Left/Right: Y=450
        p1 = Platform(400, 350, 200, 10) # Center
        p2 = Platform(150, 450, 200, 10) # Left
        p3 = Platform(650, 450, 200, 10) # Right

        self.platforms.add(p1, p2, p3)
        self.all_sprites.add(p1, p2, p3)

        self.player = Player(self, 100, SCREEN_HEIGHT)
        self.all_sprites.add(self.player)

        self.boss = Boss(self)
        self.all_sprites.add(self.boss)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                if self.player.hp <= 0 or self.boss.hp <= 0:
                    if event.key == pygame.K_RETURN:
                        self.reset_game()
                    return

                if event.key == pygame.K_SPACE:
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                        self.player.drop_timer = 15 # Allow falling through for 15 frames
                    else:
                        # If already in air and pressing space, it might be a parry attempt
                        if not self.player.is_grounded:
                            self.player.parry_active_timer = 15 # Parry window
                        self.player.jump()

                if event.key == pygame.K_LSHIFT:
                    self.player.dash()

                if event.key == pygame.K_q:
                    self.player.shoot_ex()

                if event.key == pygame.K_RETURN:
                    # Basic shoot for now, maybe move to mouse button too
                    self.player.shoot()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    self.player.shoot()
                if event.button == 3: # Right click
                    self.player.shoot_ex()

    def update(self):
        if self.player.hp > 0 and self.boss.hp > 0:
            self.all_sprites.update()

    def draw(self):
        self.screen.fill(BLACK)

        # Draw platforms
        for plat in self.platforms:
            pygame.draw.rect(self.screen, GRAY, plat.rect)

        # Draw all sprites
        for sprite in self.all_sprites:
            if hasattr(sprite, 'draw'):
                sprite.draw(self.screen)
            else:
                pygame.draw.rect(self.screen, sprite.color if hasattr(sprite, 'color') else WHITE, sprite.rect)

        self.draw_ui()

        if self.player.hp <= 0:
            self.draw_text("GAME OVER", 60, SCREEN_WIDTH//2, SCREEN_HEIGHT//2, RED)
            self.draw_text("Press ENTER to Restart", 30, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60, WHITE)
        elif self.boss.hp <= 0:
            self.draw_text("KNOCKOUT!", 60, SCREEN_WIDTH//2, SCREEN_HEIGHT//2, YELLOW)
            self.draw_text("Press ENTER to Restart", 30, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60, WHITE)

        pygame.display.flip()

    def draw_ui(self):
        # Player HP (Top Left)
        for i in range(3):
            rect = pygame.Rect(20 + i * 40, 20, 30, 30)
            if i < self.player.hp:
                pygame.draw.rect(self.screen, RED, rect)
            else:
                pygame.draw.rect(self.screen, RED, rect, 2)

        # Special Meter (Below HP)
        for i in range(5):
            rect = pygame.Rect(20 + i * 35, 60, 30, 45)
            if i < self.player.cards:
                pygame.draw.rect(self.screen, BLUE, rect)
                # Card decoration
                pygame.draw.rect(self.screen, WHITE, rect.inflate(-10, -10), 1)
            else:
                pygame.draw.rect(self.screen, BLUE, rect, 2)

        # Boss HP (Top Right)
        if self.boss.alive():
            hp_width = 300
            hp_rect_bg = pygame.Rect(SCREEN_WIDTH - hp_width - 20, 20, hp_width, 20)
            pygame.draw.rect(self.screen, GRAY, hp_rect_bg, 2)

            hp_fill = (self.boss.hp / self.boss.max_hp) * hp_width
            hp_rect_fill = pygame.Rect(SCREEN_WIDTH - hp_width - 20, 20, hp_fill, 20)
            pygame.draw.rect(self.screen, self.boss.color, hp_rect_fill)

            self.draw_text("Dr. Pythagoras", 20, SCREEN_WIDTH - 170, 50, WHITE)

    def draw_text(self, text, size, x, y, color):
        font = pygame.font.SysFont("Arial", size, bold=True)
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(x, y))
        self.screen.blit(surf, rect)

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
