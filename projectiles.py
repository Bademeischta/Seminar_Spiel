import pygame
import math
import random
from constants import *

class BaseProjectile(pygame.sprite.Sprite):
    def __init__(self, game, x, y, vel_x, vel_y, damage, color=COLOR_BLUE, size=(10, 10)):
        super().__init__()
        self.game = game
        self.width, self.height = size
        self.color = color
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.center = (x, y)
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(vel_x, vel_y)
        self.damage = damage
        self.angle = 0

    def update(self, dt):
        self.pos += self.vel * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        if self.is_off_screen():
            self.kill()

    def is_off_screen(self):
        margin = 200
        return (self.rect.right < -margin or self.rect.left > SCREEN_WIDTH + margin or
                self.rect.bottom < -margin or self.rect.top > SCREEN_HEIGHT + margin)

    def check_collision(self, target):
        return self.rect.colliderect(target.rect)

    def draw(self, screen, camera_offset):
        draw_rect = self.rect.copy()
        draw_rect.x -= camera_offset.x
        draw_rect.y -= camera_offset.y
        pygame.draw.rect(screen, self.color, draw_rect)

class PlayerProjectile(BaseProjectile):
    def __init__(self, game, x, y, vel_x, vel_y, damage, color=COLOR_BLUE, size=(10, 10), is_ex=False):
        super().__init__(game, x, y, vel_x, vel_y, damage, color, size)
        self.is_ex = is_ex
        self.trail_timer = 0
        self.angle_rot = 0

    def update(self, dt):
        super().update(dt)
        self.angle_rot += 600 * dt # 10 degrees per frame at 60fps
        self.trail_timer += dt
        if self.trail_timer > 0.033: # ~2 frames at 60fps
            self.trail_timer = 0
            self.game.particle_manager.spawn_trail(self.rect.center, COLOR_WHITE, 2)

    def draw(self, screen, camera_offset):
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(surf, self.color, (0, 0, self.width, self.height))
        
        rotated_surf = pygame.transform.rotate(surf, self.angle_rot)
        new_rect = rotated_surf.get_rect(center=(self.rect.centerx - camera_offset.x, self.rect.centery - camera_offset.y))
        screen.blit(rotated_surf, new_rect)

    def kill(self):
        self.game.particle_manager.spawn_dust(self.rect.center, count=5)
        super().kill()

class SpreadProjectile(PlayerProjectile):
    def __init__(self, game, x, y, vel_x, vel_y):
        super().__init__(game, x, y, vel_x, vel_y, 1, COLOR_CYAN, (8, 8))

class HomingProjectile(PlayerProjectile):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, 600, 0, 2, COLOR_GREEN, (10, 10))
        self.is_homing = True
        self.lifetime = 2.0

    def update(self, dt):
        target = self.game.boss
        if target and target.alive():
            target_pos = pygame.math.Vector2(target.rect.center)
            if hasattr(target, 'weak_point_rect') and target.weak_point_rect:
                target_pos = pygame.math.Vector2(target.weak_point_rect.center)

            dir_vec = (target_pos - self.pos).normalize()
            desired_vel = dir_vec * self.vel.length()
            self.vel += (desired_vel - self.vel) * 6 * dt # 0.1 per frame

        super().update(dt)
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()

class EXFlieger(PlayerProjectile):
    def __init__(self, game, x, y, direction):
        super().__init__(game, x, y, direction * 720, 0, 5, COLOR_BLUE, (40, 20), is_ex=True)
        self.flight_time = 0

    def update(self, dt):
        self.flight_time += dt
        self.vel.y = math.sin(self.flight_time * 6) * 120 # 2 * 60
        
        super().update(dt)
        # Check if hitting parryable projectiles
        hits = pygame.sprite.spritecollide(self, self.game.boss_bullets, False)
        for bullet in hits:
            if hasattr(bullet, 'is_parryable') and bullet.is_parryable:
                bullet.kill()
                self.game.player.cards = min(self.game.player.cards + 0.1, PLAYER_MAX_CARDS)

    def draw(self, screen, camera_offset):
        center = (self.rect.centerx - camera_offset.x, self.rect.centery - camera_offset.y)
        angle = math.degrees(math.atan2(self.vel.y, self.vel.x))
        
        tip = (center[0] + math.cos(math.radians(angle)) * 20, center[1] + math.sin(math.radians(angle)) * 20)
        back = (center[0] - math.cos(math.radians(angle)) * 20, center[1] - math.sin(math.radians(angle)) * 20)
        wing1 = (back[0] + math.cos(math.radians(angle + 90)) * 10, back[1] + math.sin(math.radians(angle + 90)) * 10)
        wing2 = (back[0] + math.cos(math.radians(angle - 90)) * 10, back[1] + math.sin(math.radians(angle - 90)) * 10)
        
        pygame.draw.polygon(screen, self.color, [tip, wing1, wing2])

class EXEraser(PlayerProjectile):
    def __init__(self, game, x, y, direction):
        super().__init__(game, x, y, direction * 300, 0, 3, COLOR_PURPLE, (20, 20), is_ex=True)

    def kill(self):
        self.game.particle_manager.spawn_hit(self.rect.center, color=COLOR_PURPLE)
        explosion_rect = pygame.Rect(0, 0, 200, 200)
        explosion_rect.center = self.rect.center
        if explosion_rect.colliderect(self.game.boss.rect):
             self.game.boss.take_damage(3)
        super().kill()

class EXRuler(PlayerProjectile):
    def __init__(self, game, x, y, direction):
        super().__init__(game, x, y, direction * 600, 0, 3, COLOR_BROWN, (30, 10), is_ex=True)
        self.returning = False
        self.start_x = x
        self.caught = False

    def update(self, dt):
        if not self.returning:
            if abs(self.rect.centerx - self.start_x) > 400:
                self.returning = True
        else:
            target = self.game.player.rect.center
            target_vec = pygame.math.Vector2(target)
            curr_vec = pygame.math.Vector2(self.rect.center)
            dir_vec = target_vec - curr_vec
            
            if dir_vec.length() < 40 and not self.caught:
                self.caught = True
                self.game.player.cards = min(self.game.player.cards + 1, PLAYER_MAX_CARDS)
                self.game.effect_manager.add_damage_number(self.game.player.rect.center, "CATCH!", color=COLOR_GREEN, size=24)
                self.kill()
                
            if dir_vec.length() > 0:
                self.vel = dir_vec.normalize() * 900

        super().update(dt)

class ParryDamageProjectile(PlayerProjectile):
    def __init__(self, game, x, y, vel_x, vel_y, damage):
        super().__init__(game, x, y, vel_x, vel_y, damage, COLOR_GOLD, (15, 15))
        self.is_homing = True

    def update(self, dt):
        target = self.game.boss
        if target and target.alive():
             dir_vec = (pygame.math.Vector2(target.rect.center) - self.pos).normalize()
             self.vel = dir_vec * 900
        super().update(dt)

    def draw(self, screen, camera_offset):
        points = []
        center = (self.rect.centerx - camera_offset.x, self.rect.centery - camera_offset.y)
        for i in range(10):
            angle = math.radians(i * 36 + self.angle_rot)
            r = 10 if i % 2 == 0 else 4
            points.append((center[0] + math.cos(angle) * r, center[1] + math.sin(angle) * r))
        pygame.draw.polygon(screen, self.color, points)
        pygame.draw.polygon(screen, COLOR_WHITE, points, 1)

class EXSuper(PlayerProjectile):
    def __init__(self, game, x, y, direction):
        super().__init__(game, x, y, 0, 0, 0.3, COLOR_YELLOW, (SCREEN_WIDTH, 60), is_ex=True)
        self.lifetime = 0.75 # 45 / 60
        self.rect.midleft = (0, y) if direction > 0 else (SCREEN_WIDTH, y)
        if direction < 0: self.rect.right = SCREEN_WIDTH
        else: self.rect.left = 0
        self.total_damage_dealt = 0

    def update(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()

        for bullet in self.game.boss_bullets:
            bullet.kill()

        if self.game.boss.rect.colliderect(self.rect) and self.total_damage_dealt < PLAYER_EX_SUPER_DAMAGE_CAP:
            # damage is per frame in original, but here self.damage = 0.3
            # In original it was dmg = self.damage * dt (where dt was 1.0 mostly)
            # 0.3 damage per frame at 60fps = 18 damage per second.
            dmg = 18 * dt
            if self.total_damage_dealt + dmg > PLAYER_EX_SUPER_DAMAGE_CAP:
                dmg = PLAYER_EX_SUPER_DAMAGE_CAP - self.total_damage_dealt

            self.game.boss.take_damage(dmg)
            self.total_damage_dealt += dmg

    def draw(self, screen, camera_offset):
        rect = self.rect.copy()
        rect.x -= camera_offset.x
        rect.y -= camera_offset.y
        
        pulse = math.sin(pygame.time.get_ticks() * 0.1) * 10
        draw_rect = rect.inflate(0, pulse)
        
        pygame.draw.rect(screen, self.color, draw_rect)
        pygame.draw.rect(screen, COLOR_WHITE, draw_rect.inflate(0, -20))
