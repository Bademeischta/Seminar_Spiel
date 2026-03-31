import pygame
import random
from constants import *
from projectiles import PlayerProjectile, ParryDamageProjectile

class ChallengeMode:
    def __init__(self, game, challenge_name):
        self.game = game
        self.name = challenge_name
        self.setup_challenge()

    def setup_challenge(self):
        if self.name == "No Dash":
            self.game.player.can_dash = False
        elif self.name == "One Hit KO":
            self.game.player.hp = 1
            self.game.boss.hp = 50
            self.game.boss.max_hp = 50
        elif self.name == "Parry Only":
            self.parry_damage_total = 0
        elif self.name == "Boss Rush":
            self.game.boss.hp = BOSS_PHASE_3_THRESHOLD
            self.game.boss.phase = 3
            self.game.boss.color = COLOR_DARK_RED
            self.game.boss.start_transition(3)
            self.game.boss.state_timer = 0.5
            self.game.player.cards = 3
        elif self.name == "Mirror Match":
            self.mirror_timer = 5.0
            self.action_log = []

    def update(self, dt):
        if self.name == "Mirror Match":
            self.mirror_timer -= dt
            if self.mirror_timer <= 0:
                self.execute_mirror_action()
                self.mirror_timer = 5.0

    def execute_mirror_action(self):
        if not self.game.action_log:
            return

        last_action = self.game.action_log[-1]
        if last_action == "shoot":
            self.game.boss.geometry_attack()
        elif last_action == "dash":
            self.game.boss.teleport()
        elif last_action == "parry":
            self.game.boss.shield_active = True
            self.game.boss.shield_timer = 2.0

    def handle_parry_damage(self, is_perfect):
        if self.name == "Parry Only":
            dmg = 10 if is_perfect else 5
            dir_x = 600 if self.game.player.facing_right else -600
            bullet = ParryDamageProjectile(self.game, self.game.player.rect.centerx, self.game.player.rect.centery, dir_x, 0, dmg)
            self.game.all_sprites.add(bullet)
            self.game.player_bullets.add(bullet)

            self.parry_damage_total += dmg
            return dmg
        return 0
