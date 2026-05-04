# ── Clase del jugador ──
# Cada frame del player es 120x80 px en el spritesheet original
import os
import pygame
from settings import *
from spritesheet import load_spritesheet

# Tamaño real de frame del Player (verificado con los PNGs)
PF_W = 120
PF_H = 80


class Player:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.facing_right = True
        self.on_ground = False
        self.healing_glow = False
        self.healing_timer = 0
        self.hp = PLAYER_MAX_HP
        self.mana = PLAYER_MAX_MANA
        self.super_meter = 0.0 # Medidor de Super
        self.alive = True
        self.can_double_jump = False
        self.touching_wall = 0

        # Dash
        self.dashing = False
        self.dash_timer = 0
        self.dash_cooldown = 0

        # Ataque
        self.attacking = False
        self.attack_timer = 0
        self.attack_hit = False
        
        # Sistema de Combos
        self.combo_count = 0
        self.combo_timer = 0
        self.combo_window = 40  # Frames entre ataques para contar como combo

        # Parry
        self.parrying = False
        self.parry_timer = 0
        self.parry_cooldown = 0
        self.can_parry = True

        # Invencibilidad
        self.i_frames = 0

        # Animaciones - frame size 120x80, auto-detect frame count
        S = PLAYER_SCALE
        
        death_frames = load_spritesheet("Player/_Death.png", PF_W, PF_H, 0, S)
        self.animations = {
            "idle":   load_spritesheet("Player/_Idle.png", PF_W, PF_H, 0, S),
            "run":    load_spritesheet("Player/_Run.png", PF_W, PF_H, 0, S),
            "jump":   load_spritesheet("Player/_Jump.png", PF_W, PF_H, 0, S),
            "fall":   load_spritesheet("Player/_Fall.png", PF_W, PF_H, 0, S),
            "attack": load_spritesheet("Player/_Attack.png", PF_W, PF_H, 0, S),
            "dash":   load_spritesheet("Player/_Dash.png", PF_W, PF_H, 0, S),
            "hit":    load_spritesheet("Player/_Hit.png", PF_W, PF_H, 0, S),
            "death":  death_frames,
            "revive": death_frames,  # Revive usa los frames de death en reversa
            "wall":   load_spritesheet("Player/_WallSlide.png", PF_W, PF_H, 0, S),
            "crouch": load_spritesheet("Player/_CrouchAll.png", PF_W, PF_H, 0, S),
            "roll":   load_spritesheet("Player/_Roll.png", PF_W, PF_H, 0, S),
            "parry":  load_spritesheet("Player/_Attack.png", PF_W, PF_H, 0, S),
        }
        self.state = "idle"
        self.frame_index = 0.0
        self.anim_speed = 0.15

        # Hitbox (mucho más pequeña que el sprite, centrada en el personaje)
        self.width = 28 * S
        self.height = 36 * S

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
        """Rectángulo del ataque (delante del jugador)."""
        r = self.rect
        w = PLAYER_ATTACK_RANGE * PLAYER_SCALE
        if self.facing_right:
            return pygame.Rect(r.right, r.y + 10, w, r.height - 20)
        else:
            return pygame.Rect(r.left - w, r.y + 10, w, r.height - 20)

    @property
    def parry_rect(self):
        """Rectángulo del parry (delante del jugador, más pequeño)."""
        r = self.rect
        w = 50 * PLAYER_SCALE
        h = r.height
        if self.facing_right:
            return pygame.Rect(r.right - 10, r.y, w, h)
        else:
            return pygame.Rect(r.left - w + 10, r.y, w, h)

    # ── Entrada ──
    def handle_input(self, keys, joy, events):
        if not self.alive:
            return

        move = 0
        if keys[KEY_LEFT]:
            move = -1
        if keys[KEY_RIGHT]:
            move = 1

        if joy:
            try:
                axis = joy.get_axis(0)
                if abs(axis) > JOY_DEADZONE:
                    move = 1 if axis > 0 else -1
            except Exception:
                pass

        if not self.dashing:
            if self.attacking and self.on_ground:
                target_vx = 0
            else:
                target_vx = move * PLAYER_SPEED
            self.vx += (target_vx - self.vx) * 0.4
            if abs(self.vx) < 0.1:
                self.vx = 0
            if move != 0 and not self.attacking:
                self.facing_right = move > 0

        if self.on_ground:
            self.can_double_jump = True

        # Salto
        if events.get("jump"):
            if self.on_ground and not self.dashing:
                self.vy = PLAYER_JUMP_FORCE
                self.on_ground = False
            elif self.touching_wall != 0 and not self.on_ground:
                self.vy = PLAYER_JUMP_FORCE
                self.vx = -self.touching_wall * PLAYER_SPEED * 1.5
                self.facing_right = (self.touching_wall == -1)
                self.can_double_jump = True
            elif self.can_double_jump and not self.dashing:
                self.vy = PLAYER_JUMP_FORCE
                self.can_double_jump = False

        # Ataque
        if events.get("attack") and not self.attacking and not self.dashing:
            self.attacking = True
            self.attack_timer = 0
            self.attack_hit = False
            self.frame_index = 0

        # Dash
        if events.get("dash") and not self.dashing and self.dash_cooldown <= 0 and not self.attacking:
            self.dashing = True
            self.dash_timer = PLAYER_DASH_DURATION
            self.dash_cooldown = PLAYER_DASH_COOLDOWN
            self.i_frames = max(self.i_frames, PLAYER_DASH_DURATION)
            direction = 1 if self.facing_right else -1
            self.vx = direction * PLAYER_DASH_SPEED
            self.vy = 0

        # Parry (tecla especial)
        if events.get("parry") and self.parry_cooldown <= 0 and not self.attacking and not self.dashing:
            self.parrying = True
            self.parry_timer = 15
            self.parry_cooldown = 60
            self.i_frames = 15

    # ── Actualización ──
    def update(self, platforms):
        if not self.alive:
            self._update_animation()
            return

        if self.i_frames > 0:
            self.i_frames -= 1
        
        # Actualizar timer de combo
        if self.combo_timer > 0:
            self.combo_timer -= 1
        else:
            self.combo_count = 0  # Resetear combo si pasa mucho tiempo
        
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        if self.parry_cooldown > 0:
            self.parry_cooldown -= 1

        # Dash
        if self.dashing:
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                self.dashing = False
                self.vx = 0

        # Parry
        if self.parrying:
            self.parry_timer -= 1
            if self.parry_timer <= 0:
                self.parrying = False

        # Ataque
        if self.attacking:
            self.attack_timer += 1
            atk_frames = len(self.animations["attack"])
            if self.attack_timer >= atk_frames / self.anim_speed:
                self.attacking = False

        # Gravedad / Wall Slide
        if not self.dashing:
            if self.touching_wall != 0 and self.vy > 0:
                self.vy += GRAVITY * 0.2
                if self.vy > 4:
                    self.vy = 4
            else:
                self.vy += GRAVITY
                if self.vy > MAX_FALL_SPEED:
                    self.vy = MAX_FALL_SPEED

        # Mover horizontalmente
        self.x += self.vx
        
        self.touching_wall = 0
        r = self.rect
        for p in platforms:
            if r.colliderect(p):
                if p.height > 20: # Es una pared o suelo grueso
                    if self.vx > 0:
                        self.x = float(p.left - self.width // 2)
                        self.vx = 0
                        self.touching_wall = 1
                    elif self.vx < 0:
                        self.x = float(p.right + self.width // 2)
                        self.vx = 0
                        self.touching_wall = -1

        # Mover verticalmente
        self.y += self.vy

        # Colisión vertical
        r = self.rect
        for p in platforms:
            if r.colliderect(p):
                if self.vy > 0 and r.bottom - self.vy <= p.top + 20:
                    self.y = float(p.top)
                    self.vy = 0
                elif self.vy < 0 and p.height > 20: # Solo bloquear la cabeza en techos gruesos
                    self.y = float(p.bottom + self.height)
                    self.vy = 0

        # Comprobar si está en el suelo
        self.on_ground = False
        if self.vy >= 0:
            r_down = self.rect.copy()
            r_down.y += 2
            for p in platforms:
                if r_down.colliderect(p):
                    self.on_ground = True
                    break

        # Limitar a la pantalla
        if self.x < self.width // 2 + 10:
            self.x = self.width // 2 + 10
        if self.x > ARENA_WIDTH - self.width // 2 - 10:
            self.x = ARENA_WIDTH - self.width // 2 - 10

        self._update_animation()

    def _update_animation(self):
        if not self.alive:
            new_state = "death"
        elif self.state == "revive":
            new_state = "revive"
        elif self.parrying:
            new_state = "parry"
        elif self.attacking:
            new_state = "attack"
        elif self.dashing:
            new_state = "dash"
        elif self.i_frames > 0 and not self.dashing:
            new_state = "hit"
        elif self.touching_wall != 0 and not self.on_ground and self.vy > 0:
            new_state = "wall"
        elif not self.on_ground:
            new_state = "jump" if self.vy < 0 else "fall"
        elif abs(self.vx) > 0.5:
            new_state = "run"
        else:
            new_state = "idle"

        if new_state != self.state:
            self.state = new_state
            self.frame_index = 0.0

        frames = self.animations[self.state]
        self.frame_index += self.anim_speed
        
        if self.state == "death":
            if self.frame_index >= len(frames):
                self.frame_index = len(frames) - 1
        elif self.state == "revive":
            death_len = len(self.animations["death"])
            self.frame_index -= self.anim_speed * 2
            if self.frame_index <= 0:
                self.frame_index = 0
                self.state = "idle"
        else:
            if self.frame_index >= len(frames):
                self.frame_index = 0.0

    def take_damage(self, dmg, source_x):
        if self.i_frames > 0 or not self.alive:
            return False
        self.hp -= dmg
        self.i_frames = PLAYER_I_FRAMES
        kb_dir = -1 if source_x > self.x else 1
        self.vx = kb_dir * PLAYER_KNOCKBACK
        self.vy = -6
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            self.state = "death"
            self.frame_index = 0
        return True

    def draw(self, surface, camera_x=0, camera_y=0):
        frames = self.animations[self.state]
        idx = int(self.frame_index) % len(frames)
        img = frames[idx]

        if not self.facing_right:
            img = pygame.transform.flip(img, True, False)

        # Parpadeo de invencibilidad o desvanecimiento
        if hasattr(self, 'alpha') and self.alpha < 255:
            img = img.copy()
            img.set_alpha(self.alpha)
        elif self.i_frames > 0 and self.alive:
            if (self.i_frames // 4) % 2 == 0:
                img = img.copy()
                img.set_alpha(100)

        # Centrar sprite en la posición del personaje
        draw_x = self.x - img.get_width() // 2 - camera_x
        draw_y = self.y - img.get_height() - camera_y
        
        # Efecto de resplandor de curación
        if self.healing_glow:
            import math
            t = pygame.time.get_ticks()
            # Pulso de luz verde
            glow_alpha = int(100 + 100 * math.sin(t / 100.0))
            glow_surf = img.copy()
            glow_surf.fill((100, 255, 100, glow_alpha), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(glow_surf, (draw_x, draw_y), special_flags=pygame.BLEND_RGB_ADD)

        surface.blit(img, (draw_x, draw_y))
