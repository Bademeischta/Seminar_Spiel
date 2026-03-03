import pygame
import sys
from constants import *
from player import Player
from boss import Boss
from effects import ParticleManager, EffectManager
from ui import HUD, Menu, GradeScreen, StatisticsScreen, ChallengeSelectScreen, DemoAbilityPanel
from challenge import ChallengeMode
from demo import DemoMode
from save_system import SaveSystem
from utils import draw_text, SoundManager

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(GRAY)
        self.rect = self.image.get_rect(topleft=(x, y))

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.render_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)) # For Zoom
        pygame.display.set_caption("Dr. Pythagoras 2.0 - Ultimate Boss Fight")
        self.clock = pygame.time.Clock()
        self.save_system = SaveSystem()

        self.state = "MENU"
        self.menu = Menu(self)
        self.statistics_screen = StatisticsScreen(self, self.save_system.data)
        self.challenge_screen = ChallengeSelectScreen(self)
        self.challenge = None
        self.demo = None
        self.demo_panel = DemoAbilityPanel(self)

        self.particle_manager = ParticleManager()
        self.effect_manager = EffectManager()
        self.sound_manager = SoundManager()
        self.hud = HUD(self)

        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()
        self.boss_bullets = pygame.sprite.Group()

        self.game_time = 0
        self.reality_break_timer = 0
        self.reality_break_type = None
        self.inverted_controls = False
        self.inverted_gravity = False
        
        # Stats
        self.total_parries = 0
        self.perfect_parries = 0
        self.style_points = 0

        self.reset_game()

    def reset_game(self, challenge_name=None, is_demo=False):
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

    def handle_events(self):
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if self.state == "MENU":
                action = self.menu.update([event])
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
                chal_action = self.challenge_screen.update([event])
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
                    ability = self.demo_panel.update([event])
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
                        # Parry check
                        self.player.parry_active_timer = PARRY_WINDOW
                        self.player.perfect_parry_window = PERFECT_PARRY_WINDOW
                        self.player.jump()

                    if event.key == pygame.K_LSHIFT:
                        self.player.dash()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 3: # Right click
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
        self.reality_break_timer = 120 # 2 seconds
        self.sound_manager.play("reality_break")
        if effect_type == 'invert_controls':
             self.inverted_controls = True
             self.effect_manager.apply_shake(10, 5)
        elif effect_type == 'invert_gravity':
             self.inverted_gravity = True
        elif effect_type == 'slow_mo':
             self.effect_manager.apply_slowmo(120, 0.5)

    def update(self):
        dt = self.effect_manager.time_scale
        if self.effect_manager.freeze_timer > 0:
            dt = 0

        if self.state in ["PLAYING", "DEMO"]:
            if self.state == "PLAYING":
                self.game_time += dt / 60

            if self.challenge:
                self.challenge.update(dt)

            if self.state == "DEMO":
                self.demo.update(dt)

            # Update sprites
            self.player.update(dt)
            self.boss.update(dt)
            self.player_bullets.update(dt)
            self.boss_bullets.update(dt)
            self.particle_manager.update(dt)
            self.effect_manager.update()
            
            # Reality break cleanup
            if self.reality_break_timer > 0:
                self.reality_break_timer -= dt
                if self.reality_break_timer <= 0:
                    self.inverted_controls = False
                    self.inverted_gravity = False

            if self.boss.is_dying and self.boss.state_timer <= 0:
                self.win_game()

    def win_game(self):
        # Challenge Bonuses
        style_bonus = 0
        if self.challenge:
            if self.challenge.name == "No Dash":
                 # +20 Style pro Dodge? Simplified: +100 bonus style for win
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

        # Save stats
        self.save_system.update_stat("total_wins", 1)
        self.save_system.update_stat("best_time", self.game_time, mode="min")
        self.save_system.update_stat("total_damage_dealt", BOSS_MAX_HP)

        if self.challenge:
             chal_key = f"best_grade_{self.challenge.name.replace(' ', '_')}"
             # We need to compare grades. S+ > S > A ...
             current_best = self.save_system.data["stats"].get(chal_key, "D")
             grade_order = ["D", "C", "B", "A", "S", "S+"]
             if grade_order.index(self.grade_screen.grade) > grade_order.index(current_best):
                  self.save_system.update_stat(chal_key, self.grade_screen.grade, mode="set")

             # Special unlocks
             if self.challenge.name == "No Dash" and self.grade_screen.grade in ["S", "S+"]:
                  if "Speedrunner" not in self.save_system.data["unlocks"]["skins"]:
                       self.save_system.data["unlocks"]["skins"].append("Speedrunner")
             if self.challenge.name == "One Hit KO":
                  if "Perfektionist" not in self.save_system.data["unlocks"]["skins"]:
                       self.save_system.data["unlocks"]["skins"].append("Perfektionist")
             self.save_system.save()

    def game_over(self):
        self.state = "MENU" 

    def draw(self):
        # Draw everything to render_surface
        self.render_surface.fill(BLACK)
        
        if self.state == "CHALLENGE_SELECT":
             self.challenge_screen.draw(self.screen)
             pygame.display.flip()
             return

        camera_offset = self.effect_manager.get_camera_offset()

        if self.state in ["PLAYING", "PAUSED", "WIN_SCREEN"]:
            for plat in self.platforms:
                pygame.draw.rect(self.render_surface, GRAY, plat.rect.move(-camera_offset.x, -camera_offset.y))

            self.player.draw(self.render_surface, camera_offset)
            self.boss.draw(self.render_surface, camera_offset)

            for bullet in self.player_bullets: bullet.draw(self.render_surface, camera_offset)
            for bullet in self.boss_bullets: bullet.draw(self.render_surface, camera_offset)

            self.particle_manager.draw(self.render_surface, camera_offset)
            self.effect_manager.draw(self.render_surface, camera_offset)

            # Draw HUD directly to screen later? No, usually UI is not zoomed.
            # But let's keep it consistent for now. Or better: Draw UI on screen, game on surface.
            
            if self.state == "PAUSED":
                draw_text(self.render_surface, "PAUSED", 64, SCREEN_WIDTH//2, SCREEN_HEIGHT//2, WHITE)

            if self.reality_break_timer > 0:
                # Flash based on type
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                color = (255, 0, 0, 50) # Invert controls
                if self.reality_break_type == 'invert_gravity': color = (0, 0, 255, 50)
                if self.reality_break_type == 'slow_mo': color = (255, 255, 0, 50)
                overlay.fill(color)
                self.render_surface.blit(overlay, (0, 0))
                draw_text(self.render_surface, f"REALITY BREAK: {self.reality_break_type.upper()}", 32, SCREEN_WIDTH//2, 150, WHITE)

        # Apply Zoom
        zoom = self.effect_manager.zoom_level
        if zoom != 1.0:
            w, h = int(SCREEN_WIDTH * zoom), int(SCREEN_HEIGHT * zoom)
            scaled = pygame.transform.scale(self.render_surface, (w, h))
            # Center it
            x = (SCREEN_WIDTH - w) // 2
            y = (SCREEN_HEIGHT - h) // 2
            self.screen.fill(BLACK) # Clear borders
            self.screen.blit(scaled, (x, y))
        else:
            self.screen.blit(self.render_surface, (0, 0))

        # UI is drawn ON TOP of zoomed game (no zoom for UI)
        if self.state in ["PLAYING", "PAUSED", "WIN_SCREEN", "DEMO"]:
            self.hud.draw(self.screen)
            if self.state == "DEMO" and self.demo.panel_visible:
                 self.demo_panel.draw(self.screen)

            if self.state == "DEMO":
                 draw_text(self.screen, "⚡ DEMO MODE — ESC zum Beenden", 24, SCREEN_WIDTH//2, 30, RED)

        if self.state == "MENU":
            self.menu.draw(self.screen)

        if self.state == "STATISTICS":
            self.statistics_screen.draw(self.screen)

        if self.state == "WIN_SCREEN":
            self.grade_screen.draw(self.screen)

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
            self.player.shoot_ex()
        elif ability == "Dash (normal)":
            self.player.dash()
        elif ability == "Super-Dash":
            # Force super dash
            self.player.cards = 1
            # We need to simulate CTRL press or change dash logic
            # Simplified: just call dash and hope cards are consumed
            self.player.dash()
        elif ability == "Slam Down":
            # Trigger slam by setting velocity
            self.player.vel.y = PLAYER_DASH_SPEED * 1.5
        elif ability == "Perfect Parry":
            self.demo.spawn_parry_projectile()
        elif ability == "Streber Mode":
            self.player.parry_chain = 3
            self.player.handle_parry(None) # Not ideal but might work or just set flag
            self.player.streber_mode = True
            self.player.parry_counter_timer = 600
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
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()
