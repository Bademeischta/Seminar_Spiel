import pygame
import os

# --- Konstanten & Konfiguration ---
# Farben
SCHWARZ = (0, 0, 0)
WEISS = (255, 255, 255)
BLAU = (0, 0, 255)
GRUEN = (0, 255, 0)
ROT = (255, 0, 0)
BRAUN = (139, 69, 19)

FPS = 60
TITEL = "Schul-Abenteuer"

# Physik
GRAVITY = 0.8
PLAYER_ACC = 0.5
PLAYER_FRICTION = -0.12
PLAYER_MAX_SPEED = 8.0
JUMP_FORCE = -16

# Dateipfade (Konfigurierbar)
BG_IMG_FLUR = os.path.join("sprites", "World", "Fenster.jpeg")     # Flur
BG_IMG_TOILETTE = os.path.join("sprites", "World", "Toiletten.jpeg") # Toilette
# Für die Tür haben wir kein klares Sprite, wir nutzen einen Platzhalter oder laden "Türen.jpeg" falls gewünscht.
# Da "Türen.jpeg" existiert, versuchen wir es als Textur für die Tür zu nutzen, oder als Fallback.
DOOR_TEXTURE = os.path.join("sprites", "World", "Türen.jpeg")

class ResourceManager:
    """Lädt und verwaltet Ressourcen."""
    @staticmethod
    def load_image(path, fallback_color=ROT):
        try:
            if os.path.exists(path):
                img = pygame.image.load(path)
                return img.convert() # Optimierung
            else:
                raise FileNotFoundError(f"{path} nicht gefunden")
        except Exception as e:
            print(f"Fehler beim Laden von {path}: {e}")
            surf = pygame.Surface((64, 64))
            surf.fill(fallback_color)
            return surf

class PhysicsPlayer(pygame.sprite.Sprite):
    """
    Spieler-Klasse mit verbesserter Physik (Beschleunigung, Reibung).
    """
    def __init__(self):
        super().__init__()
        # Visuelles Erscheinungsbild
        self.image = pygame.Surface([40, 60])
        self.image.fill(BLAU)
        self.rect = self.image.get_rect()

        # Physik-Vektoren
        self.pos = pygame.math.Vector2(0, 0)
        self.vel = pygame.math.Vector2(0, 0)
        self.acc = pygame.math.Vector2(0, 0)

        # Status
        self.on_ground = False

    def jump(self):
        if self.on_ground:
            self.vel.y = JUMP_FORCE
            self.on_ground = False

    def update(self, keys, platforms, world_width=None):
        self.acc = pygame.math.Vector2(0, GRAVITY)

        # Eingabe
        if keys[pygame.K_a]:
            self.acc.x = -PLAYER_ACC
        if keys[pygame.K_d]:
            self.acc.x = PLAYER_ACC

        # Reibung anwenden
        self.acc.x += self.vel.x * PLAYER_FRICTION

        # Bewegungsgleichungen
        self.vel += self.acc

        # Max Speed Begrenzung (Horizontal)
        if abs(self.vel.x) > PLAYER_MAX_SPEED:
             self.vel.x = PLAYER_MAX_SPEED if self.vel.x > 0 else -PLAYER_MAX_SPEED

        # Kleine Geschwindigkeiten auf 0 setzen (gegen Zittern)
        if abs(self.vel.x) < 0.1:
            self.vel.x = 0

        self.pos += self.vel + 0.5 * self.acc

        # Position auf Rect übertragen (zuerst X)
        self.rect.x = round(self.pos.x)

        # Welt-Begrenzung (wenn angegeben)
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
        hit_list = pygame.sprite.spritecollide(self, platforms, False)
        for block in hit_list:
            if self.vel.x > 0:
                self.rect.right = block.rect.left
            elif self.vel.x < 0:
                self.rect.left = block.rect.right
            self.pos.x = self.rect.x

        # Position Y
        self.rect.y = round(self.pos.y)

        # Kollision Y
        self.on_ground = False
        hit_list = pygame.sprite.spritecollide(self, platforms, False)
        for block in hit_list:
            if self.vel.y > 0:
                self.rect.bottom = block.rect.top
                self.vel.y = 0
                self.on_ground = True
            elif self.vel.y < 0:
                self.rect.top = block.rect.bottom
                self.vel.y = 0
            self.pos.y = self.rect.y

class Door(pygame.sprite.Sprite):
    def __init__(self, x, y, width=60, height=100):
        super().__init__()
        # Versuche Textur zu nutzen, sonst Braun
        self.image = pygame.Surface([width, height])

        # Wir laden hier keine Textur direkt, um Performance zu sparen,
        # oder wir nutzen eine statische Ressource.
        # Einfachheitshalber: Braunes Rechteck mit Rahmen
        self.image.fill(BRAUN)
        pygame.draw.rect(self.image, WEISS, (0,0,width,height), 2)

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

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
    """Basis-Klasse für Level."""
    def __init__(self, screen_width, screen_height):
        self.platforms = pygame.sprite.Group()
        self.doors = pygame.sprite.Group()
        self.all_sprites = pygame.sprite.Group() # Enthält keine Hintergründe
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.background_img = None

        # Boden erstellen (gemeinsam für alle Level, kann überschrieben werden)
        floor_h = 40
        self.floor_y = screen_height - floor_h
        # Default Boden: unendlich breit theoretisch, hier lokal
        self.floor = Platform(-50000, self.floor_y, 100000, floor_h, invisible=True)
        self.platforms.add(self.floor)

    def update(self, player):
        self.all_sprites.update()
        self.doors.update()

    def draw(self, screen, scroll_x=0):
        # Hintergrund zeichnen (muss implementiert werden)
        pass

    def draw_tiled_background(self, screen, img, scroll_x):
        if not img: return

        img_w = img.get_width()
        img_h = img.get_height()

        # Vertikal zentrieren oder kacheln? Anforderung: "Boden muss passend dazu positioniert werden"
        # Wir platzieren das Bild so, dass es unten am Boden abschließt oder füllt.
        # Option: Scale to fit height? Nein, "NICHT gestreckt".
        # Wir platzieren es Bottom-Aligned.

        draw_y = self.screen_height - img_h
        # Falls das Bild kleiner als der Screen ist, füllen wir den Rest mit Schwarz oder kacheln vertikal?
        # User sagt: "Wenn das Bild kleiner als der Bildschirm ist, soll es gekachelt (tiled) oder zentriert werden"

        # Horizontal Tiling Logic
        start_col = int(scroll_x // img_w)
        end_col = int((scroll_x + self.screen_width) // img_w) + 1

        for col in range(start_col, end_col + 1):
            draw_x = col * img_w - scroll_x
            screen.blit(img, (draw_x, draw_y))

            # Falls Bild oben nicht reicht, Farbe füllen oder kacheln?
            # Wir lassen es dabei.

class HallwayLevel(Level):
    def __init__(self, screen_width, screen_height):
        super().__init__(screen_width, screen_height)
        self.background_img = ResourceManager.load_image(BG_IMG_FLUR, WEISS)

        # Türen generieren (unregelmäßig)
        # Wir platzieren Türen alle 800 - 1500 Pixel
        import random
        current_x = 400
        for _ in range(20): # Generiere erstmal Türen für eine lange Strecke
            dist = random.randint(600, 1200)
            current_x += dist
            door = Door(current_x, self.floor_y - 100) # Türhöhe 100
            self.doors.add(door)

    def draw(self, screen, scroll_x):
        screen.fill(SCHWARZ) # Fallback
        self.draw_tiled_background(screen, self.background_img, scroll_x)

        # Zeichne Sprites mit Offset
        for sprite in self.doors:
            # Nur zeichnen wenn im Bild
            if sprite.rect.right - scroll_x > 0 and sprite.rect.left - scroll_x < self.screen_width:
                screen.blit(sprite.image, (sprite.rect.x - scroll_x, sprite.rect.y))

class ToiletLevel(Level):
    def __init__(self, screen_width, screen_height):
        super().__init__(screen_width, screen_height)
        self.background_img = ResourceManager.load_image(BG_IMG_TOILETTE, (100, 100, 100))

        # Begrenzungen (Wände)
        left_wall = Platform(-20, 0, 20, screen_height)
        right_wall = Platform(screen_width, 0, 20, screen_height)
        self.platforms.add(left_wall)
        self.platforms.add(right_wall)

        # Eine Tür zum Zurückgehen (links oder mittig?)
        # Sagen wir am Eingang (links)
        self.door_exit = Door(50, self.floor_y - 100)
        self.doors.add(self.door_exit)

    def draw(self, screen, scroll_x=0):
        # Statischer Hintergrund (zentriert oder gekachelt)
        screen.fill(SCHWARZ)

        # Zentrieren
        if self.background_img:
            img_w = self.background_img.get_width()
            x_pos = (self.screen_width - img_w) // 2
            y_pos = self.screen_height - self.background_img.get_height()
            screen.blit(self.background_img, (x_pos, y_pos))

            # Falls Bild zu schmal, links rechts schwarz (ist schon so durch fill)
            # Falls Bild zu breit, wird es abgeschnitten (Standard blit)

        for sprite in self.doors:
            screen.blit(sprite.image, (sprite.rect.x, sprite.rect.y))


class Game:
    def __init__(self):
        pygame.init()
        # Fullscreen handling
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        info = pygame.display.Info()
        self.screen_width = info.current_w
        self.screen_height = info.current_h
        pygame.display.set_caption(TITEL)

        self.clock = pygame.time.Clock()
        self.running = True

        # Zustände
        self.STATE_FLUR = "FLUR"
        self.STATE_TOILETTE = "TOILETTE"
        self.current_state = self.STATE_FLUR

        # Level-Instanzen
        self.level_flur = HallwayLevel(self.screen_width, self.screen_height)
        self.level_toilette = ToiletLevel(self.screen_width, self.screen_height)

        # Aktives Level
        self.current_level = self.level_flur

        # Spieler
        self.player = PhysicsPlayer()
        # Startposition
        self.player.rect.x = 100
        self.player.pos.x = 100
        self.player.rect.y = self.screen_height - 200
        self.player.pos.y = self.player.rect.y

        # Kamera / Persistence
        self.scroll_x = 0
        self.saved_world_x = 0

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

                # Interaktion
                if event.key == pygame.K_w:
                    self.try_interact()

        # Spieler Update (mit Physik)
        # Im Flur ist die Welt "unendlich", in der Toilette begrenzt
        world_limit = None
        if self.current_state == self.STATE_TOILETTE:
            world_limit = self.screen_width

        self.player.update(keys, self.current_level.platforms, world_width=world_limit)

    def try_interact(self):
        # Prüfe Kollision mit Türen
        # Achtung: Player ist im Screen-Space (mehr oder weniger),
        # aber im Flur müssen wir scroll_x beachten.

        player_rect = self.player.rect.copy()

        if self.current_state == self.STATE_FLUR:
            # Im Flur: Player x ist screen relative, aber Doors sind world absolute.
            # Um Kollision zu prüfen, müssen wir Player in World-Koord umrechnen
            player_world_rect = player_rect.copy()
            player_world_rect.x += int(self.scroll_x)

            # Prüfe Kollision
            hit_door = False
            for door in self.current_level.doors:
                if player_world_rect.colliderect(door.rect):
                    hit_door = True
                    break

            if hit_door:
                self.switch_to_toilet()

        elif self.current_state == self.STATE_TOILETTE:
            # In der Toilette: Keine Kameraverschiebung
            hit_door = False
            for door in self.current_level.doors:
                if player_rect.colliderect(door.rect):
                    hit_door = True
                    break

            if hit_door:
                self.switch_to_flur()

    def switch_to_toilet(self):
        # a) Speichere Position
        # Die "echte" Position im Flur ist scroll_x + player.rect.x
        # Wir wollen, dass der Spieler später an der exakt gleichen Stelle weiterläuft.
        # Am einfachsten: Wir speichern scroll_x. Die Player-Screen-Pos können wir resetten oder behalten.
        self.saved_world_x = self.scroll_x + self.player.rect.x

        # b) Wechsel Status
        self.current_state = self.STATE_TOILETTE
        self.current_level = self.level_toilette

        # c) Spieler an Eingang setzen
        self.player.rect.x = 100
        self.player.pos.x = 100
        self.player.vel.x = 0
        self.player.acc.x = 0

        # Reset scroll (Toilette hat kein Scrolling)
        self.scroll_x = 0

    def switch_to_flur(self):
        # a) Wechsel Status
        self.current_state = self.STATE_FLUR
        self.current_level = self.level_flur

        # b) Position wiederherstellen
        # Wir wollen, dass (scroll_x + player.rect.x) == saved_world_x
        # Wir setzen den Spieler in die Mitte des Screens (oder wo er war) und berechnen scroll_x entsprechend.

        target_screen_x = self.screen_width // 2
        self.player.rect.x = target_screen_x
        self.player.pos.x = target_screen_x
        self.player.vel.x = 0
        self.player.acc.x = 0

        self.scroll_x = self.saved_world_x - target_screen_x
        if self.scroll_x < 0: self.scroll_x = 0 # Sollte im unendlichen Flur kein Problem sein, aber sicherheitshalber

    def update_camera(self):
        if self.current_state == self.STATE_FLUR:
            # Side Scrolling Logic: Spieler in der Mitte halten
            # Ziel: Player.rect.x soll ~ screen_width / 2 sein
            # Wenn Player sich bewegt, passen wir scroll_x an, nicht player.rect.x (visuell)
            # ABER: Die PhysicsPlayer Logik bewegt player.rect.x
            # Wir müssen also "nachziehen".

            # Schwellenwert für Scrolling (Deadzone)
            limit_left = self.screen_width // 2 - 50
            limit_right = self.screen_width // 2 + 50

            # Einfaches Scrolling: Wenn Spieler zu weit rechts, scrollen wir
            if self.player.rect.right > limit_right:
                diff = self.player.rect.right - limit_right
                self.scroll_x += diff
                self.player.rect.right = limit_right
                self.player.pos.x = self.player.rect.x # Sync Physics pos

            if self.player.rect.left < limit_left:
                diff = limit_left - self.player.rect.left
                if self.scroll_x > 0: # Nur nach links scrollen wenn wir nicht am Anfang sind
                    self.scroll_x -= diff
                    self.player.rect.left = limit_left
                    self.player.pos.x = self.player.rect.x

            # Begrenzung Scroll
            if self.scroll_x < 0:
                self.scroll_x = 0

    def run(self):
        while self.running:
            self.handle_input()
            self.update_camera()

            # Draw
            # 1. Level Hintergrund & Türen
            self.current_level.draw(self.screen, self.scroll_x)

            # 2. Spieler (hat Offset im Flur nicht nötig, da wir scroll_x nutzen um die Welt zu verschieben,
            # und den Spieler im Screen-Space fixieren (durch update_camera).
            # Wait, PhysicsPlayer bewegt rect im Screen Space. update_camera korrigiert es.
            # Also zeichnen wir Player einfach an rect.
            self.screen.blit(self.player.image, self.player.rect)

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

if __name__ == "__main__":
    Game().run()
