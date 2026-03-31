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
        # In demo mode, boss state_timer should not decrease unless we want it to

    def update(self, dt):
        # Infinite HP/Cards
        self.game.player.hp = 999
        self.game.player.cards = 5

        # Bot Logic
        self.bot_timer += dt

        # Change direction occasionally
        if self.bot_timer % 120 < dt:
            if random.random() < 0.3:
                self.move_dir *= -1

        # Simulate Movement (Directly setting acceleration to simulate key presses)
        self.game.player.acc.x = self.move_dir * PLAYER_ACC
        self.game.player.facing_right = self.move_dir > 0

        # Occasional jump
        if random.random() < 0.01 * dt:
            self.game.player.jump()

        # Occasional shoot
        if random.random() < 0.02 * dt:
            self.game.player.shoot_basic()

        # Stop boss from attacking naturally
        if self.game.boss.state != 'idle':
            self.game.boss.state = 'idle'
        if self.game.boss.state_timer < 60:
            self.game.boss.state_timer = 120

    def spawn_parry_projectile(self):
        # Spawns a parryable projectile 150px in front of player, speed 4
        px, py = self.game.player.rect.center
        offset = 150 if self.game.player.facing_right else -150
        vel_x = -4 if self.game.player.facing_right else 4

        p = BossProjectile(self.game, px + offset, py, vel_x, 0, is_parryable=True)
        self.game.all_sprites.add(p)
        self.game.boss_bullets.add(p)
