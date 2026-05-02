# ══════════════════════════════════════════════════════════════
#  COLISEO DE LAS SOMBRAS
#  Python + Pygame-CE  |  Teclado + Mando con vibración
# ══════════════════════════════════════════════════════════════
import pygame
import sys
import random
import math
from settings import *
from player import Player
from enemies import Grunt, Commander, Guardian, Potionmaster, FlyingEye, Heart, FrostGuardian, Golem, DemonSlime, Ghost, Piranha
from hud import HUD
from spritesheet import load_single_image, load_spritesheet
from tutorial import TutorialManager

class SoundManager:
    def __init__(self):
        pygame.mixer.init()
        self.sounds = {}
        self.current_music = None
        # Load important sounds
        try:
            # Player SFX
            self.sounds["attack"] = pygame.mixer.Sound("Efectos de sonido/SFX/07_human_atk_sword_1.wav")
            self.sounds["dash"] = pygame.mixer.Sound("Efectos de sonido/SFX/15_human_dash_1.wav")
            self.sounds["damage"] = pygame.mixer.Sound("Efectos de sonido/SFX/11_human_damage_1.wav")
            self.sounds["jump"] = pygame.mixer.Sound("Efectos de sonido/SFX/12_human_jump_1.wav")
            self.sounds["cast"] = pygame.mixer.Sound("Efectos de sonido/SFX/10_human_special_atk_2.wav")
            self.sounds["heal"] = pygame.mixer.Sound("Efectos de sonido/Level up Pickup (Rpg).wav")
            
            # Enemy/Combat SFX
            self.sounds["enemy_hit"] = pygame.mixer.Sound("Efectos de sonido/SFX/26_sword_hit_1.wav")
            self.sounds["enemy_death"] = pygame.mixer.Sound("Efectos de sonido/SFX/24_orc_death_spin.wav")
            self.sounds["parry"] = pygame.mixer.Sound("Efectos de sonido/SFX/20_orc_special_atk.wav")
            self.sounds["boss_arrival"] = pygame.mixer.Sound("Efectos de sonido/SFX/18_orc_charge.wav")
            
            # UI/Other
            self.sounds["victory"] = pygame.mixer.Sound("Efectos de sonido/SFX/10_human_special_atk_1.wav")
            self.sounds["charged"] = pygame.mixer.Sound("Efectos de sonido/SFX/09_human_charging_1_loop.wav")
            self.sounds["super"] = pygame.mixer.Sound("Efectos de sonido/SFX/20_orc_special_atk.wav")
            self.sounds["super2"] = pygame.mixer.Sound("Efectos de sonido/SFX/10_human_special_atk_1.wav")
            
            # Initial Music
            self.change_music("Efectos de sonido/Music/Goblins_Den_(Regular).wav")
        except Exception as e:
            print(f"No se pudieron cargar los sonidos: {e}")

    def play(self, name):
        if name in self.sounds:
            self.sounds[name].set_volume(0.5)
            self.sounds[name].play()

    def change_music(self, path):
        if self.current_music == path:
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(0.6)
            pygame.mixer.music.play(-1)
            self.current_music = path
        except:
            print(f"Error cargando musica: {path}")

    def play_music(self):
        try:
            if not pygame.mixer.music.get_busy() and self.current_music:
                pygame.mixer.music.play(-1)
        except:
            pass


class Particle:
    """Partícula decorativa."""
    def __init__(self, x, y, color, vx=0, vy=0, life=30, size=3):
        self.x, self.y = x, y
        self.vx = vx + random.uniform(-1, 1)
        self.vy = vy + random.uniform(-2, 0)
        self.life = life
        self.max_life = life
        self.size = size
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.05
        self.life -= 1

    def draw(self, surface, camera_x=0, camera_y=0):
        alpha = int(255 * (self.life / self.max_life))
        s = max(1, int(self.size * (self.life / self.max_life)))
        surf = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
        c = (*self.color[:3], alpha)
        pygame.draw.circle(surf, c, (s, s), s)
        surface.blit(surf, (int(self.x - s - camera_x), int(self.y - s - camera_y)))


class Firework:
    """Fuego artificial para las transiciones de oleadas."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vy = random.uniform(-12, -8)
        self.color = random.choice([
            (255, 50, 50), (50, 255, 50), (50, 50, 255),
            (255, 255, 50), (255, 50, 255), (50, 255, 255),
            (255, 200, 50), (200, 50, 255)
        ])
        self.exploded = False
        self.explosion_frame = 0
        self.trail = []
        
    def update(self, particles_list):
        if not self.exploded:
            self.vy += 0.3
            self.x += random.uniform(-1, 1)
            self.y += self.vy
            self.trail.append((self.x, self.y))
            if len(self.trail) > 10:
                self.trail.pop(0)
            if self.vy >= 0:
                self.exploded = True
                self.explosion_frame = 60
                for _ in range(40):
                    angle = random.uniform(0, 6.28)
                    speed = random.uniform(2, 10)
                    particles_list.append(Particle(
                        self.x, self.y, self.color,
                        math.cos(angle) * speed, math.sin(angle) * speed,
                        random.randint(30, 60), random.randint(3, 6)
                    ))
        else:
            self.explosion_frame -= 1
            if self.explosion_frame <= 0:
                return True
        return False
    
    def draw(self, surface, camera_x=0, camera_y=0):
        if not self.exploded:
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(255 * (i + 1) / len(self.trail))
                pygame.draw.circle(surface, (*self.color, alpha), 
                                  (int(tx - camera_x), int(ty - camera_y)), 3)
            pygame.draw.circle(surface, self.color, (int(self.x - camera_x), int(self.y - camera_y)), 5)

class Projectile:
    """Proyectil mágico lanzado por el jugador."""
    def __init__(self, x, y, direction):
        self.x = float(x)
        self.y = float(y)
        self.vx = direction * 10
        self.life = 60
        self.radius = 12
        self.damage = PLAYER_ATTACK_DAMAGE * 2
        
    @property
    def rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)

    def update(self):
        self.x += self.vx
        self.life -= 1

    def draw(self, surface, camera_x=0, camera_y=0):
        s = int(self.radius * 2)
        surf = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
        # Glow exterior
        pygame.draw.circle(surf, (100, 200, 255, 80), (s, s), int(self.radius * 1.8))
        # Centro
        pygame.draw.circle(surf, (150, 220, 255, 200), (s, s), self.radius)
        # Núcleo blanco
        pygame.draw.circle(surf, (255, 255, 255, 255), (s, s), self.radius // 2)
        surface.blit(surf, (int(self.x - s - camera_x), int(self.y - s - camera_y)))

class EnemyProjectile:
    """Proyectil enemigo (Poción)."""
    def __init__(self, x, y, vx, vy, frames):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = vx, vy
        self.frames = frames
        self.frame_index = 0.0
        self.radius = 12
        self.damage = 1
        self.life = 120
        self.facing_right = vx > 0

    @property
    def rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)

    def update(self, floor_y):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.3
        self.life -= 1
        self.frame_index += 0.2
        if self.y >= floor_y:
            self.life = 0

    def draw(self, surface, camera_x=0, camera_y=0):
        if not self.frames: return
        idx = int(self.frame_index) % len(self.frames)
        img = self.frames[idx]
        if not self.facing_right:
            img = pygame.transform.flip(img, True, False)
        surface.blit(img, (int(self.x - img.get_width()//2 - camera_x), int(self.y - img.get_height()//2 - camera_y)))

class EnemyEnergyBall:
    """Bola de energía lanzada por jefes."""
    def __init__(self, x, y, vx, color):
        self.x, self.y = float(x), float(y)
        self.vx = vx
        self.color = color
        self.life = 100
        self.radius = 15
        self.damage = 2

    @property
    def rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)

    def update(self):
        self.x += self.vx
        self.y += getattr(self, "vy", 0)
        if getattr(self, "is_rock", False):
            self.vy = getattr(self, "vy", 0) + 0.5  # Gravedad
            if self.y > 620 - self.radius:  # Rebotar en el suelo
                self.y = 620 - self.radius
                self.vy = -8
        self.life -= 1

    def draw(self, surface, camera_x=0, camera_y=0):
        if getattr(self, "is_garden", False):
            if hasattr(self, "sprite"):
                if self.impact_frame > 0:
                    alpha = int(self.impact_frame / 30.0 * 255)
                    surf = self.sprite.copy()
                    surf.set_alpha(alpha)
                else:
                    surf = self.sprite
                surface.blit(surf, (int(self.x - surf.get_width() // 2 - camera_x), int(self.y - surf.get_height() // 2 - camera_y)))
        elif getattr(self, "is_rock", False):
            cx = int(self.x - camera_x)
            cy = int(self.y - camera_y)
            r = self.radius
            points = [
                (cx - r, cy - r//2), (cx - r//2, cy - r), (cx + r//2, cy - r),
                (cx + r, cy - r//3), (cx + r, cy + r//2), (cx + r//2, cy + r),
                (cx - r//3, cy + r), (cx - r, cy + r//2)
            ]
            pygame.draw.polygon(surface, (120, 100, 80), points)
            pygame.draw.polygon(surface, (80, 60, 40), points, 3)
        else:
            s = int(self.radius * 2)
            surf = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*self.color, 100), (s, s), self.radius * 1.5)
            pygame.draw.circle(surf, (*self.color, 200), (s, s), self.radius)
            pygame.draw.circle(surf, (255, 255, 255, 255), (s, s), self.radius // 2)
            surface.blit(surf, (int(self.x - s - camera_x), int(self.y - s - camera_y)))

class HomingWave:
    """Onda de energía que persigue enemigos (Superhabilidad)."""
    def __init__(self, x, y, targets):
        self.x, self.y = float(x), float(y)
        self.targets = [t for t in targets if t.alive]
        self.current_target = None
        self.hits_left = 5
        self.speed = 12
        self.radius = 25
        self.life = 300
        self.hit_cooldown = 0
        self.angle = 0
        self.timer = 0

    @property
    def rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)

    def update(self, enemies):
        if self.hit_cooldown > 0: self.hit_cooldown -= 1
        
        # Buscar nuevo objetivo de entre los enemigos vivos
        alive_enemies = [e for e in enemies if e.alive]
        
        # Si no hay objetivo o el actual murió, buscar el más cercano
        if not self.current_target or not self.current_target.alive:
            if alive_enemies:
                self.current_target = min(alive_enemies, key=lambda e: abs(e.x - self.x) + abs(e.y - self.y))
            else:
                self.current_target = None

        if self.current_target:
            self.life -= 1
            import math
            dx = self.current_target.x - self.x
            dy = (self.current_target.y - self.current_target.height // 2) - self.y
            dist = (dx**2 + dy**2)**0.5
            if dist > 0:
                self.x += (dx / dist) * self.speed
                self.y += (dy / dist) * self.speed
            
            if self.rect.colliderect(self.current_target.rect) and self.hit_cooldown <= 0:
                self.current_target.take_damage(3, ignore_iframes=True)
                self.hits_left -= 1
                self.hit_cooldown = 15
                if self.hits_left <= 0: self.life = 0
        else:
            # Flotar suavemente si no hay enemigos
            self.timer += 1
            import math
            self.y += math.sin(self.timer / 10.0) * 2
            self.x += math.cos(self.timer / 15.0) * 2
            # No reducir vida mientras espera
            pass

    def draw(self, surface, camera_x, camera_y):
        s = int(self.radius * 2)
        surf = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
        color = (100, 255, 100) if (self.life // 5) % 2 == 0 else (255, 255, 100)
        pygame.draw.circle(surf, (*color, 150), (s, s), self.radius)
        pygame.draw.circle(surf, (255, 255, 255, 200), (s, s), self.radius // 2)
        surface.blit(surf, (int(self.x - s - camera_x), int(self.y - s - camera_y)))

class Portal:
    """Portal de victoria que aparece al final de cada oleada."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 40
        self.frame_index = 0.0
        self.anim_speed = 0.25
        try:
            self.frames = load_spritesheet("Portal/portal-Sheet .png", 64, 64, 8, 3)
        except:
            self.frames = []
            
    def update(self):
        if self.frames:
            self.frame_index += self.anim_speed
            if self.frame_index >= len(self.frames):
                self.frame_index = 0

    def draw(self, surface, camera_x=0, camera_y=0):
        if self.frames:
            img = self.frames[int(self.frame_index) % len(self.frames)]
            surface.blit(img, (int(self.x - img.get_width()//2 - camera_x), 
                               int(self.y - img.get_height()//2 - camera_y)))
        else:
            pygame.draw.circle(surface, (150, 100, 255), (int(self.x - camera_x), int(self.y - camera_y)), self.radius)

class Arena:
    """Escenario del coliseo con assets reales."""
    def __init__(self):
        self.platforms = []
        self.floor_y = SCREEN_HEIGHT - 100
        self.hole_open = False

        self.set_bg("Normal BG")

        # ── Floor tiles ──
        self.floor_tile = load_single_image("Esecenarios/Floor Tiles1.png")
        tile_size = 96
        self.ground_tile = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        self.ground_tile.blit(self.floor_tile, (0, 0), (0, 0, tile_size, tile_size))
        self.ground_tile = pygame.transform.scale(self.ground_tile, (64, 64))

        # ── Decoraciones ──
        self.angel_statue = load_single_image("Esecenarios/Angel Statue.png", 3)
        
        # Antorchas animadas (192x128, 6 frames de 32x128)
        self.torch_frames = load_spritesheet("Esecenarios/Torch.png", 32, 32, 0, 3)

        # ── Construir plataformas ──
        self._build()

    def set_bg(self, theme):
        bg_path = f"Esecenarios/GandalfHardcore Background layers/{theme}/"
        self.bg_layers = []
        for i in range(5, 0, -1):
            img = load_single_image(f"{bg_path}GandalfHardcore Background layers_layer {i}.png")
            img = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
            self.bg_layers.append(img)
            
        castle_name = "Background Castle .png"
        if theme == "Autumn BG":
            castle_name = "Background Castle Autumn.png"
        elif theme == "Winter BG":
            castle_name = "Background Castle  Winter.png"
            
        self.castle = load_single_image(f"{bg_path}{castle_name}")
        self.castle = pygame.transform.scale(self.castle, (400, 200))

    def _build(self, wave=0):
        fy = self.floor_y
        self.platforms = []
        # Suelo principal
        self.platforms.append(pygame.Rect(0, fy, ARENA_WIDTH, SCREEN_HEIGHT - fy + 100))
        # Paredes invisibles
        self.platforms.append(pygame.Rect(-30, 0, 32, SCREEN_HEIGHT))
        self.platforms.append(pygame.Rect(ARENA_WIDTH - 2, 0, 32, SCREEN_HEIGHT))

        # Sin plataformas flotantes en oleadas de jefe (indices 2, 5, 8)
        if wave in (2, 5, 8):
            return

        # Plataformas más bajas y estructuradas
        pw, ph = 250, 20
        # Fila 1 (más bajas, accesibles con un salto)
        for i in range(3):
            x = 200 + i * (ARENA_WIDTH // 3.5)
            y = fy - 140
            self.platforms.append(pygame.Rect(x, y, pw, ph))

        # Fila 2 (más altas, accesibles con doble salto o desde la fila 1)
        for i in range(2):
            x = 400 + i * (ARENA_WIDTH // 3)
            y = fy - 300
            self.platforms.append(pygame.Rect(x, y, pw, ph))

    def draw(self, surface, camera_x=0, camera_y=0):
        # ── Parallax backgrounds ──
        for layer in self.bg_layers:
            surface.blit(layer, (-camera_x * 0.2, -camera_y * 0.1))
            if ARENA_WIDTH > SCREEN_WIDTH:
                surface.blit(layer, (-camera_x * 0.2 + SCREEN_WIDTH, -camera_y * 0.1))

        # Castillo (paralax ligeramente con la cámara para integrarse al escenario)
        castle_x = ARENA_WIDTH // 2 - 240 - int(camera_x * 0.25)
        castle_y = 100 - int(camera_y * 0.5)
        surface.blit(self.castle, (castle_x, castle_y))

        # ── Estatuas decorativas ──
        if self.angel_statue:
            surface.blit(self.angel_statue, (140 - camera_x, self.floor_y - self.angel_statue.get_height() - camera_y))
            flipped = pygame.transform.flip(self.angel_statue, True, False)
            surface.blit(flipped, (ARENA_WIDTH - 140 - flipped.get_width() - camera_x,
                                   self.floor_y - flipped.get_height() - camera_y))


        # ── Suelo con tiles ──
        tile_w = self.ground_tile.get_width()
        tile_h = self.ground_tile.get_height()
        start_x = -(camera_x % tile_w)
        for x in range(int(start_x), SCREEN_WIDTH + tile_w, tile_w):
            real_x = x + camera_x
            if 0 <= real_x <= ARENA_WIDTH:
                surface.blit(self.ground_tile, (x, self.floor_y - camera_y))
                # Segunda fila de tiles
                if self.floor_y + tile_h < SCREEN_HEIGHT + camera_y + 200:
                    surface.blit(self.ground_tile, (x, self.floor_y + tile_h - camera_y))

        # ── Agujero en el suelo ──
        if self.hole_open:
            hole_rect = pygame.Rect(ARENA_WIDTH // 2 - 100 - camera_x, self.floor_y - camera_y - 5, 200, 20)
            pygame.draw.rect(surface, (0, 0, 0), hole_rect)
            # Dibujar "fondo" del agujero
            pygame.draw.rect(surface, (10, 5, 15), (ARENA_WIDTH // 2 - 95 - camera_x, self.floor_y - camera_y + 10, 190, 100))

        # ── Borde superior del suelo ──
        floor_start = max(0, -camera_x)
        floor_end = min(SCREEN_WIDTH, ARENA_WIDTH - camera_x)
        pygame.draw.line(surface, (100, 80, 60), (floor_start, self.floor_y - camera_y), (floor_end, self.floor_y - camera_y), 3)

        # ── Plataformas flotantes ──
        for p in self.platforms:
            if p.height <= 20:  # Solo las flotantes
                px_on_screen = p.x - camera_x
                if px_on_screen + p.width > 0 and px_on_screen < SCREEN_WIDTH:
                    # Dibujar con tiles pequeños
                    for dx in range(0, p.width, tile_w):
                        w = min(tile_w, p.width - dx)
                        sub = self.ground_tile.subsurface((0, 0, min(w, tile_w), min(p.height, tile_h)))
                        surface.blit(sub, (px_on_screen + dx, p.y - camera_y))
                    # Borde
                    pygame.draw.rect(surface, (120, 100, 80), (px_on_screen, p.y - camera_y, p.width, p.height), 2)

        # ── Paredes laterales visibles ──
        pygame.draw.rect(surface, (20, 15, 25), (-camera_x - 100, -camera_y, 100, SCREEN_HEIGHT + 1000))
        pygame.draw.rect(surface, (20, 15, 25), (ARENA_WIDTH - camera_x, -camera_y, 100, SCREEN_HEIGHT + 1000))
        pygame.draw.line(surface, (100, 80, 60), (-camera_x, -camera_y), (-camera_x, SCREEN_HEIGHT - camera_y), 5)
        pygame.draw.line(surface, (100, 80, 60), (ARENA_WIDTH - camera_x, -camera_y), (ARENA_WIDTH - camera_x, SCREEN_HEIGHT - camera_y), 5)


class Game:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()

        # Joystick
        self.joystick = None
        self._init_joystick()

        # Arena
        self.arena = Arena()

        # HUD
        self.hud = HUD()
        self.hud.init_assets()

        # Estado
        self.game_state = "menu"
        self.score = 0
        self.current_wave = 0
        self.wave_intro_timer = 0

        # Entidades
        self.player = None
        self.enemies = []
        self.particles = []
        self.projectiles = []
        self.enemy_projectiles = []
        self.homing_waves = []
        self.hearts = []
        self.fireworks = []
        self.portal = None

        self.wave_transition = False
        self.wave_transition_timer = 0

        # Assets
        self.potion_frames = load_spritesheet("Enemies/Effects/PNGs/Green Potion.png", 32, 32, 0, 2)

        # Sounds
        self.sounds = SoundManager()

        # Vibración
        self.rumble_timer = 0
        self.start_was_pressed = False
        
        self.camera_x = 0
        self.hearts = []
        self.camera_y = 0
        self.camera_shake = 0
        self.fade_alpha = 0
        self.cinematic_timer = 0
        self.continue_timer = 0
        self.max_continue_time = 10
        self.best_wave = 0
        self.best_score = 0
        self.b_hold_timer = 0
        self.rt_was_pressed = False
        self.tutorial_manager = TutorialManager(self)
        self.tutorial_parry_success = False

    def _init_joystick(self):
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            print(f"Mando detectado: {self.joystick.get_name()}")

    def _rumble(self, intensity=0.6, duration_frames=12):
        if self.joystick:
            try:
                self.joystick.rumble(intensity, intensity, int(duration_frames * 16.67))
                self.rumble_timer = duration_frames
            except Exception:
                pass

    def _stop_rumble(self):
        if self.joystick:
            try:
                self.joystick.stop_rumble()
            except Exception:
                pass

    def _spawn_particles(self, x, y, color, count=8):
        for _ in range(count):
            self.particles.append(Particle(
                x, y, color,
                random.uniform(-3, 3), random.uniform(-4, 0),
                random.randint(15, 40), random.randint(2, 5),
            ))

    def _reset_game(self, start_wave=0):
        self.enemies = []
        self.particles = []
        self.projectiles = []
        self.enemy_projectiles = []
        self.homing_waves = []
        self.score = 0
        self.current_wave = start_wave
        self.sounds.play_music()
        self.pending_enemies = []
        self.spawn_timer = 0

        if start_wave > 0:
            # Selección directa de oleada: saltar cinemática, ir directo
            self.player = Player(300, SCREEN_HEIGHT - 100)
            self.player.on_ground = True
            self._start_wave()
        else:
            # Inicio normal con cinemática
            self.player = Player(-100, SCREEN_HEIGHT - 100)
            self.game_state = "cinematic"
            self.cinematic_timer = 180

    def _start_tutorial(self):
        self._reset_game()
        self.game_state = "tutorial"
        self.tutorial_manager.start()

    def _start_wave(self):
        self.enemies = []
        self.portal = None
        if self.player: self.player.alpha = 255
        self.arena.hole_open = False
        self.fireworks = []
        self.particles = []
        if self.current_wave >= len(WAVES):
            self.game_state = "victory"
            self._rumble(1.0, 40)
            return

        # Cambiar el escenario según la oleada (Completamente nuevo cada vez)
        themes = ["Normal BG", "Autumn BG", "Winter BG"]
        current_theme = themes[self.current_wave % len(themes)]
        self.arena.set_bg(current_theme)

        wave = WAVES[self.current_wave]
        fy = self.arena.floor_y
        
        # Efecto destrucción plataformas antiguas
        for p in self.arena.platforms:
            if p.height <= 20:
                for _ in range(15):
                    self._spawn_particles(p.x + random.randint(0, p.width), p.y, (120, 100, 80), 5)
                    
        self.arena._build(self.current_wave)
        
        # Efecto creación nuevas
        for p in self.arena.platforms:
            if p.height <= 20:
                for _ in range(15):
                    self._spawn_particles(p.x + random.randint(0, p.width), p.y, (150, 130, 255), 5)
        
        if "boss" in wave:
            self.game_state = "boss_intro"
            self.boss_intro_timer = 200
            self.enemies = []
            self.pending_enemies = []
            fy = SCREEN_HEIGHT - 100
            if wave["boss"] == "frost_guardian":
                self.enemies.append(FrostGuardian(ARENA_WIDTH - 200, -200)) # Menos caída
                self.boss_name = "FROST GUARDIAN"
                self.sounds.change_music("Efectos de sonido/Music/music boos2.wav")
            elif wave["boss"] == "golem":
                self.enemies.append(Golem(ARENA_WIDTH - 200, -200))
                self.boss_name = "STONE GOLEM"
                self.sounds.change_music("Efectos de sonido/Music/music boos2.wav")
            elif wave["boss"] == "demon_slime":
                self.enemies.append(DemonSlime(ARENA_WIDTH - 200, -200))
                self.boss_name = "DEMON SLIME"
                self.sounds.change_music("Efectos de sonido/Music/music boos1.wav")
            return # Saltamos el resto de la función
        else:
            # Musica de batalla normal
            self.sounds.change_music("Efectos de sonido/Music/Goblins_Dance_(Battle).wav")
            self.pending_enemies = []
            # Distribuir spawn normal
            spawns = [400, 800, 1200, 1600, 2000, 600, 1400, 1800]
            random.shuffle(spawns)
            idx = 0
            for _ in range(wave.get("grunts", 0)):
                self.pending_enemies.append(Grunt(spawns[idx % len(spawns)], fy - 80)) # Subido
                idx += 1
            for _ in range(wave.get("commanders", 0)):
                self.pending_enemies.append(Commander(spawns[idx % len(spawns)], fy - 100))
                idx += 1
            for _ in range(wave.get("guardians", 0)):
                self.pending_enemies.append(Guardian(spawns[idx % len(spawns)], fy - 100))
                idx += 1
            for _ in range(wave.get("potionmasters", 0)):
                self.pending_enemies.append(Potionmaster(spawns[idx % len(spawns)], fy - 100))
                idx += 1
            for _ in range(wave.get("eagles", 0)):
                self.pending_enemies.append(FlyingEye(spawns[idx % len(spawns)], fy - 300))
                idx += 1
            

            for _ in range(wave.get("ghosts", 0)):
                self.pending_enemies.append(Ghost(spawns[idx % len(spawns)], fy - 300))
                idx += 1
            for _ in range(wave.get("piranhas", 0)):
                self.pending_enemies.append(Piranha(spawns[idx % len(spawns)], fy - 80))
                idx += 1
            
            # Barajar para que no salgan todos los del mismo tipo juntos
            random.shuffle(self.pending_enemies)

            # Aplicar escalado de dificultad (HP y daño)
            hp_mult = 1.0 + (self.current_wave * 0.20) # +20% de salud por oleada
            dmg_mult = 1.0 + (self.current_wave * 0.10) # +10% de daño por oleada
            for e in self.pending_enemies:
                e.max_hp = int(e.max_hp * hp_mult)
                e.hp = e.max_hp
                e.damage = int(e.damage * dmg_mult)
            
            # El primer enemigo aparece de inmediato
            if self.pending_enemies:
                self.enemies.append(self.pending_enemies.pop(0))
                self.spawn_timer = 60 # 1 segundo para el siguiente

        themes = ["Normal BG", "Autumn BG", "Winter BG"]
        self.arena.set_bg(themes[self.current_wave % len(themes)])
        
        self.game_state = "wave_intro"
        self.wave_intro_timer = 120
        self.hud.show_message(f"¡OLEADA {self.current_wave + 1}!", 120)
        self._rumble(0.3, 20)

    def _check_attacks(self):
        if not self.player.attacking or self.player.attack_hit:
            return
        if int(self.player.frame_index) not in [1, 2]:
            return

        atk = self.player.attack_rect
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            if atk.colliderect(enemy.rect):
                hit = enemy.take_damage(PLAYER_ATTACK_DAMAGE)
                if hit:
                    if not enemy.alive:
                        self.sounds.play("enemy_death")
                    else:
                        self.sounds.play("enemy_hit")
                    self.player.attack_hit = True
                    self.player.mana = min(PLAYER_MAX_MANA, self.player.mana + 15)
                    self.player.super_meter = min(100, self.player.super_meter + 8)
                    
                    self._spawn_particles(enemy.x, enemy.y - enemy.height // 2,
                                          (255, 200, 100), 20)
                    for _ in range(12):
                        self.particles.append(Particle(enemy.x, enemy.y - enemy.height // 2,
                                                       (150, 220, 255), random.uniform(-3, 3), random.uniform(-5, -1), 35, 4))
                    for _ in range(6):
                        self.particles.append(Particle(enemy.x, enemy.y - enemy.height // 2,
                                                       (255, 255, 200), random.uniform(-2, 2), random.uniform(-3, 0), 20, 2))

                    self._rumble(0.5, 10)
                    
                    if not enemy.alive:
                        self.score += 150
                        self._spawn_particles(enemy.x, enemy.y - enemy.height // 2,
                                              (200, 50, 255), 30)
                        if getattr(enemy, "is_boss", False):
                            # Gran recompensa por jefe
                            self.player.hp = min(PLAYER_MAX_HP, self.player.hp + 50)
                            self.player.mana = min(PLAYER_MAX_MANA, self.player.mana + 100)
                            self.score += 1500
                            self._spawn_particles(enemy.x, enemy.y, (255, 255, 100), 100)
                            self._rumble(1.0, 30)

                    break  # Solo dañar a un enemigo por cada swing de la espada
                    for _ in range(20):
                        self.particles.append(Particle(enemy.x, enemy.y - enemy.height // 2,
                                                       (255, 100, 255), random.uniform(-5, 5), random.uniform(-5, -1), 45, 6))
                    for _ in range(10):
                        self.particles.append(Particle(enemy.x, enemy.y - enemy.height // 2,
                                                       (255, 255, 100), random.uniform(-3, 3), random.uniform(-3, 0), 30, 4))
                    self._rumble(1.0, 25)
                    if random.random() < 0.5:
                        self.hearts.append(Heart(enemy.x, enemy.y - enemy.height // 2))
                    break

    def _check_parry(self):
        if not self.player.parrying:
            return
        parry_rect = self.player.parry_rect
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            if parry_rect.colliderect(enemy.attack_rect):
                enemy.take_damage(PLAYER_ATTACK_DAMAGE, parry=True)
                self.sounds.play("parry")
                self.tutorial_parry_success = True
                # Chispas doradas de parry
                for _ in range(30):
                    self.particles.append(Particle(
                        enemy.x, enemy.y - enemy.height // 2,
                        (255, 255, 100), random.uniform(-6, 6), random.uniform(-6, 6),
                        random.randint(10, 30), random.randint(2, 5)
                    ))
                self.player.mana = min(PLAYER_MAX_MANA, self.player.mana + 20)
                self._rumble(1.0, 15)
                break

        # Parry proyectiles tutorial/enemigos
        for p in self.enemy_projectiles:
            if parry_rect.colliderect(p.attack_rect):
                p.take_damage(0, parry=True)
                self.sounds.play("parry")
                self.tutorial_parry_success = True
                for _ in range(20):
                    self.particles.append(Particle(p.x, p.y, (255, 255, 100), random.uniform(-5, 5), random.uniform(-5, 5), 30, 4))
                break

    def run(self):
        running = True

        while running:
            input_events = {}
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == KEY_JUMP: input_events["jump"] = True
                    if event.key == KEY_ATTACK: input_events["attack"] = True
                    if event.key == KEY_DASH: input_events["dash"] = True
                    if event.key == KEY_CAST: input_events["cast"] = True
                    if event.key == KEY_HEAL: input_events["heal"] = True
                    if event.key == KEY_PARRY: input_events["parry"] = True
                    # Menu navigation
                    if event.key in (pygame.K_w, pygame.K_UP): input_events["menu_up"] = True
                    if event.key in (pygame.K_s, pygame.K_DOWN): input_events["menu_down"] = True
                    if event.key == pygame.K_ESCAPE: input_events["menu_back"] = True
                    if event.key == pygame.K_RETURN: input_events["menu_confirm"] = True
                if event.type == pygame.JOYBUTTONDOWN:
                    if event.button == JOY_JUMP: input_events["jump"] = True
                    if event.button == JOY_ATTACK: input_events["attack"] = True
                    # B se maneja por tiempo (Hold/Press)
                    if event.button == JOY_PARRY: input_events["parry"] = True
                    if event.button == JOY_SUPER: input_events["super"] = True
                    if event.button == JOY_SUPER2: input_events["super2"] = True
                    # Menu navigation
                    if event.button == 0: input_events["menu_confirm"] = True  # A
                    if event.button == 1: pass # B manejado en polling
                if event.type == pygame.JOYDEVICEADDED:
                    self._init_joystick()
                if event.type == pygame.JOYDEVICEREMOVED:
                    self.joystick = None

            keys = pygame.key.get_pressed()


            joy = None
            if self.joystick:
                try:
                    _ = self.joystick.get_axis(0)
                    joy = self.joystick
                except Exception:
                    self.joystick = None

            # Start / Enter debounce
            start_pressed = keys[pygame.K_RETURN]
            if joy:
                try:
                    if joy.get_button(7):
                        start_pressed = True
                    
                    # RT para DASH
                    rt_val = joy.get_axis(JOY_DASH_AXIS)
                    if rt_val > JOY_RT_THRESHOLD:
                        if not self.rt_was_pressed:
                            input_events["dash"] = True
                        self.rt_was_pressed = True
                    else:
                        self.rt_was_pressed = False

                    # B para Magia (Pulsar) y Curar (Mantener)
                    b_pressed = joy.get_button(1)
                    if b_pressed:
                        self.b_hold_timer += 1
                        if self.b_hold_timer >= 30: # 0.5s para curar
                            input_events["heal"] = True
                            if self.b_hold_timer % 4 == 0:
                                self._spawn_particles(self.player.x, self.player.y - 40, (100, 255, 100), 5)
                    else:
                        if 0 < self.b_hold_timer < 30:
                            input_events["cast"] = True
                        self.b_hold_timer = 0

                except Exception:
                    pass
            
            just_pressed_start = start_pressed and not self.start_was_pressed
            self.start_was_pressed = start_pressed

            # ── Estados ──
            if self.game_state == "menu":
                # Partículas de fondo para el menú
                if random.random() < 0.15:
                    self.particles.append(Particle(random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT, (100, 150, 255), 0, random.uniform(-2, -0.5), 100, random.randint(2, 4)))
                
                # Manejo de menú con navegación
                menu_result = self.hud.handle_menu_input(input_events, joy, just_pressed_start)
                if menu_result["action"] == "play":
                    self._reset_game()
                elif menu_result["action"] == "play_wave":
                    self._reset_game(start_wave=menu_result["wave"])
                    self.hud.sub_menu = None
                elif menu_result["action"] == "tutorial":
                    self._start_tutorial()

            elif self.game_state == "paused":
                if just_pressed_start:
                    self.game_state = "playing"

            elif self.game_state == "intro_fall":
                self.player.update(self.arena.platforms)
                if self.player.on_ground:
                    self._spawn_particles(self.player.x, self.player.y, (150, 150, 150), 40)
                    self._rumble(1.0, 20)
                    self._start_wave()

            elif self.game_state == "wave_intro":
                self.wave_intro_timer -= 1
                if self.wave_intro_timer <= 0:
                    self.game_state = "playing"
                self.player.handle_input(keys, joy, input_events)
                self.player.update(self.arena.platforms)
                for e in self.enemies:
                    e.update(self.player, self.arena.platforms)

            elif self.game_state == "playing":
                if self.player:
                    # Reproducir sonido de salto y ataque
                    if input_events.get("jump") and (self.player.on_ground or self.player.touching_wall != 0 or self.player.can_double_jump):
                        self.sounds.play("jump")
                    
                    if input_events.get("attack") and not self.player.attacking:
                        self.sounds.play("attack")

                if just_pressed_start:
                    self.game_state = "paused"
                    continue

                # Spawn gradual de enemigos (límite de 2 a la vez)
                if self.pending_enemies:
                    max_concurrent = 2
                    if len(self.enemies) < max_concurrent and self.spawn_timer <= 0:
                        new_enemy = self.pending_enemies.pop(0)
                        self.enemies.append(new_enemy)
                        self._spawn_particles(new_enemy.x, new_enemy.y - 20, (200, 200, 255), 15)
                        self.spawn_timer = 60
                if self.spawn_timer > 0:
                    self.spawn_timer -= 1

                # Magia / Poder
                if input_events.get("cast") and self.player.mana >= 20:
                    self.player.mana -= 20
                    self.sounds.play("cast")
                    direction = 1 if self.player.facing_right else -1
                    px = self.player.x + (direction * 30)
                    py = self.player.y - self.player.height // 2
                    self.projectiles.append(Projectile(px, py, direction))
                    self._spawn_particles(px, py, (100, 200, 255), 10)
                    self._rumble(0.3, 5)

                if self.player.super_meter >= 100 and not getattr(self, "super_charged_sound_played", False):
                    self.sounds.play("charged")
                    self.super_charged_sound_played = True
                elif self.player.super_meter < 100:
                    self.super_charged_sound_played = False
                
                # Superpoder: Onda de Dragón (LB)
                if input_events.get("super") and self.player.super_meter >= 100:
                    self.player.super_meter = 0
                    self.player.attacking = True
                    self.player.attack_timer = 30
                    self.player.frame_index = 0
                    self.sounds.play("super")
                    px = self.player.x
                    py = self.player.y - 40
                    self.homing_waves.append(HomingWave(px, py, self.enemies))
                    for _ in range(60):
                        angle = random.uniform(0, 6.28)
                        speed = random.uniform(5, 12)
                        self.particles.append(Particle(px, py, (0, 255, 150), math.cos(angle)*speed, math.sin(angle)*speed, 40, 5))
                    for _ in range(20):
                        self.particles.append(Particle(px, py, (255, 255, 100), random.uniform(-3, 3), random.uniform(-3, 3), 25, 3))
                    self._rumble(1.0, 40)
                    self.camera_shake = 15
                    self._super_flash = 10

                # Curación gradual (Mantener B)
                if input_events.get("heal") and self.player.mana >= 1 and self.player.hp < PLAYER_MAX_HP:
                    self.player.healing_glow = True
                    self.player.healing_timer += 1
                    if self.player.healing_timer >= 12: # Curar 1 HP cada 12 frames
                        self.player.hp = min(PLAYER_MAX_HP, self.player.hp + 1)
                        self.player.mana -= 4
                        self.player.healing_timer = 0
                        self.sounds.play("heal")
                        for _ in range(10):
                            self.particles.append(Particle(
                                self.player.x, self.player.y - self.player.height // 2,
                                (100, 255, 100), random.uniform(-2, 2), random.uniform(-4, -1), 30, 4
                            ))
                        self._rumble(0.2, 5)
                else:
                    self.player.healing_glow = False
                    if not input_events.get("heal"):
                        self.player.healing_timer = 0

                self.player.handle_input(keys, joy, input_events)
                self.player.update(self.arena.platforms)
                # Superpoder 2: Explosión Astral (RB)
                if input_events.get("super2") and self.player.super_meter >= 50:
                    self.player.super_meter -= 50
                    self.sounds.play("super2")
                    self.camera_shake = 25
                    self._super_flash = 12
                    # Explosión masiva de partículas
                    for _ in range(80):
                        angle = random.uniform(0, 6.28)
                        speed = random.uniform(3, 16)
                        self.particles.append(Particle(self.player.x, self.player.y - 40, (180, 100, 255), math.cos(angle)*speed, math.sin(angle)*speed, 50, 5))
                    for _ in range(40):
                        angle = random.uniform(0, 6.28)
                        r = random.uniform(0, 400)
                        self.particles.append(Particle(self.player.x + math.cos(angle)*r, self.player.y - 40 + math.sin(angle)*r, (255, 255, 255), 0, -1, 30, 2))
                    
                    for enemy in self.enemies:
                        if enemy.alive and abs(enemy.x - self.player.x) < 450:
                            enemy.take_damage(8, ignore_iframes=True)
                            for _ in range(15):
                                self.particles.append(Particle(enemy.x, enemy.y-30, (255, 150, 255), random.uniform(-5, 5), random.uniform(-5, 5), 35, 4))


                if self.player.dashing:
                    if self.player.dash_timer == 18:
                        self.sounds.play("dash")
                    dir_x = -1 if self.player.facing_right else 1
                    self.particles.append(Particle(
                        self.player.x + dir_x * 15, self.player.y - 20,
                        (180, 220, 255), dir_x * 2, 0, 15, 4
                    ))
                    self.particles.append(Particle(
                        self.player.x, self.player.y,
                        (150, 150, 150), dir_x * 1, -1, 10, 2
                    ))
                    if self.player.dash_timer % 3 == 0:
                        self.particles.append(Particle(
                            self.player.x - dir_x * 20, self.player.y - 10,
                            (200, 230, 255), 0, 0, 8, 3
                        ))

                for e in self.enemies:
                    e.update(self.player, self.arena.platforms)
                    
                    if isinstance(e, Golem) and getattr(e, "charge_timer", 0) > 0:
                        e.charge_timer -= 1
                        if e.charge_timer <= 0:
                            e.vx = 0
                            e.state = "idle"
                            e.charge_timer = 0
                            e.special_type = None
                    
                    # Efectos de fase 2 para jefes
                    if getattr(e, "is_boss", False) and getattr(e, "phase", 1) == 2:
                        if isinstance(e, DemonSlime):
                            self.particles.append(Particle(e.x + random.randint(-50, 50), e.y - 10, (255, 60, 0), 0, -3, 25, 4))
                        elif isinstance(e, Golem):
                            self.particles.append(Particle(e.x + random.randint(-40, 40), e.y, (100, 80, 60), 0, -1, 15, 3))
                            if random.random() < 0.3:
                                self._spawn_particles(e.x, e.y, (150, 150, 150), 2)
                        elif isinstance(e, FrostGuardian):
                            self.particles.append(Particle(e.x + random.randint(-150, 150), e.y - random.randint(0, 100), (200, 230, 255), -3, 1, 40, 3))
                        if getattr(e, "current_attack_type", "") == "blizzard_dash":
                            self.particles.append(Particle(e.x, e.y - 50, (200, 255, 255), -5, 0, 20, 5))

                    # Ejecución de habilidades especiales (para todas las fases)
                    if getattr(e, "is_boss", False):
                        stype = getattr(e, "special_type", None)
                        if stype and not getattr(e, "special_fired_this_frame", False):
                            e.special_fired_this_frame = True
                            
                            if stype == "lava_spit":
                                vx = 10 if e.facing_right else -10
                                self.enemy_projectiles.append(EnemyEnergyBall(e.x, e.y - 50, vx, (255, 50, 0)))
                                self._spawn_particles(e.x, e.y - 50, (255, 80, 0), 12)
                                self.sounds.play("enemy_hit")
                            elif stype == "triple_fire":
                                for i in range(-1, 2):
                                    vx = (12 if e.facing_right else -12)
                                    eb = EnemyEnergyBall(e.x, e.y - 50, vx, (255, 100, 0))
                                    eb.y += i * 30
                                    self.enemy_projectiles.append(eb)
                                self._spawn_particles(e.x, e.y - 50, (255, 120, 0), 20)
                                self.camera_shake = 6
                                self.sounds.play("enemy_hit")
                            elif stype == "jump_slam":
                                self.camera_shake = 15
                                self._spawn_particles(e.x, e.y, (255, 80, 0), 50)
                                for i in range(-1, 2):
                                    self.particles.append(Particle(e.x + i * 30, e.y, (255, 120, 0), 0, -4, 20, 4))
                                if abs(self.player.x - e.x) < 300: self.player.take_damage(3, e.x)
                                self.sounds.play("enemy_hit")
                            elif stype == "shadow_burst":
                                self._spawn_particles(e.x, e.y - 40, (80, 0, 150), 60)
                                for i in range(-2, 3):
                                    self.particles.append(Particle(e.x + i * 40, e.y - 30, (120, 0, 200), random.uniform(-2, 2), -3, 25, 5))
                                if abs(self.player.x - e.x) < 250: self.player.take_damage(2, e.x)
                                self.camera_shake = 10
                                self.sounds.play("enemy_hit")
                            elif stype == "earthquake":
                                self.camera_shake = 15
                                self._spawn_particles(e.x, e.y, (180, 150, 80), 35)
                                for px in range(-250, 251, 50):
                                    self.particles.append(Particle(e.x + px, e.y, (200, 170, 90), random.uniform(-2, 2), -3, 20, 4))
                                for px in range(-150, 151, 30):
                                    self.particles.append(Particle(e.x + px, e.y - 10, (150, 120, 60), 0, -1, 15, 2))
                                if abs(self.player.x - e.x) < 280: self.player.take_damage(2, e.x)
                                self.sounds.play("enemy_hit")
                            elif stype == "slam":
                                self.camera_shake = 10
                                self._spawn_particles(e.x, e.y, (180, 150, 100), 20)
                                if abs(self.player.x - e.x) < 200: self.player.take_damage(3, e.x)
                                self.sounds.play("enemy_hit")
                            elif stype == "stone_pillar":
                                for i in range(-1, 2):
                                    px = self.player.x + i * 60
                                    self._spawn_particles(px, self.player.y, (120, 100, 60), 25)
                                    self.particles.append(Particle(px, self.player.y - 20, (150, 120, 70), 0, -4, 20, 5))
                                self.player.take_damage(2, self.player.x - 10)
                                self.camera_shake = 8
                                self.sounds.play("enemy_hit")
                            elif stype == "ground_slam":
                                self.camera_shake = 20
                                self._spawn_particles(e.x, e.y, (200, 170, 100), 50)
                                for px in range(-300, 301, 50):
                                    self.particles.append(Particle(e.x + px, e.y, (220, 190, 120), random.uniform(-2, 2), -4, 25, 5))
                                    self.particles.append(Particle(e.x + px, e.y - 15, (180, 150, 80), 0, -2, 15, 3))
                                if abs(self.player.x - e.x) < 320: self.player.take_damage(4, e.x)
                                self.sounds.play("enemy_hit")
                            elif stype == "rolling_charge":
                                e.vx = (10 if e.facing_right else -10)
                                e.state = "run"
                                e.charge_timer = 45
                                self.camera_shake = 8
                                self._spawn_particles(e.x, e.y, (150, 130, 100), 15)
                            elif stype == "meteor_shower":
                                for _ in range(5):
                                    mx = self.player.x + random.randint(-200, 200)
                                    meteor = EnemyEnergyBall(mx, -50, 0, (200, 100, 50))
                                    meteor.is_rock = True
                                    meteor.radius = 18
                                    meteor.vy = random.randint(6, 12)
                                    meteor.update = lambda self=meteor: (setattr(self, 'y', self.y + getattr(self, 'vy', 8)), setattr(self, 'life', self.life - 1))
                                    self.enemy_projectiles.append(meteor)
                                self.camera_shake = 12
                                self.sounds.play("enemy_hit")
                            elif stype == "rock_throw":
                                vx = 12 if e.facing_right else -12
                                rock = EnemyEnergyBall(e.x, e.y - 60, vx, (150, 130, 100))
                                rock.is_rock = True
                                rock.radius = 20
                                rock.damage = 3
                                rock.vy = -5
                                self.enemy_projectiles.append(rock)
                                self._spawn_particles(e.x, e.y - 60, (180, 160, 120), 10)
                                self.sounds.play("enemy_hit")
                            elif stype == "ice_bolt":
                                vx = 15 if e.facing_right else -15
                                self.enemy_projectiles.append(EnemyEnergyBall(e.x, e.y - 60, vx, (100, 200, 255)))
                                self._spawn_particles(e.x, e.y - 60, (150, 230, 255), 8)
                            elif stype == "frost_nova":
                                self._spawn_particles(e.x, e.y - 50, (180, 240, 255), 40)
                                if abs(self.player.x - e.x) < 220: self.player.take_damage(2, e.x)
                                self.camera_shake = 8
                                self.sounds.play("enemy_hit")
                            elif stype == "ice_rain":
                                for _ in range(3):
                                    rx = self.player.x + random.randint(-100, 100)
                                    self.enemy_projectiles.append(EnemyEnergyBall(rx, 0, 0, (200, 230, 255)))
                                    self.enemy_projectiles[-1].vy = 10 
                                    self.enemy_projectiles[-1].update = lambda self=self.enemy_projectiles[-1]: (setattr(self, 'y', self.y + self.vy), setattr(self, 'life', self.life - 1))
                                self.camera_shake = 6
                                self.sounds.play("enemy_hit")
                            elif stype == "ice_shards":
                                for angle in range(0, 360, 45):
                                    rad = math.radians(angle)
                                    vx = math.cos(rad) * 9
                                    vy = math.sin(rad) * 9
                                    eb = EnemyEnergyBall(e.x, e.y - 60, vx, (150, 210, 255))
                                    eb.vy = vy
                                    self.enemy_projectiles.append(eb)
                                self._spawn_particles(e.x, e.y - 60, (200, 255, 255), 15)
                                self.sounds.play("enemy_hit")
                            elif stype == "triple_bolt":
                                for i in range(-1, 2):
                                    vx = (16 if e.facing_right else -16)
                                    eb = EnemyEnergyBall(e.x, e.y - 60, vx, (120, 230, 255))
                                    eb.vy = i * 4
                                    self.enemy_projectiles.append(eb)
                                self.sounds.play("enemy_hit")
                                self._spawn_particles(e.x, e.y - 60, (150, 240, 255), 10)
                            elif stype == "blizzard_dash":
                                e.vx = (25 if e.facing_right else -25)
                                e.charge_timer = 25
                                self.camera_shake = 10
                                self._spawn_particles(e.x, e.y - 30, (255, 255, 255), 20)
                                self.sounds.play("dash")
                            elif stype == "garden_drop":
                                for _ in range(3):
                                    gx = self.player.x + random.randint(-150, 150)
                                    sprite = random.choice(e.garden_sprites)
                                    self.enemy_projectiles.append(EnemyEnergyBall(gx, -50, 0, (100, 150, 100)))
                                    self.enemy_projectiles[-1].vy = 10
                                    self.enemy_projectiles[-1].sprite = sprite
                                    self.enemy_projectiles[-1].is_garden = True
                                    self.enemy_projectiles[-1].impact_frame = 0
                                self.camera_shake = 10
                                self.sounds.play("enemy_hit")

                        if not stype:
                            e.special_fired_this_frame = False

                    if getattr(e, "has_thrown", False) and getattr(e, "attack_hit", False):
                        e.attack_hit = False
                        dir_x = 1 if e.facing_right else -1
                        if isinstance(e, Piranha):
                            self.enemy_projectiles.append(EnemyEnergyBall(e.x, e.y - 20, dir_x * 6, (50, 200, 50)))
                        else:
                            self.enemy_projectiles.append(EnemyProjectile(e.x, e.y - 40, dir_x * 8, -5, self.potion_frames))

                # Projectiles
                for proj in self.projectiles:
                    proj.update()
                    self.particles.append(Particle(proj.x, proj.y, (100, 200, 255), 0, 0, 10, 2))
                    for e in self.enemies:
                        if e.alive and proj.rect.colliderect(e.rect):
                            if e.take_damage(proj.damage, ignore_iframes=True):
                                proj.life = 0
                                self._spawn_particles(e.x, e.y - e.height // 2, (100, 200, 255), 15)
                                if not e.alive: 
                                    self.score += 100
                                    if getattr(e, "is_boss", False):
                                        self.player.hp = min(PLAYER_MAX_HP, self.player.hp + 50)
                                        self.player.mana = min(PLAYER_MAX_MANA, self.player.mana + 100)
                                        self.score += 1500
                                        self._spawn_particles(e.x, e.y, (255, 255, 100), 100)
                                        self._rumble(1.0, 30)
                            break
                self.projectiles = [p for p in self.projectiles if p.life > 0]
                
                # Enemy Projectiles (Pociones y Energía)
                for proj in self.enemy_projectiles:
                    if isinstance(proj, EnemyEnergyBall):
                        if getattr(proj, "is_garden", False):
                            proj.update()
                            if proj.y >= self.arena.floor_y - 20 and proj.impact_frame == 0:
                                proj.impact_frame = 30
                                proj.y = self.arena.floor_y - 20
                                proj.vy = 0
                                self._spawn_particles(proj.x, proj.y, (100, 150, 100), 20)
                                self.camera_shake = 5
                                if abs(self.player.x - proj.x) < 80:
                                    self.player.take_damage(2, proj.x)
                            elif proj.impact_frame > 0:
                                proj.impact_frame -= 1
                                if proj.impact_frame <= 0:
                                    proj.life = 0
                        else:
                            proj.update()
                    else:
                        proj.update(self.arena.floor_y)
                        
                    self.particles.append(Particle(proj.x, proj.y, (100, 255, 100), 0, 0, 10, 2))
                    if proj.life <= 0:
                        self._spawn_particles(proj.x, proj.y, (100, 255, 100), 15)
                    elif proj.rect.colliderect(self.player.rect):
                        if self.player.take_damage(proj.damage, proj.x):
                            self.sounds.play("damage")
                            proj.life = 0
                            self._spawn_particles(proj.x, proj.y, (100, 255, 100), 10)
                            self._rumble(0.5, 10)

                self.enemy_projectiles = [p for p in self.enemy_projectiles if p.life > 0]

                self._check_parry()
                self._check_attacks()

                # Flash de pantalla al golpear
                if hasattr(self, '_hit_flash') and self._hit_flash > 0:
                    flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                    flash_surf.fill((255, 0, 0, self._hit_flash * 50))
                    self.screen.blit(flash_surf, (0, 0))
                    self._hit_flash -= 1

                # Actualizar corazones
                for h in self.hearts:
                    h.update(self.arena.platforms)
                    if h.rect.colliderect(self.player.rect):
                        if self.player.hp < PLAYER_MAX_HP:
                            self.player.hp += 1
                            self.sounds.play("heal")
                            self._spawn_particles(h.x, h.y, (255, 50, 50), 15)
                            h.collect()
                self.hearts = [h for h in self.hearts if not h.collected]

                if not self.player.alive:
                    self.game_state = "gameover"
                    self.continue_timer = self.max_continue_time
                    if self.current_wave + 1 > self.best_wave:
                        self.best_wave = self.current_wave + 1
                    if self.score > self.best_score:
                        self.best_score = self.score
                    self._rumble(1.0, 30)
                    self.camera_shake = 15
                    self._spawn_particles(self.player.x, self.player.y - 30, (255, 50, 50), 50)
                elif self.player.i_frames == PLAYER_I_FRAMES - 1:
                    self._rumble(0.7, 12)
                    self._spawn_particles(self.player.x,
                                          self.player.y - self.player.height // 2,
                                          (255, 80, 80), 15)
                    self._hit_flash = 5

                self.enemies = [e for e in self.enemies if not e.death_done]

                if len(self.enemies) == 0 and not self.pending_enemies:
                    self.game_state = "wave_transition"
                    self.wave_transition_timer = 240
                    self.portal = Portal(ARENA_WIDTH // 2, self.arena.floor_y - 60)
                    self.fireworks = []
                    self.homing_waves = [] # Limpiar supers al terminar oleada
                    self.sounds.play("heal") 
            
            elif self.game_state == "tutorial":
                self.tutorial_manager.update(input_events)
                self.player.handle_input(keys, joy, input_events)
                self.player.update(self.arena.platforms)
                for e in self.enemies:
                    e.update(self.player, self.arena.platforms)
                for p in self.enemy_projectiles:
                    p.update()
                self.enemy_projectiles = [p for p in self.enemy_projectiles if p.alive]
                
                # Check tutorial portal entry
                if self.portal and self.player.rect.colliderect(self.portal.rect):
                    self.game_state = "menu"
                    self.hud.show_message("ENTRENAMIENTO COMPLETADO", 180)
                    self.portal = None
                    self.enemies = []
                    self.enemy_projectiles = []

            elif self.game_state == "cinematic":
                self.cinematic_timer -= 1
                if self.cinematic_timer <= 0:
                    self.game_state = "intro_run"
                    # Spawn un enemigo random para la intro
                    self.enemies = [Grunt(400, SCREEN_HEIGHT - 100)]
                
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, min(255, self.cinematic_timer * 2)))
                self.screen.blit(overlay, (0, 0))

            elif self.game_state == "intro_run":
                # El jugador entra corriendo
                self.player.vx = PLAYER_SPEED
                self.player.facing_right = True
                self.player.update(self.arena.platforms)
                
                if self.player.x > 200:
                    self.game_state = "wave_intro"
                    self.wave_intro_timer = 120
                    self._start_wave()

            elif self.game_state == "intro_fall":
                # Nueva entrada: Pilar de luz/Teletransporte
                self.teleport_timer += 1
                
                if self.teleport_timer > 60:
                    self.game_state = "wave_intro"
                    self.wave_intro_timer = 120
                    self.camera_shake = 10
                    self.teleport_timer = 0
                    self._start_wave()
                    self._rumble(0.5, 200)

            elif self.game_state == "boss_intro":
                self.boss_intro_timer -= 1
                # Jugador corre al centro
                if self.player.x < 300:
                    self.player.vx = PLAYER_SPEED
                    self.player.facing_right = True
                else:
                    self.player.vx = 0
                self.player.update(self.arena.platforms)

                # Jefe cae
                if self.enemies:
                    boss = self.enemies[0]
                    if boss.y < self.arena.floor_y:
                        boss.vy += 1
                        boss.y += boss.vy
                    else:
                        boss.y = self.arena.floor_y
                        if boss.vy > 0:
                            self.camera_shake = 20
                            self._spawn_particles(boss.x, boss.y, (150, 150, 150), 40)
                            boss.vy = 0

                if self.boss_intro_timer <= 0:
                    self.game_state = "playing"

            elif self.game_state == "wave_transition":
                # EL JUGADOR DEBE TENER CONTROL
                self.player.handle_input(keys, joy, input_events)
                self.player.update(self.arena.platforms)
                
                if self.portal:
                    self.portal.update()
                    # Colisión real con el centro del portal
                    portal_rect = pygame.Rect(self.portal.x - 30, self.portal.y - 60, 60, 120)
                    if self.player.rect.colliderect(portal_rect):
                        self.wave_transition_timer -= 1
                        # Efecto de succión y desaparición
                        self.player.x += (self.portal.x - self.player.x) * 0.1
                        self.player.y += (self.portal.y - 30 - self.player.y) * 0.1
                        self.player.vx = 0
                        self.player.vy = 0
                        # Desaparecer gradualmente
                        if not hasattr(self.player, 'alpha'): self.player.alpha = 255
                        self.player.alpha = max(0, self.player.alpha - 10)
                    else:
                        if self.wave_transition_timer < 180:
                            self.wave_transition_timer = 180
                else:
                    self.wave_transition_timer -= 1
                
                # Texto de Victoria
                msg = "¡OLEADA COMPLETADA! ENTRA AL PORTAL"
                font = pygame.font.Font(None, 60)
                txt = font.render(msg, True, (255, 255, 100))
                self.screen.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2, 150))

                self.player.vx *= 0.95
                self.fade_alpha = min(255, (180 - self.wave_transition_timer) * 4)
                
                if self.wave_transition_timer <= 0:
                    self.current_wave += 1
                    self.player.x = ARENA_WIDTH // 2
                    self.player.y = SCREEN_HEIGHT - 100
                    self.fade_alpha = 0
                    self._start_wave()
                    self.game_state = "intro_fall"

            elif self.game_state in ("gameover", "victory"):
                if hasattr(self, 'continue_timer') and self.continue_timer > 0:
                    self.continue_timer -= 1 / FPS
                    if self.continue_timer <= 0:
                        self.continue_timer = 0
                if just_pressed_start:
                    if self.continue_timer > 0:
                        self.player.hp = PLAYER_MAX_HP
                        self.player.alive = True
                        self.player.alpha = 255
                        self.player.i_frames = 120
                        self.player.state = "revive"
                        death_frames = len(self.player.animations["death"])
                        self.player.frame_index = float(death_frames - 1)
                        self.player.vx = 0
                        self.player.vy = 0
                        self.continue_timer = 0
                        self._spawn_particles(self.player.x, self.player.y - 30, (255, 255, 100), 50)
                        self._spawn_particles(self.player.x, self.player.y - 30, (200, 255, 200), 40)
                        self.camera_shake = 10
                        self.game_state = "playing"
                        self.sounds.play("heal")
                    else:
                        self.game_state = "menu"
                        pygame.mixer.music.stop()
                if self.player:
                    self.player.update(self.arena.platforms)

            for p in self.particles:
                p.update()
            self.particles = [p for p in self.particles if p.life > 0]
            # Rumble
            if self.rumble_timer > 0:
                self.rumble_timer -= 1
                if self.rumble_timer <= 0:
                    self._stop_rumble()

            self.hud.update()

            # Polvo ambiental
            if random.random() < 0.08:
                self.particles.append(Particle(
                    random.randint(int(self.camera_x), int(self.camera_x) + SCREEN_WIDTH),
                    random.randint(0, SCREEN_HEIGHT),
                    (120, 100, 80), 0, -0.2,
                    random.randint(40, 100), random.randint(1, 2),
                ))

            # Actualizar cámara
            if self.game_state == "boss_intro" and self.enemies:
                boss = self.enemies[0]
                target_cx = boss.x - SCREEN_WIDTH // 2
                target_cy = boss.y - SCREEN_HEIGHT // 2
            elif self.player:
                target_cx = self.player.x - SCREEN_WIDTH // 2
                if self.game_state == "intro_fall":
                    target_cy = self.player.y - SCREEN_HEIGHT // 2
                else:
                    target_cy = 0
            else:
                target_cx = self.camera_x
                target_cy = self.camera_y

            if self.player or self.game_state == "boss_intro":
                self.camera_x += (target_cx - self.camera_x) * 0.1
                self.camera_y += (target_cy - self.camera_y) * 0.1
                if self.camera_x < 0: self.camera_x = 0
                if self.camera_x > ARENA_WIDTH - SCREEN_WIDTH: self.camera_x = ARENA_WIDTH - SCREEN_WIDTH

            # Flash blanco al usar super
            if hasattr(self, '_super_flash') and self._super_flash > 0:
                flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                flash_surf.fill((255, 255, 255, self._super_flash * 25))
                self.screen.blit(flash_surf, (0, 0))
                self._super_flash -= 1

            # ── Sacudida de cámara ──
            curr_cx = self.camera_x
            curr_cy = self.camera_y
            if self.camera_shake > 0:
                curr_cx += random.randint(-self.camera_shake, self.camera_shake)
                curr_cy += random.randint(-self.camera_shake, self.camera_shake)
                self.camera_shake -= 1

            # ── DIBUJAR ──
            self.arena.draw(self.screen, curr_cx, curr_cy)

            for p in self.particles:
                p.draw(self.screen, curr_cx, curr_cy)
                
            for proj in self.projectiles:
                proj.draw(self.screen, curr_cx, curr_cy)
                
            for proj in self.enemy_projectiles:
                proj.draw(self.screen, curr_cx, curr_cy)

            for e in self.enemies:
                e.draw(self.screen, curr_cx, curr_cy)
                if getattr(e, "is_boss", False) and getattr(e, "phase", 1) == 2:
                    t = pygame.time.get_ticks()
                    aura_alpha = int(70 + 40 * __import__('math').sin(t / 250.0))
                    if isinstance(e, Golem):
                        color = (200, 170, 100, aura_alpha)
                    elif isinstance(e, DemonSlime):
                        color = (255, 80, 0, aura_alpha)
                    else:
                        color = (100, 200, 255, aura_alpha)
                    aura_surf = pygame.Surface((100, 100), pygame.SRCALPHA)
                    pygame.draw.circle(aura_surf, color, (50, 50), 40)
                    pygame.draw.circle(aura_surf, (*color[:3], aura_alpha // 2), (50, 50), 50)
                    self.screen.blit(aura_surf, (int(e.x - 50 - curr_cx), int(e.y - 90 - curr_cy)))

            # Homing Waves (Superhabilidad)
            for hw in self.homing_waves:
                hw.update(self.enemies)
                hw.draw(self.screen, curr_cx, curr_cy)
            self.homing_waves = [hw for hw in self.homing_waves if hw.life > 0]

            for h in self.hearts:
                self.screen.blit(h.image, (int(h.x - h.image.get_width()//2 - curr_cx), int(h.y - h.image.get_height()//2 - curr_cy)))

            for fw in self.fireworks:
                fw.draw(self.screen, curr_cx, curr_cy)

            if self.player:
                self.player.draw(self.screen, curr_cx, curr_cy)


            if self.portal:
                self.portal.draw(self.screen, curr_cx, curr_cy)

            # Flash de pantalla rojo al recibir daño
            if hasattr(self, '_hit_flash') and self._hit_flash > 0:
                flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                flash_surf.fill((255, 0, 0, self._hit_flash * 50))
                self.screen.blit(flash_surf, (0, 0))
                self._hit_flash -= 1

            # Flash blanco al usar super

            hp = self.player.hp if self.player else 0
            mana = self.player.mana if self.player else 0
            self.hud.draw(self.screen, hp, PLAYER_MAX_HP, mana, PLAYER_MAX_MANA,
                          self.player.super_meter if self.player else 0, 100,
                          self.current_wave, self.score, self.game_state,
                          getattr(self, 'continue_timer', 0),
                          self.best_score, self.best_wave)

            # Cinematic Boss UI
            if self.game_state == "boss_intro":
                strip_h = 100
                pygame.draw.rect(self.screen, (0, 0, 0, 200), (0, SCREEN_HEIGHT // 2 - strip_h // 2, SCREEN_WIDTH, strip_h))
                
                txt1 = self.hud.font.render("¡UN JEFE HA APARECIDO!", True, (255, 50, 50))
                self.screen.blit(txt1, (SCREEN_WIDTH // 2 - txt1.get_width() // 2, SCREEN_HEIGHT // 2 - 40))
                
                txt2 = self.hud.font_big.render(getattr(self, "boss_name", "???"), True, WHITE)
                self.screen.blit(txt2, (SCREEN_WIDTH // 2 - txt2.get_width() // 2, SCREEN_HEIGHT // 2))

            if self.player and self.player.state == "revive":
                t = self.player.frame_index
                glow = int(127 + 128 * __import__('math').sin(t * 20))
                revive_txt = self.hud.font_big.render("¡REVIVIENDO!", True, (255, 255, glow))
                self.screen.blit(revive_txt, (SCREEN_WIDTH // 2 - revive_txt.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
                circle_surf = pygame.Surface((120, 120), pygame.SRCALPHA)
                pygame.draw.circle(circle_surf, (255, 255, 200, 100), (60, 60), 45)
                pygame.draw.circle(circle_surf, (255, 255, 100, 50), (60, 60), 55)
                pygame.draw.circle(circle_surf, (255, 200, 50, 30), (60, 60), 65)
                self.screen.blit(circle_surf, (int(self.player.x - 60 - curr_cx), int(self.player.y - 90 - curr_cy)))

            # Fundido de transición
            if self.fade_alpha > 0:
                fade_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                fade_surf.fill((0, 0, 0))
                fade_surf.set_alpha(self.fade_alpha)
                self.screen.blit(fade_surf, (0, 0))

            if self.game_state == "wave_transition":
                vic_text = self.hud.font_big.render("¡VICTORIA!", True, (255, 215, 0))
                self.screen.blit(vic_text, (SCREEN_WIDTH // 2 - vic_text.get_width() // 2, 200))

            if self.game_state == "cinematic":
                cin_text = self.hud.font_title.render("EL DESCENSO", True, (200, 180, 100))
                self.screen.blit(cin_text, (SCREEN_WIDTH // 2 - cin_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))

            # Info mando
            if self.joystick and self.game_state not in ("menu",):
                joy_txt = self.hud.font.render(f"Mando: {self.joystick.get_name()}", True, (100, 90, 130))
                self.screen.blit(joy_txt, (10, SCREEN_HEIGHT - 30))

            pygame.display.flip()
            self.clock.tick(FPS)

        self._stop_rumble()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
