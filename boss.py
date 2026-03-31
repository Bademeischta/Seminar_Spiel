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
        self.color = COLOR_LIGHT_RED
        
        self.pos = pygame.math.Vector2(self.rect.center)
        self.vibrate_offset = pygame.math.Vector2(0, 0)
        
        # State Machine
        self.state = 'idle'
        self.state_timer = 2.0
        self.attack_pattern_index = 0
        self.stun_timer = 0
        
        # Phase transitions
        self.in_transition = False
        self.transition_timer = 0
        self.is_dying = False
        
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

        self.shield_active = False
        self.shield_timer = 0

    def update(self, dt):
        if self.game.state == "DEMO":
            return

        if self.in_transition:
            self.update_transition(dt)
            return

        if self.reality_break_warning_timer > 0:
            self.reality_break_warning_timer -= dt
            if self.reality_break_warning_timer <= 0:
                self.game.apply_reality_break(self.reality_break_pending_type)
                self.reality_break_pending_type = None
            # Visuals weiterführen, nur Logic-Updates überspringen
            self.update_visuals(dt)
            self.rect.center = self.pos + self.vibrate_offset
            return

        if self.stun_timer > 0:
            prev_stun = self.stun_timer
            self.stun_timer -= dt
            # Trigger every 0.33s
            if int(prev_stun * 3) != int(self.stun_timer * 3):
                self.game.effect_manager.add_damage_number(self.rect.midtop, "STUNNED!", color=COLOR_YELLOW, size=20)
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
                self.is_dying = True
                self.state_timer = 2.0
                self.game.effect_manager.apply_slowmo(2.0, 0.2)
                self.game.effect_manager.apply_zoom(1.5, duration=2.0)
            return

        new_phase = 1
        if self.hp > BOSS_PHASE_2_THRESHOLD: new_phase = 1
        elif self.hp > BOSS_PHASE_3_THRESHOLD: new_phase = 2
        else: new_phase = 3
        
        if new_phase > self.phase:
            self.sound_manager.play("boss_transition")
            self.start_transition(new_phase)

    def start_transition(self, next_phase):
        self.in_transition = True
        self.phase = next_phase
        self.transition_timer = 3.0
        self.state = 'transition'
        self.game.effect_manager.apply_shake(1.0, 10)
        self.game.effect_manager.apply_zoom(0.8, duration=1.0)
        
        if self.phase == 2:
            self.dialogue = "GENUG! Das Seminar gehört MIR!"
            self.color = COLOR_ORANGE
            if self.game.platforms:
                p = random.choice(self.game.platforms.sprites())
                p.kill()
        elif self.phase == 3:
            self.dialogue = "WENN ICH NICHT GEWINNE... DANN NIEMAND!"
            self.color = COLOR_DARK_RED
            self.dialogue_timer = 2.0
            for p in self.game.platforms:
                p.kill()
            self.game.platforms.empty()

    def update_transition(self, dt):
        self.transition_timer -= dt
        self.vibrate_offset = pygame.math.Vector2(random.randint(-5, 5), random.randint(-5, 5))
        if self.transition_timer <= 0:
            self.in_transition = False
            self.state = 'idle'
            self.state_timer = 1.0
            self.vibrate_offset = pygame.math.Vector2(0, 0)
            self.game.effect_manager.apply_zoom(1.0, duration=0.5)
            if self.phase == 3:
                self.game.effect_manager.apply_shake(2.0, 5, type='rumble')

    def update_behavior(self, dt):
        if self.state == 'dead':
            self.state_timer -= dt
            self.vibrate_offset = pygame.math.Vector2(random.randint(-10, 10), random.randint(-10, 10))
            if self.state_timer <= 0:
                self.kill()
            return

        if self.phase == 1:
            self.pos = pygame.math.Vector2(910, 450)
        elif self.phase == 2:
            self.float_offset += 3 * dt
            self.pos.y = 300 + math.sin(self.float_offset) * 150
            self.pos.x = 850
        elif self.phase == 3:
            self.vibrate_offset = pygame.math.Vector2(random.randint(-3, 3), random.randint(-3, 3))
            self.state_timer -= dt
            if self.state_timer <= 0 and self.state == 'idle':
                self.teleport()
                self.state_timer = 3.0

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

        timer = 2.0 if self.phase < 3 else 1.0
        if self.game.challenge and self.game.challenge.name == "No Dash":
             timer *= 0.8

        self.state_timer = timer

    def stun(self, duration):
        self.stun_timer = duration
        self.state = 'stunned'
        self.weak_point_timer = duration

    # --- Phase 1 Attacks ---
    def geometry_attack(self):
        if random.random() < 0.2:
            self.dialogue = random.choice(["So einfach gibst du auf?", "Zeig mir, was du gelernt hast!"])
            self.dialogue_timer = 1.5
        
        self.weak_point_timer = 1.0
        
        count = 5 if random.random() < 0.5 else 3
        for i in range(count):
            is_pink = (i == 2 or i == 4)
            p = BossProjectile(self.game, self.rect.left, self.rect.centery, -300, 0, is_parryable=is_pink)
            p.rect.x -= (count - 1 - i) * 100
            if count == 5:
                p.vel.y = (i - 2) * 60
            self.game.all_sprites.add(p)
            self.game.boss_bullets.add(p)

    def eraser_attack(self):
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
            p = BossProjectile(self.game, SCREEN_WIDTH + i*40, i*120, -180, 0, color=COLOR_WHITE, size=(40, 100), is_parryable=is_pink)
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
        e1 = ChalkboardEraser(self.game, 'left')
        e2 = ChalkboardEraser(self.game, 'right')
        e2.rect.x -= 300
        self.game.all_sprites.add(e1, e2)
        self.game.boss_bullets.add(e1, e2)

    def rain_attack_full(self):
        for i in range(10):
            is_pink = (i in [3, 7])
            x = random.randint(50, 950)
            delay_y = -i * 200
            p = EquationProjectile(self.game, x, delay_y, is_parryable=is_pink)
            self.game.all_sprites.add(p)
            self.game.boss_bullets.add(p)

    def protractor_attack(self):
        p = ProtractorSpin(self.game, self)
        self.game.all_sprites.add(p)
        self.game.boss_bullets.add(p)
        self.weak_point_timer = 1.0

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
        for burst in range(3):
            num_projs = 8
            for i in range(num_projs):
                angle = (i * (360/num_projs)) + (burst * 15)
                rad = math.radians(angle)
                speed = 240 + burst * 60
                p = BossProjectile(self.game, self.rect.centerx, self.rect.centery, math.cos(rad)*speed, math.sin(rad)*speed, is_parryable=(i%2==0))
                self.game.all_sprites.add(p)
                self.game.boss_bullets.add(p)

    def laser_attack_multi(self):
        l = Laser(self.game, self.game.player.rect.centery, duration=2.0, rotation_speed=30)
        self.game.all_sprites.add(l)
        self.game.boss_bullets.add(l)

    def reality_break(self):
        effect = random.choice(['invert_controls', 'invert_gravity', 'slow_mo'])
        self.reality_break_pending_type = effect
        self.reality_break_warning_timer = 1.0
        self.game.effect_manager.apply_shake(1.0, 2, type='rumble')
        self.dialogue = f"REALITY BREAK: {effect.upper()}!"
        self.dialogue_timer = 1.0

    def blackboard_barrage(self):
        self.sound_manager.play("ultimate_attack")
        self.dialogue = "IHR WERDET ALLE DURCHFALLEN!"
        self.dialogue_timer = 2.0
        self.eraser_attack()
        self.rain_attack_full()
        self.wipe_attack()
        self.weak_point_timer = 3.0

    def teleport_strike(self):
        target_pos = self.game.player.pos + pygame.math.Vector2(-50 if self.game.player.facing_right else 50, -20)
        self.pos = target_pos
        # Update rect immediately, not just at the end of update()
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        hitbox = pygame.Rect(0, 0, 100, 100)
        hitbox.center = self.rect.center
        if hitbox.colliderect(self.game.player.rect):
            self.game.player.take_damage()
        self.weak_point_timer = 1.0

    def teleport(self):
        self.sound_manager.play("teleport")
        valid = False
        attempts = 0
        candidates = []
        while not valid and attempts < 20:
            new_x = random.randint(100, 900)
            new_y = random.randint(100, 500)
            candidates.append(pygame.math.Vector2(new_x, new_y))
            if pygame.math.Vector2(new_x, new_y).distance_to(self.game.player.pos) > 200:
                self.pos = pygame.math.Vector2(new_x, new_y)
                valid = True
            attempts += 1

        if not valid:
            best_pos = candidates[0]
            max_dist = -1
            for cand in candidates:
                dist = cand.distance_to(self.game.player.pos)
                if dist > max_dist:
                    max_dist = dist
                    best_pos = cand
            self.pos = best_pos

    def take_damage(self, amount):
        if self.hp <= 0 or self.flash_timer > 0: return
        if self.shield_active:
            self.game.effect_manager.add_damage_number(self.rect.center, "REFLECTED", color=COLOR_CYAN, size=20)
            return

        self.sound_manager.play("boss_hit")
        self.flash_timer = 0.166
        multiplier = 1
        is_weak = False
        if self.weak_point_timer > 0:
            multiplier = 2
            if self.phase == 3: multiplier = 4
            is_weak = True

        actual_damage = amount * multiplier
        self.hp -= actual_damage
        self.game.effect_manager.add_damage_number(self.rect.center, int(actual_damage), is_weak=is_weak)
        self.game.effect_manager.apply_shake(0.08, 3)
        
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
        if self.shield_timer > 0:
            self.shield_timer -= dt
            if self.shield_timer <= 0:
                self.shield_active = False

    def draw(self, screen, camera_offset):
        if self.shield_active:
             pulse = math.sin(pygame.time.get_ticks() * 0.02) * 5
             pygame.draw.circle(screen, COLOR_CYAN, (self.rect.centerx - camera_offset.x, self.rect.centery - camera_offset.y), 100 + pulse, 3)
             pygame.draw.circle(screen, COLOR_WHITE, (self.rect.centerx - camera_offset.x, self.rect.centery - camera_offset.y), 90 + pulse, 1)

        draw_rect = self.rect.copy()
        draw_rect.x -= camera_offset.x
        draw_rect.y -= camera_offset.y

        if self.flash_timer > 0:
            pygame.draw.rect(screen, COLOR_WHITE, draw_rect)
        else:
            pygame.draw.rect(screen, self.color, draw_rect)
            pygame.draw.rect(screen, COLOR_BLACK, draw_rect.inflate(-10, -10), 2)
            
            eye_color = COLOR_YELLOW if self.phase == 2 else (COLOR_RED if self.phase == 3 else COLOR_WHITE)
            pygame.draw.rect(screen, eye_color, (draw_rect.x + 20, draw_rect.y + 40, 20, 20))
            pygame.draw.rect(screen, eye_color, (draw_rect.x + 60, draw_rect.y + 40, 20, 20))
            
            if self.dialogue:
                pygame.draw.rect(screen, COLOR_BLACK, (draw_rect.x + 30, draw_rect.y + 100, 40, 20))
            else:
                pygame.draw.line(screen, COLOR_BLACK, (draw_rect.x + 30, draw_rect.y + 110), (draw_rect.x + 70, draw_rect.y + 110), 3)

        if self.weak_point_timer > 0:
             pulse = math.sin(pygame.time.get_ticks() * 0.2) * 5
             pygame.draw.rect(screen, COLOR_YELLOW, draw_rect.inflate(10 + pulse, 10 + pulse), 4)

        if self.dialogue:
            draw_text(screen, self.dialogue, 24, draw_rect.centerx, draw_rect.top - 40, COLOR_WHITE)
