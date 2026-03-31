import pygame
import random
import math
from constants import *

class Particle:
    def __init__(self, pos, vel, lifetime, color, size, priority=1, gravity=0):
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(vel)
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.color = color
        self.size = size
        self.priority = priority
        self.gravity = gravity

    def update(self, dt):
        self.vel.y += self.gravity * dt
        self.pos += self.vel * dt
        self.lifetime -= dt
        return self.lifetime > 0

    def draw(self, screen, camera_offset):
        pass

class SquareParticle(Particle):
    def draw(self, screen, camera_offset):
        rect = pygame.Rect(0, 0, self.size, self.size)
        rect.center = (self.pos.x - camera_offset.x, self.pos.y - camera_offset.y)
        
        alpha = int(max(0, min(255, (self.lifetime / self.max_lifetime) * 255)))
        surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.rect(surf, (*self.color, alpha) if len(self.color) == 3 else self.color, (0, 0, self.size, self.size))
        screen.blit(surf, rect)

class DustParticle(Particle):
    def draw(self, screen, camera_offset):
        radius = self.size / 2
        center = (int(self.pos.x - camera_offset.x), int(self.pos.y - camera_offset.y))
        
        alpha = int(max(0, min(255, (self.lifetime / self.max_lifetime) * 255)))
        surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, alpha) if len(self.color) == 3 else self.color, (int(radius), int(radius)), int(radius))
        screen.blit(surf, (center[0] - radius, center[1] - radius))

class StarParticle(Particle):
    def draw(self, screen, camera_offset):
        points = []
        center = pygame.math.Vector2(self.pos.x - camera_offset.x, self.pos.y - camera_offset.y)
        rotation = (self.max_lifetime - self.lifetime) * 30
        
        for i in range(10):
            angle = math.radians(i * 36 + rotation)
            r = self.size if i % 2 == 0 else self.size * 0.4
            points.append((center.x + math.cos(angle) * r, center.y + math.sin(angle) * r))
            
        alpha = int(max(0, min(255, (self.lifetime / self.max_lifetime) * 255)))
        
        min_x = min(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_x = max(p[0] for p in points)
        max_y = max(p[1] for p in points)
        w, h = int(max_x - min_x + 2), int(max_y - min_y + 2)
        
        if w > 0 and h > 0:
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            local_points = [(p[0] - min_x, p[1] - min_y) for p in points]
            c = (*self.color, alpha) if len(self.color) == 3 else self.color
            pygame.draw.polygon(surf, c, local_points)
            screen.blit(surf, (min_x, min_y))

class AfterimageParticle(Particle):
    def __init__(self, pos, image, lifetime, alpha_start=200):
        super().__init__(pos, (0, 0), lifetime, COLOR_WHITE, 0, priority=0)
        self.image = image.copy()
        self.alpha_start = alpha_start
        
    def draw(self, screen, camera_offset):
        alpha = int(max(0, min(255, (self.lifetime / self.max_lifetime) * self.alpha_start)))
        self.image.set_alpha(alpha)
        screen.blit(self.image, (self.pos.x - camera_offset.x, self.pos.y - camera_offset.y))

class SpeedLineParticle(Particle):
    def draw(self, screen, camera_offset):
        rect = pygame.Rect(self.pos.x - camera_offset.x, self.pos.y - camera_offset.y, self.size * 5, 2)
        alpha = int(max(0, min(255, (self.lifetime / self.max_lifetime) * 150)))
        surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(surf, (*self.color, alpha), (0, 0, rect.width, rect.height))
        screen.blit(surf, rect)

class ImpactParticle(Particle):
    def draw(self, screen, camera_offset):
        life_pct = self.lifetime / self.max_lifetime
        size = self.size * life_pct
        if size <= 0: return
        rect = pygame.Rect(0, 0, size, size)
        rect.center = (self.pos.x - camera_offset.x, self.pos.y - camera_offset.y)

        alpha = int(max(0, min(255, life_pct * 255)))
        surf = pygame.Surface((int(size)+1, int(size)+1), pygame.SRCALPHA)
        pygame.draw.rect(surf, (*self.color, alpha), (0, 0, size, size))
        screen.blit(surf, rect)

class ParticleManager:
    def __init__(self):
        self.particles = []
        self.max_particles = 200

    def add(self, particle):
        if len(self.particles) >= self.max_particles:
            self.particles.sort(key=lambda p: (p.priority, p.lifetime))
            self.particles.pop(0)
        self.particles.append(particle)

    def update(self, dt):
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, screen, camera_offset):
        for p in self.particles:
            p.draw(screen, camera_offset)

    def spawn_dust(self, pos, count=3):
        for _ in range(count):
            self.add(DustParticle(pos, (random.uniform(-60, 60), random.uniform(-30, 0)),
                                  random.uniform(0.3, 0.6), COLOR_GRAY, random.randint(2, 5), priority=0))

    def spawn_hit(self, pos, color=COLOR_RED):
        for _ in range(10):
            self.add(SquareParticle(pos, (random.uniform(-300, 300), random.uniform(-300, 300)),
                                    random.uniform(0.3, 0.5), color, random.randint(3, 8), priority=2, gravity=720))

    def spawn_impact(self, pos, color=COLOR_WHITE):
        for _ in range(8):
            self.add(ImpactParticle(pos, (random.uniform(-240, 240), random.uniform(-240, 240)),
                                    random.uniform(0.25, 0.4), color, random.randint(2, 6), priority=2))

    def spawn_parry(self, pos, perfect=False):
        count = 30 if perfect else 15
        color = COLOR_GOLD if perfect else COLOR_WHITE
        for _ in range(count):
            self.add(StarParticle(pos, (random.uniform(-480, 480), random.uniform(-480, 480)),
                                  random.uniform(0.6, 1.0), color, random.randint(4, 10), priority=3))

    def spawn_trail(self, pos, color, size):
        self.add(SquareParticle(pos, (0, 0), 0.16, color, size, priority=0))
        
    def spawn_speed_lines(self):
        y = random.randint(0, SCREEN_HEIGHT)
        self.add(SpeedLineParticle((SCREEN_WIDTH, y), (-1800, 0), 0.16, COLOR_WHITE, random.randint(20, 50), priority=0))

class DamageNumber:
    def __init__(self, pos, text, color, size=24):
        self.pos = pygame.math.Vector2(pos)
        self.text = text
        self.color = color
        self.vel = pygame.math.Vector2(random.uniform(-60, 60), -120)
        self.lifetime = 1.0
        self.font = pygame.font.SysFont("Arial", size, bold=True)

    def update(self, dt):
        self.pos += self.vel * dt
        self.vel.y += 180 * dt
        self.lifetime -= dt
        return self.lifetime > 0

    def draw(self, screen, camera_offset):
        surf = self.font.render(self.text, True, self.color)
        alpha = int(max(0, min(255, self.lifetime * 255)))
        surf.set_alpha(alpha)
        rect = surf.get_rect(center=(self.pos.x - camera_offset.x, self.pos.y - camera_offset.y))
        screen.blit(surf, rect)

class EffectManager:
    def __init__(self):
        self.shake_timer = 0
        self.shake_magnitude = 0
        self.shake_type = 'impact'
        self.shake_vector = pygame.math.Vector2(0, 0)
        
        self.time_scale = 1.0
        self.slowmo_timer = 0
        self.freeze_timer = 0
        
        self.zoom_level = 1.0
        self.target_zoom = 1.0
        
        self.damage_numbers = []

    def apply_shake(self, duration, magnitude, type='impact', vector=(0,1)):
        self.shake_timer = duration
        self.shake_magnitude = magnitude
        self.shake_type = type
        self.shake_vector = pygame.math.Vector2(vector).normalize() if vector != (0,0) else pygame.math.Vector2(0,1)

    def apply_slowmo(self, duration, scale=0.5):
        self.slowmo_timer = duration
        self.time_scale = scale

    def apply_freeze(self, duration):
        self.freeze_timer = duration

    def apply_zoom(self, zoom, duration=0):
        self.target_zoom = zoom

    def add_damage_number(self, pos, amount, is_weak=False, is_crit=False, color=None, size=None):
        if color is None:
            color = COLOR_WHITE
            if is_weak: color = COLOR_YELLOW
            if is_crit: color = COLOR_RED
            
        if size is None:
            size = 24
            if is_weak: size = 32
            if is_crit: size = 40

        text = str(amount)
        if isinstance(amount, (int, float)):
             if is_weak: text += " WEAK!"
             if is_crit: text += " CRIT!"
        
        self.damage_numbers.append(DamageNumber(pos, text, color, size))

    def update(self, dt):
        if self.shake_timer > 0:
            self.shake_timer -= dt

        if self.freeze_timer > 0:
            self.freeze_timer -= dt
            return

        if self.slowmo_timer > 0:
            self.slowmo_timer -= dt
            if self.slowmo_timer <= 0:
                self.time_scale = 1.0

        self.damage_numbers = [d for d in self.damage_numbers if d.update(dt)]
        self.zoom_level += (self.target_zoom - self.zoom_level) * 6 * dt

    def get_camera_offset(self):
        offset = pygame.math.Vector2(0, 0)
        if self.shake_timer > 0:
            if self.shake_type == 'impact':
                offset.x = random.uniform(-self.shake_magnitude, self.shake_magnitude)
                offset.y = random.uniform(-self.shake_magnitude, self.shake_magnitude)
            elif self.shake_type == 'directional':
                offset = self.shake_vector * self.shake_magnitude * (random.random() if random.random() > 0.5 else -0.2)
            elif self.shake_type == 'rumble':
                offset.x = random.uniform(-1, 1)
                offset.y = random.uniform(-1, 1)
        return offset

    def draw(self, screen, camera_offset):
        for d in self.damage_numbers:
            d.draw(screen, camera_offset)
