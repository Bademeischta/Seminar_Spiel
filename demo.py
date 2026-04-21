import pygame
import random
from constants import *
from boss_projectiles import BossProjectile

class DemoMode:
    def __init__(self, game, is_bot=True):
        self.game = game
        self.is_bot = is_bot
        self.panel_visible = not is_bot
        self.bot_timer = 0
        self.move_dir = 1
        self.boss_active_timer = 0
        self.setup_demo()

    def setup_demo(self):
        self.game.player.hp = 999
        self.game.player.cards = 5
        self.game.boss.state = 'idle'

    def update(self, dt):
        self.game.player.hp = 999
        self.game.player.cards = 5

        if self.is_bot:
            self.update_bot(dt)
        else:
            if self.boss_active_timer <= 0:
                if self.game.boss.state != 'idle':
                    self.game.boss.state = 'idle'
                if self.game.boss.state_timer < 1.0:
                    self.game.boss.state_timer = 2.0

    def update_bot(self, dt):
        self.bot_timer += dt

        # In bot mode, simulate parry logic
        if random.random() < 0.2 * dt:
             self.spawn_parry_projectile(is_bot=True)

        # Bot parry reaction
        for bullet in self.game.boss_bullets:
             if hasattr(bullet, 'is_parryable') and bullet.is_parryable:
                  dist = pygame.math.Vector2(bullet.rect.center).distance_to(self.game.player.rect.center)
                  if dist < 100 and self.game.player.parry_active_timer <= 0:
                       self.game.player.parry_active_timer = PLAYER_PARRY_WINDOW
                       self.game.player.perfect_parry_window = PLAYER_PERFECT_PARRY_WINDOW
                       self.game.player.add_ability_label("PARRY")

        if int(self.bot_timer * 0.5) % 2 == 0:
            if random.random() < 0.3 * dt:
                self.move_dir *= -1

        self.game.player.acc.x = self.move_dir * PLAYER_ACCELERATION
        self.game.player.facing_right = self.move_dir > 0

        if random.random() < 0.6 * dt:
            if self.game.player.is_grounded or self.game.player.on_wall:
                self.game.player.jump()
                self.game.player.add_ability_label("JUMP")

        if random.random() < 1.2 * dt:
            self.game.player.shoot_basic()
            self.game.player.add_ability_label("SHOOT")

        if random.random() < 0.3 * dt:
            if self.game.player.cards >= 5:
                self.game.player.shoot_ex()
                self.game.player.add_ability_label("EX ATTACK")

        if random.random() < 0.3 * dt:
            self.game.player.dash()
            self.game.player.add_ability_label("DASH")

        if self.game.player.streber_mode:
            if random.random() < 0.1 * dt:
                 self.game.player.add_ability_label("STREBER MODE!")

        if self.game.boss.state != 'idle':
            self.game.boss.state = 'idle'
        if self.game.boss.state_timer < 1.0:
            self.game.boss.state_timer = 2.0

    def spawn_parry_projectile(self, is_bot=False):
        px, py = self.game.player.rect.center
        offset = 250 if self.game.player.facing_right else -250
        vel_x = -300 if self.game.player.facing_right else 300

        p = BossProjectile(self.game, px + offset, py, vel_x, 0, is_parryable=True)
        self.game.all_sprites.add(p)
        self.game.boss_bullets.add(p)
        if not self.is_bot and not is_bot:
            self.game.player.add_ability_label("DRÜCKE S + SPACE ZUM PARRIEREN")
