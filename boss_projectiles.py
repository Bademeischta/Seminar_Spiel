import pygame
import math
import random
from constants import *

class BossProjectile(pygame.sprite.Sprite):
    def __init__(self, game, x, y, vel_x, vel_y, color=RED, size=(20, 20), is_parryable=False):
        super().__init__()
        self.game = game
        self.image = pygame.Surface(size, pygame.SRCALPHA)
        self.color = PINK if is_parryable else color
        pygame.draw.rect(self.image, self.color, (0, 0, size[0], size[1]))
        self.rect = self.image.get_rect(center=(x, y))
        self.vel = pygame.math.Vector2(vel_x, vel_y)
        self.is_parryable = is_parryable

    def update(self, dt=1.0):
        self.rect.centerx += self.vel.x * dt
        self.rect.centery += self.vel.y * dt
        if (self.rect.right < -200 or self.rect.left > SCREEN_WIDTH + 200 or
            self.rect.bottom < -200 or self.rect.top > SCREEN_HEIGHT + 200):
            self.kill()

    def draw(self, screen, camera_offset):
        screen.blit(self.image, (self.rect.x - camera_offset.x, self.rect.y - camera_offset.y))

class BouncingEraser(BossProjectile):
    def __init__(self, game, x, y, size_mult=1.0, speed_mult=1.0):
        size = (int(40 * size_mult), int(40 * size_mult))
        super().__init__(game, x, y, random.choice([-4, 4]) * speed_mult, random.choice([-4, 4]) * speed_mult, color=BROWN, size=size)
        self.timer = 300
        self.speed_up = 1.002

    def update(self, dt=1.0):
        self.vel *= (self.speed_up ** dt)
        self.rect.x += self.vel.x * dt
        self.rect.y += self.vel.y * dt

        if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
            self.vel.x *= -1
            self.rect.x += self.vel.x * dt
        if self.rect.top <= 0 or self.rect.bottom >= SCREEN_HEIGHT:
            self.vel.y *= -1
            self.rect.y += self.vel.y * dt

        self.timer -= dt
        if self.timer <= 0: self.kill()

class ChalkboardEraser(BossProjectile):
    def __init__(self, game, direction='left'):
        super().__init__(game, 0, 0, 0, 0, color=GRAY, size=(100, SCREEN_HEIGHT))
        if direction == 'left':
            self.rect.topleft = (SCREEN_WIDTH, 0)
            self.vel = pygame.math.Vector2(-8, 0)
        else:
            self.rect.topright = (0, 0)
            self.vel = pygame.math.Vector2(8, 0)

class EquationProjectile(BossProjectile):
    def __init__(self, game, x, y, is_parryable=False):
        super().__init__(game, x, y, 0, 3, color=PINK if is_parryable else GRAY, size=(30, 30), is_parryable=is_parryable)
        self.start_x = x
        self.pos_y = float(y)
        self.amplitude = random.randint(40, 60)
        self.frequency = 0.05
        self.offset = random.random() * math.pi * 2

    def update(self, dt=1.0):
        self.pos_y += self.vel.y * dt
        self.rect.y = int(self.pos_y)
        self.rect.centerx = self.start_x + math.sin(self.pos_y * self.frequency + self.offset) * self.amplitude
        if self.rect.top > SCREEN_HEIGHT: self.kill()

class ProtractorSpin(BossProjectile):
    def __init__(self, game, boss):
        super().__init__(game, boss.rect.centerx, boss.rect.centery, 0, 0, color=BLUE, size=(200, 200))
        self.boss = boss
        self.angle = 0
        self.timer = 600 # 10 seconds

    def update(self, dt=1.0):
        self.angle += 2 * dt # Speed of rotation
        self.rect.center = self.boss.rect.center
        self.timer -= dt
        if self.timer <= 0: self.kill()

        # Check for pink tips parry (handled in player collision usually)

    def draw(self, screen, camera_offset):
        # Draw a compass/protractor
        center = (self.rect.centerx - camera_offset.x, self.rect.centery - camera_offset.y)
        pygame.draw.circle(screen, self.color, center, 100, 5)
        # Draw 4 tips
        for i in range(4):
            a = math.radians(self.angle + i * 90)
            tip_pos = (center[0] + math.cos(a) * 100, center[1] + math.sin(a) * 100)
            pygame.draw.circle(screen, PINK, tip_pos, 10)

class Laser(BossProjectile):
    def __init__(self, game, y, duration=30):
        super().__init__(game, SCREEN_WIDTH//2, y, 0, 0, color=YELLOW, size=(SCREEN_WIDTH, 40))
        self.timer = duration

    def update(self, dt=1.0):
        self.timer -= dt
        if self.timer <= 0: self.kill()

class TextbookSlam(BossProjectile):
    def __init__(self, game, x):
        super().__init__(game, x, -200, 0, 0, color=DARK_RED, size=(200, 100))
        self.target_x = x
        self.timer = 90 # 1.5s warning
        self.state = 'warning'

    def update(self, dt=1.0):
        if self.state == 'warning':
            self.timer -= dt
            if self.timer <= 0:
                self.state = 'slam'
                self.vel.y = 20
        elif self.state == 'slam':
            self.rect.y += self.vel.y * dt
            if self.rect.top > SCREEN_HEIGHT: self.kill()

    def draw(self, screen, camera_offset):
        if self.state == 'warning':
            # Draw shadow
            pygame.draw.rect(screen, (255, 0, 0, 100), (self.target_x - 100 - camera_offset.x, SCREEN_HEIGHT - 20, 200, 20))
        super().draw(screen, camera_offset)
