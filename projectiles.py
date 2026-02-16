import pygame
import math
import random
from constants import *

class Projectile(pygame.sprite.Sprite):
    def __init__(self, game, x, y, vel_x, vel_y, damage, color=BLUE, size=(10, 10)):
        super().__init__()
        self.game = game
        self.width, self.height = size
        self.color = color
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.center = (x, y)
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(vel_x, vel_y)
        self.damage = damage
        self.is_homing = False
        self.is_golden = False # Parry counter boost
        self.angle = 0 # For rotation

    def update(self, dt=1.0):
        if self.is_homing:
            self.home_on_target(dt)

        self.pos += self.vel * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.angle += 10 * dt # Rotate

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

            dir = (target_pos - self.pos).normalize()
            desired_vel = dir * self.vel.length()
            self.vel += (desired_vel - self.vel) * 0.1 * dt

    def draw(self, screen, camera_offset):
        # Basic rect draw
        draw_rect = self.rect.copy()
        draw_rect.x -= camera_offset.x
        draw_rect.y -= camera_offset.y
        pygame.draw.rect(screen, self.color, draw_rect)

class PlayerProjectile(Projectile):
    def __init__(self, game, x, y, vel_x, vel_y, damage, color=BLUE, size=(10, 10), is_ex=False):
        super().__init__(game, x, y, vel_x, vel_y, damage, color, size)
        self.is_ex = is_ex
        self.trail_timer = 0

    def update(self, dt=1.0):
        super().update(dt)
        self.trail_timer += dt
        if self.trail_timer > 2:
            self.trail_timer = 0
            # Simple white line trail
            self.game.particle_manager.spawn_trail(self.rect.center, WHITE, 2)

    def draw(self, screen, camera_offset):
        # Paper Ball: Rotate
        # Create a surface, rotate it, blit it
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(surf, self.color, (0, 0, self.width, self.height))
        
        rotated_surf = pygame.transform.rotate(surf, self.angle)
        new_rect = rotated_surf.get_rect(center=(self.rect.centerx - camera_offset.x, self.rect.centery - camera_offset.y))
        screen.blit(rotated_surf, new_rect)

    def kill(self):
        # Crumple animation (simplified as particles)
        self.game.particle_manager.spawn_dust(self.rect.center, count=5)
        super().kill()

class SpreadProjectile(PlayerProjectile):
    def __init__(self, game, x, y, vel_x, vel_y):
        super().__init__(game, x, y, vel_x, vel_y, 1, CYAN, (8, 8))

class HomingProjectile(PlayerProjectile):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, 10, 0, 2, GREEN, (10, 10))
        self.is_homing = True
        self.timer = 120 # Timeout

    def update(self, dt=1.0):
        super().update(dt)
        self.timer -= dt
        if self.timer <= 0: self.kill()

class EXFlieger(PlayerProjectile):
    def __init__(self, game, x, y, direction):
        super().__init__(game, x, y, direction * 12, 0, 5, BLUE, (40, 20), is_ex=True)
        self.start_y = y
        self.flight_time = 0

    def update(self, dt=1.0):
        self.flight_time += dt
        # Smooth glide (Sine wave on Y)
        self.vel.y = math.sin(self.flight_time * 0.1) * 2
        
        super().update(dt)
        # Check if hitting parryable projectiles
        hits = pygame.sprite.spritecollide(self, self.game.boss_bullets, False)
        for bullet in hits:
            if hasattr(bullet, 'is_parryable') and bullet.is_parryable:
                bullet.kill()
                self.game.player.cards = min(self.game.player.cards + 0.1, MAX_CARDS)

    def draw(self, screen, camera_offset):
        # Draw Paper Plane (Triangle)
        center = (self.rect.centerx - camera_offset.x, self.rect.centery - camera_offset.y)
        angle = math.degrees(math.atan2(self.vel.y, self.vel.x))
        
        # Simple triangle points based on angle
        # Tip
        tip = (center[0] + math.cos(math.radians(angle)) * 20, center[1] + math.sin(math.radians(angle)) * 20)
        # Back Wings
        back = (center[0] - math.cos(math.radians(angle)) * 20, center[1] - math.sin(math.radians(angle)) * 20)
        wing1 = (back[0] + math.cos(math.radians(angle + 90)) * 10, back[1] + math.sin(math.radians(angle + 90)) * 10)
        wing2 = (back[0] + math.cos(math.radians(angle - 90)) * 10, back[1] + math.sin(math.radians(angle - 90)) * 10)
        
        pygame.draw.polygon(screen, self.color, [tip, wing1, wing2])

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
        self.caught = False

    def update(self, dt=1.0):
        if not self.returning:
            if abs(self.rect.centerx - self.start_x) > 400:
                self.returning = True
        else:
            target = self.game.player.rect.center
            target_vec = pygame.math.Vector2(target)
            curr_vec = pygame.math.Vector2(self.rect.center)
            dir_vec = target_vec - curr_vec
            
            # Catch logic
            if dir_vec.length() < 40 and not self.caught: # Increased range
                self.caught = True
                self.game.player.cards = min(self.game.player.cards + 1, MAX_CARDS)
                self.game.effect_manager.add_damage_number(self.game.player.rect.center, "CATCH!", color=GREEN, size=24)
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
        
        # Pulsing width
        pulse = math.sin(pygame.time.get_ticks() * 0.1) * 10
        draw_rect = rect.inflate(0, pulse)
        
        pygame.draw.rect(screen, self.color, draw_rect)
        pygame.draw.rect(screen, WHITE, draw_rect.inflate(0, -20))
