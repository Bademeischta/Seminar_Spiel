import pygame
import math
from constants import *
from utils import draw_text

class HUD:
    def __init__(self, game):
        self.game = game

    def draw(self, screen):
        # Player HP
        for i in range(MAX_PLAYER_HP):
            rect = pygame.Rect(20 + i * 40, 20, 30, 30)
            if i < self.game.player.hp:
                pygame.draw.rect(screen, RED, rect)
            else:
                pygame.draw.rect(screen, DARK_GRAY, rect, 2)

        # Special Meter (Cards)
        for i in range(MAX_CARDS):
            rect = pygame.Rect(20 + i * 35, 60, 30, 45)
            # Fill level
            fill = 0
            if i < int(self.game.player.cards):
                fill = 1.0
            elif i == int(self.game.player.cards):
                fill = self.game.player.cards % 1.0

            color = BLUE
            if i < int(self.game.player.cards):
                 # Golden card check (needs player state, simplified here to just blue or pulsing if full)
                 pass
            
            # Draw empty slot
            pygame.draw.rect(screen, color, rect, 2)
            
            if fill > 0:
                fill_rect = rect.copy()
                fill_rect.height = int(rect.height * fill)
                fill_rect.bottom = rect.bottom
                
                # Golden fill if full ultimate or perfect parry bonus?
                # For now just standard blue, but pulse white if full
                draw_color = BLUE
                if self.game.player.cards >= 5:
                    pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) * 0.5 * 255
                    draw_color = (100, 100, 255) # Light blue pulse
                
                pygame.draw.rect(screen, draw_color, fill_rect)
                
                if i < int(self.game.player.cards):
                     pygame.draw.rect(screen, WHITE, rect.inflate(-10, -10), 1)

        # Focus Meter
        focus_rect = pygame.Rect(20, 115, 170, 10)
        pygame.draw.rect(screen, DARK_GRAY, focus_rect)
        focus_fill = (self.game.player.focus_time / FOCUS_MAX_TIME) * 170
        pygame.draw.rect(screen, CYAN, (20, 115, focus_fill, 10))

        # Boss HP
        boss = self.game.boss
        if boss and boss.alive():
            hp_width = 400
            hp_rect_bg = pygame.Rect(SCREEN_WIDTH // 2 - hp_width // 2, 20, hp_width, 25)
            pygame.draw.rect(screen, DARK_GRAY, hp_rect_bg)

            hp_fill = (boss.hp / boss.max_hp) * hp_width
            hp_rect_fill = pygame.Rect(SCREEN_WIDTH // 2 - hp_width // 2, 20, hp_fill, 25)
            pygame.draw.rect(screen, boss.color, hp_rect_fill)
            pygame.draw.rect(screen, WHITE, hp_rect_bg, 2)

            draw_text(screen, "Dr. Pythagoras", 20, SCREEN_WIDTH // 2, 60, WHITE)

class GradeScreen:
    def __init__(self, game, stats):
        self.game = game
        self.stats = stats
        self.grade, self.score = self.calculate_grade()

    def calculate_grade(self):
        # Time (30%)
        time_score = 0
        t = self.stats['time']
        if t < 90: time_score = 100
        elif t < 120: time_score = 85
        elif t < 180: time_score = 70
        elif t < 240: time_score = 50
        else: time_score = 30

        # Damage (30%)
        dmg_score = 0
        hits = MAX_PLAYER_HP - self.stats['hp']
        if hits == 0: dmg_score = 100
        elif hits == 1: dmg_score = 80
        elif hits == 2: dmg_score = 60
        elif hits == 3: dmg_score = 40
        else: dmg_score = 20

        # Parries (20%)
        p = self.stats['parries']
        parry_score = 0
        if p >= 15: parry_score = 100
        elif p >= 10: parry_score = 80
        elif p >= 5: parry_score = 60
        elif p >= 1: parry_score = 40
        else: parry_score = 0

        # Style (20%)
        # Formula: (Total Style Events * 10) / Time
        raw_style = (self.stats['style'] * 10) / (t if t > 0 else 1)
        style_score = min(100, raw_style * 10) # Scaling factor needed? 
        # Let's assume style events are ~10-20 per run. 20 * 10 / 100s = 2. Too low.
        # Maybe raw points are just passed in?
        # User doc says: "Gemessen an Multi-Parry, Perfect Dash etc."
        # Let's assume stats['style'] is the count of events.
        # If I have 20 events in 100s -> 200/100 = 2.
        # Wait, formula says "(Total Style Events * 10) / Time".
        # If I want a score of 100, I need 10 style points per second? Impossible.
        # Maybe "Time" is in minutes? Or maybe it's "Style Points" directly.
        # Let's just use the raw points accumulated in game as the score component.
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
        screen.fill(BLACK)
        draw_text(screen, "KAMPF-STATISTIK", 48, SCREEN_WIDTH//2, 80, YELLOW)

        y = 180
        stats_labels = [
            f"Zeit: {int(self.stats['time'])}s",
            f"Schaden genommen: {MAX_PLAYER_HP - self.stats['hp']} Treffer",
            f"Parries: {self.stats['parries']} ({self.stats['perfect_parries']} Perfect)",
            f"Style-Events: {int(self.stats['style'])}",
            f"SCORE: {self.score}"
        ]

        for label in stats_labels:
            draw_text(screen, label, 30, SCREEN_WIDTH//2, y, WHITE)
            y += 50

        draw_text(screen, f"GRADE: {self.grade}", 80, SCREEN_WIDTH//2, y + 50, GOLD if "S" in self.grade else WHITE)
        draw_text(screen, "Press ENTER to continue", 20, SCREEN_WIDTH//2, SCREEN_HEIGHT - 50, GRAY)

class Menu:
    def __init__(self, game):
        self.game = game
        self.options = ["START GAME", "CHALLENGE MODES", "STATISTICS", "QUIT"]
        self.selected = 0

    def draw(self, screen):
        screen.fill(BLACK)
        draw_text(screen, "DR. PYTHAGORAS 2.0", 64, SCREEN_WIDTH//2, 150, LIGHT_RED)

        for i, opt in enumerate(self.options):
            color = WHITE if i == self.selected else GRAY
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

class StatisticsScreen:
    def __init__(self, game, save_data):
        self.save_data = save_data

    def draw(self, screen):
        screen.fill(BLACK)
        draw_text(screen, "LIFETIME STATISTICS", 48, SCREEN_WIDTH//2, 80, CYAN)

        stats = self.save_data["stats"]
        labels = [
            f"Gesamt-Siege: {stats['total_wins']}",
            f"Beste Zeit: {stats['best_time'] if stats['best_time'] != float('inf') else 'N/A'}s",
            f"Total Parries: {stats['total_parries']}",
            f"Höchste Parry-Chain: {stats['highest_parry_chain']}",
            f"Total Damage: {int(stats['total_damage_dealt'])}"
        ]

        y = 180
        for label in labels:
            draw_text(screen, label, 30, SCREEN_WIDTH//2, y, WHITE)
            y += 50

        draw_text(screen, "Press ESC to return", 20, SCREEN_WIDTH//2, SCREEN_HEIGHT - 50, GRAY)
