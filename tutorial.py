import pygame
import random
import math
import time
from settings import *
from enemies import EnemyBase
from spritesheet import load_spritesheet

class TutorialDummy(EnemyBase):
    def __init__(self, x, y, scale=2):
        super().__init__(x, y, 1000, 0, 0, 0, 0, scale)
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
        
    def update(self, player, platforms):
        self._update_animation()
        self.vx = 0
        self.vy += GRAVITY
        # Colisión simple
        self.y += self.vy
        for p in platforms:
            if self.rect.colliderect(p):
                if self.vy > 0:
                    self.y = float(p.top)
                    self.vy = 0

class TutorialManager:
    def __init__(self, game):
        self.game = game
        self.step = 0
        self.steps = [
            {"msg": "¡BIENVENIDO AL ENTRENAMIENTO! Usa A o D para moverte.", "goal": "move"},
            {"msg": "Usa ESPACIO para saltar.", "goal": "jump"},
            {"msg": "Usa RT para hacer un DASH rápido.", "goal": "dash"},
            {"msg": "Usa J para atacar al muñeco de práctica.", "goal": "attack"},
            {"msg": "Usa B (pulsación corta) para lanzar MAGIA.", "goal": "magic"},
            {"msg": "Mantén presionado B para CURARTE (usa maná).", "goal": "heal"},
            {"msg": "Usa Y justo cuando el proyectil te vaya a dar para hacer PARRY.", "goal": "parry"},
            {"msg": "Usa LB para activar tu SUPER: ONDA DE DRAGÓN (requiere 100% energía).", "goal": "super1"},
            {"msg": "Usa RB para activar tu SUPER: EXPLOSIÓN ASTRAL (requiere 50% energía).", "goal": "super2"},
            {"msg": "¡EXCELENTE! Entra en el portal para terminar.", "goal": "portal"},
        ]
        self.dummy = None
        self.completed = False
        self.move_dist = 0
        self.jump_count = 0
        self.dash_count = 0
        self.attack_hits = 0
        self.magic_hits = 0
        self.heal_amount = 0
        self.parry_count = 0
        self.super1_count = 0
        self.super2_count = 0
        
    def get_msg(self, step_idx):
        msg_data = self.steps[step_idx]
        is_joy = self.game.joystick is not None
        if is_joy:
            m = msg_data["msg"]
            m = m.replace("A o D", "Stick Izquierdo")
            m = m.replace("ESPACIO", "Botón A")
            m = m.replace("RT", "Gatillo RT")
            m = m.replace("J", "Botón X")
            m = m.replace("B (pulsación corta)", "Botón B")
            m = m.replace("B para CURARTE", "B (MANTENER) para CURARTE")
            m = m.replace("Y", "Botón Y")
            m = m.replace("LB", "Botón LB")
            m = m.replace("RB", "Botón RB")
            return m
        return msg_data["msg"]

    def start(self):
        self.step = 0
        self.game.player.hp = PLAYER_MAX_HP
        self.game.player.mana = PLAYER_MAX_MANA
        self.game.player.super_meter = 100
        self.game.enemies = []
        self.dummy = TutorialDummy(ARENA_WIDTH // 2 + 200, self.game.arena.floor_y)
        self.game.enemies.append(self.dummy)
        self.game.hud.show_message(self.get_msg(0), 300)

    def update(self, input_events):
        if self.step >= len(self.steps):
            return

        current = self.steps[self.step]
        goal = current["goal"]
        
        # Lógica de progreso
        if goal == "move":
            if abs(self.game.player.vx) > 1:
                self.move_dist += 1
                if self.move_dist > 120: self.next_step()
        
        elif goal == "jump":
            if input_events.get("jump") and self.game.player.on_ground:
                self.jump_count += 1
                if self.jump_count >= 2: self.next_step()
                
        elif goal == "dash":
            if input_events.get("dash"):
                self.dash_count += 1
                if self.dash_count >= 2: self.next_step()
                
        elif goal == "attack":
            if self.game.player.attack_hit:
                self.attack_hits += 1
                if self.attack_hits >= 3: self.next_step()
                
        elif goal == "magic":
            # Detectar si un proyectil golpeó al dummy
            for p in self.game.projectiles:
                if p.rect.colliderect(self.dummy.rect):
                    self.magic_hits += 1
                    if self.magic_hits >= 2: self.next_step()
                    
        elif goal == "heal":
            if self.game.player.hp < PLAYER_MAX_HP - 10:
                pass # Esperar a que reciba daño? No, mejor solo detectar curación
            if self.game.player.healing_glow:
                self.heal_amount += 1
                if self.heal_amount >= 60: self.next_step()
                
        elif goal == "parry":
            # Spawn un proyectil lento hacia el jugador
            if not any(isinstance(p, TutorialProjectile) for p in self.game.enemy_projectiles):
                self.game.enemy_projectiles.append(TutorialProjectile(self.dummy.x - 100, self.dummy.y - 40, -1))
            
            # El parry se detecta en main.py, aquí solo chequeamos si parry_count subió
            if getattr(self.game, "_last_parry_count", 0) < self.game.hud.score: # Usamos score como proxy o algo
                pass
            # Mejor: chequear si hubo un parry exitoso en main.py
            if getattr(self.game, "tutorial_parry_success", False):
                self.next_step()
                self.game.tutorial_parry_success = False

        elif goal == "super1":
            if input_events.get("super") and self.game.player.super_meter >= 100:
                self.next_step()

        elif goal == "super2":
            if input_events.get("super2") and self.game.player.super_meter >= 50:
                self.next_step()
                
        elif goal == "portal":
            if not self.game.portal:
                from main import Portal
                self.game.portal = Portal(ARENA_WIDTH // 2, self.game.arena.floor_y - 60)

    def next_step(self):
        self.step += 1
        if self.step < len(self.steps):
            self.game.hud.show_message(self.get_msg(self.step), 300)
            # Reset player stats to ensure they can finish
            self.game.player.mana = PLAYER_MAX_MANA
            self.game.player.super_meter = 100
        else:
            self.completed = True

class TutorialProjectile:
    def __init__(self, x, y, direction):
        self.x, self.y = x, y
        self.vx = direction * 4
        self.radius = 8
        self.alive = True
    @property
    def rect(self): return pygame.Rect(self.x-8, self.y-8, 16, 16)
    @property
    def attack_rect(self): return self.rect
    def update(self):
        self.x += self.vx
        if self.x < 0 or self.x > ARENA_WIDTH: self.alive = False
    def take_damage(self, dmg, parry=False):
        if parry: self.alive = False
    def draw(self, surface, cx, cy):
        pygame.draw.circle(surface, (255, 50, 50), (int(self.x-cx), int(self.y-cy)), self.radius)
