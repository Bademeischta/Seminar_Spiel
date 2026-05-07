import pygame
import math
from constants import *
from boss_projectiles import BossProjectile
from utils import draw_text


class TutorialStep:
    def __init__(self, title, lines, hint, check_fn=None, timeout=25.0):
        self.title = title
        self.lines = lines
        self.hint = hint
        self.check_fn = check_fn   # callable(game) -> bool
        self.timeout = timeout


class TutorialManager:
    """
    Interactive tutorial that walks the player through core mechanics
    step by step. The boss is frozen while in TUTORIAL state (see boss.py).
    A slow parryable bullet is periodically fired from step 4 onward so the
    player can practice parrying without waiting for actual boss attacks.
    """

    STEPS = [
        TutorialStep(
            "Schritt 1: Bewegung",
            ["Benutze A / D (oder Pfeiltasten), um dich zu bewegen."],
            "Drücke A oder D",
            check_fn=lambda g: abs(g.player.vel.x) > 80,
        ),
        TutorialStep(
            "Schritt 2: Springen",
            ["Drücke SPACE zum Springen.",
             "In der Luft nochmals SPACE für den Doppelsprung!"],
            "SPACE – Springen  |  SPACE + SPACE – Doppelsprung",
            check_fn=lambda g: g.player.jump_count >= 1,
        ),
        TutorialStep(
            "Schritt 3: Dash / Ausweichen",
            ["Drücke LSHIFT für einen blitzschnellen Dash.",
             "Halte eine Richtungstaste während des Dashens!"],
            "LSHIFT – Dash (8 Richtungen)",
            check_fn=lambda g: g.player.is_dashing or g.player.dash_cooldown_timer > 0,
        ),
        TutorialStep(
            "Schritt 4: Schießen",
            ["Linksklick: Basis-Schuss.",
             "Halte die Maustaste für einen Charge Shot (mehr Schaden).",
             "Ziel: Der Boss rechts im Bild. Treffe ihn!"],
            "Linksklick – Schuss  |  Halten – Charge Shot",
            check_fn=lambda g: g.tutorial_damage_dealt > 0,
            timeout=40.0,
        ),
        TutorialStep(
            "Schritt 5: Parry (Abblocken)",
            ["ROSA Projektile können pariert werden.",
             "Halte S gedrückt und drücke SPACE, wenn ein",
             "rosa Projektil auf dich zukommt.",
             "Perfektes Timing = Extra-Karten und Slow-Motion!"],
            "S + SPACE – Parry  (bei rosa Projektilen)",
            check_fn=lambda g: g.total_parries > 0,
            timeout=60.0,
        ),
        TutorialStep(
            "Schritt 6: Schild (Notfall)",
            ["Drücke E um den Notizbuch-Schild zu aktivieren.",
             "Er hält einen Treffer ab – Cooldown: 3,5 Sekunden."],
            "E – Schild aktivieren",
            check_fn=lambda g: g.player.shield_cooldown > 0,
        ),
        TutorialStep(
            "Schritt 7: Karten & EX-Angriffe",
            ["Die blauen Balken links sind deine KARTEN.",
             "Du sammelst sie durch Schießen und Parieren.",
             "Rechtsklick feuert einen EX-Angriff (kostet Karten).",
             "Tasten 1–5 wechseln den EX-Angriff-Typ."],
            "Rechtsklick – EX-Angriff  |  1-5 – Typ wechseln",
            check_fn=lambda g: g.player.cards >= 1.5,
            timeout=40.0,
        ),
        TutorialStep(
            "Schritt 8: Fortgeschrittene Techniken",
            ["F – Focus-Modus: Zeit verlangsamt sich (blaue Leiste).",
             "3× Parieren in Folge aktiviert STREBER MODE (Gold):",
             "  Triple-Sprung, mehr Schaden, 5 Sekunden lang!",
             "Wenn der Boss GELB leuchtet: DOPPELTER Schaden!",
             "Bei 5 Karten feuert Rechtsklick den ULTIMATE-Laser."],
            "F – Focus  |  3× Parry – Streber Mode  |  Gelber Boss = 2× Schaden",
            check_fn=None,
            timeout=15.0,
        ),
        TutorialStep(
            "Tutorial abgeschlossen!",
            ["Du kennst jetzt alle Mechaniken von Dr. Pythagoras 2.0.",
             "Viel Erfolg im echten Kampf!",
             "",
             "Drücke ENTER oder SPACE um das Spiel zu starten."],
            "ENTER / SPACE – Zum Hauptmenü",
            check_fn=None,
            timeout=999.0,
        ),
    ]

    def __init__(self, game):
        self.game = game
        self.step_idx = 0
        self.step_timer = 0.0
        self.done = False

        # Delay shown after a step is completed before advancing
        self.complete_flash_timer = 0.0
        self.FLASH_DURATION = 1.2

        # Periodic tutorial bullets starting from step 4 (parry step)
        self.bullet_timer = 3.0

        # Give player a small card headstart so EX step is reachable
        game.player.cards = 0.5

    # ------------------------------------------------------------------
    def update(self, dt):
        if self.done:
            return

        step = self.STEPS[self.step_idx]

        # Show "✓ VERSTANDEN!" briefly before advancing
        if self.complete_flash_timer > 0:
            self.complete_flash_timer -= dt
            if self.complete_flash_timer <= 0:
                self._advance()
            return

        self.step_timer += dt

        # Spawn slow parryable bullets from the parry step onward
        if self.step_idx >= 4:
            self.bullet_timer -= dt
            if self.bullet_timer <= 0:
                self._spawn_tutorial_bullet()
                self.bullet_timer = 4.0

        # Check completion condition
        if step.check_fn is not None:
            try:
                if step.check_fn(self.game):
                    self._complete_step()
                    return
            except Exception:
                pass

        # Timeout fallback – skip step automatically
        if self.step_timer >= step.timeout:
            self._complete_step()

    def _complete_step(self):
        self.complete_flash_timer = self.FLASH_DURATION

    def _advance(self):
        if self.step_idx < len(self.STEPS) - 1:
            self.step_idx += 1
            self.step_timer = 0.0
            self.bullet_timer = 3.0
        else:
            self.done = True

    def skip_step(self):
        """Called when player presses ESC during a non-final step."""
        if self.step_idx < len(self.STEPS) - 1:
            self._complete_step()

    def finish(self):
        """Called when player presses ENTER/SPACE on the final step."""
        if self.step_idx == len(self.STEPS) - 1:
            self.done = True

    def _spawn_tutorial_bullet(self):
        boss = self.game.boss
        bullet = BossProjectile(
            self.game,
            boss.rect.left,
            boss.rect.centery + (0 if self.step_idx % 2 == 0 else 60),
            -120,  # slow horizontal speed
            0,
            is_parryable=True,
        )
        self.game.all_sprites.add(bullet)
        self.game.boss_bullets.add(bullet)

    # ------------------------------------------------------------------
    def draw(self, screen):
        step = self.STEPS[self.step_idx]
        total = len(self.STEPS)

        panel_h = 130
        panel_y = SCREEN_HEIGHT - panel_h

        # Semi-transparent background panel
        surf = pygame.Surface((SCREEN_WIDTH, panel_h), pygame.SRCALPHA)
        surf.fill((10, 10, 30, 210))
        screen.blit(surf, (0, panel_y))

        # Step progress dots
        dot_spacing = 16
        dots_x_start = SCREEN_WIDTH // 2 - (total * dot_spacing) // 2
        for i in range(total):
            cx = dots_x_start + i * dot_spacing + dot_spacing // 2
            if i < self.step_idx:
                color = COLOR_GREEN
                r = 5
            elif i == self.step_idx:
                color = COLOR_GOLD
                r = 6
            else:
                color = COLOR_DARK_GRAY
                r = 4
            pygame.draw.circle(screen, color, (cx, panel_y + 10), r)

        if self.complete_flash_timer > 0:
            # Flash completion message
            alpha = int(min(255, self.complete_flash_timer / self.FLASH_DURATION * 510))
            draw_text(screen, "✓  VERSTANDEN!", 42, SCREEN_WIDTH // 2,
                      panel_y + panel_h // 2 - 10, COLOR_GREEN, alpha=alpha)
        else:
            # Title
            draw_text(screen, step.title, 22, SCREEN_WIDTH // 2, panel_y + 22, COLOR_GOLD)

            # Instruction lines
            y = panel_y + 46
            for line in step.lines:
                draw_text(screen, line, 17, SCREEN_WIDTH // 2, y, COLOR_WHITE)
                y += 20

            # Key hint bar
            hint_y = SCREEN_HEIGHT - 14
            draw_text(screen, step.hint, 16, SCREEN_WIDTH // 2, hint_y, COLOR_CYAN)

            # ESC skip hint (not on final step)
            if self.step_idx < len(self.STEPS) - 1:
                draw_text(screen, "ESC = Schritt überspringen", 13,
                          SCREEN_WIDTH - 90, panel_y + 10, COLOR_GRAY)

        # Pulsing arrow pointing to boss during shooting step
        if self.step_idx == 3 and self.complete_flash_timer <= 0:
            t = pygame.time.get_ticks() / 1000.0
            offset = int(math.sin(t * 4) * 8)
            boss = self.game.boss
            bx = boss.rect.centerx
            by = boss.rect.centery - 20 + offset
            pygame.draw.polygon(screen, COLOR_YELLOW, [
                (bx - 12, by - 20), (bx + 12, by - 20), (bx, by)
            ])
