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
GAME_STATE_TRANSITION = 3

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

        # Input handling (disabled during transition via Game class logic, but good to be safe)
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

class TransitionManager:
    def __init__(self, game):
        self.game = game
        self.phase = 0  # 0: Inactive, 1: Vortex, 2: Shutter Close, 3: Shutter Open

        # Animation Settings
        self.vortex_duration = 75  # Frames (~1.25s)
        self.shutter_duration = 45 # Frames (~0.75s)

        # State
        self.timer = 0
        self.original_player_img = None
        self.start_pos = None
        self.target_pos = None
        self.shutter_bars = [] # List of (rect, start_pos, target_pos, angle)

    def start_transition(self, target_door_rect):
        """Starts the transition sequence."""
        self.game.state = GAME_STATE_TRANSITION
        self.phase = 1
        self.timer = 0

        # Vortex Setup
        # Capture original image for high-quality rotation
        self.original_player_img = self.game.player.image.copy()

        # Start and Target positions relative to screen (since camera is frozen)
        # Player pos is currently world pos. Need to convert to screen pos.
        p_screen_x = self.game.player.rect.centerx - self.game.camera_x
        p_screen_y = self.game.player.rect.centery
        self.start_pos = pygame.math.Vector2(p_screen_x, p_screen_y)

        d_screen_x = target_door_rect.centerx - self.game.camera_x
        d_screen_y = target_door_rect.centery
        self.target_pos = pygame.math.Vector2(d_screen_x, d_screen_y)

        # Shutter Setup
        self.shutter_bars = []
        bar_w, bar_h = 700, 400
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2

        # Define 4 bars outside screen moving to center
        # (Start Pos, End Pos, Angle)
        configs = [
            ((cx, -bar_h), (cx, cy - 100), 45),    # Top
            ((cx, SCREEN_HEIGHT + bar_h), (cx, cy + 100), 45), # Bottom
            ((-bar_w, cy), (cx - 150, cy), 135),   # Left
            ((SCREEN_WIDTH + bar_w, cy), (cx + 150, cy), 135) # Right
        ]

        # Actually let's make them simpler but larger to ensure coverage
        # 4 Rects coming from 4 sides to center.
        # We use surfaces to support rotation
        for i in range(4):
            surf = pygame.Surface((800, 600))
            surf.fill(BLACK)

            # Target center
            target = pygame.math.Vector2(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)

            # Start positions (Top, Right, Bottom, Left)
            if i == 0: start = pygame.math.Vector2(SCREEN_WIDTH//2, -400)
            elif i == 1: start = pygame.math.Vector2(SCREEN_WIDTH + 400, SCREEN_HEIGHT//2)
            elif i == 2: start = pygame.math.Vector2(SCREEN_WIDTH//2, SCREEN_HEIGHT + 400)
            else: start = pygame.math.Vector2(-400, SCREEN_HEIGHT//2)

            angle = 45 + (i * 90) # Rotate them a bit
            self.shutter_bars.append({'surf': surf, 'start': start, 'target': target, 'angle': angle})

    def update(self):
        self.timer += 1

        if self.phase == 1: # Vortex
            if self.timer >= self.vortex_duration:
                self.phase = 2
                self.timer = 0

        elif self.phase == 2: # Shutter Close
            if self.timer >= self.shutter_duration:
                # Screen is black, switch level
                self.game.switch_level()
                self.phase = 3
                self.timer = 0

        elif self.phase == 3: # Shutter Open
            if self.timer >= self.shutter_duration:
                self.game.state = GAME_STATE_PLAYING
                self.phase = 0

    def draw(self, screen):
        # Phase 1: Vortex (Draw spinning player)
        if self.phase == 1:
            t = self.timer / self.vortex_duration
            # Ease in/out
            t = t * t * (3 - 2 * t)

            # Lerp Position
            curr_pos = self.start_pos.lerp(self.target_pos, t)

            # Rotation & Scale
            angle = t * 360 * 4 # Spin 4 times
            scale = 1.0 - t
            if scale < 0: scale = 0

            # Rotozoom
            # rotozoom(surface, angle, scale)
            rotated_img = pygame.transform.rotozoom(self.original_player_img, angle, scale)
            new_rect = rotated_img.get_rect(center=(int(curr_pos.x), int(curr_pos.y)))
            screen.blit(rotated_img, new_rect)

        # Phase 2 & 3: Shutter
        if self.phase in [2, 3]:
            screen_center = pygame.math.Vector2(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)

            if self.phase == 2: # Closing
                t = self.timer / self.shutter_duration
            else: # Opening (reverse)
                t = 1.0 - (self.timer / self.shutter_duration)

            # Ease
            t = t * t * (3 - 2 * t)

            # Fill background black if fully closed to avoid gaps
            if self.phase == 2 and t > 0.95:
                screen.fill(BLACK)
            elif self.phase == 3 and t > 0.95:
                screen.fill(BLACK)

            for bar in self.shutter_bars:
                # Lerp position
                curr_pos = bar['start'].lerp(bar['target'], t)

                # Rotate bar
                rot_angle = bar['angle'] * t
                rotated_surf = pygame.transform.rotate(bar['surf'], rot_angle)
                rect = rotated_surf.get_rect(center=(int(curr_pos.x), int(curr_pos.y)))

                screen.blit(rotated_surf, rect)

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

        # Backgrounds
        self.bg_hallway = load_image(["sprites", "World", "Fenster.jpeg"], (SCREEN_WIDTH, SCREEN_HEIGHT), GRAY)
        self.bg_toilet = load_image(["sprites", "World", "Toiletten.jpeg"], (SCREEN_WIDTH, SCREEN_HEIGHT), GRAY)

        self.state = GAME_STATE_MENU
        self.score = 0
        self.blink_timer = 0

        # Level Management
        self.in_toilet = False
        self.saved_hallway_data = {} # To store x pos etc.

        self.transition_manager = TransitionManager(self)

        # Initialize containers (will be filled in reset_game)
        self.all_sprites = None
        self.doors = None
        self.teachers = None
        self.player = None

        self.reset_game()
        self.state = GAME_STATE_MENU

    def reset_game(self):
        """Resets the game session completely."""
        self.score = 0
        self.in_toilet = False
        self.saved_hallway_data = {}

        self.all_sprites = pygame.sprite.Group()
        self.doors = pygame.sprite.Group()
        self.teachers = pygame.sprite.Group()

        self.player = Player(100, SCREEN_HEIGHT)
        self.all_sprites.add(self.player)

        self.camera_x = 0
        self.next_spawn_x = 400
        self.state = GAME_STATE_PLAYING

    def switch_level(self):
        """Toggles between Hallway and Toilet."""
        if not self.in_toilet:
            # Go to Toilet
            self.in_toilet = True

            # Save Hallway State
            self.saved_hallway_data = {
                'camera_x': self.camera_x,
                'player_x': self.player.pos.x,
                'score_distance': self.player.score_distance,
                # Note: We technically lose enemies here if we just clear groups.
                # For simplicity, we'll clear and assume they despawned or player "escaped".
                # If we wanted to keep them, we'd need multiple sprite groups or object persistence.
                # Given requirements: "Level-Wechsel (Flur <-> Toilette)", usually implies a scene switch.
            }

            # Clear Objects
            self.doors.empty()
            self.teachers.empty()
            self.all_sprites.empty()

            # Setup Toilet
            # Safe room, bounded. Center camera conceptually or fixed 0.
            self.camera_x = 0

            # Spawn Player at entrance (left side usually)
            self.player.pos.x = 100
            self.player.pos.y = SCREEN_HEIGHT
            self.player.vel = pygame.math.Vector2(0, 0)
            self.player.rect.bottomleft = self.player.pos
            self.all_sprites.add(self.player)

            # Spawn Exit Door
            exit_door = Door(800, SCREEN_HEIGHT)
            self.doors.add(exit_door)
            self.all_sprites.add(exit_door)

        else:
            # Return to Hallway
            self.in_toilet = False

            # Restore Data
            saved = self.saved_hallway_data
            self.camera_x = saved.get('camera_x', 0)
            self.player.score_distance = saved.get('score_distance', 0)

            # Clear Toilet Objects
            self.doors.empty()
            self.teachers.empty()
            self.all_sprites.empty()

            # Restore Player
            self.player.pos.x = saved.get('player_x', 100)
            self.player.pos.y = SCREEN_HEIGHT
            self.player.vel = pygame.math.Vector2(0, 0)
            self.player.rect.bottomleft = self.player.pos
            self.all_sprites.add(self.player)

            # We need to ensure we don't spawn right on top of nothing.
            # Maybe spawn a door behind us to show where we came from?
            # Or just resume. Let's resume.
            # Ensure `next_spawn_x` is ahead of us.
            self.next_spawn_x = max(self.next_spawn_x, self.camera_x + SCREEN_WIDTH + 100)

    def generate_level(self):
        # Only generate in Hallway
        if self.in_toilet:
            return

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
        if self.in_toilet:
            return

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
                        # Check Door Interaction
                        hits = pygame.sprite.spritecollide(self.player, self.doors, False)
                        if hits:
                            # Trigger Transition!
                            # Find the closest door center (should be 'hits[0]')
                            target_door = hits[0]
                            self.transition_manager.start_transition(target_door.rect)

                # State: GAME OVER
                elif self.state == GAME_STATE_GAME_OVER:
                    if event.key == pygame.K_r:
                        self.reset_game()

    def update_playing(self):
        # Updates
        self.player.update()

        # Toilet Constraints
        if self.in_toilet:
            # Walls
            if self.player.pos.x < 50: self.player.pos.x = 50
            if self.player.pos.x > SCREEN_WIDTH - 50: self.player.pos.x = SCREEN_WIDTH - 50

            # Keep camera static
            # self.camera_x remains 0 (set in switch_level)

        else:
            # Hallway Camera
            target_cam_x = self.player.pos.x - (SCREEN_WIDTH // 3)
            if target_cam_x < 0: target_cam_x = 0
            self.camera_x = target_cam_x

            # Teachers (Only update/spawn in Hallway)
            for t in self.teachers:
                t.update()

            # Level Generation
            self.generate_level()
            self.cleanup_level()

            # Collisions: Player vs Teacher
            hits = pygame.sprite.spritecollide(self.player, self.teachers, False)
            for teacher in hits:
                if self.player.vel.y > 0 and self.player.rect.bottom < teacher.rect.top + 50:
                    teacher.kill()
                    self.player.bounce()
                    self.score += 100
                else:
                    self.state = GAME_STATE_GAME_OVER

        # Fall off map check
        if self.player.pos.y > SCREEN_HEIGHT + 100:
            self.state = GAME_STATE_GAME_OVER

    def draw_menu(self):
        self.screen.fill(BLACK)
        title_surf = self.font_title.render("Schul-Abenteuer", True, WHITE)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        self.screen.blit(title_surf, title_rect)

        self.blink_timer += 1
        if (self.blink_timer // 30) % 2 == 0:
            instr_surf = self.font_big.render("Drücke ENTER zum Starten", True, WHITE)
            instr_rect = instr_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(instr_surf, instr_rect)

    def draw_game_over(self):
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

    def draw_world(self):
        # Logic separated for reuse in transition (background stays visible)
        if self.in_toilet:
            self.screen.blit(self.bg_toilet, (0, 0))
        else:
            rel_x = self.camera_x % self.bg_hallway.get_width()
            self.screen.blit(self.bg_hallway, (-rel_x, 0))
            if rel_x < SCREEN_WIDTH:
                self.screen.blit(self.bg_hallway, (-rel_x + self.bg_hallway.get_width(), 0))

        # Draw Sprites
        for sprite in self.all_sprites:
            # During Vortex phase (1) and Shutter Close (2), hide the real player.
            # In Shutter Open (3), we want to see the player at the new position.
            if self.state == GAME_STATE_TRANSITION and self.transition_manager.phase in [1, 2] and sprite == self.player:
                continue

            screen_pos = (sprite.rect.x - self.camera_x, sprite.rect.y)
            self.screen.blit(sprite.image, screen_pos)

    def draw_hud(self):
        if self.in_toilet:
            draw_text_with_shadow(self.screen, self.font_ui, "Ort: Toiletten (Safe Room)", GREEN, 20, 20)
        else:
            hud_text = f"Distanz: {int(self.player.score_distance)} m | Score: {self.score}"
            draw_text_with_shadow(self.screen, self.font_ui, hud_text, WHITE, 20, 20)

        # Draw Door Hint
        door_hits = pygame.sprite.spritecollide(self.player, self.doors, False)
        if door_hits:
            hint_x = self.player.rect.centerx - self.camera_x - 40
            hint_y = self.player.rect.top - 30
            draw_text_with_shadow(self.screen, self.font_ui, "Drücke [W]", WHITE, hint_x, hint_y)

    def run(self):
        running = True
        while running:
            self.handle_input()

            if self.state == GAME_STATE_MENU:
                self.draw_menu()
            elif self.state == GAME_STATE_PLAYING:
                self.update_playing()
                self.draw_world()
                self.draw_hud()
            elif self.state == GAME_STATE_TRANSITION:
                # Update Transition
                self.transition_manager.update()

                # Draw World (Frozen)
                self.draw_world()

                # Draw Transition Effects
                self.transition_manager.draw(self.screen)

            elif self.state == GAME_STATE_GAME_OVER:
                self.draw_game_over()

            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()
