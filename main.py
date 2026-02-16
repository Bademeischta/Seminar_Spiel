import pygame
import sys
from constants import *
from player import Player
from boss import Boss
from effects import ParticleManager, EffectManager
from ui import HUD, Menu, GradeScreen, StatisticsScreen
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

    def reset_game(self):
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
                elif action == "STATISTICS":
                    self.state = "STATISTICS"
                elif action == "QUIT":
                    pygame.quit()
                    sys.exit()

            elif self.state == "STATISTICS":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = "MENU"

            elif self.state == "PLAYING":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        # Parry check
                        if not self.player.is_grounded:
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

        if self.state == "PLAYING":
            self.game_time += dt / 60

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

            if self.boss.hp <= 0 and not self.boss.alive():
                self.win_game()

    def win_game(self):
        stats = {
            'time': self.game_time,
            'hp': self.player.hp,
            'parries': self.total_parries,
            'perfect_parries': self.perfect_parries, 
            'style': self.style_points + (self.player.cards * 10) # Base style + leftover cards
        }
        self.grade_screen = GradeScreen(self, stats)
        self.state = "WIN_SCREEN"

        # Save stats
        self.save_system.update_stat("total_wins", 1)
        self.save_system.update_stat("best_time", self.game_time, mode="min")
        self.save_system.update_stat("total_damage_dealt", BOSS_MAX_HP)

    def game_over(self):
        self.state = "MENU" 

    def draw(self):
        # Draw everything to render_surface
        self.render_surface.fill(BLACK)
        
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
        if self.state in ["PLAYING", "PAUSED", "WIN_SCREEN"]:
            self.hud.draw(self.screen)

        if self.state == "MENU":
            self.menu.draw(self.screen)

        if self.state == "STATISTICS":
            self.statistics_screen.draw(self.screen)

        if self.state == "WIN_SCREEN":
            self.grade_screen.draw(self.screen)

        pygame.display.flip()

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()
