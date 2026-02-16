import pygame
import math
from constants import *

class Projectile(pygame.sprite.Sprite):
    def __init__(self, game, x, y, vel_x, vel_y, damage, color=BLUE, size=(10, 10)):
        super().__init__()
        self.game = game
        self.image = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(self.image, color, (0, 0, size[0], size[1]))
        self.rect = self.image.get_rect(center=(x, y))
        self.vel = pygame.math.Vector2(vel_x, vel_y)
        self.damage = damage
        self.color = color
        self.is_homing = False
        self.is_golden = False # Parry counter boost

    def update(self, dt=1.0):
        if self.is_homing:
            self.home_on_target(dt)

        self.rect.centerx += self.vel.x * dt
        self.rect.centery += self.vel.y * dt

        if (self.rect.right < -100 or self.rect.left > SCREEN_WIDTH + 100 or
            self.rect.bottom < -100 or self.rect.top > SCREEN_HEIGHT + 100):
            self.kill()

    def home_on_target(self, dt):
        target = self.game.boss
        if target and target.alive():
            target_pos = pygame.math.Vector2(target.rect.center)
            # Check for weak points
            if hasattr(target, 'weak_point_rect') and target.weak_point_rect:
                target_pos = pygame.math.Vector2(target.weak_point_rect.center)

            dir = (target_pos - pygame.math.Vector2(self.rect.center)).normalize()
            desired_vel = dir * self.vel.length()
            self.vel += (desired_vel - self.vel) * 0.1 * dt

    def draw(self, screen, camera_offset):
        screen.blit(self.image, (self.rect.x - camera_offset.x, self.rect.y - camera_offset.y))

class PlayerProjectile(Projectile):
    def __init__(self, game, x, y, vel_x, vel_y, damage, color=BLUE, size=(10, 10), is_ex=False):
        super().__init__(game, x, y, vel_x, vel_y, damage, color, size)
        self.is_ex = is_ex

class EXFlieger(PlayerProjectile):
    def __init__(self, game, x, y, direction):
        super().__init__(game, x, y, direction * 12, 0, 5, BLUE, (40, 30), is_ex=True)

    def update(self, dt=1.0):
        super().update(dt)
        # Check if hitting parryable projectiles
        hits = pygame.sprite.spritecollide(self, self.game.boss_bullets, False)
        for bullet in hits:
            if hasattr(bullet, 'is_parryable') and bullet.is_parryable:
                bullet.kill()
                self.game.player.cards = min(self.game.player.cards + 0.1, MAX_CARDS)

    def draw(self, screen, camera_offset):
        # Triangle
        p1 = self.rect.midleft if self.vel.x < 0 else self.rect.midright
        p2 = self.rect.topright if self.vel.x < 0 else self.rect.topleft
        p3 = self.rect.bottomright if self.vel.x < 0 else self.rect.bottomleft
        points = [(p.x - camera_offset.x, p.y - camera_offset.y) for p in [p1, p2, p3]]
        pygame.draw.polygon(screen, self.color, points)

class EXEraser(PlayerProjectile):
    def __init__(self, game, x, y, direction):
        super().__init__(game, x, y, direction * 5, 0, 3, PURPLE, (20, 20), is_ex=True)

    def kill(self):
        # Create explosion
        self.game.particle_manager.spawn_hit(self.rect.center, color=PURPLE)
        # Damage boss if in range
        if self.game.boss.rect.inflate(100, 100).colliderect(self.rect):
             self.game.boss.take_damage(3) # Central damage
        super().kill()

class EXRuler(PlayerProjectile):
    def __init__(self, game, x, y, direction):
        super().__init__(game, x, y, direction * 10, 0, 3, BROWN, (30, 10), is_ex=True)
        self.direction = direction
        self.returning = False
        self.start_x = x

    def update(self, dt=1.0):
        if not self.returning:
            if abs(self.rect.centerx - self.start_x) > 400:
                self.returning = True
        else:
            target = self.game.player.rect.center
            target_vec = pygame.math.Vector2(target)
            curr_vec = pygame.math.Vector2(self.rect.center)
            dir_vec = target_vec - curr_vec
            if dir_vec.length() < 20:
                self.game.player.cards = min(self.game.player.cards + 1, MAX_CARDS)
                self.kill()
            if dir_vec.length() > 0:
                self.vel = dir_vec.normalize() * 15

        super().update(dt)

class EXSuper(PlayerProjectile):
    def __init__(self, game, x, y, direction):
        super().__init__(game, x, y, 0, 0, 1.5, YELLOW, (SCREEN_WIDTH, 60), is_ex=True)
        self.lifetime = 60
        self.rect.midleft = (0, y) if direction > 0 else (SCREEN_WIDTH, y)
        if direction < 0: self.rect.right = SCREEN_WIDTH
        else: self.rect.left = 0

    def update(self, dt=1.0):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()

        # Clear all boss bullets
        for bullet in self.game.boss_bullets:
            bullet.kill()

        # Damage boss every frame
        if self.game.boss.rect.colliderect(self.rect):
            self.game.boss.take_damage(self.damage * dt)

    def draw(self, screen, camera_offset):
        # Draw huge laser
        rect = self.rect.copy()
        rect.x -= camera_offset.x
        rect.y -= camera_offset.y
        pygame.draw.rect(screen, self.color, rect)
        pygame.draw.rect(screen, WHITE, rect.inflate(0, -20))
