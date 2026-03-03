import pygame
from constants import *
from boss_projectiles import BossProjectile

class DemoMode:
    def __init__(self, game):
        self.game = game
        self.panel_visible = True
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
