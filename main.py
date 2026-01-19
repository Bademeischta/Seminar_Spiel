import pygame
import os
import random

# --- Konstanten & Konfiguration ---
# Farben
SCHWARZ = (0, 0, 0)
WEISS = (255, 255, 255)
BLAU = (0, 0, 255)
GRUEN = (0, 255, 0)
ROT = (255, 0, 0)
BRAUN = (139, 69, 19)
GELB = (255, 255, 0)

FPS = 60
TITEL = "Schul-Abenteuer"

# Physik & Gameplay
GRAVITY = 0.8
PLAYER_ACC = 0.8        # Schneller
PLAYER_FRICTION = -0.12
PLAYER_MAX_SPEED = 10.0 # Schneller
JUMP_FORCE = -18

PLAYER_SCALE = 2.0      # Größer

class ResourceManager:
    """Lädt und verwaltet Ressourcen sicher."""
    _image_cache = {}
    BASE_PATH = os.path.dirname(__file__)

    @staticmethod
    def get_path(*paths):
        return os.path.join(ResourceManager.BASE_PATH, *paths)

    @staticmethod
    def load_image(path_segments, size=None, fallback_color=ROT):
        """
        Lädt ein Bild anhand von Pfad-Segmenten (Liste von Ordnern/Dateien).
        Optional: Skaliert das Bild auf 'size' (Breite, Höhe).
        """
        full_path = ResourceManager.get_path(*path_segments)
        key = (full_path, size)

        if key in ResourceManager._image_cache:
            return ResourceManager._image_cache[key]

        try:
            if os.path.exists(full_path):
                img = pygame.image.load(full_path).convert_alpha()
                if size:
                    img = pygame.transform.scale(img, size)
                ResourceManager._image_cache[key] = img
                return img
            else:
                raise FileNotFoundError(f"Nicht gefunden: {full_path}")
        except Exception as e:
            # print(f"Ladefehler bei {full_path}: {e}") # Debug off
            surf = pygame.Surface(size if size else (50, 50))
            surf.fill(fallback_color)
            ResourceManager._image_cache[key] = surf
            return surf

class AnimatedSprite(pygame.sprite.Sprite):
    """Basisklasse für animierte Sprites (Idle/Run)."""
    def __init__(self, img_idle, img_run):
        super().__init__()
        self.img_idle = img_idle
        self.img_run = img_run
        self.image = self.img_idle
        self.rect = self.image.get_rect()

        self.animation_timer = 0
        self.animation_interval = 10 # Frames pro Bildwechsel
        self.is_running_anim = False # Frame-State

        # Physik
        self.pos = pygame.math.Vector2(0, 0)
        self.vel = pygame.math.Vector2(0, 0)
        self.acc = pygame.math.Vector2(0, 0)
        self.facing_right = True

    def animate(self):
        """Wechselt zwischen Idle und Run basierend auf Geschwindigkeit."""
        if abs(self.vel.x) > 0.5:
            self.animation_timer += 1
            if self.animation_timer >= self.animation_interval:
                self.animation_timer = 0
                self.is_running_anim = not self.is_running_anim

            current_img = self.img_run if self.is_running_anim else self.img_idle

            # Richtung
            if self.vel.x > 0:
                self.facing_right = True
            elif self.vel.x < 0:
                self.facing_right = False
        else:
            current_img = self.img_idle
            self.is_running_anim = False

        # Flip image if looking left
        if not self.facing_right:
            self.image = pygame.transform.flip(current_img, True, False)
        else:
            self.image = current_img

        # Rect position update (damit das Bild nicht "springt" beim Flip, falls Center unterschiedlich wäre)
        # Hier ignorieren wir das simple resizing, da wir skalierte Bilder nutzen.

class Player(AnimatedSprite):
    def __init__(self, platforms):
        # Bilder laden
        # Zielgröße berechnen: Original ist ca 40x60 -> Scale 2.0 -> 80x120
        # Wir laden erst und skalieren dann.
        raw_idle = ResourceManager.load_image(["sprites", "Spieler", "Spieler.jpeg"], fallback_color=BLAU)
        raw_run = ResourceManager.load_image(["sprites", "Spieler", "Spieler_run.jpeg"], fallback_color=BLAU)

        w, h = raw_idle.get_size()
        target_size = (int(w * PLAYER_SCALE), int(h * PLAYER_SCALE))

        img_idle = pygame.transform.scale(raw_idle, target_size)
        img_run = pygame.transform.scale(raw_run, target_size)

        super().__init__(img_idle, img_run)

        self.platforms = platforms
        self.on_ground = False

    def jump(self):
        if self.on_ground:
            self.vel.y = JUMP_FORCE
            self.on_ground = False

    def update(self, keys, world_width=None):
        self.acc = pygame.math.Vector2(0, GRAVITY)

        if keys[pygame.K_a]:
            self.acc.x = -PLAYER_ACC
        if keys[pygame.K_d]:
            self.acc.x = PLAYER_ACC

        # Reibung
        self.acc.x += self.vel.x * PLAYER_FRICTION
        self.vel += self.acc

        # Max Speed
        if abs(self.vel.x) > PLAYER_MAX_SPEED:
             self.vel.x = PLAYER_MAX_SPEED if self.vel.x > 0 else -PLAYER_MAX_SPEED

        if abs(self.vel.x) < 0.1: self.vel.x = 0

        # Physik Update X
        self.pos.x += self.vel.x + 0.5 * self.acc.x
        self.rect.x = round(self.pos.x)

        # Begrenzung
        if world_width is not None:
            if self.rect.left < 0:
                self.rect.left = 0
                self.pos.x = self.rect.x
                self.vel.x = 0
            if self.rect.right > world_width:
                self.rect.right = world_width
                self.pos.x = self.rect.x
                self.vel.x = 0

        # Kollision X
        hit_list = pygame.sprite.spritecollide(self, self.platforms, False)
        for block in hit_list:
            if self.vel.x > 0:
                self.rect.right = block.rect.left
            elif self.vel.x < 0:
                self.rect.left = block.rect.right
            self.pos.x = self.rect.x

        # Physik Update Y
        self.pos.y += self.vel.y + 0.5 * self.acc.y
        self.rect.y = round(self.pos.y)

        # Kollision Y
        self.on_ground = False
        hit_list = pygame.sprite.spritecollide(self, self.platforms, False)
        for block in hit_list:
            if self.vel.y > 0:
                self.rect.bottom = block.rect.top
                self.vel.y = 0
                self.on_ground = True
            elif self.vel.y < 0:
                self.rect.top = block.rect.bottom
                self.vel.y = 0
            self.pos.y = self.rect.y

        self.animate()

class Teacher(AnimatedSprite):
    def __init__(self, x, y, platforms):
        # Zufallsauswahl Lehrer 1 oder 2
        type_choice = random.choice(["Lehrer1", "Lehrer2"])

        # Pfade
        path_idle = ["sprites", "Lehrer", type_choice, f"{type_choice}.jpeg"]
        path_run = ["sprites", "Lehrer", type_choice, f"{type_choice}_run.jpeg"]

        # Laden & Skalieren (Lehrer auch etwas größer)
        raw_idle = ResourceManager.load_image(path_idle, fallback_color=ROT)
        raw_run = ResourceManager.load_image(path_run, fallback_color=ROT)

        w, h = raw_idle.get_size()
        scale = 1.5
        target_size = (int(w * scale), int(h * scale))

        img_idle = pygame.transform.scale(raw_idle, target_size)
        img_run = pygame.transform.scale(raw_run, target_size)

        super().__init__(img_idle, img_run)

        self.rect.x = x
        self.rect.y = y - self.rect.height # y ist Boden-Koordinate
        self.pos = pygame.math.Vector2(self.rect.x, self.rect.y)

        self.platforms = platforms

        # AI
        self.move_timer = 0
        self.move_duration = random.randint(60, 180)
        self.direction = random.choice([-1, 1])
        self.speed = random.uniform(2, 4)

    def update(self):
        # Einfache AI: Hin und her laufen
        self.move_timer += 1
        if self.move_timer >= self.move_duration:
            self.move_timer = 0
            self.move_duration = random.randint(60, 180)
            # Chance anzuhalten oder Richtung zu wechseln
            action = random.choice(["stop", "flip", "walk"])
            if action == "stop":
                self.direction = 0
            elif action == "flip":
                self.direction *= -1
                if self.direction == 0: self.direction = 1
            elif action == "walk":
                if self.direction == 0: self.direction = random.choice([-1, 1])

        # Physik (einfacher als Player)
        self.vel.y += GRAVITY
        self.vel.x = self.direction * self.speed

        # Bewegung X
        self.pos.x += self.vel.x
        self.rect.x = round(self.pos.x)

        # Kollision X (optional, hier einfach Umdrehen bei Hindernis wenn wir wollten, aber wir haben nur Boden)

        # Bewegung Y
        self.pos.y += self.vel.y
        self.rect.y = round(self.pos.y)

        # Kollision Y (Boden)
        hit_list = pygame.sprite.spritecollide(self, self.platforms, False)
        for block in hit_list:
            if self.vel.y > 0:
                self.rect.bottom = block.rect.top
                self.vel.y = 0
            elif self.vel.y < 0:
                self.rect.top = block.rect.bottom
                self.vel.y = 0
            self.pos.y = self.rect.y

        self.animate()


class Door(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # Tür Textur laden
        self.image = ResourceManager.load_image(["sprites", "World", "Türen.jpeg"], size=(80, 140), fallback_color=BRAUN)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y - 140 # y ist Boden

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, invisible=False):
        super().__init__()
        self.image = pygame.Surface((w, h))
        if invisible:
             self.image.set_colorkey(SCHWARZ)
             self.image.fill(SCHWARZ)
        else:
            self.image.fill(GRUEN)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Level:
    """Basis Level Manager."""
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.platforms = pygame.sprite.Group()
        self.doors = pygame.sprite.Group()
        self.npcs = pygame.sprite.Group()

        # Globaler Boden
        floor_h = 40
        self.floor_y = screen_h - floor_h
        # Sehr breiter Boden (wir versetzen ihn nicht, da scroll_x die Kamera schiebt)
        # Für infinite runner müssen wir aufpassen.
        # Einfacher: Ein sehr breiter Boden, oder wir bewegen den Boden mit dem Spieler?
        # Nein, Kamera-Scroll ist Offset beim Zeichnen.
        # Für unendlich brauchen wir einen unendlich breiten Collider oder wir setzen die Player-X-Pos zurück.
        # Hier: Ein extrem breiter Boden reicht für die Presentation (z.B. 1 Million Pixel).
        self.floor = Platform(-50000, self.floor_y, 200000, floor_h, invisible=True)
        self.platforms.add(self.floor)

    def update(self):
        self.doors.update()
        self.npcs.update()

    def draw(self, screen, scroll_x):
        pass

class HallwayLevel(Level):
    def __init__(self, screen_w, screen_h):
        super().__init__(screen_w, screen_h)
        self.bg = ResourceManager.load_image(["sprites", "World", "Fenster.jpeg"], fallback_color=WEISS)

        # Generator Status
        self.next_spawn_x = 400

        # Initiale Objekte generieren
        self.generate_chunk(0, self.screen_w * 2)

    def generate_chunk(self, start_x, end_x):
        """Generiert Türen und Lehrer in einem Bereich."""
        current_x = max(start_x, self.next_spawn_x)

        while current_x < end_x:
            # Zufall was kommt
            # Distanz zum nächsten Objekt
            step = random.randint(400, 1000)
            current_x += step

            # Objektwahl: Tür (Wichtig) oder Lehrer?
            # Sagen wir 60% Tür, 40% Lehrer
            if random.random() < 0.6:
                d = Door(current_x, self.floor_y)
                self.doors.add(d)
            else:
                t = Teacher(current_x, self.floor_y, self.platforms)
                self.npcs.add(t)

            self.next_spawn_x = current_x

    def update_generation(self, scroll_x):
        # Generiere neue Sachen voraus
        look_ahead = scroll_x + self.screen_w * 2
        if self.next_spawn_x < look_ahead:
            self.generate_chunk(self.next_spawn_x, look_ahead)

        # Cleanup alte Sachen
        cleanup_threshold = scroll_x - 500
        for sprite in self.doors:
            if sprite.rect.right < cleanup_threshold:
                sprite.kill()
        for sprite in self.npcs:
            if sprite.rect.right < cleanup_threshold:
                sprite.kill()

    def draw(self, screen, scroll_x):
        # Hintergrund Kacheln (Unten ausgerichtet)
        if self.bg:
            bg_w = self.bg.get_width()
            bg_h = self.bg.get_height()
            draw_y = self.screen_h - bg_h

            start_col = int(scroll_x // bg_w)
            end_col = int((scroll_x + self.screen_w) // bg_w) + 1

            for col in range(start_col, end_col + 1):
                draw_x = col * bg_w - scroll_x
                screen.blit(self.bg, (draw_x, draw_y))
        else:
            screen.fill(WEISS)

        # Sprites
        for sprite in self.doors:
            # Sichtbarkeitsprüfung
            if sprite.rect.right - scroll_x > 0 and sprite.rect.left - scroll_x < self.screen_w:
                screen.blit(sprite.image, (sprite.rect.x - scroll_x, sprite.rect.y))

        for sprite in self.npcs:
            if sprite.rect.right - scroll_x > 0 and sprite.rect.left - scroll_x < self.screen_w:
                screen.blit(sprite.image, (sprite.rect.x - scroll_x, sprite.rect.y))

class ToiletLevel(Level):
    def __init__(self, screen_w, screen_h):
        super().__init__(screen_w, screen_h)
        self.bg = ResourceManager.load_image(["sprites", "World", "Toiletten.jpeg"], fallback_color=(100,100,100))

        # Wände
        w = 20
        self.platforms.add(Platform(-w, 0, w, screen_h))
        self.platforms.add(Platform(screen_w, 0, w, screen_h))

        # Ausgangstür (links)
        self.exit_door = Door(100, self.floor_y)
        self.doors.add(self.exit_door)

    def draw(self, screen, scroll_x=0):
        # Statisch zentriert
        screen.fill(SCHWARZ)
        if self.bg:
             # Scale to fit width? No requirements said "original resolution" but also "fill screen" logic?
             # User said: "Wenn das Bild kleiner als der Bildschirm ist, soll es gekachelt (tiled) oder zentriert werden"
             # Wir zentrieren.
             bg_rect = self.bg.get_rect(center=(self.screen_w // 2, self.screen_h // 2))
             # Wenn zu klein, evtl scale? User sagte "NICHT gestreckt".
             # Wir richten es unten aus, wie Flur.
             bg_rect.bottom = self.screen_h
             bg_rect.centerx = self.screen_w // 2
             screen.blit(self.bg, bg_rect)

        for sprite in self.doors:
            screen.blit(sprite.image, sprite.rect)


class Game:
    def __init__(self):
        pygame.init()
        # Fullscreen
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        info = pygame.display.Info()
        self.screen_w = info.current_w
        self.screen_h = info.current_h
        pygame.display.set_caption(TITEL)

        # Font
        self.font = pygame.font.SysFont("Arial", 30, bold=True)

        self.clock = pygame.time.Clock()
        self.running = True

        # Levels
        self.level_flur = HallwayLevel(self.screen_w, self.screen_h)
        self.level_toilette = ToiletLevel(self.screen_w, self.screen_h)

        self.state = "FLUR"
        self.level = self.level_flur

        # Spieler
        self.player = Player(self.level.platforms) # Start platforms
        self.player.rect.x = 200
        self.player.pos.x = 200
        self.player.rect.bottom = self.level.floor_y
        self.player.pos.y = self.player.rect.y

        # Kamera & Persistence
        self.scroll_x = 0
        self.saved_world_x = 0

    def switch_state(self, new_state):
        if new_state == "TOILETTE":
            self.saved_world_x = self.scroll_x + self.player.rect.x
            self.state = "TOILETTE"
            self.level = self.level_toilette
            # Player Setup
            self.player.platforms = self.level.platforms
            self.player.rect.x = 150
            self.player.pos.x = 150
            self.player.vel = pygame.math.Vector2(0,0)
            self.player.acc = pygame.math.Vector2(0,0)
            self.scroll_x = 0

        elif new_state == "FLUR":
            self.state = "FLUR"
            self.level = self.level_flur
            self.player.platforms = self.level.platforms
            # Restore Pos
            center_x = self.screen_w // 2
            self.player.rect.x = center_x
            self.player.pos.x = center_x
            self.player.vel = pygame.math.Vector2(0,0)

            self.scroll_x = self.saved_world_x - center_x
            if self.scroll_x < 0: self.scroll_x = 0

    def handle_input(self):
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                if event.key == pygame.K_SPACE:
                    self.player.jump()
                if event.key == pygame.K_w:
                    self.try_interact()

        # Update Player
        world_w = self.screen_w if self.state == "TOILETTE" else None
        self.player.update(keys, world_w)

    def try_interact(self):
        p_rect = self.player.rect

        if self.state == "FLUR":
            # Check Doors (World Space)
            p_world_rect = p_rect.copy()
            p_world_rect.x += int(self.scroll_x)

            for door in self.level.doors:
                if p_world_rect.colliderect(door.rect):
                    self.switch_state("TOILETTE")
                    return

        elif self.state == "TOILETTE":
             for door in self.level.doors:
                if p_rect.colliderect(door.rect):
                    self.switch_state("FLUR")
                    return

    def update_camera(self):
        if self.state == "FLUR":
            # Generation & Cleanup
            self.level.update_generation(self.scroll_x)

            # Scrolling
            limit_right = self.screen_w // 2 + 100
            limit_left = self.screen_w // 2 - 100

            if self.player.rect.right > limit_right:
                diff = self.player.rect.right - limit_right
                self.scroll_x += diff
                self.player.rect.right = limit_right
                self.player.pos.x = self.player.rect.x

            if self.player.rect.left < limit_left:
                diff = limit_left - self.player.rect.left
                if self.scroll_x > 0:
                    self.scroll_x -= diff
                    self.player.rect.left = limit_left
                    self.player.pos.x = self.player.rect.x

            if self.scroll_x < 0: self.scroll_x = 0

    def draw_hud(self):
        if self.state == "FLUR":
            # Distanz berechnung (Scroll + Player Offset)
            # Wir nehmen Pixel / 100 = Meter (grobe Annahme)
            dist_px = self.scroll_x + self.player.rect.x
            meters = int(dist_px / 50)
            text = self.font.render(f"Distanz: {meters} m", True, SCHWARZ)
            # Hintergrund für Text
            bg = pygame.Surface((text.get_width()+10, text.get_height()+10))
            bg.fill(WEISS)
            bg.set_alpha(200)

            self.screen.blit(bg, (15, 15))
            self.screen.blit(text, (20, 20))

    def run(self):
        while self.running:
            self.handle_input()
            self.level.update() # Türen, NPCs update

            self.update_camera()

            # Zeichnen
            self.screen.fill(SCHWARZ)

            self.level.draw(self.screen, self.scroll_x)

            # Player draw
            self.screen.blit(self.player.image, self.player.rect)

            self.draw_hud()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

if __name__ == "__main__":
    Game().run()
