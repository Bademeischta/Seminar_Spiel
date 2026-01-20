"""
------------------------------------------------------------
Schul-Abenteuer
Erstellt für das Seminarfach
Credits:
- Programmierung: [Dein Name/Team]
- Assets: [Quellenangabe falls nötig]
- Framework: Pygame
------------------------------------------------------------
"""
import pygame
import os
import random
import sys

# --- Constants ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
FPS = 60

# Game States
GAME_STATE_MENU = 0
GAME_STATE_PLAYING = 1
GAME_STATE_GAME_OVER = 2

# Physics
GRAVITY = 0.8
PLAYER_ACC = 0.6
PLAYER_FRICTION = -0.12
PLAYER_MAX_SPEED = 8.0
PLAYER_JUMP_FORCE = -18

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GRAY = (100, 100, 100)

# Paths
BASE_PATH = os.path.dirname(__file__)

def get_asset_path(*path_parts):
    return os.path.join(BASE_PATH, *path_parts)

# --- Asset Loader ---
def load_image(path_parts, scale_size=None, fallback_color=RED):
    """
    Loads an image safely. If not found, returns a colored surface.
    """
    full_path = get_asset_path(*path_parts)
    try:
        image = pygame.image.load(full_path).convert_alpha()
        if scale_size:
            image = pygame.transform.scale(image, scale_size)
        return image
    except (FileNotFoundError, pygame.error) as e:
        print(f"Warning: Could not load image at {full_path}. Using fallback. Error: {e}")
        surf = pygame.Surface(scale_size if scale_size else (50, 50))
        surf.fill(fallback_color)
        return surf

# --- Helper Functions ---
def draw_text_with_shadow(surface, font, text, color, x, y, shadow_color=BLACK, offset=2):
    """Draws text with a shadow for better readability."""
    shadow_surf = font.render(text, True, shadow_color)
    text_surf = font.render(text, True, color)
    surface.blit(shadow_surf, (x + offset, y + offset))
    surface.blit(text_surf, (x, y))

# --- Classes ---

class Entity(pygame.sprite.Sprite):
    def __init__(self, x, y, image_idle, image_run):
        super().__init__()
        self.image_idle = image_idle
        self.image_run = image_run
        self.image = self.image_idle
        self.rect = self.image.get_rect()
        self.rect.bottomleft = (x, y)

        # Position and Movement
        self.pos = pygame.math.Vector2(self.rect.x, self.rect.y)
        self.vel = pygame.math.Vector2(0, 0)
        self.acc = pygame.math.Vector2(0, 0)

        # State
        self.facing_right = True
        self.animation_timer = 0
        self.is_running_frame = False

    def update_animation(self):
        current_idle = self.image_idle if self.facing_right else pygame.transform.flip(self.image_idle, True, False)
        current_run = self.image_run if self.facing_right else pygame.transform.flip(self.image_run, True, False)

        if abs(self.vel.x) < 0.5:
            self.image = current_idle
        else:
            self.animation_timer += 1
            if self.animation_timer > 10:
                self.is_running_frame = not self.is_running_frame
                self.animation_timer = 0
            self.image = current_run if self.is_running_frame else current_idle

    def apply_gravity(self):
        self.acc.y = GRAVITY

    def update_physics(self):
        self.acc.x += self.vel.x * PLAYER_FRICTION
        self.vel += self.acc
        self.pos += self.vel + 0.5 * self.acc

        FLOOR_Y = SCREEN_HEIGHT
        if self.pos.y > FLOOR_Y:
            self.pos.y = FLOOR_Y
            self.vel.y = 0

        self.rect.bottomleft = self.pos

class Player(Entity):
    def __init__(self, x, y):
        scale = (60, 90)
        img_idle = load_image(["sprites", "Spieler", "Spieler.jpeg"], scale, BLUE)
        img_run = load_image(["sprites", "Spieler", "Spieler_run.jpeg"], scale, BLUE)

        super().__init__(x, y, img_idle, img_run)
        self.score_distance = 0

    def update(self):
        self.acc = pygame.math.Vector2(0, GRAVITY)
        keys = pygame.key.get_pressed()

        if keys[pygame.K_a]:
            self.acc.x = -PLAYER_ACC
            self.facing_right = False
        if keys[pygame.K_d]:
            self.acc.x = PLAYER_ACC
            self.facing_right = True

        if abs(self.vel.x) > PLAYER_MAX_SPEED:
            self.vel.x = PLAYER_MAX_SPEED * (1 if self.vel.x > 0 else -1)

        self.update_physics()
        self.update_animation()

        if self.vel.x > 0:
            self.score_distance += self.vel.x / 100.0

    def jump(self):
        if self.rect.bottom >= SCREEN_HEIGHT:
            self.vel.y = PLAYER_JUMP_FORCE

    def bounce(self):
        self.vel.y = PLAYER_JUMP_FORCE * 0.7  # Small bounce after kill

class Teacher(Entity):
    def __init__(self, x, y, type_idx):
        path_prefix = f"Lehrer{type_idx}"
        filename = f"Lehrer{type_idx}"
        scale = (60, 90)
        img_idle = load_image(["sprites", "Lehrer", path_prefix, f"{filename}.jpeg"], scale, RED)
        img_run = load_image(["sprites", "Lehrer", path_prefix, f"{filename}_run.jpeg"], scale, RED)

        super().__init__(x, y, img_idle, img_run)

        self.direction = random.choice([-1, 1])
        self.move_speed = random.uniform(1.0, 2.5)
        self.change_dir_timer = random.randint(60, 200)

    def update(self):
        self.acc = pygame.math.Vector2(0, GRAVITY)
        self.acc.x = self.direction * (PLAYER_ACC * 0.5)

        if abs(self.vel.x) > self.move_speed:
            self.vel.x = self.move_speed * self.direction

        self.facing_right = (self.direction == 1)

        self.change_dir_timer -= 1
        if self.change_dir_timer <= 0:
            self.direction *= -1
            self.change_dir_timer = random.randint(60, 200)

        self.update_physics()
        self.update_animation()

class Door(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        scale = (80, 120)
        self.image = load_image(["sprites", "World", "Türen.jpeg"], scale, GREEN)
        self.rect = self.image.get_rect()
        self.rect.bottomleft = (x, y)

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Schul-Abenteuer")
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_ui = pygame.font.SysFont("Arial", 24, bold=True)
        self.font_title = pygame.font.SysFont("Arial", 60, bold=True)
        self.font_big = pygame.font.SysFont("Arial", 40, bold=True)

        self.bg_hallway = load_image(["sprites", "World", "Fenster.jpeg"], (SCREEN_WIDTH, SCREEN_HEIGHT), GRAY)

        self.state = GAME_STATE_MENU
        self.score = 0
        self.blink_timer = 0

        # Initialize containers (will be filled in reset_game)
        self.all_sprites = None
        self.doors = None
        self.teachers = None
        self.player = None

        # Just to have empty groups before first start if needed
        self.reset_game()
        # Ensure we start at MENU
        self.state = GAME_STATE_MENU

    def reset_game(self):
        """Resets the game session completely."""
        self.score = 0
        self.all_sprites = pygame.sprite.Group()
        self.doors = pygame.sprite.Group()
        self.teachers = pygame.sprite.Group()

        self.player = Player(100, SCREEN_HEIGHT)
        self.all_sprites.add(self.player)

        self.camera_x = 0
        self.next_spawn_x = 400
        self.state = GAME_STATE_PLAYING

    def generate_level(self):
        spawn_trigger_x = self.camera_x + SCREEN_WIDTH + 100
        if self.next_spawn_x < spawn_trigger_x:
            obj_type = random.choice(["door", "teacher", "empty", "empty"])
            spawn_x = self.next_spawn_x

            if obj_type == "door":
                door = Door(spawn_x, SCREEN_HEIGHT)
                self.doors.add(door)
                self.all_sprites.add(door)
            elif obj_type == "teacher":
                t_idx = random.choice([1, 2])
                teacher = Teacher(spawn_x, SCREEN_HEIGHT, t_idx)
                self.teachers.add(teacher)
                self.all_sprites.add(teacher)

            self.next_spawn_x += random.randint(300, 600)

    def cleanup_level(self):
        despawn_threshold = self.camera_x - 200
        for sprite in self.all_sprites:
            if sprite == self.player:
                continue
            if sprite.rect.right < despawn_threshold:
                sprite.kill()

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                # State: MENU
                if self.state == GAME_STATE_MENU:
                    if event.key == pygame.K_RETURN:
                        self.reset_game()

                # State: PLAYING
                elif self.state == GAME_STATE_PLAYING:
                    if event.key == pygame.K_SPACE:
                        self.player.jump()
                    if event.key == pygame.K_w:
                        hits = pygame.sprite.spritecollide(self.player, self.doors, False)
                        if hits:
                            print("Interacted with door! (Feature placeholder)")

                # State: GAME OVER
                elif self.state == GAME_STATE_GAME_OVER:
                    if event.key == pygame.K_r:
                        self.reset_game()

    def update_playing(self):
        # Updates
        self.player.update()

        # Camera
        target_cam_x = self.player.pos.x - (SCREEN_WIDTH // 3)
        if target_cam_x < 0: target_cam_x = 0
        self.camera_x = target_cam_x

        # Teachers
        for t in self.teachers:
            t.update()

        # Level
        self.generate_level()
        self.cleanup_level()

        # Collisions: Player vs Teacher (Mario Style)
        hits = pygame.sprite.spritecollide(self.player, self.teachers, False)
        for teacher in hits:
            # Check for Stomp: Falling AND Player Bottom slightly above/overlapping Teacher Top
            # Using a threshold: if player's bottom is within the top 40% of the enemy
            if self.player.vel.y > 0 and self.player.rect.bottom < teacher.rect.top + 50:
                teacher.kill()
                self.player.bounce()
                self.score += 100
            else:
                # Lateral collision -> Game Over
                self.state = GAME_STATE_GAME_OVER

        # Fall off map check (just in case)
        if self.player.pos.y > SCREEN_HEIGHT + 100:
            self.state = GAME_STATE_GAME_OVER

    def draw_menu(self):
        self.screen.fill(BLACK)

        # Title
        title_surf = self.font_title.render("Schul-Abenteuer", True, WHITE)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        self.screen.blit(title_surf, title_rect)

        # Blinking Text
        self.blink_timer += 1
        if (self.blink_timer // 30) % 2 == 0:
            instr_surf = self.font_big.render("Drücke ENTER zum Starten", True, WHITE)
            instr_rect = instr_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(instr_surf, instr_rect)

    def draw_game_over(self):
        # We can draw over the last frame of the game for effect, or black screen.
        # Let's do a semi-transparent overlay or just black for simplicity/clarity.
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(200)
        self.screen.blit(overlay, (0, 0))

        title_surf = self.font_title.render("Nachsitzen!", True, RED)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        self.screen.blit(title_surf, title_rect)

        score_text = f"Score: {self.score} | Distanz: {int(self.player.score_distance)}m"
        score_surf = self.font_big.render(score_text, True, WHITE)
        score_rect = score_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(score_surf, score_rect)

        restart_surf = self.font_ui.render("Drücke R für Neustart", True, WHITE)
        restart_rect = restart_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        self.screen.blit(restart_surf, restart_rect)

    def draw_playing(self):
        # Draw Background
        rel_x = self.camera_x % self.bg_hallway.get_width()
        self.screen.blit(self.bg_hallway, (-rel_x, 0))
        if rel_x < SCREEN_WIDTH:
            self.screen.blit(self.bg_hallway, (-rel_x + self.bg_hallway.get_width(), 0))

        # Draw Sprites
        for sprite in self.all_sprites:
            screen_pos = (sprite.rect.x - self.camera_x, sprite.rect.y)
            self.screen.blit(sprite.image, screen_pos)

        # Draw Door Hint
        # Check overlap without spritecollide (since we need camera offset) OR use spritecollide
        door_hits = pygame.sprite.spritecollide(self.player, self.doors, False)
        if door_hits:
            # Draw above player
            hint_x = self.player.rect.centerx - self.camera_x - 40
            hint_y = self.player.rect.top - 30
            draw_text_with_shadow(self.screen, self.font_ui, "Drücke [W]", WHITE, hint_x, hint_y)

        # HUD
        hud_text = f"Distanz: {int(self.player.score_distance)} m | Score: {self.score}"
        draw_text_with_shadow(self.screen, self.font_ui, hud_text, WHITE, 20, 20)

    def run(self):
        running = True
        while running:
            self.handle_input()

            if self.state == GAME_STATE_MENU:
                self.draw_menu()
            elif self.state == GAME_STATE_PLAYING:
                self.update_playing()
                self.draw_playing()
            elif self.state == GAME_STATE_GAME_OVER:
                self.draw_game_over()

            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()
