import pygame
import random
from constants import *
from boss_projectiles import BossProjectile

class DemoMode:
    def __init__(self, game):
        self.game = game
        self.panel_visible = True
        self.bot_timer = 0
        self.move_dir = 1
        self.setup_demo()

    def setup_demo(self):
        self.game.player.hp = 999
        self.game.player.cards = 5
        self.game.boss.state = 'idle'

    def update(self, dt):
        self.game.player.hp = 999
        self.game.player.cards = 5

        self.bot_timer += dt

        if int(self.bot_timer * 0.5) % 2 == 0:
            if random.random() < 0.3 * dt:
                self.move_dir *= -1

        self.game.player.acc.x = self.move_dir * PLAYER_ACCELERATION
        self.game.player.facing_right = self.move_dir > 0

        if random.random() < 0.6 * dt:
            self.game.player.jump()

        if random.random() < 1.2 * dt:
            self.game.player.shoot_basic()

        if self.game.boss.state != 'idle':
            self.game.boss.state = 'idle'
        if self.game.boss.state_timer < 1.0:
            self.game.boss.state_timer = 2.0

    def spawn_parry_projectile(self):
        px, py = self.game.player.rect.center
        offset = 150 if self.game.player.facing_right else -150
        vel_x = -240 if self.game.player.facing_right else 240

        p = BossProjectile(self.game, px + offset, py, vel_x, 0, is_parryable=True)
        self.game.all_sprites.add(p)
        self.game.boss_bullets.add(p)
