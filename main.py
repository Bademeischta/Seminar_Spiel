import pygame
import os
import random
import sys

# --- Constants ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
FPS = 60

# Physics
GRAVITY = 0.8
PLAYER_ACC = 0.6
PLAYER_FRICTION = -0.12
PLAYER_MAX_SPEED = 8.0
PLAYER_JUMP_FORCE = -18  # Stronger jump for bigger character

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
    path_parts: list of strings, e.g. ["sprites", "Player", "Player.jpeg"]
    scale_size: tuple (width, height) or None
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
        # Flip images if facing left
        current_idle = self.image_idle if self.facing_right else pygame.transform.flip(self.image_idle, True, False)
        current_run = self.image_run if self.facing_right else pygame.transform.flip(self.image_run, True, False)

        # Idle check (small threshold for velocity)
        if abs(self.vel.x) < 0.5:
            self.image = current_idle
        else:
            # Run animation toggle
            self.animation_timer += 1
            if self.animation_timer > 10:  # Switch every 10 frames
                self.is_running_frame = not self.is_running_frame
                self.animation_timer = 0

            self.image = current_run if self.is_running_frame else current_idle

    def apply_gravity(self):
        self.acc.y = GRAVITY

    def update_physics(self):
        self.acc.x += self.vel.x * PLAYER_FRICTION
        self.vel += self.acc
        self.pos += self.vel + 0.5 * self.acc

        # Floor collision (Simple floor at bottom of screen for now)
        # We assume the floor is at SCREEN_HEIGHT - 50 (to leave space or match bg)
        FLOOR_Y = SCREEN_HEIGHT

        if self.pos.y > FLOOR_Y:
            self.pos.y = FLOOR_Y
            self.vel.y = 0

        self.rect.bottomleft = self.pos

class Player(Entity):
    def __init__(self, x, y):
        # Load Assets
        # Scaling Player to ~80px height (Factor 2.0 roughly from original description)
        scale = (60, 90)
        img_idle = load_image(["sprites", "Spieler", "Spieler.jpeg"], scale, BLUE)
        img_run = load_image(["sprites", "Spieler", "Spieler_run.jpeg"], scale, BLUE)

        super().__init__(x, y, img_idle, img_run)
        self.score_distance = 0

    def update(self):
        self.acc = pygame.math.Vector2(0, GRAVITY)
        keys = pygame.key.get_pressed()

        # Input
        if keys[pygame.K_a]:
            self.acc.x = -PLAYER_ACC
            self.facing_right = False
        if keys[pygame.K_d]:
            self.acc.x = PLAYER_ACC
            self.facing_right = True

        # Limit Speed
        if abs(self.vel.x) > PLAYER_MAX_SPEED:
            self.vel.x = PLAYER_MAX_SPEED * (1 if self.vel.x > 0 else -1)

        # Physics
        self.update_physics()
        self.update_animation()

        # Update Distance Score (only counts moving right)
        if self.vel.x > 0:
            self.score_distance += self.vel.x / 100.0  # Scale down for meters

    def jump(self):
        # Only jump if on floor (simple check)
        if self.rect.bottom >= SCREEN_HEIGHT:
            self.vel.y = PLAYER_JUMP_FORCE

class Teacher(Entity):
    def __init__(self, x, y, type_idx):
        # Randomly choose teacher 1 or 2
        path_prefix = f"Lehrer{type_idx}"
        filename = f"Lehrer{type_idx}"

        scale = (60, 90) # Match player size roughly
        img_idle = load_image(["sprites", "Lehrer", path_prefix, f"{filename}.jpeg"], scale, RED)
        img_run = load_image(["sprites", "Lehrer", path_prefix, f"{filename}_run.jpeg"], scale, RED)

        super().__init__(x, y, img_idle, img_run)

        # AI State
        self.direction = random.choice([-1, 1])
        self.move_speed = random.uniform(1.0, 2.5)
        self.change_dir_timer = random.randint(60, 200)

    def update(self):
        self.acc = pygame.math.Vector2(0, GRAVITY)

        # Patrol Logic
        self.acc.x = self.direction * (PLAYER_ACC * 0.5) # Slower than player

        # Max Speed for Teacher
        if abs(self.vel.x) > self.move_speed:
            self.vel.x = self.move_speed * self.direction

        self.facing_right = (self.direction == 1)

        # Change direction randomly
        self.change_dir_timer -= 1
        if self.change_dir_timer <= 0:
            self.direction *= -1
            self.change_dir_timer = random.randint(60, 200)

        self.update_physics()
        self.update_animation()

class Door(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # Load Door
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
        self.font = pygame.font.SysFont("Arial", 24, bold=True)

        # Load Backgrounds
        self.bg_hallway = load_image(["sprites", "World", "Fenster.jpeg"], (SCREEN_WIDTH, SCREEN_HEIGHT), GRAY)
        # We don't need Toilet bg for the main loop unless we implement room switching.
        # Focusing on the "Runner" aspect for now as per "Distance" requirement.

        self.reset()

    def reset(self):
        self.all_sprites = pygame.sprite.Group()
        self.doors = pygame.sprite.Group()
        self.teachers = pygame.sprite.Group()

        self.player = Player(100, SCREEN_HEIGHT)
        self.all_sprites.add(self.player)

        # Level Generation State
        self.camera_x = 0
        self.next_spawn_x = 400 # Start spawning objects a bit ahead

    def generate_level(self):
        # As player moves right, camera_x increases.
        # We spawn things ahead of the camera (Screen Width + Buffer)

        spawn_trigger_x = self.camera_x + SCREEN_WIDTH + 100

        if self.next_spawn_x < spawn_trigger_x:
            # Decide what to spawn
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

            # Advance spawn point randomly
            self.next_spawn_x += random.randint(300, 600)

    def cleanup_level(self):
        # Remove objects that are far to the left
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
                if event.key == pygame.K_SPACE:
                    self.player.jump()
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                # Interaction logic (entering door) could go here
                if event.key == pygame.K_w:
                    hits = pygame.sprite.spritecollide(self.player, self.doors, False)
                    if hits:
                        print("Interacted with door! (Feature placeholder)")

    def run(self):
        running = True
        while running:
            self.handle_input()

            # Updates
            self.player.update()

            # Camera Logic: Follow player
            # Target camera is player.x - offset. We smooth it or just lock it.
            # Simple locking: Camera shows player at 1/3rd of screen
            target_cam_x = self.player.pos.x - (SCREEN_WIDTH // 3)
            # Don't scroll left past 0 (start)
            if target_cam_x < 0:
                target_cam_x = 0
            self.camera_x = target_cam_x

            # Update other entities
            for t in self.teachers:
                t.update()

            # Level Management
            self.generate_level()
            self.cleanup_level()

            # Drawing
            # Draw Background (Parallax/Tiling)
            # We tile the background image based on camera_x
            rel_x = self.camera_x % self.bg_hallway.get_width()
            self.screen.blit(self.bg_hallway, (-rel_x, 0))
            if rel_x < SCREEN_WIDTH:
                self.screen.blit(self.bg_hallway, (-rel_x + self.bg_hallway.get_width(), 0))

            # Draw Sprites with Camera Offset
            for sprite in self.all_sprites:
                # Calculate screen position
                screen_pos = (sprite.rect.x - self.camera_x, sprite.rect.y)
                self.screen.blit(sprite.image, screen_pos)

            # UI / HUD
            dist_text = self.font.render(f"Distanz: {int(self.player.score_distance)} m", True, BLACK)
            self.screen.blit(dist_text, (20, 20))

            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()
