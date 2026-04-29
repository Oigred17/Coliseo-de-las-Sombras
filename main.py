# ══════════════════════════════════════════════════════════════
#  COLISEO DE LAS SOMBRAS  –  Juego estilo Hollow Knight
#  Python + Pygame-CE  |  Teclado + Mando con vibración
# ══════════════════════════════════════════════════════════════
import pygame
import sys
import random
import math
from settings import *
from player import Player
from enemies import Grunt, Commander, Guardian, Potionmaster, Eagle
from hud import HUD
from spritesheet import load_single_image, load_spritesheet

class SoundManager:
    def __init__(self):
        pygame.mixer.init()
        self.sounds = {}
        # Load important sounds
        try:
            self.sounds["attack"] = pygame.mixer.Sound(r"Efectos de sonido\SFX\07_human_atk_sword_1.wav")
            self.sounds["dash"] = pygame.mixer.Sound(r"Efectos de sonido\SFX\15_human_dash_1.wav")
            self.sounds["damage"] = pygame.mixer.Sound(r"Efectos de sonido\SFX\11_human_damage_1.wav")
            self.sounds["jump"] = pygame.mixer.Sound(r"Efectos de sonido\SFX\12_human_jump_1.wav")
            self.sounds["enemy_hit"] = pygame.mixer.Sound(r"Efectos de sonido\SFX\26_sword_hit_1.wav")
            
            # Music
            pygame.mixer.music.load(r"Efectos de sonido\Music\Goblins_Dance_(Battle).wav")
            pygame.mixer.music.set_volume(0.3)
        except Exception as e:
            print(f"No se pudieron cargar los sonidos: {e}")

    def play(self, name):
        if name in self.sounds:
            self.sounds[name].set_volume(0.5)
            self.sounds[name].play()

    def play_music(self):
        try:
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

    def draw(self, surface, camera_x=0):
        alpha = int(255 * (self.life / self.max_life))
        s = max(1, int(self.size * (self.life / self.max_life)))
        surf = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
        c = (*self.color[:3], alpha)
        pygame.draw.circle(surf, c, (s, s), s)
        surface.blit(surf, (int(self.x - s - camera_x), int(self.y - s)))

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

    def draw(self, surface, camera_x=0):
        s = int(self.radius * 2)
        surf = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
        # Glow exterior
        pygame.draw.circle(surf, (100, 200, 255, 80), (s, s), int(self.radius * 1.8))
        # Centro
        pygame.draw.circle(surf, (150, 220, 255, 200), (s, s), self.radius)
        # Núcleo blanco
        pygame.draw.circle(surf, (255, 255, 255, 255), (s, s), self.radius // 2)
        surface.blit(surf, (int(self.x - s - camera_x), int(self.y - s)))

class EnemyProjectile:
    """Proyectil enemigo (Poción)."""
    def __init__(self, x, y, vx, vy, frames):
        self.x = float(x)
        self.y = float(y)
        self.vx = vx
        self.vy = vy
        self.frames = frames
        self.frame_index = 0
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

    def draw(self, surface, camera_x=0):
        if not self.frames: return
        idx = int(self.frame_index) % len(self.frames)
        img = self.frames[idx]
        if not self.facing_right:
            img = pygame.transform.flip(img, True, False)
        surface.blit(img, (int(self.x - img.get_width()//2 - camera_x), int(self.y - img.get_height()//2)))

class Arena:
    """Escenario del coliseo con assets reales."""
    def __init__(self):
        self.platforms = []
        self.floor_y = SCREEN_HEIGHT - 100

        self.set_bg("Normal BG")

        # ── Floor tiles ──
        self.floor_tile = load_single_image("Esecenarios/Floor Tiles1.png")
        # Extraer un tile del tileset (primera fila, primer tile ~96x96)
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
        self.platforms.append(pygame.Rect(0, fy, ARENA_WIDTH, SCREEN_HEIGHT - fy + 50))
        # Paredes invisibles
        self.platforms.append(pygame.Rect(-30, 0, 32, SCREEN_HEIGHT))
        self.platforms.append(pygame.Rect(ARENA_WIDTH - 2, 0, 32, SCREEN_HEIGHT))
        
        # Plataformas aleatorias según oleada
        random.seed(wave)
        num_plats = random.randint(3, 6)
        pw, ph = 200, 16
        for _ in range(num_plats):
            x = random.randint(100, ARENA_WIDTH - pw - 100)
            y = fy - random.randint(150, 400)
            self.platforms.append(pygame.Rect(x, y, pw, ph))
        random.seed()

    def draw(self, surface, camera_x=0):
        # ── Parallax backgrounds ──
        for layer in self.bg_layers:
            # Desplazar capas del fondo de acuerdo a la cámara para el efecto parallax
            surface.blit(layer, (-camera_x * 0.2, 0))
            if ARENA_WIDTH > SCREEN_WIDTH:
                surface.blit(layer, (-camera_x * 0.2 + SCREEN_WIDTH, 0))

        # Castillo
        surface.blit(self.castle, (ARENA_WIDTH // 2 - 200 - camera_x * 0.1, 100))

        # ── Estatuas decorativas ──
        if self.angel_statue:
            surface.blit(self.angel_statue, (140 - camera_x, self.floor_y - self.angel_statue.get_height()))
            flipped = pygame.transform.flip(self.angel_statue, True, False)
            surface.blit(flipped, (ARENA_WIDTH - 140 - flipped.get_width() - camera_x,
                                   self.floor_y - flipped.get_height()))

        # ── Antorchas animadas ──
        if self.torch_frames:
            t = pygame.time.get_ticks()
            idx = (t // 120) % len(self.torch_frames)
            torch_img = self.torch_frames[idx]
            # Izquierda
            surface.blit(torch_img, (300 - camera_x, self.floor_y - 230))
            # Derecha
            surface.blit(torch_img, (ARENA_WIDTH - 300 - torch_img.get_width() - camera_x,
                                      self.floor_y - 230))

        # ── Suelo con tiles ──
        tile_w = self.ground_tile.get_width()
        tile_h = self.ground_tile.get_height()
        start_x = -(camera_x % tile_w)
        for x in range(int(start_x), SCREEN_WIDTH + tile_w, tile_w):
            real_x = x + camera_x
            if 0 <= real_x <= ARENA_WIDTH:
                surface.blit(self.ground_tile, (x, self.floor_y))
                # Segunda fila de tiles
                if self.floor_y + tile_h < SCREEN_HEIGHT:
                    surface.blit(self.ground_tile, (x, self.floor_y + tile_h))

        # ── Borde superior del suelo ──
        floor_start = max(0, -camera_x)
        floor_end = min(SCREEN_WIDTH, ARENA_WIDTH - camera_x)
        pygame.draw.line(surface, (100, 80, 60), (floor_start, self.floor_y), (floor_end, self.floor_y), 3)

        # ── Plataformas flotantes ──
        for p in self.platforms:
            if p.height <= 20:  # Solo las flotantes
                px_on_screen = p.x - camera_x
                if px_on_screen + p.width > 0 and px_on_screen < SCREEN_WIDTH:
                    # Dibujar con tiles pequeños
                    for dx in range(0, p.width, tile_w):
                        w = min(tile_w, p.width - dx)
                        sub = self.ground_tile.subsurface((0, 0, min(w, tile_w), min(p.height, tile_h)))
                        surface.blit(sub, (px_on_screen + dx, p.y))
                    # Borde
                    pygame.draw.rect(surface, (120, 100, 80), (px_on_screen, p.y, p.width, p.height), 2)

        # ── Paredes laterales visibles ──
        pygame.draw.rect(surface, (20, 15, 25), (-camera_x - 100, 0, 100, SCREEN_HEIGHT))
        pygame.draw.rect(surface, (20, 15, 25), (ARENA_WIDTH - camera_x, 0, 100, SCREEN_HEIGHT))
        pygame.draw.line(surface, (100, 80, 60), (-camera_x, 0), (-camera_x, SCREEN_HEIGHT), 5)
        pygame.draw.line(surface, (100, 80, 60), (ARENA_WIDTH - camera_x, 0), (ARENA_WIDTH - camera_x, SCREEN_HEIGHT), 5)


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

        # Assets
        self.potion_frames = load_spritesheet("Enemies/Effects/PNGs/Green Potion.png", 32, 32, 0, 2)

        # Sounds
        self.sounds = SoundManager()

        # Vibración
        self.rumble_timer = 0
        self.start_was_pressed = False
        
        self.camera_x = 0

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

    def _reset_game(self):
        self.player = Player(ARENA_WIDTH // 2, -200) # Cae del cielo
        self.enemies = []
        self.particles = []
        self.projectiles = []
        self.enemy_projectiles = []
        self.score = 0
        self.current_wave = 0
        self.game_state = "intro_fall"
        self.sounds.play_music()

    def _start_wave(self):
        self.enemies = []
        if self.current_wave >= len(WAVES):
            self.game_state = "victory"
            self._rumble(1.0, 40)
            return

        # Cambiar el escenario según la oleada
        if self.current_wave < 2:
            self.arena.set_bg("Normal BG")
        elif self.current_wave < 4:
            self.arena.set_bg("Autumn BG")
        else:
            self.arena.set_bg("Winter BG")

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
        
        # Distribuir spawn a lo largo de ARENA_WIDTH
        spawns = [400, 800, 1200, 1600, 2000, 600, 1400, 1800]
        idx = 0

        for _ in range(wave.get("grunts", 0)):
            self.enemies.append(Grunt(spawns[idx % len(spawns)], fy - 50))
            idx += 1
        for _ in range(wave.get("commanders", 0)):
            self.enemies.append(Commander(spawns[idx % len(spawns)], fy - 50))
            idx += 1
        for _ in range(wave.get("guardians", 0)):
            self.enemies.append(Guardian(spawns[idx % len(spawns)], fy - 50))
            idx += 1
        for _ in range(wave.get("potionmasters", 0)):
            self.enemies.append(Potionmaster(spawns[idx % len(spawns)], fy - 50))
            idx += 1
        for _ in range(wave.get("eagles", 0)):
            self.enemies.append(Eagle(spawns[idx % len(spawns)], fy - 300))
            idx += 1

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
                    self.sounds.play("enemy_hit")
                    self.player.attack_hit = True
                    # GANAR MANÁ (SOUL) ESTILO HOLLOW KNIGHT
                    self.player.mana = min(PLAYER_MAX_MANA, self.player.mana + 15)
                    
                    # Partículas de sangre/daño normal
                    self._spawn_particles(enemy.x, enemy.y - enemy.height // 2,
                                          (255, 200, 100), 12)
                    # Partículas azules de alma (Soul) subiendo
                    for _ in range(8):
                        self.particles.append(Particle(enemy.x, enemy.y - enemy.height // 2,
                                                       (150, 220, 255), random.uniform(-2, 2), random.uniform(-4, -1), 30, 3))

                    self._rumble(0.4, 8)
                    if not enemy.alive:
                        self.score += 100
                        self._spawn_particles(enemy.x, enemy.y - enemy.height // 2,
                                              (200, 50, 255), 20)
                        self._rumble(0.8, 15)
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
                if event.type == pygame.JOYBUTTONDOWN:
                    if event.button == JOY_JUMP: input_events["jump"] = True
                    if event.button == JOY_ATTACK: input_events["attack"] = True
                    if event.button == JOY_DASH: input_events["dash"] = True
                    if event.button == JOY_CAST: input_events["cast"] = True
                    if event.button == JOY_HEAL: input_events["heal"] = True
                if event.type == pygame.JOYDEVICEADDED:
                    self._init_joystick()
                if event.type == pygame.JOYDEVICEREMOVED:
                    self.joystick = None

            keys = pygame.key.get_pressed()

            # Reproducir sonido de salto y ataque
            if input_events.get("jump") and (self.player.on_ground or self.player.touching_wall != 0 or self.player.can_double_jump):
                self.sounds.play("jump")
            
            if input_events.get("attack") and not self.player.attacking:
                self.sounds.play("attack")

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
                except Exception:
                    pass
            
            just_pressed_start = start_pressed and not self.start_was_pressed
            self.start_was_pressed = start_pressed

            # ── Estados ──
            if self.game_state == "menu":
                if just_pressed_start:
                    self._reset_game()

            elif self.game_state == "paused":
                if just_pressed_start:
                    self.game_state = "playing"

            elif self.game_state == "intro_fall":
                self.player.update(self.arena.platforms)
                # Partículas de aire cayendo
                self.particles.append(Particle(self.player.x, self.player.y - 20, (200, 200, 200), 0, -2, 10, 2))
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
                if just_pressed_start:
                    self.game_state = "paused"
                    continue

                # Magia / Poder
                if input_events.get("cast") and self.player.mana >= 20:
                    self.player.mana -= 20
                    direction = 1 if self.player.facing_right else -1
                    px = self.player.x + (direction * 30)
                    py = self.player.y - self.player.height // 2
                    self.projectiles.append(Projectile(px, py, direction))
                    self._spawn_particles(px, py, (100, 200, 255), 10)
                    self._rumble(0.3, 5)

                if input_events.get("heal") and self.player.mana >= 30 and self.player.hp < PLAYER_MAX_HP:
                    self.player.mana -= 30
                    self.player.hp += 1
                    self._spawn_particles(self.player.x, self.player.y - 20, (100, 255, 100), 20)
                    self._rumble(0.2, 5)

                self.player.handle_input(keys, joy, input_events)
                self.player.update(self.arena.platforms)

                if self.player.dashing:
                    if self.player.dash_timer == 18: # DURATION
                        self.sounds.play("dash")
                    # Partículas de polvo y estela de velocidad del dash
                    dir_x = -1 if self.player.facing_right else 1
                    # Estela translúcida
                    self.particles.append(Particle(
                        self.player.x + dir_x * 15, self.player.y - 20,
                        (180, 220, 255), dir_x * 2, 0, 15, 4
                    ))
                    # Polvo en los pies
                    self.particles.append(Particle(
                        self.player.x, self.player.y,
                        (150, 150, 150), dir_x * 1, -1, 10, 2
                    ))

                for e in self.enemies:
                    e.update(self.player, self.arena.platforms)
                    if getattr(e, "has_thrown", False) and getattr(e, "attack_hit", False):
                        e.attack_hit = False
                        dir_x = 1 if e.facing_right else -1
                        self.enemy_projectiles.append(EnemyProjectile(e.x, e.y - 40, dir_x * 8, -5, self.potion_frames))

                # Projectiles
                for proj in self.projectiles:
                    proj.update()
                    self.particles.append(Particle(proj.x, proj.y, (100, 200, 255), 0, 0, 10, 2))
                    for e in self.enemies:
                        if e.alive and proj.rect.colliderect(e.rect):
                            if e.take_damage(proj.damage):
                                proj.life = 0 # Destroy projectile
                                self._spawn_particles(e.x, e.y - e.height // 2, (100, 200, 255), 15)
                                if not e.alive:
                                    self.score += 100
                            break
                self.projectiles = [p for p in self.projectiles if p.life > 0]
                
                # Enemy Projectiles
                for proj in self.enemy_projectiles:
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

                self._check_attacks()

                if not self.player.alive:
                    self.game_state = "gameover"
                    self._rumble(1.0, 30)
                elif self.player.i_frames == PLAYER_I_FRAMES - 1:
                    self._rumble(0.7, 12)
                    self._spawn_particles(self.player.x,
                                          self.player.y - self.player.height // 2,
                                          (255, 80, 80), 15)

                self.enemies = [e for e in self.enemies if not e.death_done]

                if len(self.enemies) == 0:
                    self.current_wave += 1
                    self._start_wave()

            elif self.game_state in ("gameover", "victory"):
                if just_pressed_start:
                    self.game_state = "menu"
                    pygame.mixer.music.stop()
                if self.player:
                    self.player.update(self.arena.platforms)

            # Partículas
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
            if self.player:
                target_cx = self.player.x - SCREEN_WIDTH // 2
                self.camera_x += (target_cx - self.camera_x) * 0.1
                if self.camera_x < 0: self.camera_x = 0
                if self.camera_x > ARENA_WIDTH - SCREEN_WIDTH: self.camera_x = ARENA_WIDTH - SCREEN_WIDTH

            # ── DIBUJAR ──
            self.arena.draw(self.screen, self.camera_x)

            for p in self.particles:
                p.draw(self.screen, self.camera_x)
                
            for proj in self.projectiles:
                proj.draw(self.screen, self.camera_x)
                
            for proj in self.enemy_projectiles:
                proj.draw(self.screen, self.camera_x)

            for e in self.enemies:
                e.draw(self.screen, self.camera_x, 0)

            if self.player:
                self.player.draw(self.screen, self.camera_x, 0)

            hp = self.player.hp if self.player else 0
            mana = self.player.mana if self.player else 0
            self.hud.draw(self.screen, hp, PLAYER_MAX_HP, mana, PLAYER_MAX_MANA, self.current_wave, self.score, self.game_state)

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
