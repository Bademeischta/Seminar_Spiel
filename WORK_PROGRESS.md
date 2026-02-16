# Projekt-Statusbericht: Schul-Abenteuer - Boss-Kampf Prototyp

## 1. Vorheriger Stand (Referenz: `main.py`)
Vor der aktuellen Erweiterung bestand das Projekt aus einem funktionalen **Infinite Runner**:
* **Movement:** Basis-Steuerung (A/D) und ein einfacher Sprung (Leertaste).
* **Gegner:** Lehrer patrouillierten im Flur; Kollision von der Seite führte zum Game Over, Sprung auf den Kopf besiegte sie.
* **Level-System:** Endlose Generierung von Türen und Lehrern. Ein Wechsel in den "Toiletten"-Raum als Safe-Room war implementiert.
* **Grafik:** Direkte Verwendung von Bild-Assets (`.jpeg`).

## 2. Der neue Boss-Prototyp (`boss_prototype.py`)

### Warum eine neue Datei?
Um das bestehende Spiel nicht zu "zerbrechen", wurde für den Boss-Kampf eine neue Struktur in `boss_prototype.py` gewählt. Dies erlaubt es, die Mechaniken isoliert zu testen, bevor sie später in das Hauptspiel integriert werden.

### Warum Greyboxing (Bunte Rechtecke)?
Es wurde bewusst auf Grafiken verzichtet, um die **Spielmechanik (Game Feel)** zu perfektionieren. Wenn sich das Spiel mit einfachen Rechtecken gut anfühlt, wird es mit finalen Assets fantastisch sein.

---

## 3. Detaillierte Änderungen & Implementierungen

### A. Erweitertes Spieler-Movement
Das Movement wurde deutlich komplexer gestaltet, um dem "Cuphead-Feeling" gerecht zu werden:
* **Variabler Sprung:** Die Sprunghöhe hängt nun davon ab, wie lange die Leertaste gedrückt wird.
* **Pausenhof-Dash (Shift):**
    * Schneller Vorstoß (ca. 150px).
    * **I-Frames:** Während des Dashes ist der Spieler unverwundbar.
    * Limitierung: Nur ein Dash pro Luftsprung möglich.
* **Streber-Parry:**
    * Pinke Projektile können parriert werden, wenn man in der Luft im richtigen Moment (15 Frames Fenster) erneut die Leertaste drückt.
    * Belohnung: Der Spieler macht einen Doppelsprung und füllt seine **Spickzettel-Leiste (Cards)**.
* **EX-Angriff (Q / Rechtsklick):** Verbraucht eine "Karte" für einen massiven Papierflieger-Angriff mit 5x Schaden.

### B. Die Arena (Das Spielfeld)
* **Plattformen:** Es wurde ein pyramidales System mit 3 Plattformen eingeführt.
* **One-Way-Collision:** Der Spieler kann von unten durch Plattformen hindurchspringen.
* **Drop-Down:** Durch Halten von `S` oder `Pfeil Runter` + `Leertaste` fällt der Spieler durch die Plattform nach unten.

### C. Boss-Kampf: Dr. Pythagoras (100 HP)
Der Boss nutzt eine **State-Machine**, um zwischen 3 Phasen zu wechseln:

1. **Phase 1 (Hellrot, 100-70 HP):** Stationär.
    * *Angriff 1 (Geometrie-Schuss):* 3 Projektile, das letzte ist pink (Parry!).
    * *Angriff 2 (Radiergummi):* Ein abprallender Block, der immer schneller wird.
2. **Phase 2 (Orange, 69-30 HP):** Schwebt auf und ab.
    * *Angriff 3 (Tafel-Wischer):* Eine riesige Wand rast von rechts nach links. Man muss durch sie hindurch-dashen.
    * *Angriff 4 (Gleichungs-Regen):* Sinusförmig fallende Objekte von der Decke.
3. **Phase 3 (Dunkelrot, 29-0 HP):** Teleportiert sich wild umher.
    * *Angriff 5 (Zirkel-Hölle):* 8-Richtungs-Schuss (Stern-Muster) in 3 Salven.
    * *Angriff 6 (Zeigestock des Todes):* Ein Laser-Visier peilt den Spieler an, gefolgt von einem dicken Laserstrahl.

### D. Benutzeroberfläche (UI)
* **Spieler-HP:** 3 rote Quadrate oben links.
* **Special-Meter:** 5 blaue Karten-Slots, die sich durch Parries füllen.
* **Boss-HP:** Ein klassischer Boss-Balken oben rechts mit Namensanzeige.

---

## 4. Technische Umsetzung
Die gesamte Logik wurde strikt **objektorientiert (OOP)** umgesetzt:
* `class Player`: Verwaltet Physik, Input, Dash-Timer und Parry-Fenster.
* `class Boss`: Verwaltet die Phasen, Movement-Muster und die Angriffs-KI.
* `class BossProjectile`: Eine Basis-Klasse für alle feindlichen Geschosse (auch parry-bare).
* `class Platform`: Ermöglicht die spezielle One-Way-Physik.

**Ergebnis:** Ein hochgradig modularer Prototyp, der bereit für finale Assets und die Verschmelzung mit dem Hauptspiel ist.
