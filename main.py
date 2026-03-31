import pygame
import sys
from constants import *
from player import Player
from boss import Boss
from projectiles import EXSuper
from effects import ParticleManager, EffectManager
from ui import UIManager, GradeScreen
from challenge import ChallengeMode
from demo import DemoMode
from save_system import SaveSystem
from utils import draw_text, SoundManager

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(COLOR_GRAY)
        self.rect = self.image.get_rect(topleft=(x, y))

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.render_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Dr. Pythagoras 2.0 - Ultimate Boss Fight")
        self.clock = pygame.time.Clock()
        self.save_system = SaveSystem()

        self.state = "MENU"
        self.ui_manager = UIManager(self)
        self.challenge = None
        self.demo = None

        self.particle_manager = ParticleManager()
        self.effect_manager = EffectManager()
        self.sound_manager = SoundManager()

        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()
        self.boss_bullets = pygame.sprite.Group()

        self.game_time = 0
        self.reality_break_timer = 0
        self.reality_break_type = None
        self.inverted_controls = False
        self.inverted_gravity = False
        
        self.total_parries = 0
        self.perfect_parries = 0
        self.style_points = 0
        self.inactivity_timer = 0

        self.reset_game()

    def reset_game(self, challenge_name=None, is_demo=False):
        self.inactivity_timer = 0
        self.all_sprites.empty()
        self.platforms.empty()
        self.player_bullets.empty()
        self.boss_bullets.empty()
        self.particle_manager.particles = []
        self.effect_manager.damage_numbers = []

        p1 = Platform(400, 350, 200, 10)
        p2 = Platform(150, 450, 200, 10)
        p3 = Platform(650, 450, 200, 10)
        self.platforms.add(p1, p2, p3)
        self.all_sprites.add(p1, p2, p3)

        self.player = Player(self, 100, SCREEN_HEIGHT)
        self.all_sprites.add(self.player)

        self.boss = Boss(self)
        self.all_sprites.add(self.boss)

        self.action_log = []
        if challenge_name:
            self.challenge = ChallengeMode(self, challenge_name)
        else:
            self.challenge = None

        if is_demo:
            self.demo = DemoMode(self)
            self.state = "DEMO"
        else:
            self.demo = None

        self.game_time = 0
        self.reality_break_timer = 0
        self.inverted_controls = False
        self.inverted_gravity = False
        
        self.total_parries = 0
        self.perfect_parries = 0
        self.style_points = 0

        self.effect_manager.time_scale = 1.0
        self.effect_manager.slowmo_timer = 0
        self.effect_manager.freeze_timer = 0
        self.effect_manager.zoom_level = 1.0
        self.effect_manager.target_zoom = 1.0

    def handle_events(self):
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                 self.inactivity_timer = 0
                 if self.state == "DEMO":
                      self.state = "MENU"

            if self.state == "MENU":
                action = self.ui_manager.menu.update([event])
                if action == "START GAME":
                    self.reset_game()
                    self.state = "PLAYING"
                elif action == "CHALLENGE MODES":
                    self.state = "CHALLENGE_SELECT"
                elif action == "DEMO MODE":
                    self.reset_game(challenge_name=None, is_demo=True)
                elif action == "STATISTICS":
                    self.state = "STATISTICS"
                elif action == "QUIT":
                    pygame.quit()
                    sys.exit()

            elif self.state == "CHALLENGE_SELECT":
                chal_action = self.ui_manager.challenge_screen.update([event])
                if chal_action == "BACK":
                    self.state = "MENU"
                elif chal_action:
                    self.reset_game(challenge_name=chal_action)
                    self.state = "PLAYING"

            elif self.state == "STATISTICS":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = "MENU"

            elif self.state in ["PLAYING", "DEMO"]:
                if self.state == "DEMO":
                    ability = self.ui_manager.demo_panel.update([event])
                    if ability:
                        self.handle_demo_ability(ability)

                if event.type == pygame.KEYDOWN:
                    if self.state == "DEMO":
                        if event.key == pygame.K_TAB:
                            self.demo.panel_visible = not self.demo.panel_visible
                        if event.key == pygame.K_r:
                            self.boss.hp = 100
                            self.boss.phase = 1
                            self.boss.state = 'idle'
                        if event.key == pygame.K_b:
                            self.player.pos = pygame.math.Vector2(100, SCREEN_HEIGHT)
                        if event.key == pygame.K_ESCAPE:
                            self.state = "MENU"

                    if event.key == pygame.K_SPACE:
                        keys_held = pygame.key.get_pressed()
                        if self.player.is_grounded and (keys_held[pygame.K_s] or keys_held[pygame.K_DOWN]):
                            # Duck + Parry on ground
                            self.player.parry_active_timer = PLAYER_PARRY_WINDOW
                            self.player.perfect_parry_window = PLAYER_PERFECT_PARRY_WINDOW
                        else:
                            if not self.player.is_grounded:
                                # Aerial Parry
                                self.player.parry_active_timer = PLAYER_PARRY_WINDOW
                                self.player.perfect_parry_window = PLAYER_PERFECT_PARRY_WINDOW
                            self.player.jump()

                    if event.key == pygame.K_LSHIFT:
                        self.player.dash()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 3:
                        self.player.shoot_ex()

                if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                     self.state = "PAUSED"

            elif self.state == "PAUSED":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    self.state = "PLAYING"

            elif self.state == "WIN_SCREEN":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    self.state = "MENU"

    def apply_reality_break(self, effect_type):
        self.reality_break_type = effect_type
        self.reality_break_timer = 2.0
        self.sound_manager.play("reality_break")
        if effect_type == 'invert_controls':
             self.inverted_controls = True
             self.effect_manager.apply_shake(0.16, 5)
        elif effect_type == 'invert_gravity':
             self.inverted_gravity = True
        elif effect_type == 'slow_mo':
             self.effect_manager.apply_slowmo(2.0, 0.5)

    def update(self):
        dt_raw = self.clock.tick(FPS) / 1000.0
        dt = dt_raw * self.effect_manager.time_scale
        if self.effect_manager.freeze_timer > 0:
            dt = 0

        if self.state == "MENU":
            self.inactivity_timer += dt_raw
            if self.inactivity_timer >= 15.0:
                self.reset_game(is_demo=True)

        if self.state in ["PLAYING", "DEMO"]:
            if self.state == "PLAYING":
                self.game_time += dt

            if self.challenge:
                self.challenge.update(dt)

            if self.state == "DEMO":
                self.demo.update(dt)

            self.player.update(dt)
            if self.state == "PLAYING":
                self.boss.update(dt)
            else:
                self.boss.update_weak_point(dt)
                self.boss.update_visuals(dt)
                self.boss.rect.center = self.boss.pos + self.boss.vibrate_offset
            self.player_bullets.update(dt)
            self.boss_bullets.update(dt)
            self.particle_manager.update(dt)
            self.effect_manager.update(dt)
            
            if self.reality_break_timer > 0:
                self.reality_break_timer -= dt
                if self.reality_break_timer <= 0:
                    self.inverted_controls = False
                    self.inverted_gravity = False

            if self.player.alive() and self.boss.alive():
                hits = pygame.sprite.spritecollide(self.boss, self.player_bullets, True)
                for bullet in hits:
                    self.boss.take_damage(bullet.damage)
                    self.particle_manager.spawn_impact(bullet.rect.center, color=COLOR_WHITE)
                    # Style: Weak Point Treffer
                    if self.boss.weak_point_timer > 0:
                        self.style_points += 5
                    # Style: Treffer während Streber Mode
                    if self.player.streber_mode:
                        self.style_points += 2

            if self.boss.is_dying and self.boss.state_timer <= 0:
                self.win_game()

    def win_game(self):
        self.inactivity_timer = 0
        style_bonus = 0
        if self.challenge:
            if self.challenge.name == "No Dash":
                 style_bonus = 100
            elif self.challenge.name == "Parry Only":
                 style_bonus = self.total_parries * 30

        stats = {
            'time': self.game_time,
            'hp': self.player.hp,
            'parries': self.total_parries,
            'perfect_parries': self.perfect_parries, 
            'style': self.style_points + (self.player.cards * 10) + style_bonus
        }
        self.grade_screen = GradeScreen(self, stats)
        self.state = "WIN_SCREEN"

        self.save_system.update_stat("total_wins", 1)
        self.save_system.update_stat("best_time", self.game_time, mode="min")
        self.save_system.update_stat("total_damage_dealt", BOSS_MAX_HP)

        if self.challenge:
             chal_key = f"best_grade_{self.challenge.name.replace(' ', '_')}"
             current_best = self.save_system.data["stats"].get(chal_key, "D")
             grade_order = ["D", "C", "B", "A", "S", "S+"]
             if grade_order.index(self.grade_screen.grade) > grade_order.index(current_best):
                  self.save_system.update_stat(chal_key, self.grade_screen.grade, mode="set")

             if self.challenge.name == "No Dash" and self.grade_screen.grade in ["S", "S+"]:
                  if "Speedrunner" not in self.save_system.data["unlocks"]["skins"]:
                       self.save_system.data["unlocks"]["skins"].append("Speedrunner")
             if self.challenge.name == "One Hit KO":
                  if "Perfektionist" not in self.save_system.data["unlocks"]["skins"]:
                       self.save_system.data["unlocks"]["skins"].append("Perfektionist")
             self.save_system.save()

    def game_over(self):
        self.inactivity_timer = 0
        self.state = "MENU" 

    def draw(self):
        self.render_surface.fill(COLOR_BLACK)
        
        if self.state == "CHALLENGE_SELECT":
             self.ui_manager.draw(self.screen)
             pygame.display.flip()
             return

        camera_offset = self.effect_manager.get_camera_offset()

        if self.state in ["PLAYING", "PAUSED", "WIN_SCREEN", "DEMO"]:
            for plat in self.platforms:
                pygame.draw.rect(self.render_surface, COLOR_GRAY, plat.rect.move(-camera_offset.x, -camera_offset.y))

            self.player.draw(self.render_surface, camera_offset)
            self.boss.draw(self.render_surface, camera_offset)

            for bullet in self.player_bullets: bullet.draw(self.render_surface, camera_offset)
            for bullet in self.boss_bullets: bullet.draw(self.render_surface, camera_offset)

            self.particle_manager.draw(self.render_surface, camera_offset)
            self.effect_manager.draw(self.render_surface, camera_offset)
            
            if self.reality_break_timer > 0:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                color = (255, 0, 0, 50)
                if self.reality_break_type == 'invert_gravity': color = (0, 0, 255, 50)
                if self.reality_break_type == 'slow_mo': color = (255, 255, 0, 50)
                overlay.fill(color)
                self.render_surface.blit(overlay, (0, 0))
                draw_text(self.render_surface, f"REALITY BREAK: {self.reality_break_type.upper()}", 32, SCREEN_WIDTH//2, 150, COLOR_WHITE)

        zoom = self.effect_manager.zoom_level
        if zoom != 1.0:
            w, h = int(SCREEN_WIDTH * zoom), int(SCREEN_HEIGHT * zoom)
            scaled = pygame.transform.scale(self.render_surface, (w, h))
            x = (SCREEN_WIDTH - w) // 2
            y = (SCREEN_HEIGHT - h) // 2
            self.screen.fill(COLOR_BLACK)
            self.screen.blit(scaled, (x, y))
        else:
            self.screen.blit(self.render_surface, (0, 0))

        self.ui_manager.draw(self.screen)
        pygame.display.flip()

    def handle_demo_ability(self, ability):
        self.player.add_ability_label(ability.upper())

        if ability == "Basis-Schuss":
            self.player.shoot_basic()
        elif ability == "Charge Shot":
            self.player.shoot_charge()
        elif ability == "Spread Shot":
            self.player.shoot_spread()
        elif ability == "Homing Shot":
            self.player.shoot_homing()
        elif ability == "EX-Flieger":
            self.player.selected_ex = "Flieger"
            self.player.cards = 5
            self.player.shoot_ex()
        elif ability == "EX-Eraser":
            self.player.selected_ex = "Eraser"
            self.player.cards = 5
            self.player.shoot_ex()
        elif ability == "EX-Ruler":
            self.player.selected_ex = "Ruler"
            self.player.cards = 5
            self.player.shoot_ex()
        elif ability == "Ultimate Laser":
            self.player.cards = 5
            bullet = EXSuper(self, self.player.rect.centerx, self.player.rect.centery, 1 if self.player.facing_right else -1)
            self.all_sprites.add(bullet)
            self.player_bullets.add(bullet)
            self.effect_manager.apply_shake(1.0, 15)
            self.effect_manager.apply_zoom(1.3, duration=0.5)
        elif ability == "Dash (normal)":
            self.player.dash()
        elif ability == "Super-Dash":
            self.player.cards = 1
            self.player.is_super_dash = True
            self.player.sound_manager.play("super_dash")
            self.player.is_dashing = True
            self.player.dash_timer = PLAYER_DASH_DURATION * 2
            self.player.dash_cooldown_timer = PLAYER_DASH_COOLDOWN
            self.player.i_frames = self.player.dash_timer
            self.player.perfect_dash_window = 0.16
            self.player.dash_direction = pygame.math.Vector2(1 if self.player.facing_right else -1, 0)
            self.particle_manager.spawn_speed_lines()
        elif ability == "Slam Down":
            self.player.vel.y = PLAYER_DASH_SPEED * 1.5
        elif ability == "Perfect Parry":
            self.demo.spawn_parry_projectile()
        elif ability == "Streber Mode":
            self.player.parry_chain = 3
            self.player.streber_mode = True
            self.player.parry_counter_timer = 10.0
            self.player.parry_chain_timer = 10.0
            self.player.max_jumps = 3
            self.effect_manager.add_damage_number(
                self.player.rect.center, "STREBER MODE!", color=COLOR_GOLD, size=32)
        elif ability == "Notizbuch-Schild":
            self.player.activate_shield()
        elif ability == "Boss: Phase 1":
            self.boss.hp = 85
            self.boss.phase = 1
        elif ability == "Boss: Phase 2":
            self.boss.hp = 50
            self.boss.check_phase()
        elif ability == "Boss: Phase 3":
            self.boss.hp = 15
            self.boss.check_phase()
        elif ability == "Boss: Reality Break":
            self.boss.reality_break()
        elif ability == "Boss: Blackboard Barrage":
            self.boss.blackboard_barrage()
        elif ability == "Boss: Compass Hell":
            self.boss.compass_hell_advanced()

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()

if __name__ == "__main__":
    game = Game()
    game.run()
