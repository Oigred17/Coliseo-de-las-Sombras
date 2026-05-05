# ── Enemigos del Coliseo ──
import os
import pygame
import random
from settings import *
from spritesheet import load_spritesheet, load_single_image


class Heart(pygame.sprite.Sprite):
    """Corazón que sueltan los enemigos al morir."""
    def __init__(self, x, y):
        super().__init__()
        # Intentar cargar con la ruta proporcionada por el usuario o la interna
        try:
            self.image = load_single_image("Hearts/PNG/basic/heart.png", 2)
        except:
            self.image = pygame.Surface((20, 20))
            self.image.fill((255, 0, 0))
            
        self.rect = self.image.get_rect()
        self.x = float(x)
        self.y = float(y)
        self.rect.center = (int(self.x), int(self.y))
        self.vy = -8
        self.vx = random.uniform(-3, 3)
        self.bounces = 0
        self.max_bounces = 2
        self.collected = False
        
    def update(self, platforms):
        self.vy += 0.5
        self.x += self.vx
        self.y += self.vy
        
        self.rect.center = (int(self.x), int(self.y))
        
        for plat in platforms:
            if self.rect.colliderect(plat):
                if self.vy > 0 and self.rect.bottom - self.vy <= plat.top + 10:
                    self.y = float(plat.top - self.rect.height // 2)
                    self.vy = -self.vy * 0.5
                    self.vx *= 0.8
                    self.bounces += 1
                    if self.bounces >= self.max_bounces:
                        self.vy = 0
                        self.vx = 0
                    break
        
        if self.x < 20: self.x = 20
        if self.x > ARENA_WIDTH - 20: self.x = ARENA_WIDTH - 20
        self.rect.center = (int(self.x), int(self.y))
    
    def collect(self):
        self.collected = True
        self.kill()


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
        
        self.can_parry = True
        self.parry_window = 8

        self.width = 24 * scale
        self.height = 32 * scale

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
        # Reducimos un poco el ancho del ataque visual para que sea más justo
        w = (self.atk_range * self.scale) * 0.8
        if self.facing_right:
            return pygame.Rect(r.centerx, r.y + 10, w, r.height - 20)
        return pygame.Rect(r.centerx - w, r.y + 10, w, r.height - 20)

    def take_damage(self, dmg, parry=False, ignore_iframes=False):
        if (self.i_frames > 0 and not ignore_iframes) or not self.alive:
            return False
        
        if parry and self.can_parry:
            self.vx = -8 if self.facing_right else 8
            self.vy = -6
            self.i_frames = 30
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
            if self.attack_timer == mid_frame and not self.attack_hit:
                if self.melee_attack_enabled and self.attack_rect.colliderect(player.rect):
                    player.take_damage(self.damage, self.x)
                    self.attack_hit = True
            if self.attack_timer >= atk_frames / self.anim_speed:
                self.state = "idle"
                self.attack_cooldown = 90
                self.attack_hit = False
                self.last_state = "attack" # Para detectar el cambio de estado
        elif dist < self.atk_range * self.scale and self.attack_cooldown <= 0 and player.alive:
            self.state = "attack"
            self.attack_timer = 0
            self.attack_hit = False
            self.last_state = "idle" # Trigger para elegir habilidad
            self.frame_index = 0
            self.vx = 0
            self.facing_right = (dx > 0)
        elif dist < self.detect_range and player.alive:
            direction = 1 if dx > 0 else -1
            # Persecución más activa
            self.vx = direction * self.speed * 1.3
            self.facing_right = dx > 0
            if self.state != "run":
                self.state = "run"
            
            # Decidir saltar si el jugador está arriba (IA más agresiva)
            if self.on_ground and player.y < self.y - 40:
                # Si el jugador está arriba, saltar con más frecuencia
                if random.random() < 0.08 or (dist < 150 and player.y < self.y - 100):
                    self.vy = -20 # Salto potente para jefes grandes
                    # Impulso lateral hacia el jugador
                    self.vx = direction * self.speed * 2.0
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
                    self.x -= self.vx
                    self.patrol_dir = -1
                    if self.on_ground and p.top < self.y and p.height > 20:
                        self.vy = -12 
                elif self.vx < 0:
                    self.x -= self.vx
                    self.patrol_dir = 1
                    if self.on_ground and p.top < self.y and p.height > 20:
                        self.vy = -12 


        # Mover Y
        self.y += self.vy
        r = self.rect
        self.on_ground = False
        for p in platforms:
            if r.colliderect(p):
                if self.vy > 0 and r.bottom - self.vy <= p.top + 15:
                    self.y = float(p.top)
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0 and p.height > 20:
                    self.y = float(p.bottom + self.height)
                    self.vy = 0

        # Límites del escenario para evitar que los jefes desaparezcan
        from settings import ARENA_WIDTH
        if self.x < 50: 
            self.x = 50
            if self.vx < 0: self.vx *= -0.5
        elif self.x > ARENA_WIDTH - 50:
            self.x = ARENA_WIDTH - 50
            if self.vx > 0: self.vx *= -0.5

        self.on_ground = False
        if self.vy >= 0:
            r_down = self.rect.copy()
            r_down.y += 2
            for p in platforms:
                if r_down.colliderect(p):
                    self.on_ground = True
                    break

        # Limitar a la arena real
        from settings import ARENA_WIDTH
        if self.x < self.width // 2 + 10:
            self.x = self.width // 2 + 10
            self.patrol_dir = 1
        if self.x > ARENA_WIDTH - self.width // 2 - 10:
            self.x = ARENA_WIDTH - self.width // 2 - 10
            self.patrol_dir = -1

        # Comprobación de seguridad para evitar que caigan al vacío (el suelo está en SCREEN_HEIGHT-100)
        from settings import SCREEN_HEIGHT
        if self.y > SCREEN_HEIGHT + 200:
            self.y = float(SCREEN_HEIGHT - 100)
            self.vy = 0
            self.on_ground = True

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

        # Si el sprite mira a la izquierda por defecto (como el Slime), invertimos la lógica
        flip = not self.facing_right
        if getattr(self, "sprite_faces_left", False):
            flip = self.facing_right

        if flip:
            img = pygame.transform.flip(img, True, False)

        if self.i_frames > 0 and self.alive:
            if getattr(self, "is_boss", False):
                if (self.i_frames // 8) % 2 == 0:
                    img = img.copy()
                    img.set_alpha(200)
            else:
                if (self.i_frames // 3) % 2 == 0:
                    img = img.copy()
                    img.set_alpha(120)

        draw_x = self.x - img.get_width() // 2 - camera_x
        draw_y = self.y - img.get_height() + self.y_offset - camera_y
        surface.blit(img, (draw_x, draw_y))

        # Barra de vida (Solo si no es jefe)
        if self.alive and not getattr(self, "is_boss", False):
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
        self.width = 30 * S
        self.height = 40 * S


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
        self.width = 30 * S
        self.height = 35 * S

    def take_damage(self, dmg, source_x=None, parry=False, ignore_iframes=False):
        if parry and self.can_parry and self.state != "death":
            self.vx = -10 if self.facing_right else 10
            self.vy = -7
            self.i_frames = 25
            return False
        
        if (self.i_frames > 0 and not ignore_iframes) or not self.alive:
            return False
        if source_x is not None:
            if (self.facing_right and source_x > self.x) or (not self.facing_right and source_x < self.x):
                self.vx = -4 if self.facing_right else 4
                self.vy = -3
                return False
        return super().take_damage(dmg, ignore_iframes=ignore_iframes)


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


class FlyingEye(EnemyBase):
    """Demonio Ojo Volador."""
    def __init__(self, x, y):
        super().__init__(x, y, EAGLE_HP, EAGLE_SPEED, EAGLE_DAMAGE,
                         EAGLE_ATTACK_RANGE, EAGLE_DETECT_RANGE, ENEMY_SCALE)
        self.y_offset = 0
        S = self.scale
        
        base = "Enemies/flying-eye-demon/Sprites/flying-eye-demon"
        anim = []
        for i in range(1, 9):
            try:
                full_path = os.path.join(SPRITES_DIR, f"{base}{i}.png")
                img = pygame.image.load(full_path).convert_alpha()
                scaled = pygame.transform.scale(img, (int(img.get_width() * S), int(img.get_height() * S)))
                anim.append(scaled)
            except:
                anim.append(pygame.Surface((1,1)))

        self.animations = {
            "idle":   anim,
            "run":    anim,
            "attack": anim,
            "hurt":   anim,
            "death":  anim,
        }
        self.width = 40 * S * 0.7
        self.height = 30 * S * 0.5
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
                
            if self.rect.colliderect(player.rect) and self.attack_cooldown <= 0:
                if player.take_damage(self.damage, self.x):
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

        # Límites para que no salgan de la pantalla (especialmente águilas)
        if self.x < self.width // 2 + 10:
            self.x = self.width // 2 + 10
        if self.x > ARENA_WIDTH - self.width // 2 - 10:
            self.x = ARENA_WIDTH - self.width // 2 - 10
        if self.y < 50:
            self.y = 50
        if self.y > SCREEN_HEIGHT - 100:
            self.y = SCREEN_HEIGHT - 100

        self._update_animation()



class Ghost(EnemyBase):
    """Fantasma que flota hacia el jugador."""
    def __init__(self, x, y):
        super().__init__(x, y, GHOST_HP, GHOST_SPEED, GHOST_DAMAGE,
                         GHOST_ATTACK_RANGE, GHOST_DETECT_RANGE, ENEMY_SCALE)
        self.y_offset = 0
        self.sprite_faces_left = True
        S = self.scale
        FW, FH = 64, 80
        base = "Enemies/Ghost-Files/Spritesheets/"
        self.animations = {
            "idle":   load_spritesheet(f"{base}ghost-Idle.png", FW, FH, 0, S),
            "run":    load_spritesheet(f"{base}ghost-Chase.png", FW, FH, 0, S),
            "attack": load_spritesheet(f"{base}ghost-Shriek.png", FW, FH, 0, S),
            "hurt":   load_spritesheet(f"{base}ghost-Vanish.png", FW, FH, 0, S),
            "death":  load_spritesheet(f"{base}ghost-Vanish.png", FW, FH, 0, S),
        }
        self.width = 30 * S
        self.height = 40 * S
        self.vy = 0 

    def update(self, player, platforms):
        if not self.alive:
            self.vy += 0.5
            self.y += self.vy
            self._update_animation()
            if int(self.frame_index) >= len(self.animations.get("death", [None])) - 1:
                self.death_done = True
            return

        super().update(player, platforms)
        if self.alive:
            # Sobrescribir gravedad, vuela directo
            self.vy = 0
            dy = player.y - self.y
            if abs(dy) > 10:
                self.y += (1 if dy > 0 else -1) * self.speed * 0.5


class Piranha(EnemyBase):
    """Planta piraña que dispara."""
    def __init__(self, x, y):
        super().__init__(x, y, PIRANHA_HP, PIRANHA_SPEED, PIRANHA_DAMAGE,
                         PIRANHA_ATTACK_RANGE, PIRANHA_DETECT_RANGE, ENEMY_SCALE)
        self.y_offset = 0
        S = self.scale
        base = "Enemies/piranha/"
        
        def load_seq(folder, prefix, frames):
            anim = []
            for i in range(1, frames+1):
                try:
                    full = os.path.join(SPRITES_DIR, f"{base}{folder}/sprites/{prefix}{i}.png")
                    img = pygame.image.load(full).convert_alpha()
                    scaled = pygame.transform.scale(img, (int(img.get_width() * S), int(img.get_height() * S)))
                    anim.append(scaled)
                except:
                    anim.append(pygame.Surface((1,1)))
            return anim

        shoot_anim = load_seq("shooting", "piranha-plant-shoot", 4)
        hurt_anim = load_seq("hurt", "piranha-plant-hurt", 8)

        self.animations = {
            "idle":   shoot_anim[:1],
            "run":    shoot_anim[:1],
            "attack": shoot_anim,
            "hurt":   hurt_anim,
            "death":  hurt_anim,
        }
        self.width = 30 * S
        self.height = 40 * S
        self.has_thrown = False
        self.melee_attack_enabled = False

    def update(self, player, platforms):
        self.vx = 0 
        super().update(player, platforms)
        if self.state == "attack":
            mid_frame = len(self.animations["attack"]) // 2
            if int(self.frame_index) == mid_frame and not self.has_thrown:
                self.has_thrown = True
                self.attack_hit = True 
        else:
            self.has_thrown = False


class BossBase(EnemyBase):
    """Clase base para los Jefes."""
    def __init__(self, x, y, hp, speed, damage, atk_range, detect_range, scale):
        super().__init__(x, y, hp, speed, damage, atk_range, detect_range, scale)
        self.is_boss = True
        self.special_fired_this_frame = False


class FrostGuardian(BossBase):
    """Jefe: Guardián de Escarcha."""
    def __init__(self, x, y):
        # BUFF: Más HP, más velocidad y más daño
        super().__init__(x, y, BOSS_HP * 1.5, BOSS_SPEED * 1.4, BOSS_DAMAGE + 1, 
                         BOSS_ATTACK_RANGE * 1.2, BOSS_DETECT_RANGE, 3.2)
        S = self.scale
        FW, FH = 192, 128
        # El sprite tiene 18px de padding abajo (pies en fila 109 de 128)
        # y_offset positivo empuja hacia abajo para que los pies toquen el suelo
        self.y_offset = 57
        self.sprite_faces_left = True
        base = "Boss/Frost_Guardian_FREE_v1.0/frost_guardian_free_192x128_SpriteSheet.png"
        
        full_sheet = load_spritesheet(base, FW, FH, 0, S)

        # El spritesheet está organizado por FILAS (16 cols x 5 rows):
        # Fila 0: Idle (6 frames)   -> indices 0-5
        # Fila 1: Run (10 frames)   -> indices 16-25
        # Fila 2: Attack (14 frames)-> indices 32-45
        # Fila 3: Hurt (7 frames)   -> indices 48-54
        # Fila 4: Death (16 frames) -> indices 64-79
        COLS = 16
        total = len(full_sheet)
        def _row_slice(row, count):
            start = row * COLS
            return full_sheet[start:min(start + count, total)]
        def _ensure(frames):
            if frames and len(frames) > 0:
                return frames
            surf = pygame.Surface((int(FW * S), int(FH * S)), pygame.SRCALPHA)
            surf.fill((255, 0, 255, 180))
            return [surf]
        self.animations = {
            "idle":   _ensure(_row_slice(0, 6)),
            "run":    _ensure(_row_slice(1, 10)),
            "attack": _ensure(_row_slice(2, 14)),
            "hurt":   _ensure(_row_slice(3, 7)),
            "death":  _ensure(_row_slice(4, 16)),
        }
        self.width = 50 * S
        self.height = 70 * S
        self.anim_speed = 0.15
        self.phase = 1
        self.special_cooldown = 0
        self.current_attack_type = "slash"
        self.last_state = "idle"

    def update(self, player, platforms):
        if self.hp < self.max_hp // 2 and self.phase == 1:
            self.phase = 2
            self.speed *= 1.4
            self.anim_speed *= 1.2
            print("FROST PHASE 2: BLIZZARD")
        
        if self.special_cooldown > 0:
            self.special_cooldown -= 1
            
        # Elegir habilidad solo al iniciar el ataque
        if self.state == "attack" and self.last_state != "attack":
            pool = ["ice_bolt", "frost_nova", "slash", "ice_bolt", "frost_nova", "ice_shards"]
            if self.phase == 2:
                pool += ["blizzard_dash", "ice_rain", "ice_rain", "triple_bolt"]
            self.current_attack_type = random.choice(pool)
            
        self.last_state = self.state
        super().update(player, platforms)

        # En Fase 2, puede lanzar proyectiles extra mientras hace otras cosas
        if self.phase == 2 and self.special_cooldown <= 0:
            if random.random() < 0.02: # 2% chance per frame
                self.special_type = "ice_bolt"
                self.special_cooldown = 120

        
        if self.state == "attack":
            frame = int(self.frame_index)
            if self.current_attack_type == "ice_bolt" and frame == 5:
                self.special_type = "ice_bolt"
            elif self.current_attack_type == "frost_nova" and frame == 15:
                self.special_type = "frost_nova"
            elif self.current_attack_type == "ice_rain" and frame == 10:
                self.special_type = "ice_rain"
            elif self.current_attack_type == "ice_shards" and frame == 8:
                self.special_type = "ice_shards"
            elif self.current_attack_type == "triple_bolt" and frame == 5:
                self.special_type = "triple_bolt"
            else:
                self.special_type = None
        else:
            self.special_type = None


class Golem(BossBase):
    """Jefe: Golem de Piedra."""
    def __init__(self, x, y):
        super().__init__(x, y, BOSS_HP * 1.5, BOSS_SPEED * 0.8, BOSS_DAMAGE + 1, 
                         BOSS_ATTACK_RANGE * 1.5, BOSS_DETECT_RANGE, 3.5)
        S = self.scale
        # Los frames del Golem son 90x64 (NO 64x64)
        # Contenido visible ~38px alto, centrado en la mitad derecha del frame
        FW, FH = 90, 64
        GOLEM_SCALE = 4.0  # Ajustado para el nuevo tamaño de frame
        self.y_offset = 0  # bottom_pad = 0, pies al final del frame
        base = "Boss/Golems_Free_Version/Golem_1/Blue/No_Swoosh_VFX/"
        self.animations = {
            "idle":   load_spritesheet(f"{base}Golem_1_idle.png", FW, FH, 8, GOLEM_SCALE),
            "run":    load_spritesheet(f"{base}Golem_1_walk.png", FW, FH, 10, GOLEM_SCALE),
            "attack": load_spritesheet(f"{base}Golem_1_attack.png", FW, FH, 11, GOLEM_SCALE),
            "hurt":   load_spritesheet(f"{base}Golem_1_hurt.png", FW, FH, 4, GOLEM_SCALE),
            "death":  load_spritesheet(f"{base}Golem_1_die.png", FW, FH, 13, GOLEM_SCALE),
        }
        self.width = 40 * GOLEM_SCALE * 0.5
        self.height = 38 * GOLEM_SCALE * 0.7
        self.phase = 1
        self.special_cooldown = 0
        self.current_attack_type = "slam"
        self.last_state = "idle"
        self.anim_speed = 0.15  # Velocidad fluida para que se vean bien las animaciones
        self.charge_timer = 0
        self.sprite_faces_left = False
        self.i_frames = 0
        self.meteor_cooldown = 0
        self.stomp_timer = 0
        self.pillar_cooldown = 0
        self.rolling_cooldown = 0
        self.garden_cooldown = 0
        S2 = 3.5  # Escala fija para decoraciones de jardín
        garden_path = resource_path("Sprites/Esecenarios/Garden Decorations.png")
        garden_sheet = pygame.image.load(garden_path).convert_alpha()
        gw, gh = 32, 32
        self.garden_sprites = []
        for row in range(3):
            for col in range(7):
                x = col * 32
                y = row * 32
                if x + gw <= garden_sheet.get_width() and y + gh <= garden_sheet.get_height():
                    sprite = garden_sheet.subsurface(x, y, gw, gh)
                    self.garden_sprites.append(pygame.transform.scale(sprite, (int(gw * S2), int(gh * S2))))

    def update(self, player, platforms):
        if self.hp < self.max_hp // 2 and self.phase == 1:
            self.phase = 2
            self.speed *= 1.3
            self.anim_speed *= 1.2
            self.earthquake_active = True
        
        if self.special_cooldown > 0:
            self.special_cooldown -= 1
        if self.pillar_cooldown > 0:
            self.pillar_cooldown -= 1
        if self.meteor_cooldown > 0:
            self.meteor_cooldown -= 1
        if self.garden_cooldown > 0:
            self.garden_cooldown -= 1

        if self.state == "attack" and self.last_state != "attack":
            pool = ["rock_throw", "earthquake", "slam", "rock_throw", "earthquake"]
            if self.phase == 2:
                pool += ["rolling_charge", "stone_pillar", "ground_slam", "ground_slam", "meteor_shower", "garden_drop"]
            self.current_attack_type = random.choice(pool)

        self.last_state = self.state
        super().update(player, platforms)
        
        if self.state == "attack":
            frame = int(self.frame_index)
            if self.current_attack_type == "earthquake" and frame == 4:
                self.special_type = "earthquake"
            elif self.current_attack_type == "rock_throw" and frame == 2:
                self.special_type = "rock_throw"
            elif self.current_attack_type == "stone_pillar" and frame == 3:
                self.special_type = "stone_pillar"
            elif self.current_attack_type == "ground_slam" and frame == 5:
                self.special_type = "ground_slam"
            elif self.current_attack_type == "rolling_charge" and frame == 1:
                self.special_type = "rolling_charge"
            elif self.current_attack_type == "slam" and frame == 5:
                self.special_type = "slam"
            elif self.current_attack_type == "meteor_shower" and frame == 3:
                self.special_type = "meteor_shower"
            elif self.current_attack_type == "garden_drop" and frame == 4:
                self.special_type = "garden_drop"
            else:
                self.special_type = None
        else:
            self.special_type = None


class DemonSlime(BossBase):
    """Jefe: Slime Demoniaco."""
    def __init__(self, x, y):
        super().__init__(x, y, BOSS_HP * 2, BOSS_SPEED, BOSS_DAMAGE, 
                         BOSS_ATTACK_RANGE * 2, BOSS_DETECT_RANGE, 3.0)
        self.y_offset = 5 * self.scale # Casi nada, para que se vea sobre el suelo
        S = self.scale
        FW, FH = 288, 160
        base = "Boss/boss_demon_slime_FREE_v1.0/spritesheets/demon_slime_FREE_v1.0_288x160_spritesheet.png"
        full_sheet = load_spritesheet(base, FW, FH, 0, S)
        
        # Construir animaciones de forma robusta, incluso si el sheet tiene menos frames de los esperados.
        total = len(full_sheet)
        def _slice(start, end):
            return full_sheet[start:min(end, total)]
        def _ensure(frames):
            if frames and len(frames) > 0:
                return frames
            # Placeholder si falta algún frame
            surf = pygame.Surface((FW, FH), pygame.SRCALPHA)
            surf.fill((255, 0, 255, 180))
            return [surf]

        self.animations = {
            "idle":   _ensure(_slice(0, 6)),
            "run":    _ensure(_slice(22, 22 + 12)), # Fila 2
            "attack": _ensure(_slice(44, 44 + 15)), # Fila 3
            "hurt":   _ensure(_slice(66, 66 + 5)),  # Fila 4
            "death":  _ensure(_slice(88, 88 + 22)), # Fila 5
        }
        self.phase = 1
        self.sprite_faces_left = True
        self.width = 120 * S 
        self.height = 60 * S
        self.special_cooldown = 0
        self.current_attack_type = "bite"
        self.last_state = "idle"

    def update(self, player, platforms):
        if self.hp < self.max_hp // 2 and self.phase == 1:
            self.phase = 2
            self.speed *= 1.5
            self.anim_speed *= 1.3
            print("BOSS PHASE 2!")
        
        if self.special_cooldown > 0:
            self.special_cooldown -= 1
            
        # Elegir habilidad solo al iniciar el ataque
        if self.state == "attack" and self.last_state != "attack":
            # Pool de habilidades con mayor peso a las especiales
            pool = ["lava_spit", "jump_slam", "bite", "lava_spit", "jump_slam"]
            if self.phase == 2:
                pool += ["shadow_burst", "triple_fire", "shadow_burst", "triple_fire"]
            self.current_attack_type = random.choice(pool)
            self.special_fired_this_frame = False  # Reset para nueva habilidad
            
        self.last_state = self.state
        super().update(player, platforms)
        
        if self.state == "attack":
            frame = int(self.frame_index)
            # Sincronizar special_type para main.py
            if self.current_attack_type == "lava_spit" and frame == 10:
                self.special_type = "lava_spit"
            elif self.current_attack_type == "jump_slam" and frame == 12:
                self.special_type = "jump_slam"
            elif self.current_attack_type == "shadow_burst" and frame == 8:
                self.special_type = "shadow_burst"
            elif self.current_attack_type == "triple_fire" and frame == 10:
                self.special_type = "triple_fire"
            else:
                self.special_type = None
        else:
            self.special_type = None
            
        # Corregir rango para evitar "golpes fantasma"
        if self.state != "attack":
            self.atk_range = BOSS_ATTACK_RANGE * 1.5
        else:
            # Solo aumenta el rango en el momento del impacto visual
            if 8 <= int(self.frame_index) <= 12:
                self.atk_range = BOSS_ATTACK_RANGE * (3.5 if self.phase == 2 else 2.5)
            else:
                self.atk_range = 10
