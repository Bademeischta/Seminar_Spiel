import pygame
import math
import random
from constants import *
from projectiles import BaseProjectile
from utils import get_font

EQUATION_FONT = None

class BossProjectile(BaseProjectile):
    def __init__(self, game, x, y, vel_x, vel_y, color=COLOR_RED, size=(20, 20), is_parryable=False):
        super().__init__(game, x, y, vel_x, vel_y, 1, COLOR_PINK if is_parryable else color, size)
        self.is_parryable = is_parryable
        self.rot_speed = random.choice([-300, 300]) # 5 * 60

    def update(self, dt):
        super().update(dt)
        self.angle += self.rot_speed * dt

    def draw(self, screen, camera_offset):
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(surf, self.color, (0, 0, self.width, self.height))
        
        rotated_surf = pygame.transform.rotate(surf, self.angle)
        new_rect = rotated_surf.get_rect(center=(self.rect.centerx - camera_offset.x, self.rect.centery - camera_offset.y))
        screen.blit(rotated_surf, new_rect)

class BouncingEraser(BossProjectile):
    def __init__(self, game, x, y, size_mult=1.0, speed_mult=1.0):
        size = (int(40 * size_mult), int(40 * size_mult))
        super().__init__(game, x, y, random.choice([-240, 240]) * speed_mult, random.choice([-240, 240]) * speed_mult, color=COLOR_BROWN, size=size)
        self.lifetime = 5.0 # 300 / 60
        self.speed_up = 1.12 # 1.002^60 approx 1.12
        self.squash = pygame.math.Vector2(1.0, 1.0)
        self.squash_timer = 0

    def update(self, dt):
        self.vel *= (self.speed_up ** dt)
        self.pos.x += self.vel.x * dt
        self.rect.centerx = int(self.pos.x)
        
        if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
            self.vel.x *= -1
            self.pos.x += self.vel.x * dt
            self.squash = pygame.math.Vector2(0.6, 1.4)
            self.squash_timer = 0.166 # 10 / 60
            
        self.pos.y += self.vel.y * dt
        self.rect.centery = int(self.pos.y)
        
        if self.rect.top <= 0 or self.rect.bottom >= SCREEN_HEIGHT:
            self.vel.y *= -1
            self.pos.y += self.vel.y * dt
            self.squash = pygame.math.Vector2(1.4, 0.6)
            self.squash_timer = 0.166

        self.lifetime -= dt
        if self.lifetime <= 0: self.kill()
        
        if self.squash_timer > 0:
            self.squash_timer -= dt
            self.squash += (pygame.math.Vector2(1.0, 1.0) - self.squash) * 12 * dt # 0.2 per frame approx

    def draw(self, screen, camera_offset):
        w = self.width * self.squash.x
        h = self.height * self.squash.y
        rect = pygame.Rect(0, 0, w, h)
        rect.center = (self.pos.x - camera_offset.x, self.pos.y - camera_offset.y)
        pygame.draw.rect(screen, self.color, rect)
        pygame.draw.rect(screen, COLOR_WHITE, rect.inflate(-10, -10), 2)

class ChalkboardEraser(BossProjectile):
    def __init__(self, game, direction='left'):
        super().__init__(game, 0, 0, 0, 0, color=COLOR_GRAY, size=(100, SCREEN_HEIGHT))
        if direction == 'left':
            self.pos = pygame.math.Vector2(SCREEN_WIDTH + 50, SCREEN_HEIGHT/2)
            self.vel = pygame.math.Vector2(-720, 0)
        else:
            self.pos = pygame.math.Vector2(-50, SCREEN_HEIGHT/2)
            self.vel = pygame.math.Vector2(720, 0)
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def update(self, dt):
        super().update(dt)
        if (self.vel.x < 0 and self.rect.right < 0) or (self.vel.x > 0 and self.rect.left > SCREEN_WIDTH):
            self.kill()

class EquationProjectile(BossProjectile):
    def __init__(self, game, x, y, is_parryable=False):
        super().__init__(game, x, y, 0, 180, color=COLOR_PINK if is_parryable else COLOR_GRAY, size=(30, 30), is_parryable=is_parryable)
        self.start_x = x
        self.pos_y = float(y)
        self.amplitude = random.randint(40, 60)
        self.frequency = 0.05
        self.offset = random.random() * math.pi * 2
        self.shimmer_time = 0

    def update(self, dt):
        self.pos_y += self.vel.y * dt
        self.rect.y = int(self.pos_y)
        self.rect.centerx = self.start_x + math.sin(self.pos_y * self.frequency + self.offset) * self.amplitude
        self.shimmer_time += dt
        if self.rect.top > SCREEN_HEIGHT: self.kill()

    def draw(self, screen, camera_offset):
        global EQUATION_FONT
        if EQUATION_FONT is None:
            EQUATION_FONT = get_font("Arial", 24, bold=True)

        alpha = int(200 + math.sin(self.shimmer_time * 12) * 55)
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        text_color = (*self.color, alpha) if len(self.color) == 3 else self.color
        text = EQUATION_FONT.render("∑" if not self.is_parryable else "π", True, text_color)
        rect = text.get_rect(center=(self.width//2, self.height//2))
        surf.blit(text, rect)
        
        screen.blit(surf, (self.rect.x - camera_offset.x, self.rect.y - camera_offset.y))

class ProtractorSpin(BossProjectile):
    def __init__(self, game, boss):
        super().__init__(game, boss.rect.centerx, boss.rect.centery, 0, 0, color=COLOR_BLUE, size=(200, 200))
        self.is_parryable = True
        self.boss = boss
        self.timer = 10.0 # 600 / 60
        self.tips = []

    def update(self, dt):
        self.angle += 120 * dt # 2 * 60
        self.rect.center = self.boss.rect.center
        self.timer -= dt
        if self.timer <= 0: self.kill()
        
        self.tips = []
        center = pygame.math.Vector2(self.rect.center)
        for i in range(4):
            a = math.radians(self.angle + i * 90)
            tip_pos = center + pygame.math.Vector2(math.cos(a) * 100, math.sin(a) * 100)
            self.tips.append(tip_pos)
            
            if self.game.player.parry_active_timer > 0:
                dist = tip_pos.distance_to(self.game.player.rect.center)
                if dist < 30:
                    self.game.player.handle_parry(self)
                    self.boss.stun(2.0) # 120 / 60
                    self.kill()
                    return

    def draw(self, screen, camera_offset):
        center = (self.rect.centerx - camera_offset.x, self.rect.centery - camera_offset.y)
        pygame.draw.circle(screen, self.color, center, 100, 5)
        for i in range(4):
            a = math.radians(self.angle + i * 90)
            tip_pos = (center[0] + math.cos(a) * 100, center[1] + math.sin(a) * 100)
            pygame.draw.circle(screen, COLOR_PINK, tip_pos, 10)

class Laser(BossProjectile):
    def __init__(self, game, y, duration=0.5, rotation_speed=0):
        super().__init__(game, SCREEN_WIDTH//2, y, 0, 0, color=COLOR_YELLOW, size=(SCREEN_WIDTH, 40))
        self.timer = duration
        self.state = 'charge'
        self.charge_timer = 1.0 # 60 / 60
        self.rotation_speed = rotation_speed
        self.pivot = pygame.math.Vector2(0, y) if rotation_speed > 0 else pygame.math.Vector2(SCREEN_WIDTH, y)

    def update(self, dt):
        if self.state == 'charge':
            self.charge_timer -= dt
            if self.charge_timer <= 0:
                self.state = 'fire'
        else:
            self.timer -= dt
            if self.timer <= 0: self.kill()
            
        if self.rotation_speed != 0:
            self.angle += self.rotation_speed * dt

    def draw(self, screen, camera_offset):
        if self.state == 'charge':
            rect = pygame.Rect(0, self.rect.y - camera_offset.y, SCREEN_WIDTH, 2)
            rect.y += (pygame.time.get_ticks() % 40)
            pygame.draw.rect(screen, COLOR_RED, rect)
            pygame.draw.line(screen, COLOR_RED, (0, self.rect.centery - camera_offset.y), (SCREEN_WIDTH, self.rect.centery - camera_offset.y), 1)
        else:
            if self.rotation_speed == 0:
                rect = self.rect.copy()
                rect.y -= camera_offset.y
                pygame.draw.rect(screen, self.color, rect)
            else:
                start = self.pivot - camera_offset
                end = start + pygame.math.Vector2(SCREEN_WIDTH * 2, 0).rotate(self.angle)
                pygame.draw.line(screen, self.color, start, end, 40)

class TextbookSlam(BossProjectile):
    def __init__(self, game, x):
        super().__init__(game, x, -200, 0, 0, color=COLOR_DARK_RED, size=(200, 100))
        self.target_x = x
        self.timer = 1.5 # 90 / 60
        self.state = 'warning'
        self.pos.x = x

    def update(self, dt):
        if self.state == 'warning':
            self.timer -= dt
            if self.timer <= 0:
                self.state = 'slam'
                self.vel.y = 1200 # 20 * 60
        elif self.state == 'slam':
            self.pos.y += self.vel.y * dt
            self.rect.centery = int(self.pos.y)
            if self.rect.top > SCREEN_HEIGHT: self.kill()

    def draw(self, screen, camera_offset):
        if self.state == 'warning':
            warn_surf = pygame.Surface((200, 20), pygame.SRCALPHA)
            warn_surf.fill((255, 0, 0, 100))
            screen.blit(warn_surf, (self.target_x - 100 - camera_offset.x, SCREEN_HEIGHT - 20))
        
        rect = self.rect.copy()
        rect.x -= camera_offset.x
        rect.y -= camera_offset.y
        pygame.draw.rect(screen, self.color, rect)
        pygame.draw.rect(screen, COLOR_WHITE, rect.inflate(-10, -10))
