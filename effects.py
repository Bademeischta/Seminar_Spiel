import pygame
import random
import math
from constants import *

class Particle:
    def __init__(self, pos, vel, lifetime, color, size, priority=1, gravity=0, fade=True):
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(vel)
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.color = list(color)
        self.size = size
        self.priority = priority
        self.gravity = gravity
        self.fade = fade

    def update(self, dt=1.0):
        self.vel.y += self.gravity * dt
        self.pos += self.vel * dt
        self.lifetime -= dt
        if self.fade:
            alpha = max(0, int((self.lifetime / self.max_lifetime) * 255))
            # Pygame Surface alpha is easier for fading, but here we just handle life
        return self.lifetime > 0

    def draw(self, screen, camera_offset):
        rect = pygame.Rect(self.pos.x - camera_offset.x - self.size//2,
                           self.pos.y - camera_offset.y - self.size//2,
                           self.size, self.size)
        pygame.draw.rect(screen, self.color, rect)

class ParticleManager:
    def __init__(self):
        self.particles = []
        self.max_particles = 200

    def spawn(self, type_name, pos, vel, lifetime, color, size, priority=1, gravity=0):
        if len(self.particles) >= self.max_particles:
            # Delete lowest priority/oldest
            self.particles.sort(key=lambda p: (p.priority, p.lifetime))
            self.particles.pop(0)

        p = Particle(pos, vel, lifetime, color, size, priority, gravity)
        self.particles.append(p)

    def update(self, dt=1.0):
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, screen, camera_offset):
        for p in self.particles:
            p.draw(screen, camera_offset)

    def spawn_dust(self, pos):
        for _ in range(3):
            self.spawn("dust", pos, (random.uniform(-1, 1), random.uniform(-0.5, 0)),
                       random.randint(20, 40), GRAY, random.randint(2, 5), priority=0)

    def spawn_hit(self, pos, color=RED):
        for _ in range(10):
            self.spawn("hit", pos, (random.uniform(-5, 5), random.uniform(-5, 5)),
                       random.randint(20, 30), color, random.randint(3, 8), priority=2, gravity=0.2)

    def spawn_parry(self, pos):
        for _ in range(20):
            self.spawn("parry", pos, (random.uniform(-8, 8), random.uniform(-8, 8)),
                       random.randint(40, 60), GOLD, random.randint(4, 10), priority=3)

    def spawn_trail(self, pos, color, size):
        self.spawn("trail", pos, (0, 0), 10, color, size, priority=0, gravity=0)

class DamageNumber:
    def __init__(self, pos, text, color, size=24):
        self.pos = pygame.math.Vector2(pos)
        self.text = text
        self.color = color
        self.vel = pygame.math.Vector2(random.uniform(-1, 1), -2)
        self.lifetime = 60
        self.font = pygame.font.SysFont("Arial", size, bold=True)

    def update(self):
        self.pos += self.vel
        self.vel.y += 0.05
        self.lifetime -= 1
        return self.lifetime > 0

    def draw(self, screen, camera_offset):
        surf = self.font.render(self.text, True, self.color)
        alpha = min(255, self.lifetime * 4)
        surf.set_alpha(alpha)
        rect = surf.get_rect(center=(self.pos.x - camera_offset.x, self.pos.y - camera_offset.y))
        screen.blit(surf, rect)

class EffectManager:
    def __init__(self):
        self.shake_timer = 0
        self.shake_magnitude = 0
        self.time_scale = 1.0
        self.slowmo_timer = 0
        self.freeze_timer = 0
        self.zoom_level = 1.0
        self.target_zoom = 1.0
        self.damage_numbers = []

    def apply_shake(self, duration, magnitude):
        self.shake_timer = duration
        self.shake_magnitude = magnitude

    def apply_slowmo(self, duration, scale=0.5):
        self.slowmo_timer = duration
        self.time_scale = scale

    def apply_freeze(self, duration):
        self.freeze_timer = duration

    def add_damage_number(self, pos, amount, is_weak=False, is_crit=False):
        color = WHITE
        size = 24
        text = str(amount)
        if is_weak:
            color = YELLOW
            size = 32
        if is_crit:
            color = RED
            size = 40
            text += "!"
        self.damage_numbers.append(DamageNumber(pos, text, color, size))

    def update(self):
        if self.shake_timer > 0:
            self.shake_timer -= 1

        if self.freeze_timer > 0:
            self.freeze_timer -= 1
            return # Don't update other timers during freeze

        if self.slowmo_timer > 0:
            self.slowmo_timer -= 1
            if self.slowmo_timer <= 0:
                self.time_scale = 1.0

        self.damage_numbers = [d for d in self.damage_numbers if d.update()]

        # Smooth zoom
        self.zoom_level += (self.target_zoom - self.zoom_level) * 0.1

    def get_camera_offset(self):
        offset = pygame.math.Vector2(0, 0)
        if self.shake_timer > 0:
            offset.x = random.uniform(-self.shake_magnitude, self.shake_magnitude)
            offset.y = random.uniform(-self.shake_magnitude, self.shake_magnitude)
        return offset

    def draw(self, screen, camera_offset):
        for d in self.damage_numbers:
            d.draw(screen, camera_offset)
