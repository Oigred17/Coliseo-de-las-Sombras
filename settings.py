# ── Configuración general del juego ──
import os

import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def resource_path(relative_path):
    """Obtiene la ruta absoluta al recurso, compatible con PyInstaller."""
    return os.path.join(BASE_DIR, relative_path)

SPRITES_DIR = resource_path("Sprites")

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
PLAYER_JUMP_FORCE = -16
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
EAGLE_SPEED = 3.0
EAGLE_DAMAGE = 1
EAGLE_ATTACK_RANGE = 50
EAGLE_DETECT_RANGE = 400

EAGLE_DETECT_RANGE = 400

GHOST_HP = 4
GHOST_SPEED = 2.5
GHOST_DAMAGE = 2
GHOST_ATTACK_RANGE = 50
GHOST_DETECT_RANGE = 400

PIRANHA_HP = 5
PIRANHA_SPEED = 0
PIRANHA_DAMAGE = 2
PIRANHA_ATTACK_RANGE = 400
PIRANHA_DETECT_RANGE = 500

# Oleadas
WAVES = [
    {"grunts": 1, "commanders": 0, "guardians": 0, "potionmasters": 0, "eagles": 1, "ghosts": 0, "piranhas": 0},
    {"grunts": 3, "commanders": 1, "guardians": 1, "potionmasters": 1, "eagles": 1, "ghosts": 1, "piranhas": 0},
    {"boss": "demon_slime"},
    {"grunts": 3, "commanders": 1, "guardians": 1, "potionmasters": 1, "eagles": 2, "ghosts": 2, "piranhas": 1},
    {"grunts": 4, "commanders": 2, "guardians": 2, "potionmasters": 2, "eagles": 2, "ghosts": 2, "piranhas": 2},
    {"boss": "golem"},
    {"grunts": 5, "commanders": 3, "guardians": 3, "potionmasters": 3, "eagles": 3, "ghosts": 3, "piranhas": 3},
    {"grunts": 6, "commanders": 3, "guardians": 3, "potionmasters": 4, "eagles": 4, "ghosts": 4, "piranhas": 4},
    {"boss": "frost_guardian"},
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
KEY_PARRY = pygame.K_u

# Controles mando (Xbox layout)
JOY_JUMP = 0       # A
JOY_ATTACK = 2     # X
JOY_MAGIC = 1      # B (Pulsar)
JOY_HEAL = 1       # B (Mantener)
JOY_SUPER2 = 5     # RB (Nueva Super)
JOY_SUPER = 4      # LB (Súper original)
JOY_DASH_AXIS = 5  # RT (Trigger Derecho)
JOY_RT_THRESHOLD = 0.5
JOY_CROUCH = 7     # Start
JOY_PARRY = 3      # Y
JOY_DEADZONE = 0.25

# Boss configuration
BOSS_HP = 25
BOSS_SPEED = 1.5
BOSS_DAMAGE = 2
BOSS_ATTACK_RANGE = 40
BOSS_DETECT_RANGE = 400
