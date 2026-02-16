import pygame
import math
import random
from constants import *
from boss_projectiles import *
from utils import draw_text, SoundManager

class Boss(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.sound_manager = SoundManager()
        
        self.width = 100
        self.height = 150
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.midright = (950, 450)
        
        self.hp = BOSS_MAX_HP
        self.max_hp = BOSS_MAX_HP
        self.phase = 1
        self.color = LIGHT_RED
        
        self.pos = pygame.math.Vector2(self.rect.center)
        self.vibrate_offset = pygame.math.Vector2(0, 0)
        
        # State Machine
        self.state = 'idle'
        self.state_timer = 120
        self.attack_pattern_index = 0
        self.stun_timer = 0
        
        # Phase transitions
        self.in_transition = False
        self.transition_timer = 0
        
        # Weak point
        self.weak_point_rect = None
        self.weak_point_timer = 0
        self.flash_timer = 0
        
        # Visuals
        self.float_offset = 0
        self.dialogue = ""
        self.dialogue_timer = 0
        
        self.reality_break_warning_timer = 0
        self.reality_break_pending_type = None

    def update(self, dt=1.0):
        if self.in_transition:
            self.update_transition(dt)
            return

        if self.reality_break_warning_timer > 0:
            self.reality_break_warning_timer -= dt
            if self.reality_break_warning_timer <= 0:
                self.game.apply_reality_break(self.reality_break_pending_type)
                self.reality_break_pending_type = None
            return # Pause boss logic during warning? Or just continue? Maybe continue moving but no new attacks.
            # Design says "Screen flashes", implies interrupt.
            # Let's return to prevent new attack logic, but keep movement if needed. 
            # For simplicity, freeze boss logic briefly or just return.
            # Actually, let's allow movement but block new attacks.
            pass

        if self.stun_timer > 0:
            self.stun_timer -= dt
            # Visual stun effect (stars?)
            if int(self.stun_timer) % 20 == 0:
                self.game.effect_manager.add_damage_number(self.rect.midtop, "STUNNED!", color=YELLOW, size=20)
            return

        self.check_phase()
        self.update_behavior(dt)
        self.update_weak_point(dt)
        self.update_visuals(dt)
        
        self.rect.center = self.pos + self.vibrate_offset

    def check_phase(self):
        if self.hp <= 0:
            if self.state != 'dead':
                self.state = 'dead'
                self.state_timer = 120 # Death animation time
                self.game.effect_manager.apply_slowmo(120, 0.2)
                self.game.effect_manager.apply_zoom(1.5, duration=120)
            return

        new_phase = 1
        if self.hp > PHASE_2_THRESHOLD: new_phase = 1
        elif self.hp > PHASE_3_THRESHOLD: new_phase = 2
        else: new_phase = 3
        
        if new_phase > self.phase:
            self.sound_manager.play("boss_transition")
            self.start_transition(new_phase)

    def start_transition(self, next_phase):
        self.in_transition = True
        self.phase = next_phase
        self.transition_timer = 180 # 3 seconds
        self.state = 'transition'
        self.game.effect_manager.apply_shake(60, 10)
        self.game.effect_manager.apply_zoom(0.8, duration=60) # Zoom out
        
        if self.phase == 2:
            self.dialogue = "GENUG! Das Seminar gehört MIR!"
            self.color = ORANGE
            if self.game.platforms:
                p = random.choice(self.game.platforms.sprites())
                p.kill()
        elif self.phase == 3:
            self.dialogue = "WENN ICH NICHT GEWINNE... DANN NIEMAND!"
            self.color = DARK_RED
            self.dialogue_timer = 120
            for p in self.game.platforms:
                p.kill()

    def update_transition(self, dt):
        self.transition_timer -= dt
        self.vibrate_offset = pygame.math.Vector2(random.randint(-5, 5), random.randint(-5, 5))
        if self.transition_timer <= 0:
            self.in_transition = False
            self.state = 'idle'
            self.state_timer = 60
            self.vibrate_offset = pygame.math.Vector2(0, 0)
            self.game.effect_manager.apply_zoom(1.0, duration=30) # Zoom back
            if self.phase == 3:
                self.game.effect_manager.apply_shake(120, 5, type='rumble')

    def update_behavior(self, dt):
        if self.state == 'dead':
            self.state_timer -= dt
            self.vibrate_offset = pygame.math.Vector2(random.randint(-10, 10), random.randint(-10, 10))
            if self.state_timer <= 0:
                self.kill()
            return

        # Movement
        if self.phase == 1:
            self.pos = pygame.math.Vector2(910, 450)
        elif self.phase == 2:
            self.float_offset += 0.05 * dt
            self.pos.y = 300 + math.sin(self.float_offset) * 150
            self.pos.x = 850
        elif self.phase == 3:
            self.vibrate_offset = pygame.math.Vector2(random.randint(-3, 3), random.randint(-3, 3))
            self.state_timer -= dt
            if self.state_timer <= 0 and self.state == 'idle':
                self.teleport()
                self.state_timer = 180

        # Attack logic
        if self.state == 'idle':
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.run_attack()

    def run_attack(self):
        patterns = {
            1: [self.geometry_attack, self.eraser_attack, self.wipe_attack, self.rain_attack_mini],
            2: [self.eraser_attack_full, self.rain_attack_full, self.protractor_attack, self.slam_attack, self.laser_attack_double],
            3: [self.compass_hell_advanced, self.laser_attack_multi, self.teleport_strike, self.reality_break, self.blackboard_barrage]
        }
        
        current_patterns = patterns[self.phase]
        pattern = current_patterns[self.attack_pattern_index % len(current_patterns)]
        pattern()
        self.attack_pattern_index += 1
        self.state = 'idle'
        self.state_timer = 120 if self.phase < 3 else 60

    def stun(self, duration):
        self.stun_timer = duration
        self.state = 'stunned'
        self.weak_point_timer = duration # Weak point while stunned!

    # --- Phase 1 Attacks ---
    def geometry_attack(self):
        if random.random() < 0.2:
            self.dialogue = random.choice(["So einfach gibst du auf?", "Zeig mir, was du gelernt hast!"])
            self.dialogue_timer = 90
        
        self.weak_point_timer = 60 # Hand glow weak point
        
        # Advanced: Burst
        count = 5 if random.random() < 0.5 else 3
        for i in range(count):
            is_pink = (i == 2 or i == 4)
            p = BossProjectile(self.game, self.rect.left, self.rect.centery, -5, 0, is_parryable=is_pink)
            p.rect.x -= (count - 1 - i) * 100 # Spacing
            if count == 5: # Fanned slightly
                p.vel.y = (i - 2) * 1
            self.game.all_sprites.add(p)
            self.game.boss_bullets.add(p)

    def eraser_attack(self):
        # Chaos Mode: 2 erasers
        e1 = BouncingEraser(self.game, self.rect.centerx, self.rect.centery, size_mult=1.0)
        self.game.all_sprites.add(e1)
        self.game.boss_bullets.add(e1)
        
        if random.random() < 0.5:
            e2 = BouncingEraser(self.game, self.rect.centerx, self.rect.centery, size_mult=0.5, speed_mult=1.5)
            self.game.all_sprites.add(e2)
            self.game.boss_bullets.add(e2)

    def wipe_attack(self):
        for i in range(5):
            is_pink = (i == 2)
            p = BossProjectile(self.game, SCREEN_WIDTH + i*40, i*120, -3, 0, color=WHITE, size=(40, 100), is_parryable=is_pink)
            self.game.all_sprites.add(p)
            self.game.boss_bullets.add(p)

    def rain_attack_mini(self):
        for i in range(3):
            is_pink = (i == 1)
            x = 200 + i * 300
            p = EquationProjectile(self.game, x, -100, is_parryable=is_pink)
            self.game.all_sprites.add(p)
            self.game.boss_bullets.add(p)

    # --- Phase 2 Attacks ---
    def eraser_attack_full(self):
        # Hard Mode: Left AND Right
        e1 = ChalkboardEraser(self.game, 'left')
        e2 = ChalkboardEraser(self.game, 'right')
        e2.rect.x -= 300 # delay
        self.game.all_sprites.add(e1, e2)
        self.game.boss_bullets.add(e1, e2)

    def rain_attack_full(self):
        # Wave spawning not easily done in one frame without a coroutine/timer system.
        # Simplified: Spawn all with different start Y (delays appearance)
        for i in range(10):
            is_pink = (i in [3, 7])
            x = random.randint(50, 950)
            delay_y = -i * 200 # Spaced out vertically = wave effect
            p = EquationProjectile(self.game, x, delay_y, is_parryable=is_pink)
            self.game.all_sprites.add(p)
            self.game.boss_bullets.add(p)

    def protractor_attack(self):
        p = ProtractorSpin(self.game, self)
        self.game.all_sprites.add(p)
        self.game.boss_bullets.add(p)
        self.weak_point_timer = 60 # Center is weak

    def slam_attack(self):
        s = TextbookSlam(self.game, self.game.player.rect.centerx)
        self.game.all_sprites.add(s)
        self.game.boss_bullets.add(s)

    def laser_attack_double(self):
        y1 = self.game.player.rect.centery
        y2 = y1 + random.choice([-100, 100])
        l1 = Laser(self.game, y1)
        l2 = Laser(self.game, y2)
        self.game.all_sprites.add(l1, l2)
        self.game.boss_bullets.add(l1, l2)

    # --- Phase 3 Attacks ---
    def compass_hell_advanced(self):
        # 5 Bursts, rotating
        # Again, needs coroutine. Simplified: Spawn 5 waves with different delays/positions
        # We can spawn 5 projectiles that "burst" themselves later? 
        # Or just spawn one massive wave for now to avoid complex timer logic in this class
        for burst in range(3): # Reduced to 3 for performance/simplicity
            num_projs = 8
            for i in range(num_projs):
                angle = (i * (360/num_projs)) + (burst * 15)
                rad = math.radians(angle)
                speed = 4 + burst
                p = BossProjectile(self.game, self.rect.centerx, self.rect.centery, math.cos(rad)*speed, math.sin(rad)*speed, is_parryable=(i%2==0))
                self.game.all_sprites.add(p)
                self.game.boss_bullets.add(p)

    def laser_attack_multi(self):
        # Sweeping Laser
        l = Laser(self.game, self.game.player.rect.centery, duration=120, rotation_speed=30)
        self.game.all_sprites.add(l)
        self.game.boss_bullets.add(l)

    def reality_break(self):
        effect = random.choice(['invert_controls', 'invert_gravity', 'slow_mo'])
        self.reality_break_pending_type = effect
        self.reality_break_warning_timer = 60 # 1 second warning
        self.game.effect_manager.apply_shake(60, 2, type='rumble')
        # Dialogue?
        self.dialogue = f"REALITY BREAK: {effect.upper()}!"
        self.dialogue_timer = 60

    def blackboard_barrage(self):
        self.sound_manager.play("ultimate_attack")
        self.dialogue = "IHR WERDET ALLE DURCHFALLEN!"
        self.dialogue_timer = 120
        self.eraser_attack()
        self.rain_attack_full()
        self.wipe_attack()
        self.weak_point_timer = 180 # Exhausted after

    def teleport_strike(self):
        target_pos = self.game.player.pos + pygame.math.Vector2(-50 if self.game.player.facing_right else 50, -20)
        self.pos = target_pos
        # Instant damage zone
        hitbox = pygame.Rect(0, 0, 100, 100)
        hitbox.center = self.rect.center
        if hitbox.colliderect(self.game.player.rect):
            self.game.player.take_damage()
        self.weak_point_timer = 60 # Recovery

    def teleport(self):
        self.sound_manager.play("teleport")
        valid = False
        while not valid:
            new_x = random.randint(100, 900)
            new_y = random.randint(100, 500)
            if pygame.math.Vector2(new_x, new_y).distance_to(self.game.player.pos) > 200:
                self.pos = pygame.math.Vector2(new_x, new_y)
                valid = True

    def take_damage(self, amount):
        if self.hp <= 0: return
        
        self.sound_manager.play("boss_hit")
        multiplier = 1
        is_weak = False
        if self.weak_point_timer > 0:
            multiplier = 2
            if self.phase == 3: multiplier = 4
            is_weak = True

        actual_damage = amount * multiplier
        self.hp -= actual_damage
        self.flash_timer = 5
        self.game.effect_manager.add_damage_number(self.rect.center, int(actual_damage), is_weak=is_weak)
        self.game.effect_manager.apply_shake(5, 3)
        
        if self.hp < 0: self.hp = 0

    def update_weak_point(self, dt):
        if self.weak_point_timer > 0:
            self.weak_point_timer -= dt
            self.weak_point_rect = self.rect.inflate(-20, -20)
        else:
            self.weak_point_rect = None

    def update_visuals(self, dt):
        if self.dialogue_timer > 0:
            self.dialogue_timer -= dt
        else:
            self.dialogue = ""
        if self.flash_timer > 0:
            self.flash_timer -= dt

    def draw(self, screen, camera_offset):
        draw_rect = self.rect.copy()
        draw_rect.x -= camera_offset.x
        draw_rect.y -= camera_offset.y

        if self.flash_timer > 0:
            pygame.draw.rect(screen, WHITE, draw_rect)
        else:
            # Draw Boss Face/Shape
            pygame.draw.rect(screen, self.color, draw_rect)
            pygame.draw.rect(screen, BLACK, draw_rect.inflate(-10, -10), 2)
            
            # Eyes
            eye_color = YELLOW if self.phase == 2 else (RED if self.phase == 3 else WHITE)
            pygame.draw.rect(screen, eye_color, (draw_rect.x + 20, draw_rect.y + 40, 20, 20))
            pygame.draw.rect(screen, eye_color, (draw_rect.x + 60, draw_rect.y + 40, 20, 20))
            
            # Mouth
            if self.dialogue:
                pygame.draw.rect(screen, BLACK, (draw_rect.x + 30, draw_rect.y + 100, 40, 20)) # Open mouth
            else:
                pygame.draw.line(screen, BLACK, (draw_rect.x + 30, draw_rect.y + 110), (draw_rect.x + 70, draw_rect.y + 110), 3)

        if self.weak_point_timer > 0:
             # Pulsing weak point
             pulse = math.sin(pygame.time.get_ticks() * 0.2) * 5
             pygame.draw.rect(screen, YELLOW, draw_rect.inflate(10 + pulse, 10 + pulse), 4)

        if self.dialogue:
            draw_text(screen, self.dialogue, 24, draw_rect.centerx, draw_rect.top - 40, WHITE)
