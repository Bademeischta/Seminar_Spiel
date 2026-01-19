import pygame

# --- Konstanten ---
# Farben
SCHWARZ = (0, 0, 0)
WEISS = (255, 255, 255)
BLAU = (0, 0, 255)
GRUEN = (0, 255, 0)

# Bildschirmeinstellungen
BILDSCHIRM_BREITE = 800
BILDSCHIRM_HOEHE = 600
TITEL = "Schul-Abenteuer"
FPS = 60

class Platform(pygame.sprite.Sprite):
    """
    Klasse für Plattformen (Boden, Wände, schwebende Plattformen).
    """
    def __init__(self, breite, hoehe, x, y):
        super().__init__()
        # Erstelle ein grünes Rechteck
        self.image = pygame.Surface([breite, hoehe])
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
        # Der Spieler ist ein blaues Rechteck (Breite 40, Höhe 60)
        self.image = pygame.Surface([40, 60])
        self.image.fill(BLAU)
        self.rect = self.image.get_rect()

        # Geschwindigkeitsvektoren
        self.change_x = 0
        self.change_y = 0

        # Referenz auf die Plattform-Gruppe für Kollisionsabfragen
        self.platforms = platforms

    def update(self):
        """
        Bewegt den Spieler und behandelt Kollisionen.
        """
        # Schwerkraft anwenden
        self.calc_grav()

        # Bewegung links/rechts
        self.rect.x += self.change_x

        # Horizontale Kollision prüfen
        block_hit_list = pygame.sprite.spritecollide(self, self.platforms, False)
        for block in block_hit_list:
            # Wenn wir uns nach rechts bewegen
            if self.change_x > 0:
                self.rect.right = block.rect.left
            # Wenn wir uns nach links bewegen
            elif self.change_x < 0:
                self.rect.left = block.rect.right

        # Bewegung oben/unten
        self.rect.y += self.change_y

        # Vertikale Kollision prüfen
        block_hit_list = pygame.sprite.spritecollide(self, self.platforms, False)
        for block in block_hit_list:
            # Wenn wir fallen (nach unten bewegen)
            if self.change_y > 0:
                self.rect.bottom = block.rect.top
                self.change_y = 0
            # Wenn wir nach oben springen
            elif self.change_y < 0:
                self.rect.top = block.rect.bottom
                self.change_y = 0

    def calc_grav(self):
        """
        Berechnet die Schwerkraft.
        """
        if self.change_y == 0:
            self.change_y = 1
        else:
            self.change_y += 0.8

        # Boden-Limit (Sicherheit, falls man durch den Boden fällt - optional)
        # In diesem Setup fangen die Plattformen das ab.

    def jump(self):
        """
        Lässt den Spieler springen, wenn er auf einer Plattform steht.
        """
        # Wir bewegen uns temporär 2 Pixel nach unten, um zu sehen, ob dort eine Plattform ist.
        self.rect.y += 2
        platform_hit_list = pygame.sprite.spritecollide(self, self.platforms, False)
        self.rect.y -= 2

        # Wenn wir auf etwas stehen (Liste ist nicht leer), springen wir.
        if len(platform_hit_list) > 0:
            self.change_y = -16

    def go_left(self):
        """ Gehe nach links """
        self.change_x = -6

    def go_right(self):
        """ Gehe nach rechts """
        self.change_x = 6

    def stop(self):
        """ Stoppe die horizontale Bewegung """
        self.change_x = 0

def main():
    """
    Hauptprogramm.
    """
    # 1. Setup: Initialisiere Pygame
    pygame.init()

    # Öffne ein Fenster
    screen = pygame.display.set_mode([BILDSCHIRM_BREITE, BILDSCHIRM_HOEHE])
    pygame.display.set_caption(TITEL)

    # Sprite-Gruppen
    all_sprites = pygame.sprite.Group()
    platforms = pygame.sprite.Group()

    # 6. Level-Setup
    # Erstelle einen Boden (Breite 800, Höhe 20, ganz unten)
    # y = 600 - 20 = 580
    boden = Platform(800, 20, 0, 580)
    platforms.add(boden)
    all_sprites.add(boden)

    # Erstelle 3 Plattformen in der Luft
    # Plattform 1
    p1 = Platform(200, 20, 100, 450)
    platforms.add(p1)
    all_sprites.add(p1)

    # Plattform 2
    p2 = Platform(200, 20, 500, 300)
    platforms.add(p2)
    all_sprites.add(p2)

    # Plattform 3 (Optional, z.B. höher oder dazwischen)
    p3 = Platform(100, 20, 350, 150)
    platforms.add(p3)
    all_sprites.add(p3)

    # Spieler erstellen
    # Wir übergeben die 'platforms' Gruppe an den Spieler für Kollisionen
    player = Player(platforms)
    # Startposition
    player.rect.x = 50
    player.rect.y = 500
    all_sprites.add(player)

    # Definiere eine Game-Loop mit 60 FPS
    clock = pygame.time.Clock()
    done = False

    while not done:
        # Event-Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True

            # Tasten gedrückt
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    player.go_left()
                if event.key == pygame.K_RIGHT:
                    player.go_right()
                if event.key == pygame.K_SPACE:
                    player.jump()

            # Tasten losgelassen
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT and player.change_x < 0:
                    player.stop()
                if event.key == pygame.K_RIGHT and player.change_x > 0:
                    player.stop()

        # Update
        all_sprites.update()

        # Zeichnen
        screen.fill(WEISS) # Weißer Hintergrund
        all_sprites.draw(screen)

        # Update das Display
        pygame.display.flip()

        # 60 FPS
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
