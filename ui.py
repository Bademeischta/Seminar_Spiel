import pygame
import math
import os
from constants import *
from utils import draw_text

def _load_icon(filename, size):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sprites', 'icons', filename)
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, size)
    except Exception:
        return None

class HUD:
    def __init__(self, game):
        self.game = game
        self._icons = None

    def _ensure_icons(self):
        if self._icons is not None:
            return
        card_size = (30, 45)
        ex_size = (28, 28)
        self._icons = {
            'blitz_voll': _load_icon('Blitz voll.png', card_size),
            'blitz_halb': _load_icon('Blitz halb.png', card_size),
            'blitz_leer': _load_icon('Blitz leer.png', card_size),
            'ex_flieger': _load_icon('Stift 1.png', ex_size),
            'ex_eraser':  _load_icon('Rauchverbot.png', ex_size),
            'ex_ruler':   _load_icon('Lineal.png', ex_size),
        }

    def draw(self, screen):
        self._ensure_icons()

        # Player HP
        for i in range(PLAYER_MAX_HP):
            rect = pygame.Rect(20 + i * 40, 20, 30, 30)
            if i < self.game.player.hp:
                pygame.draw.rect(screen, COLOR_RED, rect)
            else:
                pygame.draw.rect(screen, COLOR_DARK_GRAY, rect, 2)

        # Special Meter (Cards) – lightning bolt icons
        for i in range(PLAYER_MAX_CARDS):
            rect = pygame.Rect(20 + i * 35, 60, 30, 45)
            fill = 0
            if i < int(self.game.player.cards):
                fill = 1.0
            elif i == int(self.game.player.cards):
                fill = self.game.player.cards % 1.0

            if fill >= 1.0:
                icon_key = 'blitz_voll'
            elif fill > 0:
                icon_key = 'blitz_halb'
            else:
                icon_key = 'blitz_leer'

            icon = self._icons.get(icon_key)
            if icon:
                if self.game.player.cards >= 5 and fill >= 1.0:
                    pulse = int((math.sin(pygame.time.get_ticks() * 0.01) + 1) * 0.5 * 60)
                    tinted = icon.copy()
                    tinted.fill((pulse, pulse, 0, 0), special_flags=pygame.BLEND_RGBA_ADD)
                    screen.blit(tinted, rect.topleft)
                else:
                    screen.blit(icon, rect.topleft)
            else:
                # Fallback to rectangles
                color = COLOR_BLUE
                pygame.draw.rect(screen, color, rect, 2)
                if fill > 0:
                    fill_rect = rect.copy()
                    fill_rect.height = int(rect.height * fill)
                    fill_rect.bottom = rect.bottom
                    pygame.draw.rect(screen, color, fill_rect)

        # Focus Meter
        focus_rect = pygame.Rect(20, 115, 170, 10)
        pygame.draw.rect(screen, COLOR_DARK_GRAY, focus_rect)
        focus_fill = (self.game.player.focus_time / PLAYER_FOCUS_MAX_DURATION) * 170
        pygame.draw.rect(screen, COLOR_CYAN, (20, 115, focus_fill, 10))

        # EX-Ability Selector icons
        ex_map = [('Flieger', 'ex_flieger'), ('Eraser', 'ex_eraser'), ('Ruler', 'ex_ruler')]
        selected_ex = self.game.player.selected_ex
        for j, (name, key) in enumerate(ex_map):
            ix = 20 + j * 36
            iy = 130
            icon = self._icons.get(key)
            is_selected = (selected_ex == name)
            if is_selected:
                pygame.draw.rect(screen, COLOR_WHITE, (ix - 2, iy - 2, 32, 32), 2)
            if icon:
                screen.blit(icon, (ix, iy))
            else:
                color = COLOR_WHITE if is_selected else COLOR_DARK_GRAY
                pygame.draw.rect(screen, color, (ix, iy, 28, 28), 1 if not is_selected else 0)
                draw_text(screen, name[:1], 14, ix + 14, iy + 14, COLOR_WHITE)

        p = self.game.player
        y_status = 168

        # Shield cooldown bar
        shield_cd = p.shield_cooldown
        if shield_cd > 0:
            bar_fill = max(0.0, 1.0 - shield_cd / PLAYER_SHIELD_COOLDOWN)
            pygame.draw.rect(screen, COLOR_DARK_GRAY, (20, y_status, 80, 8))
            pygame.draw.rect(screen, COLOR_CYAN, (20, y_status, int(80 * bar_fill), 8))
            draw_text(screen, "E-CD", 12, 105, y_status + 4, COLOR_GRAY)
        else:
            pygame.draw.rect(screen, COLOR_CYAN, (20, y_status, 80, 8))
            draw_text(screen, "E bereit", 12, 110, y_status + 4, COLOR_CYAN)
        y_status += 14

        # Dash cooldown indicator
        dash_cd = p.dash_cooldown_timer
        if dash_cd > 0:
            bar_fill = max(0.0, 1.0 - dash_cd / PLAYER_DASH_COOLDOWN)
            pygame.draw.rect(screen, COLOR_DARK_GRAY, (20, y_status, 80, 8))
            pygame.draw.rect(screen, COLOR_ORANGE, (20, y_status, int(80 * bar_fill), 8))
            draw_text(screen, "Dash-CD", 12, 115, y_status + 4, COLOR_GRAY)
        else:
            pygame.draw.rect(screen, COLOR_ORANGE, (20, y_status, 80, 8))
            draw_text(screen, "Dash bereit", 12, 120, y_status + 4, COLOR_ORANGE)
        y_status += 14

        # Parry chain counter
        if p.parry_chain > 0 or p.streber_mode:
            if p.streber_mode:
                label = "STREBER!"
                color = COLOR_GOLD
            else:
                label = f"Chain {p.parry_chain}/3"
                color = COLOR_PINK
            draw_text(screen, label, 14, 60, y_status + 4, color)

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
        draw_text(screen, "KAMPF-STATISTIK", 48, SCREEN_WIDTH//2, 60, COLOR_YELLOW)

        t = self.stats['time']
        hits = PLAYER_MAX_HP - self.stats['hp']
        p_count = self.stats['parries']
        style = int(self.stats['style'])
        perfect = self.stats.get('perfect_parries', 0)

        # Recalculate individual scores for the breakdown display
        if t < 90:   ts = 100
        elif t < 120: ts = 85
        elif t < 180: ts = 70
        elif t < 240: ts = 50
        else:         ts = 30

        if hits == 0:   ds = 100
        elif hits == 1: ds = 80
        elif hits == 2: ds = 60
        elif hits == 3: ds = 40
        else:           ds = 20

        if p_count >= 15:   ps = 100
        elif p_count >= 10: ps = 80
        elif p_count >= 5:  ps = 60
        elif p_count >= 1:  ps = 40
        else:               ps = 0

        ss = min(100, style)

        rows = [
            (f"Zeit:           {int(t)}s", f"{int(ts * 0.3)}/30 Pkt",   ts >= 85),
            (f"Treffer:        {hits}",    f"{int(ds * 0.3)}/30 Pkt",   ds >= 80),
            (f"Parries:        {p_count} ({perfect} Perfect)", f"{int(ps * 0.2)}/20 Pkt", ps >= 60),
            (f"Style-Events:   {style}",  f"{int(ss * 0.2)}/20 Pkt",   ss >= 60),
        ]

        y = 155
        for label, pts, good in rows:
            col = COLOR_GREEN if good else COLOR_WHITE
            draw_text(screen, label, 24, SCREEN_WIDTH // 2 - 60, y, col, center=False)
            draw_text(screen, pts, 24, SCREEN_WIDTH // 2 + 230, y, col)
            y += 38

        draw_text(screen, f"SCORE: {self.score}", 28, SCREEN_WIDTH//2, y + 10, COLOR_WHITE)
        draw_text(screen, f"GRADE: {self.grade}", 80, SCREEN_WIDTH//2, y + 60,
                  COLOR_GOLD if "S" in self.grade else COLOR_WHITE)

        if self.grade not in ("S", "S+"):
            if p_count < 10:
                hint = f"Tipp: Mehr Parieren ({p_count}/15) verbessert den Rang!"
            elif hits > 2:
                hint = "Tipp: Weniger Treffer einstecken für S-Rang!"
            elif t > 150:
                hint = "Tipp: Schneller spielen verbessert den Zeit-Score!"
            else:
                hint = "Tipp: Style-Punkte durch Weak-Point-Treffer sammeln!"
            draw_text(screen, hint, 18, SCREEN_WIDTH//2, y + 155, COLOR_GRAY)

        draw_text(screen, "Press ENTER to continue", 20, SCREEN_WIDTH//2, SCREEN_HEIGHT - 20, COLOR_GRAY)

class Menu:
    def __init__(self, game):
        self.game = game
        self.options = ["TUTORIAL", "START GAME", "CHALLENGE MODES", "DEMO MODE", "STATISTICS", "QUIT"]
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
            {"name": "Mirror Match", "desc": "Boss kopiert deine Aktionen.", "diff": 3}
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
        time_str = f"{int(best_time)}s" if best_time != -1 else "N/A"
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

    def draw_game_over(self, screen):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        draw_text(screen, "GAME OVER", 80, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60, COLOR_RED)
        draw_text(screen, "Dr. Pythagoras hat gewonnen... diesmal.", 28,
                  SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20, COLOR_GRAY)
        remaining = max(0, self.game.game_over_timer)
        draw_text(screen, f"Zurück zum Menü in {int(remaining) + 1}s  (SPACE / ENTER zum Überspringen)",
                  20, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70, COLOR_WHITE)

    def draw(self, screen):
        if self.game.state == "MENU":
            self.menu.draw(screen)
        elif self.game.state == "CHALLENGE_SELECT":
            self.challenge_screen.draw(screen)
        elif self.game.state == "STATISTICS":
            self.statistics_screen.draw(screen)
        elif self.game.state == "GAME_OVER":
            self.draw_game_over(screen)
        elif self.game.state in ["PLAYING", "PAUSED", "WIN_SCREEN", "DEMO", "TUTORIAL"]:
            self.hud.draw(screen)
            if self.game.state == "DEMO" and self.game.demo.panel_visible:
                self.demo_panel.draw(screen)

            if self.game.state == "PAUSED":
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 140))
                screen.blit(overlay, (0, 0))
                draw_text(screen, "PAUSE", 64, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80, COLOR_WHITE)
                controls = [
                    "A / D  –  Bewegen",
                    "SPACE  –  Springen  |  S + SPACE  –  Parry",
                    "LSHIFT  –  Dash",
                    "Linksklick  –  Schießen  |  Rechtsklick  –  EX-Angriff",
                    "E  –  Schild  |  F  –  Focus-Modus",
                    "1-5  –  EX-Typ wählen",
                    "",
                    "P  –  Weiterspielen",
                ]
                y = SCREEN_HEIGHT // 2 - 20
                for line in controls:
                    draw_text(screen, line, 20, SCREEN_WIDTH // 2, y, COLOR_GRAY if line else COLOR_BLACK)
                    y += 26

            if self.game.state == "DEMO":
                draw_text(screen, "⚡ DEMO MODE — ESC zum Beenden", 24, SCREEN_WIDTH//2, 30, COLOR_RED)

            if self.game.state == "TUTORIAL" and self.game.tutorial_manager:
                self.game.tutorial_manager.draw(screen)

            if self.game.state == "WIN_SCREEN":
                self.game.grade_screen.draw(screen)
