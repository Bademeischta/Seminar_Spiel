import pygame
import random
from constants import *
from projectiles import PlayerProjectile

class ChallengeMode:
    def __init__(self, game, challenge_name):
        self.game = game
        self.name = challenge_name
        self.setup_challenge()

    def setup_challenge(self):
        if self.name == "No Dash":
            self.game.player.can_dash = False # We need to check this in player.dash()
        elif self.name == "One Hit KO":
            self.game.player.hp = 1
            self.game.boss.hp = 50
            self.game.boss.max_hp = 50
            # We'll need to handle I-frames in player.take_damage()
        elif self.name == "Parry Only":
            self.parry_damage_total = 0
        elif self.name == "Boss Rush":
            self.game.boss.hp = PHASE_3_THRESHOLD
            self.game.boss.phase = 3
            self.game.boss.color = DARK_RED
            self.game.boss.start_transition(3)
            self.game.boss.state_timer = 30
            self.game.player.cards = 3
        elif self.name == "Mirror Match":
            self.mirror_timer = 300 # 5 seconds
            self.action_log = [] # Moved to game object as well?

    def update(self, dt):
        if self.name == "No Dash":
            pass # Logic handled in boss.run_attack or similar if we want to speed up state_timer

        elif self.name == "Mirror Match":
            self.mirror_timer -= dt
            if self.mirror_timer <= 0:
                self.execute_mirror_action()
                self.mirror_timer = 300

    def execute_mirror_action(self):
        if not self.game.action_log:
            return

        last_action = self.game.action_log[-1]
        if last_action == "shoot":
            # Boss shoots back
            self.game.boss.geometry_attack()
        elif last_action == "dash":
            # Boss teleports
            self.game.boss.teleport()
        elif last_action == "parry":
            # Boss activates shield
            self.game.boss.shield_active = True # We need to implement this for boss
            self.game.boss.shield_timer = 120

    def handle_parry_damage(self, is_perfect):
        if self.name == "Parry Only":
            dmg = 10 if is_perfect else 5
            # Spawn a visual projectile from player to boss
            bullet = PlayerProjectile(self.game, self.game.player.rect.centerx, self.game.player.rect.centery, 0, 0, dmg, GOLD)
            bullet.is_homing = True
            bullet.vel = pygame.math.Vector2(10, 0)
            self.game.all_sprites.add(bullet)
            self.game.player_bullets.add(bullet)

            self.parry_damage_total += dmg
            return dmg
        return 0
