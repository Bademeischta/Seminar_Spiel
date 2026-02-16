import pygame
import math
import random
from constants import *

class BossProjectile(pygame.sprite.Sprite):
    def __init__(self, game, x, y, vel_x, vel_y, color=RED, size=(20, 20), is_parryable=False):
        super().__init__()
        self.game = game
        self.width, self.height = size
        self.color = PINK if is_parryable else color
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.center = (x, y)
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(vel_x, vel_y)
        self.is_parryable = is_parryable
        self.angle = 0
        self.rot_speed = random.choice([-5, 5])

    def update(self, dt=1.0):
        self.pos += self.vel * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.angle += self.rot_speed * dt
        
        if (self.rect.right < -200 or self.rect.left > SCREEN_WIDTH + 200 or
            self.rect.bottom < -200 or self.rect.top > SCREEN_HEIGHT + 200):
            self.kill()

    def draw(self, screen, camera_offset):
        # Chalk: Rotate
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(surf, self.color, (0, 0, self.width, self.height))
        
        rotated_surf = pygame.transform.rotate(surf, self.angle)
        new_rect = rotated_surf.get_rect(center=(self.rect.centerx - camera_offset.x, self.rect.centery - camera_offset.y))
        screen.blit(rotated_surf, new_rect)

class BouncingEraser(BossProjectile):
    def __init__(self, game, x, y, size_mult=1.0, speed_mult=1.0):
        size = (int(40 * size_mult), int(40 * size_mult))
        super().__init__(game, x, y, random.choice([-4, 4]) * speed_mult, random.choice([-4, 4]) * speed_mult, color=BROWN, size=size)
        self.timer = 300
        self.speed_up = 1.002
        self.squash = pygame.math.Vector2(1.0, 1.0)
        self.squash_timer = 0

    def update(self, dt=1.0):
        self.vel *= (self.speed_up ** dt)
        self.pos.x += self.vel.x * dt
        self.rect.centerx = int(self.pos.x)
        
        if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
            self.vel.x *= -1
            self.pos.x += self.vel.x * dt # Push back
            self.squash = pygame.math.Vector2(0.6, 1.4) # Vertical stretch on wall hit? Or horizontal squash?
            self.squash_timer = 10
            
        self.pos.y += self.vel.y * dt
        self.rect.centery = int(self.pos.y)
        
        if self.rect.top <= 0 or self.rect.bottom >= SCREEN_HEIGHT:
            self.vel.y *= -1
            self.pos.y += self.vel.y * dt
            self.squash = pygame.math.Vector2(1.4, 0.6) # Horizontal stretch
            self.squash_timer = 10

        self.timer -= dt
        if self.timer <= 0: self.kill()
        
        if self.squash_timer > 0:
            self.squash_timer -= dt
            self.squash += (pygame.math.Vector2(1.0, 1.0) - self.squash) * 0.2

    def draw(self, screen, camera_offset):
        w = self.width * self.squash.x
        h = self.height * self.squash.y
        rect = pygame.Rect(0, 0, w, h)
        rect.center = (self.pos.x - camera_offset.x, self.pos.y - camera_offset.y)
        pygame.draw.rect(screen, self.color, rect)
        pygame.draw.rect(screen, WHITE, rect.inflate(-10, -10), 2) # Detail

class ChalkboardEraser(BossProjectile):
    def __init__(self, game, direction='left'):
        super().__init__(game, 0, 0, 0, 0, color=GRAY, size=(100, SCREEN_HEIGHT))
        if direction == 'left':
            self.pos = pygame.math.Vector2(SCREEN_WIDTH + 50, SCREEN_HEIGHT/2)
            self.vel = pygame.math.Vector2(-12, 0)
        else:
            self.pos = pygame.math.Vector2(-50, SCREEN_HEIGHT/2)
            self.vel = pygame.math.Vector2(12, 0)
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def update(self, dt=1.0):
        self.pos += self.vel * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        if (self.vel.x < 0 and self.rect.right < 0) or (self.vel.x > 0 and self.rect.left > SCREEN_WIDTH):
            self.kill()

class EquationProjectile(BossProjectile):
    def __init__(self, game, x, y, is_parryable=False):
        super().__init__(game, x, y, 0, 3, color=PINK if is_parryable else GRAY, size=(30, 30), is_parryable=is_parryable)
        self.start_x = x
        self.pos_y = float(y)
        self.amplitude = random.randint(40, 60)
        self.frequency = 0.05
        self.offset = random.random() * math.pi * 2
        self.shimmer_time = 0

    def update(self, dt=1.0):
        self.pos_y += self.vel.y * dt
        self.rect.y = int(self.pos_y)
        self.rect.centerx = self.start_x + math.sin(self.pos_y * self.frequency + self.offset) * self.amplitude
        self.shimmer_time += dt
        if self.rect.top > SCREEN_HEIGHT: self.kill()

    def draw(self, screen, camera_offset):
        # Shimmer effect (opacity pulse)
        alpha = int(200 + math.sin(self.shimmer_time * 0.2) * 55)
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        # Draw a symbol like ∑ or π or √
        font = pygame.font.SysFont("Arial", 24, bold=True)
        text = font.render("∑" if not self.is_parryable else "π", True, (*self.color, alpha) if len(self.color) == 3 else self.color)
        rect = text.get_rect(center=(self.width//2, self.height//2))
        surf.blit(text, rect)
        
        screen.blit(surf, (self.rect.x - camera_offset.x, self.rect.y - camera_offset.y))

class ProtractorSpin(BossProjectile):
    def __init__(self, game, boss):
        super().__init__(game, boss.rect.centerx, boss.rect.centery, 0, 0, color=BLUE, size=(200, 200))
        self.boss = boss
        self.angle = 0
        self.timer = 600 # 10 seconds
        self.tips = []

    def update(self, dt=1.0):
        self.angle += 2 * dt
        self.rect.center = self.boss.rect.center
        self.timer -= dt
        if self.timer <= 0: self.kill()
        
        # Update tips for collision checking
        self.tips = []
        center = pygame.math.Vector2(self.rect.center)
        for i in range(4):
            a = math.radians(self.angle + i * 90)
            tip_pos = center + pygame.math.Vector2(math.cos(a) * 100, math.sin(a) * 100)
            self.tips.append(tip_pos)
            
            # Check collision with player parry
            if self.game.player.parry_active_timer > 0:
                dist = tip_pos.distance_to(self.game.player.rect.center)
                if dist < 30: # Hit tip
                    # Trigger parry logic manually since this isn't a sprite collision
                    self.game.player.handle_parry(self)
                    self.boss.stun(120) # 2 seconds stun
                    self.kill()
                    return

    def draw(self, screen, camera_offset):
        center = (self.rect.centerx - camera_offset.x, self.rect.centery - camera_offset.y)
        pygame.draw.circle(screen, self.color, center, 100, 5)
        # Draw 4 tips
        for i in range(4):
            a = math.radians(self.angle + i * 90)
            tip_pos = (center[0] + math.cos(a) * 100, center[1] + math.sin(a) * 100)
            pygame.draw.circle(screen, PINK, tip_pos, 10)

class Laser(BossProjectile):
    def __init__(self, game, y, duration=30, rotation_speed=0):
        super().__init__(game, SCREEN_WIDTH//2, y, 0, 0, color=YELLOW, size=(SCREEN_WIDTH, 40))
        self.timer = duration
        self.state = 'charge'
        self.charge_timer = 60 # 1 sec charge
        self.rotation_speed = rotation_speed
        self.angle = 0
        self.pivot = pygame.math.Vector2(0, y) if rotation_speed > 0 else pygame.math.Vector2(SCREEN_WIDTH, y)

    def update(self, dt=1.0):
        if self.state == 'charge':
            self.charge_timer -= dt
            if self.charge_timer <= 0:
                self.state = 'fire'
        else:
            self.timer -= dt
            if self.timer <= 0: self.kill()
            
        if self.rotation_speed != 0:
            self.angle += self.rotation_speed * dt
            # Update rect for collision (simplified to a line check usually, but here we keep rect for now)
            # Complex laser rotation collision is hard with AABB. 
            # For sweeping laser, we might need a mask or multiple hitboxes.
            # Simplified: Moves vertically? No, rotates.
            pass

    def draw(self, screen, camera_offset):
        if self.state == 'charge':
            # Scanline effect
            rect = pygame.Rect(0, self.rect.y - camera_offset.y, SCREEN_WIDTH, 2)
            rect.y += (pygame.time.get_ticks() % 40)
            pygame.draw.rect(screen, RED, rect)
            pygame.draw.line(screen, RED, (0, self.rect.centery - camera_offset.y), (SCREEN_WIDTH, self.rect.centery - camera_offset.y), 1)
        else:
            # Full beam
            if self.rotation_speed == 0:
                rect = self.rect.copy()
                rect.y -= camera_offset.y
                pygame.draw.rect(screen, self.color, rect)
            else:
                # Draw rotated line
                start = self.pivot - camera_offset
                end = start + pygame.math.Vector2(SCREEN_WIDTH * 2, 0).rotate(self.angle)
                pygame.draw.line(screen, self.color, start, end, 40)

class TextbookSlam(BossProjectile):
    def __init__(self, game, x):
        super().__init__(game, x, -200, 0, 0, color=DARK_RED, size=(200, 100))
        self.target_x = x
        self.timer = 90 # 1.5s warning
        self.state = 'warning'
        self.pos.x = x

    def update(self, dt=1.0):
        if self.state == 'warning':
            self.timer -= dt
            if self.timer <= 0:
                self.state = 'slam'
                self.vel.y = 20
        elif self.state == 'slam':
            self.pos.y += self.vel.y * dt
            self.rect.centery = int(self.pos.y)
            if self.rect.top > SCREEN_HEIGHT: self.kill()

    def draw(self, screen, camera_offset):
        if self.state == 'warning':
            # Draw shadow
            pygame.draw.rect(screen, (255, 0, 0, 100), (self.target_x - 100 - camera_offset.x, SCREEN_HEIGHT - 20, 200, 20))
        
        # Draw Book
        rect = self.rect.copy()
        rect.x -= camera_offset.x
        rect.y -= camera_offset.y
        pygame.draw.rect(screen, self.color, rect)
        # Pages
        pygame.draw.rect(screen, WHITE, rect.inflate(-10, -10))
