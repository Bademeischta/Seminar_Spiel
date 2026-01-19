import pygame
import os

# --- Konstanten ---
# Farben
SCHWARZ = (0, 0, 0)
WEISS = (255, 255, 255)
BLAU = (0, 0, 255)
GRUEN = (0, 255, 0) # Nur für Fallback
ROT = (255, 0, 0)   # Nur für Fallback

FPS = 60
TITEL = "Schul-Abenteuer"

class Platform(pygame.sprite.Sprite):
    """
    Klasse für Plattformen (Boden, Wände).
    """
    def __init__(self, breite, hoehe, x, y, invisible=False):
        super().__init__()
        self.image = pygame.Surface([breite, hoehe])
        if invisible:
            # Wir machen die Surface unsichtbar, indem wir schwarz als transparent definieren
            # oder einfach nicht zeichnen (wird im Draw-Loop gehandhabt)
            self.image.set_colorkey(SCHWARZ)
            self.image.fill(SCHWARZ)
            # Alternativ mit Alpha-Kanal für komplette Transparenz
            self.image = pygame.Surface([breite, hoehe], pygame.SRCALPHA)
            self.image.fill((0,0,0,0))
        else:
            self.image.fill(GRUEN)

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Player(pygame.sprite.Sprite):
    """
    Klasse für den Spieler.
    """
    def __init__(self, platforms):
        super().__init__()
        self.image = pygame.Surface([40, 60])
        self.image.fill(BLAU)
        self.rect = self.image.get_rect()

        self.change_x = 0
        self.change_y = 0

        self.platforms = platforms

    def update(self):
        self.calc_grav()

        self.rect.x += self.change_x

        block_hit_list = pygame.sprite.spritecollide(self, self.platforms, False)
        for block in block_hit_list:
            if self.change_x > 0:
                self.rect.right = block.rect.left
            elif self.change_x < 0:
                self.rect.left = block.rect.right

        self.rect.y += self.change_y

        block_hit_list = pygame.sprite.spritecollide(self, self.platforms, False)
        for block in block_hit_list:
            if self.change_y > 0:
                self.rect.bottom = block.rect.top
                self.change_y = 0
            elif self.change_y < 0:
                self.rect.top = block.rect.bottom
                self.change_y = 0

    def calc_grav(self):
        if self.change_y == 0:
            self.change_y = 1
        else:
            self.change_y += 0.8

    def jump(self):
        self.rect.y += 2
        platform_hit_list = pygame.sprite.spritecollide(self, self.platforms, False)
        self.rect.y -= 2

        if len(platform_hit_list) > 0:
            self.change_y = -16

    def go_left(self):
        self.change_x = -6

    def go_right(self):
        self.change_x = 6

    def stop(self):
        self.change_x = 0

def load_backgrounds(width, height):
    bg_images = []
    # Logische Reihenfolge: Eingang (Türen) -> Flur (Fenster) -> Klassenzimmer (Toiletten)
    # Annahme der Reihenfolge basierend auf Dateinamen.

    files = ["Türen.jpeg", "Fenster.jpeg", "Toiletten.jpeg"]
    base_path = os.path.join("sprites", "World")

    colors = [WEISS, (200, 200, 200), (150, 150, 150)] # Fallback colors

    for i, filename in enumerate(files):
        path = os.path.join(base_path, filename)
        try:
            if os.path.exists(path):
                img = pygame.image.load(path)
                img = pygame.transform.scale(img, (width, height))
                bg_images.append(img)
            else:
                raise FileNotFoundError(f"{filename} nicht gefunden")
        except (pygame.error, FileNotFoundError) as e:
            print(f"Warnung: Konnte {filename} nicht laden ({e}). Nutze Platzhalter.")
            surf = pygame.Surface((width, height))
            surf.fill(colors[i % len(colors)])
            bg_images.append(surf)

    return bg_images

def main():
    pygame.init()

    # 1. Fenster & Display: Vollbild
    # Wir nutzen (0, 0) und FULLSCREEN um die native Auflösung zu bekommen
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    info = pygame.display.Info()
    BILDSCHIRM_BREITE = info.current_w
    BILDSCHIRM_HOEHE = info.current_h

    pygame.display.set_caption(TITEL)

    # Hintergründe laden
    backgrounds = load_backgrounds(BILDSCHIRM_BREITE, BILDSCHIRM_HOEHE)

    # Sprite-Gruppen
    all_sprites = pygame.sprite.Group()
    platforms = pygame.sprite.Group()

    # 3. Level-Design: Unsichtbarer Boden über gesamte Welt
    # Weltgröße = 3 * Bildschirmbreite (da wir 3 Hintergrundbilder haben)
    world_width = BILDSCHIRM_BREITE * 3

    # Boden am unteren Bildschirmrand
    boden_hoehe = 40
    # Boden über die gesamte Breite der Welt
    boden = Platform(world_width, boden_hoehe, 0, BILDSCHIRM_HOEHE - boden_hoehe, invisible=True)
    platforms.add(boden)
    # Wir fügen den Boden NICHT zu all_sprites hinzu, damit er nicht automatisch gezeichnet wird (oder wir handhaben es manuell)

    # Spieler erstellen
    player = Player(platforms)
    player.rect.x = 100
    # Startposition knapp über dem Boden
    player.rect.y = BILDSCHIRM_HOEHE - boden_hoehe - player.rect.height - 10
    all_sprites.add(player)

    clock = pygame.time.Clock()
    done = False

    scroll_x = 0

    while not done:
        # Event-Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True

            # Keydown
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    done = True
                # 2. Steuerung: A (links), D (rechts), LEER (springen)
                if event.key == pygame.K_a:
                    player.go_left()
                if event.key == pygame.K_d:
                    player.go_right()
                if event.key == pygame.K_SPACE:
                    player.jump()

            # Keyup
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_a and player.change_x < 0:
                    player.stop()
                if event.key == pygame.K_d and player.change_x > 0:
                    player.stop()

        # Update
        all_sprites.update()

        # 4. Kamera / Scrolling
        # Der Spieler soll sich "mittig" anfühlen.
        # Wir berechnen scroll_x so, dass der Spieler in der Mitte des Bildschirms wäre.

        target_scroll_x = player.rect.x - BILDSCHIRM_BREITE // 2

        # Limits für Scrolling:
        # Links: 0 (Start der Welt)
        # Rechts: world_width - BILDSCHIRM_BREITE (Ende der Welt, damit man nicht ins Schwarze scrollt)
        if target_scroll_x < 0:
            target_scroll_x = 0
        if target_scroll_x > world_width - BILDSCHIRM_BREITE:
            target_scroll_x = world_width - BILDSCHIRM_BREITE

        scroll_x = target_scroll_x

        # Zeichnen
        screen.fill(SCHWARZ)

        # Hintergründe zeichnen
        # Positionen: 0, W, 2W. Wir subtrahieren scroll_x für den Sidescrolling-Effekt.
        for i, bg in enumerate(backgrounds):
            bg_x = i * BILDSCHIRM_BREITE - scroll_x
            # Performance-Optimierung: Nur zeichnen wenn im Bild
            # Ein Bild ist sichtbar, wenn seine rechte Kante > 0 ist UND seine linke Kante < Bildschirmbreite
            if bg_x + BILDSCHIRM_BREITE > 0 and bg_x < BILDSCHIRM_BREITE:
                screen.blit(bg, (bg_x, 0))

        # Sprites zeichnen mit Offset (scroll_x)
        for sprite in all_sprites:
            screen.blit(sprite.image, (sprite.rect.x - scroll_x, sprite.rect.y))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
