# ── Enemigos del Coliseo ──
import pygame
import random
from settings import *
from spritesheet import load_spritesheet


class EnemyBase:
    """Clase base para todos los enemigos."""

    def __init__(self, x, y, hp, speed, damage, atk_range, detect_range, scale):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.hp = hp
        self.max_hp = hp
        self.speed = speed
        self.damage = damage
        self.atk_range = atk_range
        self.detect_range = detect_range
        self.alive = True
        self.on_ground = False
        self.facing_right = False
        self.scale = scale

        self.i_frames = 0
        self.state = "idle"
        self.frame_index = 0.0
        self.anim_speed = 0.12
        self.attack_timer = 0
        self.attack_cooldown = 0
        self.attack_hit = False
        self.death_done = False
        self.melee_attack_enabled = True

        self.width = 30 * scale
        self.height = 36 * scale

        self.patrol_dir = random.choice([-1, 1])
        self.patrol_timer = random.randint(60, 180)

        self.y_offset = 0
        self.animations = {}

    @property
    def rect(self):
        return pygame.Rect(
            self.x - self.width // 2,
            self.y - self.height,
            self.width,
            self.height,
        )

    @property
    def attack_rect(self):
        r = self.rect
        w = self.atk_range * self.scale
        if self.facing_right:
            return pygame.Rect(r.right, r.y + 5, w, r.height - 10)
        return pygame.Rect(r.left - w, r.y + 5, w, r.height - 10)

    def take_damage(self, dmg):
        if self.i_frames > 0 or not self.alive:
            return False
        self.hp -= dmg
        self.i_frames = 20
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            self.state = "death"
            self.frame_index = 0
        return True

    def update(self, player, platforms):
        if not self.alive:
            self._update_animation()
            if self.state == "death":
                if int(self.frame_index) >= len(self.animations.get("death", [None])) - 1:
                    self.death_done = True
            return

        if self.i_frames > 0:
            self.i_frames -= 1
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        # IA
        dx = player.x - self.x
        dist = abs(dx)
        attacking = self.state == "attack"

        if attacking:
            self.vx = 0
            self.attack_timer += 1
            atk_frames = len(self.animations.get("attack", [None]))
            mid_frame = int(atk_frames / (2 * self.anim_speed))
            if self.attack_timer == mid_frame:
                if self.melee_attack_enabled and self.attack_rect.colliderect(player.rect):
                    player.take_damage(self.damage, self.x)
                    self.attack_hit = True
            if self.attack_timer >= atk_frames / self.anim_speed:
                self.state = "idle"
                self.attack_cooldown = 60
        elif dist < self.atk_range * self.scale and self.attack_cooldown <= 0 and player.alive:
            self.state = "attack"
            self.attack_timer = 0
            self.attack_hit = False
            self.frame_index = 0
            self.vx = 0
            self.facing_right = dx > 0
        elif dist < self.detect_range and player.alive:
            direction = 1 if dx > 0 else -1
            self.vx = direction * self.speed
            self.facing_right = dx > 0
            if self.state != "run":
                self.state = "run"
        else:
            self.patrol_timer -= 1
            if self.patrol_timer <= 0:
                self.patrol_dir *= -1
                self.patrol_timer = random.randint(60, 180)
            self.vx = self.patrol_dir * self.speed * 0.4
            self.facing_right = self.patrol_dir > 0
            if self.state not in ("run", "idle"):
                self.state = "run"

        # Física
        self.vy += GRAVITY
        if self.vy > MAX_FALL_SPEED:
            self.vy = MAX_FALL_SPEED

        # Mover X
        self.x += self.vx
        r = self.rect
        for p in platforms:
            if r.colliderect(p):
                if self.vx > 0:
                    self.x = p.left - self.width // 2
                    self.patrol_dir = -1
                elif self.vx < 0:
                    self.x = p.right + self.width // 2
                    self.patrol_dir = 1

        # Mover Y
        self.y += self.vy
        r = self.rect
        for p in platforms:
            if r.colliderect(p):
                if self.vy > 0 and r.bottom - self.vy <= p.top + 20:
                    self.y = float(p.top)
                    self.vy = 0
                elif self.vy < 0 and p.height > 20:
                    self.y = float(p.bottom + self.height)
                    self.vy = 0

        self.on_ground = False
        if self.vy >= 0:
            r_down = self.rect.copy()
            r_down.y += 2
            for p in platforms:
                if r_down.colliderect(p):
                    self.on_ground = True
                    break

        # Limitar
        if self.x < self.width // 2 + 10:
            self.x = self.width // 2 + 10
            self.patrol_dir = 1
        if self.x > SCREEN_WIDTH - self.width // 2 - 10:
            self.x = SCREEN_WIDTH - self.width // 2 - 10
            self.patrol_dir = -1

        self._update_animation()

    def _update_animation(self):
        frames = self.animations.get(self.state, self.animations.get("idle", [None]))
        if not frames:
            return
        self.frame_index += self.anim_speed
        if self.state == "death":
            if self.frame_index >= len(frames):
                self.frame_index = len(frames) - 1
        elif self.state == "attack":
            if self.frame_index >= len(frames):
                self.frame_index = len(frames) - 1
        else:
            if self.frame_index >= len(frames):
                self.frame_index = 0

    def draw(self, surface, camera_x=0, camera_y=0):
        frames = self.animations.get(self.state, self.animations.get("idle"))
        if not frames:
            return
        idx = int(self.frame_index) % len(frames)
        img = frames[idx]

        if not self.facing_right:
            img = pygame.transform.flip(img, True, False)

        if self.i_frames > 0 and self.alive:
            if (self.i_frames // 3) % 2 == 0:
                img = img.copy()
                img.set_alpha(120)

        draw_x = self.x - img.get_width() // 2 - camera_x
        draw_y = self.y - img.get_height() + self.y_offset - camera_y
        surface.blit(img, (draw_x, draw_y))

        # Barra de vida
        if self.alive:
            bar_w = 50
            bar_h = 5
            bx = self.x - bar_w // 2 - camera_x
            by = draw_y - 8
            ratio = self.hp / self.max_hp
            pygame.draw.rect(surface, (60, 20, 20), (bx, by, bar_w, bar_h))
            pygame.draw.rect(surface, (200, 40, 40), (bx, by, int(bar_w * ratio), bar_h))
            pygame.draw.rect(surface, WHITE, (bx, by, bar_w, bar_h), 1)


class Grunt(EnemyBase):
    """Soldado básico. Frames 64x64."""
    def __init__(self, x, y):
        super().__init__(x, y, GRUNT_HP, GRUNT_SPEED, GRUNT_DAMAGE,
                         GRUNT_ATTACK_RANGE, GRUNT_DETECT_RANGE, ENEMY_SCALE)
        self.y_offset = 14 * self.scale
        S = self.scale
        FW, FH = 64, 64
        base = "Enemies/Grunt/Spritesheets/"
        self.animations = {
            "idle":   load_spritesheet(f"{base}Grunt Idle.png", FW, FH, 0, S),
            "run":    load_spritesheet(f"{base}Grunt Run.png", FW, FH, 0, S),
            "attack": load_spritesheet(f"{base}Grunt Attack.png", FW, FH, 0, S),
            "hurt":   load_spritesheet(f"{base}Grunt Hurt.png", FW, FH, 0, S),
            "death":  load_spritesheet(f"{base}Grunt Death.png", FW, FH, 0, S),
        }


class Commander(EnemyBase):
    """Comandante con espada grande. Frames 96x96."""
    def __init__(self, x, y):
        super().__init__(x, y, COMMANDER_HP, COMMANDER_SPEED, COMMANDER_DAMAGE,
                         COMMANDER_ATTACK_RANGE, COMMANDER_DETECT_RANGE, ENEMY_SCALE)
        self.y_offset = 30 * self.scale
        S = self.scale
        FW, FH = 96, 96
        base = "Enemies/Commander/Spritesheets/"
        self.animations = {
            "idle":   load_spritesheet(f"{base}Commander Idle.png", FW, FH, 0, S),
            "run":    load_spritesheet(f"{base}Commander Run.png", FW, FH, 0, S),
            "attack": load_spritesheet(f"{base}Commander Attack 01.png", FW, FH, 0, S),
            "hurt":   load_spritesheet(f"{base}Commander Hurt.png", FW, FH, 0, S),
            "death":  load_spritesheet(f"{base}Commander Death.png", FW, FH, 0, S),
        }
        self.width = 35 * S
        self.height = 45 * S


class Guardian(EnemyBase):
    """Guardián con escudo. Frames 96x96."""
    def __init__(self, x, y):
        super().__init__(x, y, GUARDIAN_HP, GUARDIAN_SPEED, GUARDIAN_DAMAGE,
                         GUARDIAN_ATTACK_RANGE, GUARDIAN_DETECT_RANGE, ENEMY_SCALE)
        self.y_offset = 30 * self.scale
        S = self.scale
        FW, FH = 96, 96
        base = "Enemies/Guardian/Spritesheet/"
        self.animations = {
            "idle":   load_spritesheet(f"{base}Guardian Idle.png", FW, FH, 0, S),
            "run":    load_spritesheet(f"{base}Guardian Walk.png", FW, FH, 0, S),
            "attack": load_spritesheet(f"{base}Guardian Attack.png", FW, FH, 0, S),
            "hurt":   load_spritesheet(f"{base}Guardian Hurt.png", FW, FH, 0, S),
            "death":  load_spritesheet(f"{base}Guardian Death.png", FW, FH, 0, S),
        }
        self.width = 35 * S
        self.height = 40 * S

    def take_damage(self, dmg, source_x=None):
        if self.i_frames > 0 or not self.alive:
            return False
        # Si tiene el escudo y está mirando hacia el ataque, bloquea
        if source_x is not None:
            if (self.facing_right and source_x > self.x) or (not self.facing_right and source_x < self.x):
                # Bloqueo: se echa para atrás y anula el daño
                self.vx = -4 if self.facing_right else 4
                self.vy = -3
                return False
        return super().take_damage(dmg)


class Potionmaster(EnemyBase):
    """Lanza pociones (proyectiles)."""
    def __init__(self, x, y):
        super().__init__(x, y, POTIONMASTER_HP, POTIONMASTER_SPEED, POTIONMASTER_DAMAGE,
                         POTIONMASTER_ATTACK_RANGE, POTIONMASTER_DETECT_RANGE, ENEMY_SCALE)
        self.y_offset = 30 * self.scale
        S = self.scale
        FW, FH = 96, 96
        base = "Enemies/Potionmaster/Spritesheets/"
        self.animations = {
            "idle":   load_spritesheet(f"{base}Potionmaster Idle.png", FW, FH, 0, S),
            "run":    load_spritesheet(f"{base}Potionmaster Run.png", FW, FH, 0, S),
            "attack": load_spritesheet(f"{base}Potionmaster Attack throw.png", FW, FH, 0, S),
            "hurt":   load_spritesheet(f"{base}Potionmaster Hurt.png", FW, FH, 0, S),
            "death":  load_spritesheet(f"{base}Potionmaster Death.png", FW, FH, 0, S),
        }
        self.has_thrown = False
        self.melee_attack_enabled = False
        
    def update(self, player, platforms):
        super().update(player, platforms)
        if self.state == "attack":
            mid_frame = len(self.animations["attack"]) // 2
            if int(self.frame_index) == mid_frame and not self.has_thrown:
                self.has_thrown = True
                # Lanzar poción
                self.attack_hit = True # Usamos esto de flag para que main.py lo lea
        else:
            self.has_thrown = False


class Eagle(EnemyBase):
    """Águila voladora."""
    def __init__(self, x, y):
        super().__init__(x, y, EAGLE_HP, EAGLE_SPEED, EAGLE_DAMAGE,
                         EAGLE_ATTACK_RANGE, EAGLE_DETECT_RANGE, ENEMY_SCALE)
        self.y_offset = 0
        S = self.scale
        FW, FH = 40, 41
        base = "Enemies/eagle/"
        idle_anim = load_spritesheet(f"{base}dive attack/spritesheet.png", FW, FH, 0, S)
        hurt_anim = load_spritesheet(f"{base}hurt/spritesheet.png", FW, FH, 0, S)
        self.animations = {
            "idle":   idle_anim,
            "run":    idle_anim,
            "attack": idle_anim,
            "hurt":   hurt_anim,
            "death":  hurt_anim,
        }
        self.y_base = y
        self.vy = 0 # Vuelo

    def update(self, player, platforms):
        if not self.alive:
            self.vy += 0.5 # Gravedad al morir
            self.y += self.vy
            self._update_animation()
            if int(self.frame_index) >= len(self.animations.get("death", [None])) - 1:
                self.death_done = True
            return

        if self.i_frames > 0:
            self.i_frames -= 1
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        dx = player.x - self.x
        dy = player.y - self.y
        dist = (dx**2 + dy**2)**0.5

        if dist < self.detect_range and player.alive:
            self.state = "run"
            self.facing_right = dx > 0
            if dist > 0:
                self.x += (dx / dist) * self.speed
                self.y += (dy / dist) * self.speed
                
            if dist < self.atk_range and self.attack_cooldown <= 0:
                if player.i_frames <= 0:
                    player.take_damage(self.damage, self.x)
                self.attack_cooldown = 90
                # Rebote tras atacar
                self.x -= (dx / dist) * 40
                self.y -= 30
        else:
            # Patrulla volando
            self.state = "idle"
            self.x += self.speed * self.patrol_dir * 0.4
            import math
            self.y = self.y_base + math.sin(self.x * 0.05) * 20
            self.patrol_timer -= 1
            if self.patrol_timer <= 0:
                self.patrol_dir *= -1
                self.facing_right = self.patrol_dir > 0
                self.patrol_timer = random.randint(60, 180)

        self._update_animation()
