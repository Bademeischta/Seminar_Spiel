import pygame
import random
from constants import *

class DemoBot:
    def __init__(self, game):
        self.game = game
        self.timer = 0
        self.direction = 1
        self.jump_timer = 0
        self.shoot_timer = 0
        self.change_dir_timer = 0

        # Simulated key state
        self.keys = {
            pygame.K_a: False,
            pygame.K_d: False,
            pygame.K_SPACE: False,
            pygame.K_RETURN: False,
            pygame.K_f: False,
            pygame.K_e: False,
            pygame.K_1: False,
            pygame.K_2: False,
            pygame.K_3: False,
            pygame.K_4: False,
            pygame.K_5: False,
            pygame.K_LSHIFT: False,
            pygame.K_LCTRL: False,
            pygame.K_s: False,
            pygame.K_DOWN: False,
            pygame.K_p: False,
            pygame.K_TAB: False,
            pygame.K_r: False,
            pygame.K_b: False,
            pygame.K_ESCAPE: False
        }

    def get_input(self, dt):
        self.timer += dt

        # Reset per-frame keys
        self.keys[pygame.K_SPACE] = False
        self.keys[pygame.K_RETURN] = False

        # Randomly change direction every few seconds
        self.change_dir_timer -= dt
        if self.change_dir_timer <= 0:
            self.direction = random.choice([-1, 1])
            self.change_dir_timer = random.uniform(2.0, 5.0)

        # Update movement keys
        self.keys[pygame.K_a] = (self.direction == -1)
        self.keys[pygame.K_d] = (self.direction == 1)

        # Occasional jumps
        self.jump_timer -= dt
        if self.jump_timer <= 0:
            if random.random() < 0.4:
                self.keys[pygame.K_SPACE] = True
            self.jump_timer = random.uniform(0.5, 2.0)

        # Occasional shooting
        self.shoot_timer -= dt
        if self.shoot_timer <= 0:
            if random.random() < 0.6:
                self.keys[pygame.K_RETURN] = True
            self.shoot_timer = random.uniform(0.3, 1.0)

        return self.keys
