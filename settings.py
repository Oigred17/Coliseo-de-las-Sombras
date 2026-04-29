# ── Configuración general del juego ──
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SPRITES_DIR = os.path.join(BASE_DIR, "Sprites")

# Pantalla
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
ARENA_WIDTH = 1800  # Escenario un poco más pequeño
FPS = 60
TITLE = "Coliseo de las Sombras"

# Física
GRAVITY = 0.8
MAX_FALL_SPEED = 15
TILE_SIZE = 48

# Colores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (200, 50, 50)
DARK_BG = (15, 10, 25)
ARENA_FLOOR_COLOR = (40, 30, 50)
ARENA_WALL_COLOR = (55, 40, 70)
ARENA_ACCENT = (80, 50, 110)
HUD_BG = (20, 15, 30, 180)

# Jugador
PLAYER_SPEED = 6.0
PLAYER_JUMP_FORCE = -15
PLAYER_DASH_SPEED = 14
PLAYER_DASH_DURATION = 18
PLAYER_DASH_COOLDOWN = 40
PLAYER_MAX_HP = 5
PLAYER_MAX_MANA = 100
PLAYER_ATTACK_RANGE = 60
PLAYER_ATTACK_DAMAGE = 1
PLAYER_I_FRAMES = 60
PLAYER_KNOCKBACK = 8
PLAYER_SCALE = 3

# Enemigos
ENEMY_SCALE = 2.5

GRUNT_HP = 3
GRUNT_SPEED = 2
GRUNT_DAMAGE = 1
GRUNT_ATTACK_RANGE = 45
GRUNT_DETECT_RANGE = 300

COMMANDER_HP = 5
COMMANDER_SPEED = 2.5
COMMANDER_DAMAGE = 2
COMMANDER_ATTACK_RANGE = 55
COMMANDER_DETECT_RANGE = 350

GUARDIAN_HP = 4
GUARDIAN_SPEED = 1.5
GUARDIAN_DAMAGE = 1
GUARDIAN_ATTACK_RANGE = 50
GUARDIAN_DETECT_RANGE = 280

POTIONMASTER_HP = 3
POTIONMASTER_SPEED = 2
POTIONMASTER_DAMAGE = 2
POTIONMASTER_ATTACK_RANGE = 200
POTIONMASTER_DETECT_RANGE = 400

EAGLE_HP = 2
EAGLE_SPEED = 3.5
EAGLE_DAMAGE = 1
EAGLE_ATTACK_RANGE = 50
EAGLE_DETECT_RANGE = 400

# Oleadas
WAVES = [
    {"grunts": 2, "commanders": 0, "guardians": 0, "potionmasters": 1, "eagles": 1},
    {"grunts": 2, "commanders": 1, "guardians": 0, "potionmasters": 1, "eagles": 1},
    {"grunts": 2, "commanders": 1, "guardians": 1, "potionmasters": 2, "eagles": 2},
    {"grunts": 3, "commanders": 2, "guardians": 1, "potionmasters": 2, "eagles": 2},
    {"grunts": 4, "commanders": 2, "guardians": 2, "potionmasters": 3, "eagles": 3},
]

# Controles teclado
import pygame
KEY_LEFT = pygame.K_a
KEY_RIGHT = pygame.K_d
KEY_JUMP = pygame.K_SPACE
KEY_ATTACK = pygame.K_j
KEY_DASH = pygame.K_k
KEY_CAST = pygame.K_l
KEY_HEAL = pygame.K_h
KEY_CROUCH = pygame.K_s

# Controles mando (Xbox layout)
JOY_JUMP = 0       # A
JOY_ATTACK = 2     # X
JOY_DASH = 1       # B
JOY_CAST = 5       # RB
JOY_HEAL = 4       # LB
JOY_CROUCH = 3     # Y
JOY_DEADZONE = 0.25
