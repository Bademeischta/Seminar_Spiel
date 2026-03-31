import pygame
import math
from constants import *
from utils import draw_text

class HUD:
    def __init__(self, game):
        self.game = game

    def draw(self, screen):
        # Player HP
        for i in range(PLAYER_MAX_HP):
            rect = pygame.Rect(20 + i * 40, 20, 30, 30)
            if i < self.game.player.hp:
                pygame.draw.rect(screen, COLOR_RED, rect)
            else:
                pygame.draw.rect(screen, COLOR_DARK_GRAY, rect, 2)

        # Special Meter (Cards)
        for i in range(PLAYER_MAX_CARDS):
            rect = pygame.Rect(20 + i * 35, 60, 30, 45)
            fill = 0
            if i < int(self.game.player.cards):
                fill = 1.0
            elif i == int(self.game.player.cards):
                fill = self.game.player.cards % 1.0

            color = COLOR_BLUE
            pygame.draw.rect(screen, color, rect, 2)
            
            if fill > 0:
                fill_rect = rect.copy()
                fill_rect.height = int(rect.height * fill)
                fill_rect.bottom = rect.bottom
                
                draw_color = COLOR_BLUE
                if self.game.player.cards >= 5:
                    pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) * 0.5 * 255
                    draw_color = (100, 100, 255)
                
                pygame.draw.rect(screen, draw_color, fill_rect)
                
                if i < int(self.game.player.cards):
                     pygame.draw.rect(screen, COLOR_WHITE, rect.inflate(-10, -10), 1)

        # Focus Meter
        focus_rect = pygame.Rect(20, 115, 170, 10)
        pygame.draw.rect(screen, COLOR_DARK_GRAY, focus_rect)
        focus_fill = (self.game.player.focus_time / PLAYER_FOCUS_MAX_DURATION) * 170
        pygame.draw.rect(screen, COLOR_CYAN, (20, 115, focus_fill, 10))

        if self.game.challenge:
             draw_text(screen, f"CHALLENGE: {self.game.challenge.name}", 20, SCREEN_WIDTH - 150, 100, COLOR_GOLD)
             if self.game.challenge.name == "Parry Only":
                  draw_text(screen, f"PARRY DAMAGE: {self.game.challenge.parry_damage_total}", 20, SCREEN_WIDTH - 150, 130, COLOR_WHITE)

        boss = self.game.boss
        if boss and boss.alive():
            hp_width = 400
            hp_rect_bg = pygame.Rect(SCREEN_WIDTH // 2 - hp_width // 2, 20, hp_width, 25)
            pygame.draw.rect(screen, COLOR_DARK_GRAY, hp_rect_bg)

            hp_fill = (boss.hp / boss.max_hp) * hp_width
            hp_rect_fill = pygame.Rect(SCREEN_WIDTH // 2 - hp_width // 2, 20, hp_fill, 25)
            pygame.draw.rect(screen, boss.color, hp_rect_fill)
            pygame.draw.rect(screen, COLOR_WHITE, hp_rect_bg, 2)

            draw_text(screen, "Dr. Pythagoras", 20, SCREEN_WIDTH // 2, 60, COLOR_WHITE)

class GradeScreen:
    def __init__(self, game, stats):
        self.game = game
        self.stats = stats
        self.grade, self.score = self.calculate_grade()

    def calculate_grade(self):
        time_score = 0
        t = self.stats['time']
        if t < 90: time_score = 100
        elif t < 120: time_score = 85
        elif t < 180: time_score = 70
        elif t < 240: time_score = 50
        else: time_score = 30

        dmg_score = 0
        hits = PLAYER_MAX_HP - self.stats['hp']
        if hits == 0: dmg_score = 100
        elif hits == 1: dmg_score = 80
        elif hits == 2: dmg_score = 60
        elif hits == 3: dmg_score = 40
        else: dmg_score = 20

        p = self.stats['parries']
        parry_score = 0
        if p >= 15: parry_score = 100
        elif p >= 10: parry_score = 80
        elif p >= 5: parry_score = 60
        elif p >= 1: parry_score = 40
        else: parry_score = 0

        style_score = min(100, self.stats['style']) 

        total = (time_score * 0.3) + (dmg_score * 0.3) + (parry_score * 0.2) + (style_score * 0.2)

        grade = "D"
        if total >= 95: grade = "S+"
        elif total >= 90: grade = "S"
        elif total >= 80: grade = "A"
        elif total >= 70: grade = "B"
        elif total >= 60: grade = "C"

        return grade, int(total)

    def draw(self, screen):
        screen.fill(COLOR_BLACK)
        draw_text(screen, "KAMPF-STATISTIK", 48, SCREEN_WIDTH//2, 80, COLOR_YELLOW)

        y = 180
        stats_labels = [
            f"Zeit: {int(self.stats['time'])}s",
            f"Schaden genommen: {PLAYER_MAX_HP - self.stats['hp']} Treffer",
            f"Parries: {self.stats['parries']} ({self.stats['perfect_parries']} Perfect)",
            f"Style-Events: {int(self.stats['style'])}",
            f"SCORE: {self.score}"
        ]

        for label in stats_labels:
            draw_text(screen, label, 30, SCREEN_WIDTH//2, y, COLOR_WHITE)
            y += 50

        draw_text(screen, f"GRADE: {self.grade}", 80, SCREEN_WIDTH//2, y + 50, COLOR_GOLD if "S" in self.grade else COLOR_WHITE)
        draw_text(screen, "Press ENTER to continue", 20, SCREEN_WIDTH//2, SCREEN_HEIGHT - 50, COLOR_GRAY)

class Menu:
    def __init__(self, game):
        self.game = game
        self.options = ["START GAME", "CHALLENGE MODES", "DEMO MODE", "STATISTICS", "QUIT"]
        self.selected = 0

    def draw(self, screen):
        screen.fill(COLOR_BLACK)
        draw_text(screen, "DR. PYTHAGORAS 2.0", 64, SCREEN_WIDTH//2, 150, COLOR_LIGHT_RED)

        for i, opt in enumerate(self.options):
            color = COLOR_WHITE if i == self.selected else COLOR_GRAY
            size = 40 if i == self.selected else 30
            draw_text(screen, opt, size, SCREEN_WIDTH//2, 300 + i * 60, color)

    def update(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w or event.key == pygame.K_UP:
                    self.selected = (self.selected - 1) % len(self.options)
                elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                    self.selected = (self.selected + 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    return self.options[self.selected]
        return None

class DemoAbilityPanel:
    def __init__(self, game):
        self.game = game
        self.width = 200
        self.rect = pygame.Rect(SCREEN_WIDTH - self.width, 0, self.width, SCREEN_HEIGHT)
        self.buttons = [
            "Basis-Schuss", "Charge Shot", "Spread Shot", "Homing Shot",
            "EX-Flieger", "EX-Eraser", "EX-Ruler", "Ultimate Laser",
            "Dash (normal)", "Super-Dash", "Slam Down", "Perfect Parry",
            "Streber Mode", "Notizbuch-Schild",
            "Boss: Phase 1", "Boss: Phase 2", "Boss: Phase 3",
            "Boss: Reality Break", "Boss: Blackboard Barrage", "Boss: Compass Hell"
        ]
        self.button_rects = []
        for i, name in enumerate(self.buttons):
             r = pygame.Rect(SCREEN_WIDTH - self.width + 10, 50 + i * 25, self.width - 20, 20)
             self.button_rects.append(r)

    def draw(self, screen):
        surf = pygame.Surface((self.width, SCREEN_HEIGHT), pygame.SRCALPHA)
        surf.fill((50, 50, 50, 180))
        screen.blit(surf, (SCREEN_WIDTH - self.width, 0))

        mouse_pos = pygame.mouse.get_pos()
        for i, name in enumerate(self.buttons):
            r = self.button_rects[i]
            color = COLOR_YELLOW if r.collidepoint(mouse_pos) else COLOR_WHITE
            pygame.draw.rect(screen, (30, 30, 30), r)
            draw_text(screen, name, 14, r.centerx, r.centery, color)

    def update(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, r in enumerate(self.button_rects):
                    if r.collidepoint(event.pos):
                        return self.buttons[i]
        return None

class ChallengeSelectScreen:
    def __init__(self, game):
        self.game = game
        self.challenges = [
            {"name": "No Dash", "desc": "Kein Dash möglich. Boss ist schneller.", "diff": 3},
            {"name": "One Hit KO", "desc": "Ein Treffer = Tod. Weniger Boss-HP.", "diff": 5},
            {"name": "Parry Only", "desc": "Nur Parries machen Schaden.", "diff": 4},
            {"name": "Boss Rush", "desc": "Direkt zu Phase 3.", "diff": 4},
            {"name": "Mirror Match", "desc": "Boss kopiert deine Aktionen.", "diff": 5}
        ]
        self.selected = 0

    def draw(self, screen):
        screen.fill(COLOR_BLACK)
        draw_text(screen, "CHALLENGE MODES", 48, SCREEN_WIDTH//2, 80, COLOR_YELLOW)

        for i, chal in enumerate(self.challenges):
            color = COLOR_WHITE if i == self.selected else COLOR_GRAY
            y = 180 + i * 80

            stars = "★" * chal["diff"] + "☆" * (5 - chal["diff"])
            draw_text(screen, f"{chal['name']} {stars}", 32, SCREEN_WIDTH//2, y, color)
            draw_text(screen, chal["desc"], 18, SCREEN_WIDTH//2, y + 30, color)

            best = self.game.save_system.data["stats"].get(f"best_grade_{chal['name'].replace(' ', '_')}", "N/A")
            draw_text(screen, f"Best: {best}", 18, SCREEN_WIDTH - 150, y, COLOR_GOLD)

        draw_text(screen, "W/S zum Wählen, ENTER zum Starten, ESC zum Zurück", 20, SCREEN_WIDTH//2, SCREEN_HEIGHT - 50, COLOR_GRAY)

    def update(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w or event.key == pygame.K_UP:
                    self.selected = (self.selected - 1) % len(self.challenges)
                elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                    self.selected = (self.selected + 1) % len(self.challenges)
                elif event.key == pygame.K_RETURN:
                    return self.challenges[self.selected]["name"]
                elif event.key == pygame.K_ESCAPE:
                    return "BACK"
        return None

class StatisticsScreen:
    def __init__(self, game, save_data):
        self.save_data = save_data

    def draw(self, screen):
        screen.fill(COLOR_BLACK)
        draw_text(screen, "LIFETIME STATISTICS", 48, SCREEN_WIDTH//2, 80, COLOR_CYAN)

        stats = self.save_data["stats"]
        best_time = stats['best_time']
        time_str = f"{int(best_time)}s" if best_time != float('inf') else "N/A"
        labels = [
            f"Gesamt-Siege: {stats['total_wins']}",
            f"Beste Zeit: {time_str}",
            f"Total Parries: {stats['total_parries']}",
            f"Höchste Parry-Chain: {stats['highest_parry_chain']}",
            f"Total Damage: {int(stats['total_damage_dealt'])}"
        ]

        y = 180
        for label in labels:
            draw_text(screen, label, 30, SCREEN_WIDTH//2, y, COLOR_WHITE)
            y += 50

        draw_text(screen, "Press ESC to return", 20, SCREEN_WIDTH//2, SCREEN_HEIGHT - 50, COLOR_GRAY)

class UIManager:
    def __init__(self, game):
        self.game = game
        self.hud = HUD(game)
        self.menu = Menu(game)
        self.statistics_screen = StatisticsScreen(game, game.save_system.data)
        self.challenge_screen = ChallengeSelectScreen(game)
        self.demo_panel = DemoAbilityPanel(game)

    def draw(self, screen):
        if self.game.state == "MENU":
            self.menu.draw(screen)
        elif self.game.state == "CHALLENGE_SELECT":
            self.challenge_screen.draw(screen)
        elif self.game.state == "STATISTICS":
            self.statistics_screen.draw(screen)
        elif self.game.state in ["PLAYING", "PAUSED", "WIN_SCREEN", "DEMO"]:
            self.hud.draw(screen)
            if self.game.state == "DEMO" and self.game.demo.panel_visible:
                self.demo_panel.draw(screen)

            if self.game.state == "PAUSED":
                draw_text(screen, "PAUSED", 64, SCREEN_WIDTH//2, SCREEN_HEIGHT//2, COLOR_WHITE)

            if self.game.state == "DEMO":
                draw_text(screen, "⚡ DEMO MODE — ESC zum Beenden", 24, SCREEN_WIDTH//2, 30, COLOR_RED)

            if self.game.state == "WIN_SCREEN":
                self.game.grade_screen.draw(screen)
